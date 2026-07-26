"""Create a readable overview of all ten rendered master-deck slides."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


MASTER_DIRECTORY = Path(__file__).resolve().parent
PREVIEW_DIRECTORY = MASTER_DIRECTORY / "preview"
OUTPUT_PATH = PREVIEW_DIRECTORY / "BPhO_Master_Contact_Sheet.png"
FONT_PATH = Path("/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf")


def main() -> int:
    slides = sorted(PREVIEW_DIRECTORY.glob("*preview-[0-9][0-9].png"))
    if len(slides) != 10:
        raise RuntimeError(f"expected ten rendered slides, found {len(slides)}")

    canvas = Image.new("RGB", (2000, 2910), "#EEF2F7")
    draw = ImageDraw.Draw(canvas)
    title_font = ImageFont.truetype(str(FONT_PATH), 52)
    label_font = ImageFont.truetype(str(FONT_PATH), 34)
    title = "BPhO Computational Challenge · Tasks 1–10"
    title_box = draw.textbbox((0, 0), title, font=title_font)
    draw.text(
        ((2000 - (title_box[2] - title_box[0])) // 2, 26),
        title,
        font=title_font,
        fill="#142038",
    )

    for index, path in enumerate(slides):
        row, column = divmod(index, 2)
        x = 30 + column * 990
        y = 115 + row * 555
        draw.rounded_rectangle(
            (x, y, x + 960, y + 525),
            radius=20,
            fill="white",
            outline="#CBD5E1",
            width=3,
        )
        draw.text((x + 24, y + 14), f"Task {index + 1}", font=label_font, fill="#142038")
        with Image.open(path) as slide:
            thumbnail = ImageOps.contain(
                slide.convert("RGB"),
                (912, 440),
                method=Image.Resampling.LANCZOS,
            )
        left = x + (960 - thumbnail.width) // 2
        top = y + 68 + (440 - thumbnail.height) // 2
        canvas.paste(thumbnail, (left, top))

    canvas.save(OUTPUT_PATH, dpi=(180, 180), optimize=True)
    print(OUTPUT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
