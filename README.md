# vidstats

Extract per-frame colour and luminosity metrics from video using
[ffprobe's `signalstats` filter](https://ffmpeg.org/ffmpeg-filters.html#signalstats).
Output goes to Parquet, CSV, IPC/Feather, or NDJSON.

Designed for research pipelines that need a fast, dependency-light way to turn
a video into a tabular time series — for example, non-contact cardiac monitoring
in animals via colour/motion video analysis.

## Installation

**pixi** (recommended — pulls in ffmpeg automatically):

```bash
pixi global install vidstats
```

**uv** (global install):

```bash
uv tool install vidstats
```

**conda**:

```bash
conda install -c conda-forge vidstats
```

**pip** (requires ffmpeg on PATH separately):

```bash
pip install vidstats
```

## Usage

```bash
# Extract all metrics → Parquet
vidstats spider_abdomen.mp4 output.parquet

# Extract only luminance and saturation averages → CSV
vidstats spider_abdomen.mp4 output.csv --metrics YAVG,SATAVG

# Include both frame number and timestamp in seconds
vidstats spider_abdomen.mp4 output.parquet --timestamps both

# Override FPS when stream metadata is missing or wrong
vidstats spider_abdomen.mp4 output.parquet --timestamps both --fps 30

# Apply a crop region (X Y W H) before extraction
vidstats spider_abdomen.mp4 output.parquet --crop "10 20 180 180"

# Force format regardless of extension
vidstats spider_abdomen.mp4 output.dat --format csv

# Disable hardware acceleration
vidstats spider_abdomen.mp4 output.parquet --no-hwaccel

# List all available metric names and their output column names
vidstats --list-metrics
```

## Supported output formats

| Extension(s)                   | Format    |
|--------------------------------|-----------|
| `.parquet`                     | Parquet   |
| `.csv`                         | CSV       |
| `.tsv`                         | TSV       |
| `.ipc`, `.arrow`, `.feather`   | Arrow IPC |
| `.ndjson`, `.jsonl`            | NDJSON    |

## Available metrics

All 25 `signalstats` metrics are extracted by default. Run
`vidstats --list-metrics` for the full table of ffprobe names, output column
names, and descriptions. They cover:

- **Luminance**: `YMIN`, `YLOW`, `YAVG`, `YHIGH`, `YMAX`
- **Cb chrominance (U)**: same set of five
- **Cr chrominance (V)**: same set of five
- **Saturation**: `SATMIN`, `SATLOW`, `SATAVG`, `SATHIGH`, `SATMAX`
- **Hue**: `HUEMED`, `HUEAVG`
- **Quality flags**: `TOUT`, `VREP`, `BRNG`

The `--metrics` flag accepts ffprobe names (e.g. `YAVG,SATAVG`).
Output columns use descriptive snake_case names (e.g. `luminance_mean`,
`saturation_mean`) — see `--list-metrics` for the full mapping.

## Output schema

| Column    | Type    | Condition                          |
|-----------|---------|------------------------------------|
| `frame`   | UInt32  | always                             |
| `time_s`  | Float64 | `--timestamps seconds` or `both`   |
| metrics…  | Float32 | selected metrics                   |

`time_s` is computed as `frame / fps`. FPS is read from stream metadata
automatically; use `--fps` to override it or supply it when metadata is absent.

## Hardware acceleration

vidstats auto-detects CUDA and passes `-hwaccel cuda` to ffprobe if available.
This accelerates the **decode** stage only — `signalstats` itself always runs
on CPU. For small (e.g. 200×200) videos the gain is negligible, but the
detection is there for larger inputs. Suppress with `--no-hwaccel`.

No special CUDA packages or drivers are required beyond what you already have.
vidstats uses ffprobe's built-in NVDEC hardware decoding, which talks directly
to the NVIDIA driver on your system — there is no `cudatoolkit`, no
`pytorch-cuda`, and no GPU-specific installation step.

## License

MIT