# RPG Maker 2 Godot

CLI tool written in Python 3.13+ to convert RPG Maker MV/MZ tilesets into Godot resources.

## Command-line options

```
rpgmaker2godot [-h] [--mode {TILESET,CHARACTER}] [--simple]
               [--tileset TILESET] [--no-merge] [--tolerance TOLERANCE]
               [--no-terrains] input output
```

Each option is described below with an example; `rpgmaker2godot --help`
prints the same reference inline.

### `input` — input directory (positional)

Directory containing the RPG Maker MV/MZ tilesheets to convert: the
`A4.png`, `A5.png` and `B.png`–`E.png` sheets, optionally prefixed
(e.g. `world_B.png`), typically a project's `img/tilesets/` folder. A
`Tilesets.json` placed in the same directory is used to resolve the
collision flags.

```bash
rpgmaker2godot --simple "C:/RPG Maker/MyProject/img/tilesets" output
```

### `output` — output directory (positional)

Directory receiving the generated Godot resources: one `<tileset>.png`
atlas and one `<tileset>.tres` TileSet per converted tileset. It is
created when missing.

```bash
rpgmaker2godot --simple img/tilesets "C:/Godot/MyGame/assets/tilesets"
```

### `--mode MODE`

Selects what the input directory contains and which pipeline runs.
The value is case-insensitive:

* `TILESET` (default) — the directory holds RPG Maker MV/MZ
  tilesheets, converted into Godot `TileSet` resources for maps
  (this mode requires `--simple`);
* `CHARACTER` — the directory holds character spritesheets
  (`player-1.png`, `player-2.png`, …) storing their animations
  natively (RPG Maker character sheets are **not** supported — they
  have no `idle` rows); each one is converted into a Godot
  `SpriteFrames` resource ready for an `AnimatedSprite2D`. See
  [Character conversion](#character-conversion-mode) for the expected
  layout.

```bash
rpgmaker2godot --mode CHARACTER img/characters output
```

### `--simple`

Selects the simple conversion mode (`A5`, `B`–`E`, plus the `A4`
autotile unfolding) — the only mode currently supported, so the flag
is required for every tileset run (`--mode TILESET`, the default).
It is not used — and rejected — in `--mode CHARACTER`.

```bash
rpgmaker2godot --simple img/tilesets output
```

### `--tileset TILESET`

Restricts the conversion to a single tileset (TILESET mode only). The
value is either a tileset family prefix (`Inside` converts every
`Inside_*.png` sheet) or one exact sheet file (`Inside_B.png`; the
`.png` extension is assumed when omitted, so `--tileset Inside_B`
works too). Matching is case-insensitive. When nothing in the input
directory matches, a warning is displayed and nothing is converted.
Without the option, every tileset found in the input directory is
converted.

```bash
rpgmaker2godot --simple --tileset Outside img/tilesets output
```

### `--no-merge`

Keeps the source sheets split: exports one PNG atlas and one `.tres`
per input sheet (`Inside_A5.png` + `Inside_A5.tres`, `Inside_B.png` +
`Inside_B.tres`, …) instead of merging the sheets sharing a prefix
into a single stacked output (the default behaviour).

```bash
rpgmaker2godot --simple --no-merge img/tilesets output
```

### `--tolerance TOLERANCE`

Merges unfolded A4 autotiles whose pixel difference is within `N`
pixels, discarding source-image noise. Defaults to `0` (byte-exact
match) and must be `>= 0`.

```bash
rpgmaker2godot --simple --tolerance 8 img/tilesets output
```

### `--no-terrains`

Skips the Godot terrain generation for the unfolded A4 autotiles
(terrains power the automatic connection tool in the Godot editor);
the generated `.tres` then contains no `terrain_set_*` metadata.

```bash
rpgmaker2godot --simple --no-terrains img/tilesets output
```

### `-h`, `--help`

Prints the usage reference (the block shown at the top of this
section) and exits.

```bash
rpgmaker2godot --help
```

## Development

Create the virtual environment:

```bash
python -m venv .venv
```

Activate it:

```bash
.\.venv\Scripts\activate
```

And install the project with the development extras (`ruff` + `mypy`):

```bash
python -m pip install -e ".[dev]"
```

Alternatively, the activation and editable-install steps above can be
performed with the `scripts/setup_dev.ps1` helper — it must be run
from the project directory (`C:\My Program Files\rpgmaker2godot`) and
displays an error message from anywhere else (it also reminds you to
create the virtual environment if it is missing):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_dev.ps1
```

Run:

```bash
rpgmaker2godot
```

### Linting and type checking

Lint with ruff (checks the whole repository, using the rules configured in `[tool.ruff]`):

```bash
python -m ruff check
```

Apply ruff's automatic fixes (`--fix`, `--unsafe-fixes` for the broader ones) before committing:

```bash
python -m ruff check --fix
python -m ruff check --fix --unsafe-fixes
```

Type-check with mypy (targets `src/rpgmaker2godot`, as configured in `[tool.mypy]`):

```bash
python -m mypy
```

### Architecture
```text
src/rpgmaker2godot/
├── cli.py                          # CLI entry point (main) — reads Tilesets.json to resolve collisions
├── analysis/                       # PNG sheet detection (TilesetDetector, CharacterDetector)
│   ├── detector.py                 # TilesetDetector: scans the input directory for RPG Maker sheets
│   │                               #   (A4/A5/B/C/D/E.png), validates their dimensions against the tile
│   │                               #   size and produces an AnalysisResult
│   ├── character_detector.py       # CharacterDetector: scans the input directory for character
│   │                               #   spritesheets (any *.png), validates the 3-column × 9-row layout
│   │                               #   and produces a CharacterAnalysisResult
│   └── models.py                   # SheetInfo, AnalysisResult, RPGMakerVersion — analysis data model
│                                   #   (+ CharacterSheetInfo, CharacterAnalysisResult)
├── character/                      # Character spritesheet conversion (--mode CHARACTER)
│   ├── layout.py                   # Fixed 9-row layout (walk ×4, idle ×4, damaged) + playback defaults
│   ├── models.py                   # CharacterFrame, CharacterAnimation, CharacterSpriteSheet,
│   │                               #   CharacterConversionResult — internal character model
│   └── spritesheet_builder.py      # CharacterSpriteSheetBuilder: layout rows → animations + frame regions
├── conversion/                     # AnalysisResult → internal model transformation
│   └── converter.py                # SimpleConverter
├── tileset/                        # Reading/parsing of RPG Maker flags
│   ├── reader.py                   # TilesetsJsonReader
│   ├── flags.py                    # decode_tile_flags() — 16-bit decoding
│   ├── model.py                    # TileProperties, TilesetFlags
│   ├── resolver.py                 # TilePropertiesResolver
│   ├── collision.py                # tile_properties_to_collision()
│   ├── tile_id.py                  # TileRef → global Tile ID conversion
│   └── autotile/                   # RPG Maker autotile composition
│       ├── shapes.py               # FLOOR_AUTOTILE_TABLE (48) + WALL_AUTOTILE_TABLE (16), verbatim
│       ├── composer.py             # compose 48x48 tiles from 24x24 quarters (+ unfold helpers)
│       └── a4.py                   # A4 sheet geometry + the 48 autotiles' source regions and
│       │                           #   shape quarters; unique compositions (2304 raw → 1536) then
│       │                           #   pixel-level dedup of graphically identical tiles
├── model/                          # Shared internal model (immutable)
│   ├── enums.py                    # SheetType enum + its canonical stacking order (A4, A5, B, C, D, E)
│   ├── sheet.py                    # Sheet — one source tilesheet together with its extracted tiles
│   ├── tile.py                     # Tile + TileRef — one tile with its geometry, optional RPG Maker
│   │                               #   properties and derived collision
│   ├── tileset.py                  # Tileset + ConversionResult — group of sheets assembled together
│   └── tile_collision.py           # TileCollision — directional passage blocking, free of any Godot concept
├── atlas/                          # PNG atlas building and writing
│   ├── builder.py                  # AtlasBuilder: stacks a tileset's sheets into a single atlas
│   │                               #   geometry; composes the unfolded A4 tiles (4 quarters each)
│   ├── models.py                   # Atlas + AtlasPlacement + AtlasQuarter — each tile's coordinates
│   │                               #   (AtlasQuarter = one 24x24 piece of a composed A4 tile)
│   └── writer.py                   # AtlasWriter: renders an internal Atlas to a PNG image, A4 tiles
│                                   #   composited quarter by quarter onto a transparent canvas
├── image/                          # Image extraction (PIL/Pillow)
│   ├── extractor.py                # TileExtractor: crops a single Tile out of an ImageSource
│   └── source.py                   # ImageSource: lazy access to an image file (open/close, context manager)
├── utils/                          # Console messages (rich banner)
└── godot/                          # Godot resource generation
    ├── model.py                    # Godot models (GodotTileSet, etc.)
    ├── atlas/                      # atlas_builder.py, atlas_mapper.py
    ├── tileset/                    # collision.py (GodotTileCollision), tileset_builder.py
    ├── resource/                   # resource.py, resource_serializer.py, resource_writer.py, path.py
    ├── spriteframes/               # models.py, serializer.py, writer.py — SpriteFrames .tres resources
    ├── export/                     # simple.py (SimpleExporter — tilesets), characters.py
    │                               #   (CharacterExporter — character spritesheets)
    └── collision/                  # tile_collision.py (has_collision — guards the semantic/geometry boundary)
```

### Logging

The pipeline is silent by default. Drop a `rpgmaker2godot.yaml` file into the working directory to enable debug logging (raw flags, decoded properties and generated polygons, tile by tile). Records are written **to the configured file only** — never to the console:

```yaml
# Configuration for logging
logger:
  enabled: true
  level: "DEBUG"
  file: "rpgmaker2godot.log"
  mode: "OVERWRITE"
```

The settings live in the `logger` section:

* `enabled`: master switch;
* `level`: minimum severity (`DEBUG`, `INFO`, `WARNING`, `ERROR`);
* `file`: **required** — the sole destination of the records; without this field, logging stays disabled;
* `mode`: `APPEND` (default) appends records at the end of the existing file, `OVERWRITE` recreates the file on every run — any missing or unknown value falls back to `APPEND`.

> Running the test-suite never writes to this file: every test executes in an isolated working directory, so an ambient `rpgmaker2godot.yaml` left next to the sources is invisible to the application under test.

### Windows executable

A standalone binary is generated in `dist\rpgmaker2godot.exe` (all dependencies — Pillow, rich — are bundled, no Python interpreter required on the target machine):

```powershell
pip install -e ".[build]"
powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1
```

The build recipe is described by the versioned `rpgmaker2godot.spec` file (onefile, console, package metadata embedded for the banner).

Every generation **automatically increments the numeric `build` entry** of the `[tool.rpgmaker2godot]` table of `pyproject.toml`; this number is displayed by the banner right after the version: `rpgmaker2godot v0.1.0 build 35`.

Once the executable is built, the script **packages the GitHub release archive** into `dist\`:

* `RpgMaker2Godot-win-x64-v{VERSION}{BUILD}.zip` — e.g. `RpgMaker2Godot-win-x64-v0.1.035.zip` — containing `rpgmaker2godot.exe` (additional assets such as sample tilesets can be added to the archive via the build script's staging step);
* `RpgMaker2Godot-win-x64-v{VERSION}{BUILD}.zip.sha256` — its SHA256 checksum, in `<hash>  <filename>` format.

`VERSION` is the `[project].version` from `pyproject.toml` and `BUILD` the freshly incremented build number.

The executable embeds the application icon (`assets/icon/rpgmaker2godot.ico`, also shipped as standalone PNGs from 512 down to 16 px). To tweak the artwork, edit `scripts/generate_icon.py`, regenerate with `python scripts/generate_icon.py`, then rebuild.

It also carries Windows version metadata (description, file & product version including the build number, product name, French language, copyright, original filename), defined once in `rpgmaker2godot.spec` from the `pyproject.toml` values.

* slower first startup: the executable extracts itself into `%TEMP%`;
* unsigned binary: SmartScreen or your antivirus may show a warning when running it.

### RPG Maker tileset structure

Reference for the sheet format handled by the pipeline, as defined by RPG Maker MV/MZ and its core script (`rmmz_core.js`).

**Objective.** A tileset is not a single image: `Tilesets.json` references up to nine PNG *sheets* (`A1`–`A5`, `B`–`E`) which the engine draws stacked on top of each other (A4 and A5 underneath, then the overlay layers `B` → `C` → `D` → `E`). Everything is laid out on a **48×48 px grid**: one tile is 48×48 px, and autotiles are composed from four **24×24 px quarters**. Sheets come in two families:

* **normal sheets** (`A5`, `B`–`E`) — every cell is an independent, ready-to-draw tile;
* **autotile sheets** (`A1`–`A4`) — cells are raw material: for every map cell the engine picks a *shape* from hardcoded tables (`FLOOR_AUTOTILE_TABLE` = 48 shapes, `WALL_AUTOTILE_TABLE` = 16, `WATERFALL_AUTOTILE_TABLE` = 4) and assembles the final 48×48 tile from four 24×24 quarters. This tool performs that composition at conversion time (*unfolding*), so Godot only sees plain static tiles.

**Organisation, number and size of tiles:**

| Sheet | Pixels | Content | Engine IDs | Purpose |
| ----- | ------ | ------- | ---------- | ------- |
| A1 | 768×576 | 16 autotiles | 768 | animated water and waterfalls |
| A2 | 768×576 | 32 autotiles | 1536 | ground autotiles (grass, paths…) |
| A3 | 768×576 | 32 autotiles | 1536 | building autotiles (roofs, walls) |
| A4 | 768×720 | 48 autotiles → 1536 compositions → only graphically distinct tiles kept (1390 for the stock Inside_A4) | 1536 | interior walls & ceilings (houses, caves, castles, dungeons) |
| A5 | 384×768 | 128 normal tiles (8×16) | 512 (128 used) | plain ground without autotile |
| B–E | 768×768 each | 256 normal tiles (16×16) each | 256 each | ordinary tiles, four overlay layers (B lowest → E highest) |

Global tile IDs are fixed by the engine — `B=0, C=256, D=512, E=768, A5=1536, A1=2048, A2=2816, A3=4352, A4=5888`, `TILE_ID_MAX=8192` — which is how the `Tilesets.json` flags array is matched to tiles.

**A4 layout in detail** (fully unfolded by the converter):

```text
768×720 px = 8 columns of 96 px × 3 bands of 240 px; each band stacks one
Wall Top row over one Wall Side row:

  y =   0..144    Wall Top  ×8   (96×144, FLOOR_AUTOTILE_TABLE, 48 shapes)
  y = 144..240    Wall Side ×8   (96×96,  WALL_AUTOTILE_TABLE,  16 shapes)
  y = 240..384    Wall Top  ×8
  y = 384..480    Wall Side ×8
  y = 480..624    Wall Top  ×8
  y = 624..720    Wall Side ×8
```

That gives 24 Wall Tops + 24 Wall Sides = 48 autotiles (`TILE_ID_A4 = 5888`; `kind % 16 < 8` ⇒ Wall Top). Each kind reserves 48 shape IDs, but Wall Sides cycle through their 16 shapes only: the 2304 raw variants contain duplicates, and the converter unfolds the **1536 unique ready-to-place 48×48 tiles** (24 Wall Tops × 48 + 24 Wall Sides × 16), dropping the redundant ones.

**What this tool converts:** `*_A4.png` (unfolded), `*_A5.png` and `*_B/C/D/E.png`. Sheets A1–A3 are not converted yet.

### Conversion pipeline

RPG Maker → Godot conversion pipeline:

```mermaid
flowchart LR
    CLI --> A["TilesetDetector.analyze()"]
    A --> B["SimpleConverter.convert()"]
    B --> C["SimpleExporter.export()"]
    C --> D["atlas_builder"]
    D --> E["atlas_writer"]
    E --> F["godot mapper"]
    F --> G["tileset_builder"]
    G --> H["resource_writer"]
    H --> I[".tres"]

    A -.->|"directory scan<br/>A4/A5/B/C/D/E.png regex"| A
    B -.->|"Tile creation — TileRef + coordinates<br/>A4: 2304 raw variants → 1536 unique unfolded tiles"| B
    E -.->|"A4 tiles composed from four 24×24 quarters<br/>(AtlasQuarter, transparent canvas)"| E
```

The pipeline is split in three phases, orchestrated by `rpgmaker2godot.cli.main()`.

#### 1. Analysis — `analysis/`

`TilesetDetector.analyze()` scans the input directory for supported RPG Maker sheets (`A4.png`, `A5.png`, `B.png`, `C.png`, `D.png`, `E.png`, matched case-insensitively and optionally prefixed, e.g. `world_B.png`). For each sheet it validates that both dimensions are divisible by the tile size (48 px by default), then produces an `analysis.SheetInfo` per sheet and wraps them in an `analysis.AnalysisResult`:

* detects the dimensions, column/row count and tile size of every sheet;
* collects non-fatal issues as warnings (e.g. an unsupported/invalid PNG) without aborting the whole scan;
* raises `ValueError` if no supported sheet is found at all.

By default every detected sheet is converted. Passing `--tileset NAME` restricts the run to a single tileset: the value may be a tileset family prefix (`--tileset world` converts every `world_*.png` sheet) or one exact sheet file (`--tileset world_B.png` — the `.png` extension is assumed when omitted, so `--tileset world_B` works too). When nothing in the input directory matches the value, a warning is displayed and nothing is converted (exit code 1).

```mermaid
sequenceDiagram
    autonumber
    participant CLI as cli.main()
    participant D as TilesetDetector
    participant FS as input directory

    CLI->>D: analyze(directory, tile_size=48)
    loop For each file
        D->>FS: iterdir()
        FS-->>D: path
        D-->>D: match A4/A5/B/C/D/E.png (regex, case-insensitive)
        alt no match
            Note over D: file ignored
        else match
            D->>FS: Image.open(path)
            FS-->>D: width, height
            D-->>D: validate width/height % tile_size == 0
            alt dimensions valid
                D-->>D: build SheetInfo (columns, rows, prefix)
            else invalid dimensions
                D-->>CLI: warning (sheet skipped)
            end
        end
    end
    Note over D: no supported sheet found → raise ValueError
    D-->>CLI: AnalysisResult(sheets, warnings)
```

#### 2. Conversion — `conversion/`, `tileset/`

`SimpleConverter.convert()` turns the `AnalysisResult` into the internal, immutable `ConversionResult` model. Sheets sharing the same filename prefix are grouped into one `Tileset` and ordered by their canonical stacking order (A4, A5, B, C, D, E).

This prefix grouping is the default **merging** behaviour: every sheet sharing a prefix ends up stacked in a single atlas/`.tres`. Passing `--no-merge` keeps the source sheet split instead — each detected sheet becomes its own `Tileset`, named after the sheet file itself (so `world_B.png` yields a `world_B` tileset), and the export step then emits one `<sheet>.png` + `<sheet>.tres` per input sheet.

For every sheet, one `Tile` is created per cell — except A4, which is *unfolded*:

* **A4 unfolding** — the sheet must have the canonical 768×720 dimensions, then the converter emits one 48×48 tile per **graphically distinct** (autotile kind, shape) composition: the Wall Side table only holds 16 of the 48 reserved shape IDs (2304 raw variants → 1536 compositions), and a pixel-level deduplication then keeps only the tiles that truly render differently — 1390 for the stock `Inside_A4.png`. Each kept tile is encoded as `TileRef.index = kind × 48 + shape` (first occurrence) and laid out on the packed 16-column grid the atlas step consumes. `--tolerance N` additionally merges tiles differing by at most N pixels to discard source-image noise (default 0 = byte-exact match);
* a `TileRef` (tileset name, sheet type, zero-based column-major index) plus its coordinates;
* **collision resolution** — when a `TilePropertiesResolver` is configured (i.e. a `Tilesets.json` is present), the tile's `TileRef` is mapped to the RPG Maker global Tile ID via `tile_to_tile_id()` (`B=0, C=256, D=512, E=768, A5=1536, A4=5888`, then row/column offset; for A4 the offset is `kind × 48 + shape`), the flags are decoded into `TileProperties`, and `tile_properties_to_collision()` converts the directional passage permissions into a Godot-agnostic `TileCollision`. Without a resolver the tile is kept collisionless, preserving the original behaviour.

```mermaid
sequenceDiagram
    autonumber
    participant CLI as cli.main()
    participant C as SimpleConverter
    participant R as TilePropertiesResolver

    CLI->>C: convert(analysis)
    C-->>C: group sheets by prefix → Tileset(s),<br/>ordered by SheetType.order
    loop For each sheet
        alt A4 sheet (autotile unfolding)
            Note over C: 2304 raw variants → graphically distinct tiles only<br/>TileRef.index = kind × 48 + shape (first occurrence)
        else other sheet
            Note over C: one Tile per cell (column, row, index)
        end
        C-->>C: _create_tile(TileRef, geometry)
        alt resolver configured
            C-->>C: tile_to_tile_id(tile) → global Tile ID
            C->>R: resolve(tile)
            R-->>R: decode_tile_flags(raw_flags)
            R-->>C: TileProperties
            C-->>C: tile_properties_to_collision(properties)<br/>→ TileCollision (direction inversion)
            C-->>C: replace(tile, properties, collision)
        else no resolver
            C-->>C: keep tile collisionless
        end
    end
    C-->>CLI: ConversionResult(tilesets)
```

#### 3. Export — `atlas/`, `image/`, `godot/`

`SimpleExporter.export()` writes, for each `Tileset`, a PNG atlas and a Godot `.tres` resource into the output directory:

1. `AtlasBuilder.build()` stacks the tileset's sheets into a single atlas geometry (`Atlas`), recording each tile's source and atlas coordinates. A4 tiles are *composed*: their placement holds four `AtlasQuarter` pieces (24×24 each) selected by the engine shape tables, not a single rectangular crop.
2. `AtlasWriter.write()` renders that atlas to `<name>.png` — normal tiles are cropped from their source sheet, while every A4 tile is composited from its four quarters onto a transparent 48×48 canvas (`image/`'s `TileExtractor`/`ImageSource` handle the per-tile image access).
3. `GodotAtlasMapper.map()` translates the atlas into Godot's atlas model.
4. `GodotTileSetBuilder.build()` produces the `GodotTileSet` (tile shapes, source regions, collisions).
5. `GodotResourceWriter.write()` serializes it to the `<name>.tres` resource (Godot text-format), referencing the atlas texture.

The output directory therefore receives, per tileset: `<name>.png` (atlas) and `<name>.tres` (Godot resource).

```mermaid
sequenceDiagram
    autonumber
    participant CLI as cli.main()
    participant E as SimpleExporter
    participant AB as AtlasBuilder
    participant AW as AtlasWriter
    participant GM as GodotAtlasMapper
    participant TB as GodotTileSetBuilder
    participant RW as GodotResourceWriter
    participant FS as output directory

    CLI->>E: export(conversion, output_directory)
    loop For each Tileset
        E->>AB: build(tileset)
        Note over AB: A4 tiles carry four AtlasQuarter<br/>pieces (engine shape tables)
        AB-->>E: Atlas (geometry + placements)
        E->>AW: write(atlas, <name>.png)
        Note over AW: A4 tiles composited from their<br/>quarters onto a transparent canvas
        AW->>FS: <name>.png
        E->>GM: map(atlas)
        GM-->>GM: tile_collision_to_godot() (semantic → geometry)
        GM-->>E: GodotAtlasMapping
        E->>TB: build(mapping, atlas_path)
        TB-->>TB: validate grid alignment + bounds
        TB-->>E: GodotTileSet
        E->>RW: write(tileset, <name>.tres, texture_path)
        RW-->>RW: GodotResourceSerializer → .tres text
        RW->>FS: <name>.tres
    end
    E-->>CLI: generated paths (atlas + resource)
```

## Character conversion (`--mode CHARACTER`)

Character spritesheets intentionally do **not** follow the sheets
generated by RPG Maker (RPG Maker has no `idle` concept). Each
character lives in its own file (e.g. `player-1.png`, `player-2.png`,
…) and stores its animations natively, following the same fixed
9-row grid with at most three frames per row:

| Row | Animation  | Frames |
|-----|------------|--------|
| 1   | walk-down  | 3      |
| 2   | walk-left  | 3      |
| 3   | walk-right | 3      |
| 4   | walk-up    | 3      |
| 5   | idle-down  | 2      |
| 6   | idle-left  | 2      |
| 7   | idle-right | 2      |
| 8   | idle-up    | 2      |
| 9   | damaged    | 3      |

Two-frame rows simply leave their third cell empty (transparent). The
frame size is derived from the image size: the width holds exactly
three frames and the height exactly nine rows, so a 144×432 px sheet
stores 48×48 frames.

A character spritesheet cannot be told apart from an arbitrary PNG by
its name alone, so the processing is selected explicitly with
`--mode CHARACTER` (tilesets remain the default `--mode TILESET`).
The pipeline then runs in three steps:

1. **Analyzing** — `CharacterDetector` scans every `.png` of the
   input directory and validates the layout (width divisible by 3,
   height divisible by 9). Invalid files are reported as warnings and
   skipped, like in the tileset pipeline.
2. **Building sprite frames** — `CharacterSpriteSheetBuilder` turns
   each row into a `CharacterAnimation` following the layout table:
   `walk-*` at 6 fps and `idle-*` at 2 fps (both looping), and
   `damaged` at 8 fps, played once.
3. **Exporting** — `CharacterExporter` copies the spritesheet PNG
   into the output directory and writes one `<name>.tres` Godot
   `SpriteFrames` resource — 23 `AtlasTexture` sub-resources for a
   full sheet — ready to be assigned to an `AnimatedSprite2D`.

```bash
rpgmaker2godot --mode CHARACTER "C:/RPG Maker/MyProject/img/characters" "C:/Godot/MyGame/assets/characters"
```

The output directory therefore receives, per character:
`<name>.png` (the copied spritesheet) and `<name>.tres` (the
`SpriteFrames` resource referencing it through a `res://` path).