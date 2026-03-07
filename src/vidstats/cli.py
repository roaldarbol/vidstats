from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Annotated, Optional

import typer

from .hwaccel import detect_hwaccel
from .metrics import ALL_METRICS, COLUMN_NAMES, METRIC_DESCRIPTIONS, validate_metrics
from .output import SUPPORTED_FORMATS, infer_format, write
from .parse import parse
from .probe import FFprobeError, FFprobeNotFoundError, build_command, get_fps, run

app = typer.Typer(
    name="vidstats",
    help=(
        "Extract per-frame colour and luminosity metrics from a video "
        "using ffprobe's signalstats filter."
    ),
    add_completion=True,
)


class TimestampMode(str, Enum):
    frames = "frames"
    seconds = "seconds"
    both = "both"


def _echo_err(msg: str) -> None:
    typer.echo(msg, err=True)


def _abort(msg: str) -> None:
    _echo_err(f"Error: {msg}")
    raise typer.Exit(code=1)


def _list_metrics_callback(value: bool | None) -> None:
    if not value:
        return
    ffprobe_w = max(len(m) for m in ALL_METRICS)
    col_w = max(len(COLUMN_NAMES[m]) for m in ALL_METRICS)
    header = f"  {'ffprobe name':<{ffprobe_w}}  {'output column':<{col_w}}  description"
    typer.echo(header)
    typer.echo("  " + "-" * (ffprobe_w + col_w + len("  description") + 4))
    for m in ALL_METRICS:
        typer.echo(
            f"  {m:<{ffprobe_w}}  {COLUMN_NAMES[m]:<{col_w}}  {METRIC_DESCRIPTIONS[m]}"
        )
    raise typer.Exit()


@app.command()
def main(
    input: Annotated[
        Path,
        typer.Argument(help="Input video file."),
    ],
    output: Annotated[
        Path,
        typer.Argument(
            help=(
                "Output file. Format is inferred from the extension "
                f"({', '.join(sorted({'.parquet', '.csv', '.tsv', '.ipc', '.arrow', '.feather', '.ndjson', '.jsonl'}))})."
            )
        ),
    ],
    metrics: Annotated[
        Optional[str],
        typer.Option(
            "--metrics", "-m",
            help=(
                "Comma-separated list of signalstats metrics to extract "
                "(e.g. YAVG,UAVG,SATAVG). Defaults to all metrics. "
                "Run --list-metrics to see available names."
            ),
        ),
    ] = None,
    crop: Annotated[
        Optional[str],
        typer.Option(
            "--crop",
            help=(
                "Crop region applied before metric extraction, as 'X Y W H' "
                "(top-left pixel coordinates and dimensions, space-separated)."
            ),
        ),
    ] = None,
    timestamps: Annotated[
        TimestampMode,
        typer.Option(
            "--timestamps", "-t",
            help=(
                "Timestamp columns to include: "
                "'frames' (zero-based integer, default), "
                "'seconds' (float, requires FPS), or "
                "'both'."
            ),
        ),
    ] = TimestampMode.frames,
    fps: Annotated[
        Optional[float],
        typer.Option(
            "--fps",
            help=(
                "Override frame rate (frames per second) used to compute time_s. "
                "If not provided, FPS is read from the video stream metadata. "
                "Only relevant when --timestamps is 'seconds' or 'both'."
            ),
        ),
    ] = None,
    hwaccel: Annotated[
        Optional[str],
        typer.Option(
            "--hwaccel",
            help=(
                "Hardware acceleration backend for decoding (e.g. 'cuda'). "
                "Auto-detected by default. Only affects the decode stage."
            ),
        ),
    ] = None,
    no_hwaccel: Annotated[
        bool,
        typer.Option("--no-hwaccel", help="Disable hardware acceleration entirely."),
    ] = False,
    format: Annotated[
        Optional[str],
        typer.Option(
            "--format", "-f",
            help=(
                f"Override output format ({', '.join(SUPPORTED_FORMATS)}). "
                "Useful when the output extension does not match the desired format."
            ),
        ),
    ] = None,
    list_metrics: Annotated[
        Optional[bool],
        typer.Option(
            "--list-metrics",
            help="Print all available metric names and exit.",
            is_eager=True,
            callback=_list_metrics_callback,
        ),
    ] = None,
) -> None:

    # --- validate input file ---
    if not input.exists():
        _abort(f"Input file not found: '{input}'.")
    if not input.is_file():
        _abort(f"Input path is not a file: '{input}'.")

    # --- validate fps if provided ---
    if fps is not None and fps <= 0:
        _abort("--fps must be a positive number.")

    # --- resolve metrics ---
    if metrics:
        selected = [m.strip().upper() for m in metrics.split(",") if m.strip()]
        invalid = validate_metrics(selected)
        if invalid:
            _abort(
                f"Unknown metric(s): {', '.join(invalid)}. "
                f"Run --list-metrics to see valid names."
            )
    else:
        selected = ALL_METRICS

    # --- resolve crop ---
    crop_tuple: tuple[int, int, int, int] | None = None
    if crop is not None:
        try:
            parts = [int(v) for v in crop.split()]
            if len(parts) != 4:
                raise ValueError
            if any(v < 0 for v in parts):
                raise ValueError
            crop_tuple = (parts[0], parts[1], parts[2], parts[3])
        except ValueError:
            _abort("--crop must be four non-negative integers: 'X Y W H'.")

    # --- resolve output format ---
    try:
        fmt = infer_format(output, format)
    except ValueError as exc:
        _abort(str(exc))
        return  # unreachable, satisfies type checker

    # --- resolve hardware acceleration ---
    resolved_hwaccel: str | None
    if no_hwaccel:
        resolved_hwaccel = None
    elif hwaccel:
        resolved_hwaccel = hwaccel
        _echo_err(f"Hardware acceleration: {resolved_hwaccel} (user-specified).")
    else:
        resolved_hwaccel = detect_hwaccel()
        if resolved_hwaccel:
            _echo_err(f"Hardware acceleration: {resolved_hwaccel} (auto-detected).")

    # --- resolve fps for time_s column ---
    resolved_fps: float | None = None
    want_seconds = timestamps in (TimestampMode.seconds, TimestampMode.both)
    if want_seconds:
        if fps is not None:
            resolved_fps = fps
            _echo_err(f"FPS: {resolved_fps} (user-specified).")
        else:
            resolved_fps = get_fps(input)
            if resolved_fps is not None:
                _echo_err(f"FPS: {resolved_fps} (from stream metadata).")
            else:
                _echo_err(
                    "Warning: could not determine FPS from stream metadata. "
                    "time_s column will be omitted. Use --fps to provide it manually."
                )

    # --- build and run ffprobe ---
    try:
        cmd = build_command(
            input_path=input,
            metrics=selected,
            crop=crop_tuple,
            hwaccel=resolved_hwaccel,
        )
    except FFprobeNotFoundError as exc:
        _abort(str(exc))
        return

    _echo_err(f"Processing '{input}'...")

    try:
        stdout = run(cmd)
    except FFprobeError as exc:
        _abort(str(exc))
        return

    # --- parse and write ---
    df = parse(stdout, selected, resolved_fps)

    if len(df) == 0:
        _echo_err(
            "Warning: no frames were extracted. "
            "Check that the input is a valid video file."
        )

    _echo_err(f"Extracted {len(df)} frames, {len(df.columns)} columns.")

    try:
        write(df, output, fmt)
    except Exception as exc:
        _abort(f"Failed to write output: {exc}")

    _echo_err(f"Written to '{output}'.")


def cli() -> None:
    app()