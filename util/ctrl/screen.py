import ctypes
from ctypes import windll, wintypes
from plugin_oracle.util.time import crloop
from plugin_oracle.util.img import Pixel, PixelBuffer
from math import ceil, sqrt

class Screen:
    def __init__(self):
        # Acquire the screen device context once.
        self.hdc_screen: int = windll.user32.GetDC(0)

        self.width: int = windll.user32.GetSystemMetrics(0)
        self.height: int = windll.user32.GetSystemMetrics(1)

        self.hdc_compatible: int = windll.gdi32.CreateCompatibleDC(self.hdc_screen)
        # Create a compatible bitmap matching screen dimensions.
        self.hbitmap: int = windll.gdi32.CreateCompatibleBitmap(self.hdc_screen, self.width, self.height)
        # Select the bitmap into the compatible DC, and cache the old object.
        self.old_obj: int = windll.gdi32.SelectObject(self.hdc_compatible, self.hbitmap)
        
        # Preallocate the buffer for the pixel data.
        self.buffer_size: int = self.width * self.height * 4
        self.buffer: ctypes.Array[ctypes.c_char]  = (ctypes.c_char * self.buffer_size)()
        
    def __del__(self):
        # Restore the old GDI object.
        if self.hdc_compatible and self.old_obj:
            windll.gdi32.SelectObject(self.hdc_compatible, self.old_obj)
        # Cleanup cached GDI objects.
        if self.hbitmap:
            windll.gdi32.DeleteObject(self.hbitmap)
        if self.hdc_compatible:
            windll.gdi32.DeleteDC(self.hdc_compatible)
        if self.hdc_screen:
            windll.user32.ReleaseDC(0, self.hdc_screen)
    
    def pscreenshot(self, lo: tuple[int, int] | None = None, hi: tuple[int, int] | None = None) -> PixelBuffer:
        if lo is None:
            lo = 0, 0
        if hi is None:
            hi = self.width, self.height
        r = hi[0] - lo[0], hi[1] - lo[1]
        bytes_needed = r[0] * r[1] * 4

        windll.gdi32.BitBlt(
            self.hdc_compatible, 0, 0, 
            r[0], r[1], 
            self.hdc_screen, lo[0], lo[1], 
            0x00CC0020  # SRCCOPY
        )

        windll.gdi32.GetBitmapBits(self.hbitmap, bytes_needed, self.buffer)
        raw = bytes(self.buffer)[:bytes_needed]
        pixels: list[Pixel] = []
        # Windows bitmaps are stored as BGRA; convert to RGBA.
        for i in range(0, len(raw), 4):
            pixels.append(Pixel(raw[i+2], raw[i+1], raw[i], raw[i+3]))
        return PixelBuffer(pixels, r[0], r[1])
    
    def screenshot(self, lo: tuple[float, float] | None = None, hi: tuple[float, float] | None = None) -> PixelBuffer:
        if lo is None:
            lo = 0, 0
        if hi is None:
            hi = 1, 1
        ilo = round(self.width * lo[0]), round(self.height * lo[1])
        ihi = round(self.width * hi[0]), round(self.height * hi[1])
        return self.pscreenshot(ilo, ihi)
    
    def getpcursor(self) -> tuple[int, int]:
        point = wintypes.POINT()
        windll.user32.GetCursorPos(ctypes.byref(point))
        return (point.x, point.y)
    
    def setpcursor(self, x: int, y: int) -> None:
        windll.user32.SetCursorPos(x, y)
    
    def setcursor(self, x: float, y: float) -> None:
        """Set the cursor based on a (0.0-1.0)-scaled coordinate relative to primary screen size."""
        abs_x = int(round(x * self.width))
        abs_y = int(round(y * self.height))
        self.setpcursor(abs_x, abs_y)
    
    def getcursor(self) -> tuple[float, float]:
        """Return the cursor position scaled to (0.0-1.0) based on the primary screen size."""
        cx, cy = self.getpcursor()
        return (cx / self.width, cy / self.height)
    
    def ptrace(self, x: int, y: int, ms: int = 0) -> None:
        rate: int = 15
        if ms <= rate:
            self.setpcursor(x, y)
            return
        start = self.getpcursor()
        if start == (x, y):
            return
        cnt = ms // rate
        step = (x - start[0]) / cnt, (y - start[1]) / cnt
        
        def move(it: int) -> bool:
            cpos = start[0] + step[0] * it, start[1] + step[1] * it
            tpos = round(cpos[0]), round(cpos[1])
            self.setpcursor(tpos[0], tpos[1])
            return it < cnt
        crloop(rate, move)
        self.setpcursor(x, y)
        
    def trace(self, x: float, y: float, ms: int = 0) -> None:
        px, py = round(x * self.width), round(y * self.height)
        self.ptrace(px, py, ms)
    
    def sptrace(self, x: int, y: int, speed: float = 0.5) -> None:
        if speed <= 0.0:
            return
        cpos = self.getpcursor()
        dist = sqrt((x - cpos[0]) ** 2 + (y - cpos[1]) ** 2)
        ms = ceil(dist / speed)
        self.ptrace(x, y, ms)
    
    def strace(self, x: float, y: float, speed: float = 0.5) -> None:
        px, py = round(x * self.width), round(y * self.height)
        self.sptrace(px, py, speed)