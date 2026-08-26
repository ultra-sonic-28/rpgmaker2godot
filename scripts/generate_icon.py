"""Generate the rpgmaker2godot icon set.

Draws a 512x512 master (supersampled 2x for clean anti-aliasing)
depicting the conversion story of the tool:

    [ RPG Maker tile grid ]  --->  [ Godot robot head ]

on a Godot-blue rounded square, then exports:

* ``icon_<size>.png``      for 512 and every ICO_SIZES entry;
* ``rpgmaker2godot.ico``   bundling exactly the ICO_SIZES list,
                           ready for future executable integration.

Usage (from the repository root):

    python scripts/generate_icon.py
"""

from pathlib import Path

from PIL import Image, ImageDraw

MASTER_SIZE = 512
SUPERSAMPLE = 2
ICO_SIZES = [
    (256, 256),
    (128, 128),
    (64, 64),
    (48, 48),
    (32, 32),
    (16, 16),
]

OUTPUT_DIRECTORY = Path(__file__).resolve().parents[1] / "assets" / "icon"

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
BACKGROUND_TOP = (71, 140, 191)     # Godot blue
BACKGROUND_BOTTOM = (46, 100, 146)  # deeper blue
TILE_OUTLINE = (31, 42, 56)         # dark navy backing
TILE_ORANGE = (232, 89, 58)         # RPG Maker warmth
TILE_AMBER = (240, 145, 66)
ARROW_WHITE = (255, 255, 255)
HEAD_WHITE = (255, 255, 255)
EAR_GRAY = (208, 218, 230)
VISOR_NAVY = (30, 43, 58)
EYE_CYAN = (86, 196, 255)

ICON_NAME = "rpgmaker2godot"


def build_master() -> Image.Image:
    """Draw the supersampled master artwork and return it at 512x512."""

    size = MASTER_SIZE * SUPERSAMPLE
    s = SUPERSAMPLE

    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # ------------------------------------------------------------------
    # Rounded-square background with a subtle vertical gradient.
    # ------------------------------------------------------------------
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, size - 1, size - 1),
        radius=96 * s,
        fill=255,
    )

    gradient = Image.new("RGBA", (size, size))
    gradient_draw = ImageDraw.Draw(gradient)

    for y in range(size):
        ratio = y / (size - 1)
        row_color = tuple(
            int(
                BACKGROUND_TOP[channel]
                + (BACKGROUND_BOTTOM[channel] - BACKGROUND_TOP[channel])
                * ratio,
            )
            for channel in range(3)
        ) + (255,)
        gradient_draw.line([(0, y), (size, y)], fill=row_color)

    image.paste(gradient, (0, 0), mask)

    draw = ImageDraw.Draw(image)

    # ------------------------------------------------------------------
    # Left group: 2x2 RPG Maker tile grid (checker of warm tiles,
    # each backed by a thin dark outline for contrast on blue).
    # ------------------------------------------------------------------
    tile_size = 74 * s
    tile_gap = 14 * s
    grid_origin_x = 66 * s
    grid_origin_y = 174 * s

    tile_colors = (
        TILE_ORANGE,
        TILE_AMBER,
        TILE_AMBER,
        TILE_ORANGE,
    )

    for index, color in enumerate(tile_colors):
        column = index % 2
        row = index // 2

        x0 = grid_origin_x + column * (tile_size + tile_gap)
        y0 = grid_origin_y + row * (tile_size + tile_gap)
        x1 = x0 + tile_size
        y1 = y0 + tile_size

        draw.rounded_rectangle(
            (x0 - 5 * s, y0 - 5 * s, x1 + 5 * s, y1 + 5 * s),
            radius=14 * s,
            fill=TILE_OUTLINE,
        )
        draw.rounded_rectangle(
            (x0, y0, x1, y1),
            radius=10 * s,
            fill=color,
        )

    # ------------------------------------------------------------------
    # Middle: chunky white conversion arrow.
    # ------------------------------------------------------------------
    arrow_y = 256 * s
    draw.rectangle(
        (240 * s, arrow_y - 14 * s, 284 * s, arrow_y + 14 * s),
        fill=ARROW_WHITE,
    )
    draw.polygon(
        [
            (280 * s, arrow_y - 27 * s),
            (312 * s, arrow_y),
            (280 * s, arrow_y + 27 * s),
        ],
        fill=ARROW_WHITE,
    )

    # ------------------------------------------------------------------
    # Right group: simplified Godot robot head.
    # ------------------------------------------------------------------
    # Side "ears".
    draw.rounded_rectangle(
        (330 * s, 166 * s, 364 * s, 206 * s),
        radius=10 * s,
        fill=EAR_GRAY,
    )
    draw.rounded_rectangle(
        (420 * s, 166 * s, 454 * s, 206 * s),
        radius=10 * s,
        fill=EAR_GRAY,
    )

    # Head.
    draw.rounded_rectangle(
        (318 * s, 184 * s, 466 * s, 332 * s),
        radius=36 * s,
        fill=HEAD_WHITE,
    )

    # Visor with two cyan eyes.
    draw.rounded_rectangle(
        (336 * s, 238 * s, 448 * s, 308 * s),
        radius=24 * s,
        fill=VISOR_NAVY,
    )
    for eye_center_x in (372, 412):
        draw.ellipse(
            (
                (eye_center_x - 14) * s,
                (273 - 14) * s,
                (eye_center_x + 14) * s,
                (273 + 14) * s,
            ),
            fill=EYE_CYAN,
        )

    return image.resize((MASTER_SIZE, MASTER_SIZE), Image.LANCZOS)


def export_icon_set(master: Image.Image) -> None:
    """Write every PNG size plus the multi-resolution .ico file."""

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    png_sizes = [MASTER_SIZE] + [width for width, _ in ICO_SIZES]
    for png_size in sorted(set(png_sizes), reverse=True):
        target = master.resize((png_size, png_size), Image.LANCZOS)
        target_path = OUTPUT_DIRECTORY / f"{ICON_NAME}_{png_size}.png"
        target.save(target_path)

        print(f"  wrote {target_path.name} ({png_size}x{png_size})")

    ico_path = OUTPUT_DIRECTORY / f"{ICON_NAME}.ico"
    master.save(ico_path, format="ICO", sizes=ICO_SIZES)
    print(f"  wrote {ico_path.name} (sizes: {ICO_SIZES})")


def main() -> None:
    print(f"Generating icons into {OUTPUT_DIRECTORY}")
    export_icon_set(build_master())
    print("Done.")


if __name__ == "__main__":
    main()