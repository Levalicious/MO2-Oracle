class Pixel:
    def __init__(self, r: int, g: int, b: int, a: int) -> None:
        self.r: int = r
        self.g: int = g
        self.b: int = b
        self.a: int = a

    def __repr__(self) -> str:
        return f"#{self.r:02X}{self.g:02X}{self.b:02X}{self.a:02X}"
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Pixel):
            return NotImplemented
        return (self.r, self.g, self.b, self.a) == (other.r, other.g, other.b, other.a)

class PixelBuffer:
    def __init__(self, pixels: list[Pixel], width: int, height: int) -> None:
        self.pixels: list[Pixel] = pixels
        self.width: int = width
        self.height: int = height

    def __getitem__(self, pos: tuple[int, int]) -> Pixel:
        x, y = pos
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            raise IndexError("PixelBuffer index out of range")
        return self.pixels[y * self.width + x]
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PixelBuffer):
            return NotImplemented
        return (self.width, self.height, self.pixels) == (other.width, other.height, other.pixels)
    
    def __repr__(self) -> str:
        return f"PixelBuffer(width={self.width}, height={self.height}, pixels=[...])"
    
    def pcrop(self, x: int, y: int, w: int, h: int) -> "PixelBuffer":
        end_x = min(x + w, self.width)
        end_y = min(y + h, self.height)
        new_pixels: list[Pixel] = []
        for j in range(y, end_y):
            for i in range(x, end_x):
                new_pixels.append(self[i, j])
        return PixelBuffer(new_pixels, end_x - x, end_y - y)

    def crop(self, x: float, y: float, w: float, h: float) -> "PixelBuffer":
        ix = int(x * self.width)
        iy = int(y * self.height)
        iw = int(w * self.width)
        ih = int(h * self.height)
        return self.pcrop(ix, iy, iw, ih)