# vidstats

Extract per-frame colour and luminosity metrics from video using
[ffprobe's `signalstats` filter](https://ffmpeg.org/ffmpeg-filters.html#signalstats).
Output goes to Parquet, CSV, IPC/Feather, or NDJSON.

Designed for research pipelines that need a fast, dependency-light way to turn
a video into a tabular time series — for example, non-contact cardiac monitoring
in animals via colour/motion video analysis.

## Installation

```bash
# With conda / pixi (recommended — pulls in ffmpeg automatically)
conda install -c conda-forge vidstats

# With pip (requires ffmpeg on PATH separately)
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

# Apply a crop region (X Y W H) before extraction
vidstats spider_abdomen.mp4 output.parquet --crop "10 20 180 180"

# Force format regardless of extension
vidstats spider_abdomen.mp4 output.dat --format csv

# Disable hardware acceleration
vidstats spider_abdomen.mp4 output.parquet --no-hwaccel

# List all available metric names
vidstats --list-metrics
```

## Supported output formats

| Extension(s)           | Format  |
|------------------------|---------|
| `.parquet`             | Parquet |
| `.csv`                 | CSV     |
| `.tsv`                 | TSV     |
| `.ipc`, `.arrow`, `.feather` | Arrow IPC |
| `.ndjson`, `.jsonl`    | NDJSON  |

## Available metrics

All 25 `signalstats` metrics are extracted by default. Run
`vidstats --list-metrics` for descriptions. They cover:

- **Y** — luminance: `YMIN`, `YLOW`, `YAVG`, `YHIGH`, `YMAX`
- **U / V** — chrominance (same set of five per channel)
- **Saturation**: `SATMIN`, `SATLOW`, `SATAVG`, `SATHIGH`, `SATMAX`
- **Hue**: `HUEMED`, `HUEAVG`
- **Quality flags**: `TOUT`, `VREP`, `BRNG`

## Output schema

| Column    | Type    | Condition              |
|-----------|---------|------------------------|
| `frame`   | UInt32  | always                 |
| `time_s`  | Float64 | `--timestamps seconds` or `both` |
| metrics…  | Float32 | selected metrics       |

## Hardware acceleration

vidstats auto-detects CUDA and passes `-hwaccel cuda` to ffprobe if
available. This accelerates the **decode** stage only — `signalstats`
itself always runs on CPU. For small (e.g. 200×200) videos the gain is
negligible, but the detection is there for larger inputs. Suppress with
`--no-hwaccel`.

## Integration with pixi

```toml
# pixi.toml
[dependencies]
vidstats = { version = ">=0.1.0", channel = "conda-forge" }
```

```bash
pixi run vidstats spider_abdomen.mp4 output.parquet
```

## License

MIT
