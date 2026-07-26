"""Build 4K Times New Roman summary visuals for Tasks 1 and 2."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parent.parent
CANVAS_SIZE = (3840, 2160)
WHITE = "#FFFFFF"
INK = "#142038"
MUTED = "#61728B"
GRID = "#CBD5E1"
BLUE = "#087DB7"
GREEN = "#0A9B72"
ORANGE = "#D45A00"

FONT_DIRECTORY = Path("/System/Library/Fonts/Supplemental")
FONT_REGULAR = FONT_DIRECTORY / "Times New Roman.ttf"
FONT_BOLD = FONT_DIRECTORY / "Times New Roman Bold.ttf"
FONT_ITALIC = FONT_DIRECTORY / "Times New Roman Italic.ttf"


def _font(size: int, *, bold: bool = False, italic: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold else FONT_ITALIC if italic else FONT_REGULAR
    if not path.is_file():
        raise FileNotFoundError(f"Times New Roman font is unavailable: {path}")
    return ImageFont.truetype(str(path), size=size)


def _trim_white(image: Image.Image, *, margin: int = 24) -> Image.Image:
    rgb = image.convert("RGB")
    background = Image.new("RGB", rgb.size, WHITE)
    difference = ImageChops.difference(rgb, background).convert("L")
    difference = difference.point(lambda value: 255 if value > 8 else 0)
    box = difference.getbbox()
    if box is None:
        return rgb
    left = max(0, box[0] - margin)
    top = max(0, box[1] - margin)
    right = min(rgb.width, box[2] + margin)
    bottom = min(rgb.height, box[3] + margin)
    return rgb.crop((left, top, right, bottom))


def _place_image(
    canvas: Image.Image,
    source: Path,
    box: tuple[int, int, int, int],
    *,
    border: bool = True,
) -> None:
    x, y, width, height = box
    image = _trim_white(Image.open(source))
    fitted = ImageOps.contain(image, (width, height), method=Image.Resampling.LANCZOS)
    left = x + (width - fitted.width) // 2
    top = y + (height - fitted.height) // 2
    canvas.paste(fitted, (left, top))
    if border:
        draw = ImageDraw.Draw(canvas)
        draw.rounded_rectangle(
            (x, y, x + width, y + height),
            radius=22,
            outline=GRID,
            width=3,
        )


def _centred_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: int,
    font: ImageFont.FreeTypeFont,
    *,
    fill: str = INK,
) -> None:
    box = draw.textbbox((0, 0), text, font=font)
    x = (CANVAS_SIZE[0] - (box[2] - box[0])) // 2
    draw.text((x, y), text, font=font, fill=fill)


def _card(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    label: str,
    value_lines: tuple[str, ...],
    *,
    fill: str,
    accent: str,
    value_size: int = 54,
) -> None:
    x, y, width, height = box
    draw.rounded_rectangle(
        (x, y, x + width, y + height),
        radius=28,
        fill=fill,
        outline=GRID,
        width=3,
    )
    draw.text((x + 38, y + 28), label.upper(), font=_font(38, bold=True), fill=MUTED)
    line_y = y + 92
    for line in value_lines:
        draw.text((x + 38, line_y), line, font=_font(value_size, bold=True), fill=accent)
        line_y += value_size + 18


def build_task01() -> Path:
    canvas = Image.new("RGB", CANVAS_SIZE, WHITE)
    draw = ImageDraw.Draw(canvas)
    _centred_text(
        draw,
        "Task 1 · Two-dimensional random walk",
        38,
        _font(126, bold=True),
    )
    _centred_text(
        draw,
        "Fixed-length steps with uniformly sampled direction produce unbiased isotropic diffusion.",
        184,
        _font(54),
        fill=MUTED,
    )

    figure_dir = ROOT / "figures" / "task01"
    _place_image(canvas, figure_dir / "fifty_walks.png", (70, 300, 1560, 1700))
    _place_image(canvas, figure_dir / "endpoint_distribution.png", (1670, 300, 1370, 1700))

    _card(
        draw,
        (3090, 350, 680, 410),
        "Model",
        ("θ ~ Uniform", "0 to 2π", "step length = s"),
        fill="#EDF5FB",
        accent=BLUE,
        value_size=50,
    )
    _card(
        draw,
        (3090, 800, 680, 400),
        "Theory",
        ("Mean r² = Ns²", "RMS = s√N"),
        fill="#ECF8F3",
        accent=GREEN,
        value_size=60,
    )
    _card(
        draw,
        (3090, 1240, 680, 470),
        "Simulation",
        ("MSD slope", "0.9992 ± 0.0031", "50,000 walks"),
        fill="#FFF4EA",
        accent=ORANGE,
        value_size=48,
    )
    draw.rounded_rectangle(
        (3110, 1760, 3750, 1925),
        radius=26,
        fill="#F0FBF5",
        outline="#8BD2AD",
        width=4,
    )
    draw.text((3190, 1802), "37/37 CHECKS PASS", font=_font(50, bold=True), fill=GREEN)
    draw.text(
        (90, 2054),
        "50 trajectories show the model; 400,000 independent walks provide the quantitative test.",
        font=_font(36),
        fill=MUTED,
    )

    output = figure_dir / "task01_summary.png"
    canvas.save(output, dpi=(300, 300), optimize=True)
    return output


def build_task02() -> Path:
    canvas = Image.new("RGB", CANVAS_SIZE, WHITE)
    draw = ImageDraw.Draw(canvas)
    _centred_text(
        draw,
        "Task 2 · Collision-driven Brownian motion",
        38,
        _font(126, bold=True),
    )
    _centred_text(
        draw,
        "A large tracer receives many microscopic impulses, producing an irregular but statistically diffusive path.",
        184,
        _font(52),
        fill=MUTED,
    )

    figure_dir = ROOT / "task02_brownian_motion" / "figures"
    _place_image(canvas, figure_dir / "reference_particle_scene.png", (70, 305, 1100, 1710))
    _place_image(canvas, figure_dir / "baseline_statistics.png", (1220, 305, 2550, 1120))

    _card(
        draw,
        (1260, 1480, 760, 420),
        "Microscopic model",
        ("1,000 particles", "200 ps", "seed = 2026"),
        fill="#EDF5FB",
        accent=BLUE,
        value_size=51,
    )
    _card(
        draw,
        (2080, 1480, 760, 420),
        "Diffusion fit",
        ("R² = 0.983", "D = 0.00225", "nm² per ps"),
        fill="#FFF4EA",
        accent=ORANGE,
        value_size=50,
    )
    _card(
        draw,
        (2900, 1480, 830, 420),
        "Ensemble evidence",
        ("64 trajectories", "mean includes zero", "unbiased spread"),
        fill="#ECF8F3",
        accent=GREEN,
        value_size=47,
    )
    draw.text(
        (1240, 2030),
        "A single irregular path illustrates Brownian motion; the ensemble MSD and endpoint cloud establish diffusion and lack of drift.",
        font=_font(35),
        fill=MUTED,
    )

    output = figure_dir / "task02_summary.png"
    canvas.save(output, dpi=(300, 300), optimize=True)
    return output


def main() -> int:
    for output in (build_task01(), build_task02()):
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
