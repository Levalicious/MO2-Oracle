from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QMouseEvent, QPaintEvent, QWheelEvent, QPainter
from PyQt6.QtWidgets import QWidget, QTabWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
from typing import Callable

from plugin_oracle.base.oracle.oracle import Oracle
from plugin_oracle.util.ml.graph import random_toposort
from plugin_oracle.util.render.metro import MetroRender, MetroConfig

class OracleWidget(QWidget):
    def __init__(self, oracle: Oracle, samplers: list[Callable[[bool], None]], reporter: Callable[[], str], permutation: Callable[[], list[bytes]]) -> None:
        super().__init__()
        self.oracle: Oracle = oracle
        self.sample: list[Callable[[bool], None]] = samplers
        self.permutation: Callable[[], list[bytes]] = permutation
        self.report: Callable[[], str] = reporter
        self.setWindowTitle("Oracle")
        layout = QVBoxLayout()
        self.setLayout(layout)
        tab_widget = QTabWidget()
        tabs: list[QWidget] = [QWidget()]
        layouts: list[QVBoxLayout] = [QVBoxLayout()]
        tabnames: list[str] = ['Graph']

        fsets = self.oracle.db.fsets
        hmap = {m.hash: m.name for m in self.oracle.db.mods.values()}
        tsort = random_toposort(fsets)
        if tsort is None:
            label = QLabel("Cannot render: the mod graph contains a cycle.")
            layouts[0].addWidget(label)
        else:
            edgelist: list[tuple[bytes, bytes]] = []
            perm = self.permutation()
            for hash in perm:
                for f in fsets[hash]:
                    if f in perm:
                        edgelist.append((hash, f))
            label_dict = {k: hmap.get(k, k.hex()) for k in fsets.keys()}
            graph_widget = OracleGraph(edgelist, label_dict)
            layouts[0].addWidget(graph_widget)
        for i in range(len(tabs)):
            tabs[i].setLayout(layouts[i])
            _ = tab_widget.addTab(tabs[i], tabnames[i])
        layout.addWidget(tab_widget)

        # Add buttons below the tab contents
        btn_sample = QPushButton("Sample")
        btn_samplerandom = QPushButton("Sample Random")
        btn_predict = QPushButton("Predict")
        layout.addWidget(btn_sample)
        layout.addWidget(btn_samplerandom)
        layout.addWidget(btn_predict)

        _ = btn_sample.clicked.connect(self.on_sample)             # pyright: ignore [reportUnknownMemberType]
        _ = btn_samplerandom.clicked.connect(self.on_samplerandom) # pyright: ignore [reportUnknownMemberType]
        _ = btn_predict.clicked.connect(self.on_predict)           # pyright: ignore [reportUnknownMemberType]

    def on_sample(self):
        try:
            self.sample[0](False)
        except Exception as e:
            _ = QMessageBox.warning(self, "Sample Error", str(e))

    def on_samplerandom(self):
        try:
            self.sample[0](True)
        except Exception as e:
            _ = QMessageBox.warning(self, "Sample Random Error", str(e))

    def on_predict(self):
        try:
            result = self.report()
            _ = QMessageBox.information(self, "Predict", result)
        except Exception as e:
            _ = QMessageBox.warning(self, "Predict Error", str(e))

class OracleGraph(QWidget):
    def __init__(self, edgelist: list[tuple[bytes, bytes]], label_dict: dict[bytes, str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.config: MetroConfig = MetroConfig()
        self.renderer: MetroRender = MetroRender.from_edgelist_and_labels(self.config, edgelist, label_dict)
        self._scale: float = 4.0
        self._offset_x: float = 100
        self._offset_y: float = 0
        self.setMinimumSize(400, 400)
        self._last_mouse_pos: None | QPointF = None
        self._panning: bool = False
        self._fit_done: bool = False
        self.setMouseTracking(True)

    def wheelEvent(self, a0: QWheelEvent | None) -> None:
        # Zoom at cursor position
        if not a0:
            return
        pos = a0.position()
        cursor_x, cursor_y = pos.x(), pos.y()
        old_scale = self._scale
        # Typical zoom factor per wheel step
        delta = a0.angleDelta().y()
        if delta == 0:
            return
        factor = 1.15 if delta > 0 else 1/1.15
        self._scale *= factor
        # Clamp scale
        self._scale = max(0.1, min(self._scale, 10.0))
        # Adjust offset so the point under cursor stays fixed
        self._offset_x = cursor_x - (cursor_x - self._offset_x) * (self._scale / old_scale)
        self._offset_y = cursor_y - (cursor_y - self._offset_y) * (self._scale / old_scale)
        self.update()

    def mousePressEvent(self, a0: QMouseEvent | None) -> None:
        if not a0:
            return
        if a0.button() == Qt.MouseButton.LeftButton:
            pos = a0.position()
            x, y = (pos.x() - self._offset_x) / self._scale, (pos.y() - self._offset_y) / self._scale
            # Compute grid row/col for cursor only
            y_min, x_min, _, _ = self.renderer.box()
            scale = self.config.scale
            # Identify the column and row being clicked using the bounding box and scale
            col = (int((x - x_min) // (2 * scale)) - self.renderer.shift)
            row = int((y - y_min) // (2 * scale))
            plot = self.renderer.graph
            if row < 0 or row >= len(plot.rows):
                return
            row_obj = plot.rows[row]
            col_obj = row_obj.columns.get(col + 1)
            if not col_obj:
                return
            if col_obj.is_node:
                _ = QMessageBox.information(self, "Node Label", f"Label: {row_obj.label}")
                return
            if col_obj.is_input:
                trow = row - 1
                while trow >= 0:
                    ncol = plot.rows[trow].columns.get(col + 1)
                    if ncol is None or ncol.is_node:
                        break
                    trow -= 1

                _ = QMessageBox.information(self, 'Grid Cell', f'{plot.rows[trow].label} -> {row_obj.label}')
            return
                            
        if a0.button() == Qt.MouseButton.RightButton:
            self._panning = True
            self._last_mouse_pos = a0.position()

    def mouseMoveEvent(self, a0: QMouseEvent | None) -> None:
        if not a0:
            return
        if self._panning and self._last_mouse_pos is not None:
            pos = a0.position()
            dx = pos.x() - self._last_mouse_pos.x()
            dy = pos.y() - self._last_mouse_pos.y()
            self._offset_x += dx
            self._offset_y += dy
            self._last_mouse_pos = pos
            self.update()

    def mouseReleaseEvent(self, a0: QMouseEvent | None) -> None:
        if not a0:
            return
        if a0.button() == Qt.MouseButton.RightButton:
            self._panning = False
            self._last_mouse_pos = None

    def paintEvent(self, a0: QPaintEvent | None) -> None:
        if not a0:
            return
        # On first paint, fit the graph vertically to the window
        if not self._fit_done:
            box = self.renderer.box()
            y_min, x_min, y_max, _ = box
            window_height = self.height()
            box_height = y_max - y_min
            if box_height > 0:
                self._scale = window_height / box_height
                # Center vertically
                self._offset_y = -y_min * self._scale
            # Update x offset so left of graph aligns with left of window (no x scaling)
            self._offset_x = -x_min * self._scale
            self._fit_done = True
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.renderer.render(
            painter,
            scale=self._scale,
            offset_x=self._offset_x,
            offset_y=self._offset_y
        )
        _ = painter.end()
