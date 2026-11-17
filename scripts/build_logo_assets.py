"""Generate web logo assets from the source logo.

Source: design/vrobot_logo.png (raster, near-white background, no SVG exists).
Output: core/static/core/img/ (transparent, cropped, web-sized) and favicons.

Run from the project root after changing the source logo:

    uv run python scripts/build_logo_assets.py
"""

from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "design" / "vrobot_logo.png"
OUT = ROOT / "core" / "static" / "core" / "img"

# The symbol (V with gear) sits above the wordmark; everything above this
# y coordinate in the source belongs to the symbol.
SYMBOL_BOTTOM = 615

# Pixels this close to white become transparent; a soft ramp avoids jaggies.
WHITE_FULL = 14  # distance from white below which a pixel is fully transparent
WHITE_RAMP = 60  # distance from white above which a pixel is fully opaque


def remove_white(img: Image.Image) -> Image.Image:
    """Make the near-white background transparent."""
    rgb = img.convert("RGB")
    r, g, b = rgb.split()
    darkest = ImageChops.darker(ImageChops.darker(r, g), b)
    alpha = darkest.point(lambda v: _alpha(255 - v))
    result = rgb.convert("RGBA")
    result.putalpha(alpha)
    return result


def _alpha(distance: int) -> int:
    if distance <= WHITE_FULL:
        return 0
    if distance >= WHITE_RAMP:
        return 255
    return round(255 * (distance - WHITE_FULL) / (WHITE_RAMP - WHITE_FULL))


def crop_to_content(img: Image.Image, padding: int = 0) -> Image.Image:
    left, top, right, bottom = img.getchannel("A").getbbox()
    return img.crop(
        (
            max(left - padding, 0),
            max(top - padding, 0),
            min(right + padding, img.width),
            min(bottom + padding, img.height),
        )
    )


def resize_to_height(img: Image.Image, height: int) -> Image.Image:
    width = round(img.width * height / img.height)
    return img.resize((width, height), Image.LANCZOS)


def resize_to_width(img: Image.Image, width: int) -> Image.Image:
    height = round(img.height * width / img.width)
    return img.resize((width, height), Image.LANCZOS)


def square(img: Image.Image, size: int, background=(0, 0, 0, 0), margin=0.08):
    """Fit `img` centred into a square canvas."""
    inner = round(size * (1 - 2 * margin))
    scale = inner / max(img.width, img.height)
    fitted = img.resize(
        (round(img.width * scale), round(img.height * scale)), Image.LANCZOS
    )
    canvas = Image.new("RGBA", (size, size), background)
    canvas.alpha_composite(
        fitted, ((size - fitted.width) // 2, (size - fitted.height) // 2)
    )
    return canvas


def save(img: Image.Image, name: str) -> None:
    path = OUT / name
    # The logo has only a few colours; a small palette removes the noise of
    # the source image and keeps the PNGs small (smaller than WebP here).
    # Alpha is preserved.
    img.quantize(colors=48, method=Image.Quantize.FASTOCTREE).save(path, optimize=True)
    print(
        f"{path.relative_to(ROOT)}  {img.width}x{img.height}  {path.stat().st_size // 1024} KB"
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    source = remove_white(Image.open(SOURCE))

    # Full logo (symbol + wordmark), e.g. for the home page hero.
    full = crop_to_content(source, padding=4)
    for width in (480, 960):
        save(resize_to_width(full, width), f"logo-full-{width}.png")

    # Symbol only, for the header (displayed ~56 px high; 2x for HiDPI).
    symbol = crop_to_content(source.crop((0, 0, source.width, SYMBOL_BOTTOM)), 2)
    save(resize_to_height(symbol, 112), "logo-mark-112.png")

    # Favicons from the symbol.
    save(square(symbol, 192, margin=0.04), "icon-192.png")
    # Apple touch icon: iOS adds no transparency, so use a white background.
    save(square(symbol, 180, background=(255, 255, 255, 255)), "apple-touch-icon.png")
    ico = square(symbol, 48, margin=0.02)
    ico.save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    print(f"{(OUT / 'favicon.ico').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
