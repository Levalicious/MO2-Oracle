from plugin_oracle.util.render.metro.color import palette
from plugin_oracle.util.render.metro.plot import AbstractPlot, AbstractColumn
import math
import re
from dataclasses import dataclass
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QPainterPath, QPainter
from PyQt6.QtCore import Qt, QPointF

_XY = tuple[float, float]

@dataclass
class MetroConfig:
    """
    Styling options for the metro style.
    """

    scale: float = 10.0
    "The size of a single cell."

    node_radius: float = 6.0
    "The size of a node."

    node_fill: str | None = None
    "Optional. The fill color of the node. Colors will be assigned automatically if unspecified."

    node_stroke: str = "white"
    "The border color of a node"

    node_stroke_width: float = 2.0
    "The border width of a node"

    edge_stroke_width: float = 2.0
    "The line width of an edge"

    label_font_family: str = "sans-serif"
    "The font family of the label"

    label_font_size: str | float = "inherit"
    "The font family of the label"

    label_arrow_stroke: str = "lightgrey"
    "The line color for the line from the label to the node"

    label_arrow_dash_array: str = "2"
    "The dashing style for the line from the label to the node"

    arc_radius: float = 15.0
    "The radius of an input arc"

    minimal_width: float = 500
    "The minimal width of the view box"

@dataclass
class MetroNode:
    id: str
    pos: _XY
    radius: float
    fill: str | tuple[int, int, int]
    stroke: str
    stroke_width: float
    label: str
    color_index: int

@dataclass
class MetroHLineBase:
    a: _XY
    b: _XY
    color: int

@dataclass
class MetroEdge(MetroHLineBase):
    pass

@dataclass
class MetroArc(MetroHLineBase):
    radius: float
    clockwise: bool

MetroHLine = MetroEdge  # For clarity, normal hlines are MetroEdge

@dataclass
class MetroLabel:
    text: str
    pos: _XY
    font_family: str
    font_size: str | float

def _arc(
    a: _XY,
    b: _XY,
    radius: float,
    clockwise: bool = True,
    color: int = 0
) -> MetroArc:
    """
    Create a MetroArc object representing an arc from a to b with the given radius and direction.
    This replaces the SVG arc path with a data structure suitable for later QPainter rendering.
    Args:
        a: Start point (x, y)
        b: End point (x, y)
        radius: Arc radius
        clockwise: Arc direction
        color: Color index
    Returns:
        MetroArc instance
    """
    return MetroArc(a=a, b=b, radius=radius, clockwise=clockwise, color=color)

class MetroRender:
    @staticmethod
    def from_edgelist_and_labels(
        config: MetroConfig,
        edgelist: list[tuple[bytes, bytes]],
        label_dict: dict[bytes, str]
    ) -> "MetroRender":
        succ: dict[bytes, list[bytes]] = {}
        pred: dict[bytes, list[bytes]] = {}
        for a, b in edgelist:
            succ.setdefault(a, []).append(b)
            pred.setdefault(b, []).append(a)
        in_deg: dict[bytes, int] = {n: 0 for n in label_dict}
        for b in pred:
            in_deg[b] = len(pred[b])
        queue: list[bytes] = [n for n in label_dict if in_deg[n] == 0]
        order: list[bytes] = []
        while queue:
            n = queue.pop(0)
            order.append(n)
            for m in succ.get(n, []):
                in_deg[m] -= 1
                if in_deg[m] == 0:
                    queue.append(m)
        plot: AbstractPlot[bytes] = AbstractPlot[bytes]()
        for nd in order:
            row = plot.add_row(label_dict[nd])
            for p in pred.get(nd, []):
                row.add_input(p)
            row.add_node(nd, len(succ.get(nd, [])))
        return MetroRender(config, plot.colors, plot, -plot.columns.start)

    def __init__(
        self,
        config: MetroConfig,
        colors: int,
        graph: AbstractPlot[bytes] | None = None,
        shift: int = 0
    ) -> None:
        self._top: float = math.inf
        self._left: float = math.inf
        self._bottom: float = -math.inf
        self._right: float = -math.inf
        self.config: MetroConfig = config
        self.shift: int = shift
        self.colors: list[tuple[int, int, int]] = palette(colors)
        self.nodes: list[MetroNode] = []  # Store node drawing info
        self.vlines: list[MetroEdge] = []
        self.hline_borders: list[MetroEdge] = []
        self.hlines: list[MetroEdge | MetroArc] = []
        self.background: list[MetroEdge] = []  # For label arrows and similar background lines
        self.labels: list[MetroLabel] = []     # For label text info
        if graph is not None:
            self._populate_from_graph(graph)
            self.graph: AbstractPlot[bytes] = graph
        else:
            self.graph = AbstractPlot[bytes]()
            
    def box(self) -> tuple[float, float, float, float]:
        return (
            self._top - self.config.scale,
            self._left - self.config.scale,
            self._bottom + self.config.scale,
            max(self.config.minimal_width, self._right * 2),
        )
    
    def coord(self, xy: tuple[int, int], dxy: _XY = (0.0, 0.0)) -> _XY:
        x = self.config.scale * (xy[0] + self.shift) * 2 + self.config.arc_radius * (
            dxy[0] + 1
        )
        y = self.config.scale * xy[1] * 2 + self.config.arc_radius * (dxy[1] + 1)
        self._top = min(y, self._top)
        self._left = min(x, self._left)
        self._bottom = max(y, self._bottom)
        self._right = max(x, self._right)
        return (x, y)
    
    def top(self, xy: tuple[int, int]) -> _XY:
        return self.coord(xy, (0, -1))

    def right(self, xy: tuple[int, int]) -> _XY:
        return self.coord(xy, (1, 0))

    def left(self, xy: tuple[int, int]) -> _XY:
        return self.coord(xy, (-1, 0))

    def place_node(self, at: tuple[int, int], color: int, label: str) -> None:
        """
        Place a node on the plot. Stores node info for later rendering.
        Args:
            at:    The (column, row) coordinate of the node
            color: The color number to use for this node
            label: The label of the node
        """
        node_id = "N" + re.sub(r"[^0-9a-zA-Z_-]+", "", label)
        node = MetroNode(
            id=node_id,
            pos=self.coord(at),
            radius=self.config.node_radius,
            fill=self.config.node_fill or self.colors[color],
            stroke=self.config.node_stroke,
            stroke_width=self.config.node_stroke_width,
            label=label,
            color_index=color
        )
        self.nodes.append(node)
    
    def _place_edge(self, group: list[MetroEdge | MetroArc] | list[MetroEdge], a: _XY, b: _XY, color: int) -> None:
        """
        Store edge info for later rendering, using the provided group directly.
        Args:
            group: The group list to append to (e.g. self.hlines, self.vlines, self.hline_borders)
            a:     Start coordinate
            b:     End coordinate
            color: Color index
        """
        edge = MetroEdge(a=a, b=b, color=color)
        group.append(edge)

    def _place_hline_border(self, a: _XY, b: _XY) -> None:
        """
        Store hline border info for later rendering, matching the original metro.py API.
        Args:
            a:     Start coordinate
            b:     End coordinate
        """
        edge = MetroEdge(a=a, b=b, color=-1)
        self.hline_borders.append(edge)
    
    def place_left_hline(
        self, left: tuple[int, int], right: tuple[int, int], color: int
    ) -> None:
        a, b = self.right(left), self.coord(right)
        self._place_hline_border(a, b)
        self._place_edge(self.hlines, a, b, color)
    
    def place_right_hline(
        self, left: tuple[int, int], right: tuple[int, int], color: int
    ) -> None:
        a, b = self.coord(left), self.left(right)
        self._place_hline_border(a, b)
        self._place_edge(self.hlines, a, b, color)
    
    def place_vline_arc(
        self, top: tuple[int, int], bottom: tuple[int, int], color: int
    ) -> None:
        self._place_edge(self.vlines, self.coord(top), self.top(bottom), color)

    def place_vline_node(
        self, top: tuple[int, int], bottom: tuple[int, int], color: int
    ) -> None:
        self._place_edge(self.vlines, self.coord(top), self.coord(bottom), color)

    def place_left_arc(self, at: tuple[int, int], color: int) -> None:
        center = self.coord(at)
        a = (center[0], center[1] - self.config.arc_radius)
        b = (center[0] - self.config.arc_radius, center[1])
        self.hlines.append(
            _arc(
                a,
                b,
                self.config.arc_radius,
                clockwise=True,
                color=color
            )
        )

    def place_right_arc(self, at: tuple[int, int], color: int) -> None:
        center = self.coord(at)
        a = (center[0], center[1] - self.config.arc_radius)
        b = (center[0] + self.config.arc_radius, center[1])
        self.hlines.append(
            _arc(
                a,
                b,
                self.config.arc_radius,
                clockwise=False,
                color=color
            )
        )

    def place_label(
        self, nodepos: tuple[int, int], at: tuple[int, int], label: str
    ) -> None:
        label_obj = MetroLabel(
            text=label,
            pos=self.coord(at),
            font_family=self.config.label_font_family,
            font_size=self.config.label_font_size
        )
        self.labels.append(label_obj)
        arrow = MetroEdge(
            a=self.right(nodepos),
            b=self.coord(at, (-0.4, 0.0)),
            color=-2  # Use a special color index for label arrows if needed
        )
        self.background.append(arrow)

    def render(self, painter: QPainter, scale: float = 1.0, offset_x: float = 0.0, offset_y: float = 0.0) -> None:
        # Apply translation and scaling
        painter.save()
        painter.translate(offset_x, offset_y)
        painter.scale(scale, scale)

        # Draw background lines (label arrows, etc.)
        for edge in self.background:
            color = (128, 128, 128)  # Default for label arrows
            painter.setPen(self._make_pen(color, 1.0, dash=True))
            painter.drawLine(int(round(edge.a[0])), int(round(edge.a[1])), int(round(edge.b[0])), int(round(edge.b[1])))
        
        # Draw vlines
        for edge in self.vlines:
            color = self.colors[edge.color] if edge.color >= 0 else (128,128,128)
            painter.setPen(self._make_pen(color, self.config.edge_stroke_width))
            painter.drawLine(int(round(edge.a[0])), int(round(edge.a[1])), int(round(edge.b[0])), int(round(edge.b[1])))
        
        # Draw hline borders
        for edge in self.hline_borders:
            painter.setPen(self._make_pen((255,255,255), self.config.edge_stroke_width + 2 * min(self.config.edge_stroke_width, self.config.node_stroke_width)))
            painter.drawLine(int(round(edge.a[0])), int(round(edge.a[1])), int(round(edge.b[0])), int(round(edge.b[1])))

        # Draw hlines (edges and arcs)
        for h in self.hlines:
            if isinstance(h, MetroEdge):
                color = self.colors[h.color] if h.color >= 0 else (128,128,128)
                painter.setPen(self._make_pen(color, self.config.edge_stroke_width))
                painter.drawLine(int(round(h.a[0])), int(round(h.a[1])), int(round(h.b[0])), int(round(h.b[1])))
            else:  # MetroArc
                color = self.colors[h.color] if h.color >= 0 else (128,128,128)
                painter.setPen(self._make_pen(color, self.config.edge_stroke_width))
                self._draw_arc(painter, h)

        # Draw nodes
        for node in self.nodes:
            color = node.fill if isinstance(node.fill, tuple) else (128,128,128)
            painter.setPen(self._make_pen(node.stroke, node.stroke_width))
            painter.setBrush(self._make_brush(color))
            painter.drawEllipse(int(round(node.pos[0] - node.radius)), int(round(node.pos[1] - node.radius)), int(round(node.radius*2)), int(round(node.radius*2)))

        # Draw labels
        for label in self.labels:
            painter.setPen(self._make_pen((0,0,0), 1.0))
            painter.setFont(self._make_font(label.font_family, label.font_size))
            off = painter.fontInfo().pixelSize() / 4
            painter.drawText(int(round(label.pos[0])), int(round(label.pos[1] + off)), label.text)

        painter.restore()

    # Helper methods for QPainter setup
    def _make_pen(self, color: str | tuple[int, int, int], width: float, dash: bool = False) -> QPen:
        if isinstance(color, str):
            qcolor = QColor(color)
        else:
            qcolor = QColor(*color)
        pen = QPen(qcolor)
        pen.setWidthF(width)
        if dash:
            pen.setStyle(Qt.PenStyle.DashLine)
        return pen

    def _make_brush(self, color: str | tuple[int, int, int]) -> QBrush:
        if isinstance(color, str):
            return QBrush(QColor(color))
        return QBrush(QColor(*color))

    def _make_font(self, family: str, size: str | float) -> QFont:
        font = QFont()
        font.setFamily(family)
        if isinstance(size, (int, float)):
            font.setPointSizeF(float(size))
        return font

    def _draw_arc(self, painter: QPainter, arc: MetroArc) -> None:
        x0, y0 = arc.a
        x1, y1 = arc.b
        dx = x1 - x0
        dy = y1 - y0
        d = math.hypot(dx, dy)
        if d == 0 or arc.radius == 0:
            return  # Degenerate
        if d > 2 * abs(arc.radius):
            # Impossible arc, fallback to line
            painter.drawLine(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1)))
            return
        # Midpoint
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        # Distance from midpoint to center
        h = math.sqrt(abs(arc.radius**2 - (d/2)**2))
        # Perpendicular vector
        perp_dx = -dy / d
        perp_dy = dx / d
        if arc.clockwise:
            cx = mx + h * perp_dx
            cy = my + h * perp_dy
        else:
            cx = mx - h * perp_dx
            cy = my - h * perp_dy
        # Angles
        angle0 = math.degrees(math.atan2(y0 - cy, x0 - cx))
        angle1 = math.degrees(math.atan2(y1 - cy, x1 - cx))
        # Compute span
        if not arc.clockwise:
            span = (angle0 - angle1)
        else:
            span = (angle0 - angle1)
        rect = (cx - arc.radius, cy - arc.radius, 2 * arc.radius, 2 * arc.radius)
        path = QPainterPath(QPointF(x0, y0))
        path.arcTo(*rect, angle0, span)
        painter.drawPath(path)

    def _populate_from_graph(self, plot: AbstractPlot[bytes]) -> None:
        for row in plot.rows:
            last_col: int = 0
            arcs: list[AbstractColumn[bytes]] = []
            nodepos: tuple[int, int] = (0, 0)
            node_pos: int = 1
            for col in row:
                last_col = col.column
                curpos: tuple[int, int] = (col.column, row.row)
                if col.is_node:
                    nodepos = curpos
                    self.place_node(curpos, col.color, row.label)
                    if len(arcs) != 0:
                        self.place_left_hline((arcs[0].column, row.row), curpos, arcs[0].color)
                        arcs = []
                    arcs.append(col)
                    node_pos = 0
                if col.is_input:
                    if node_pos < 0:
                        arcs.append(col)
                        self.place_left_arc(curpos, col.color)
                        if col.is_last:
                            self.place_vline_arc((col.column, col.start_row.row), curpos, col.start_row.columns[col.column].color)
                    elif node_pos == 0:
                        self.place_vline_node((col.column, col.start_row.row), curpos, col.start_row.columns[col.column].color)
                    else:
                        arcs.append(col)
                        self.place_right_arc(curpos, col.color)
                        if col.is_last:
                            self.place_vline_arc((col.column, col.start_row.row), curpos, col.start_row.columns[col.column].color)
                if col.is_node:
                    node_pos = -1
            if len(arcs) >= 2:
                self.place_right_hline((arcs[0].column, row.row), (arcs[-1].column, row.row), arcs[-1].color)
            self.place_label(nodepos, (last_col + 1, row.row), row.label)

