from colorsys import hls_to_rgb

def palette(ncolors: int) -> list[tuple[int, int, int]]:
    colors: list[tuple[int, int, int]] = []
    hue, lightness, saturation = 0.0, 1.0, 0.5
    for _ in range(ncolors):
        r, g, b = hls_to_rgb(hue / 6, 0.4 + (lightness / 2) * 0.3, saturation)
        hue = (hue + 1) % 7
        if hue == 0:
            lightness = (lightness + 1) % 3
        colors.append((int(r*256), int(g*256), int(b*256)))
    return colors