from __future__ import annotations

from pathlib import Path

import polars as pl

from .metrics import ALL_METRICS
from .parse import parse
from .probe import build_command, get_fps, run


def extract(
    input: str | Path,
    metrics: list[str] | None = None,
    crop: tuple[int, int, int, int] | None = None,
    fps: float | None = None,
    hwaccel: str | None = None,
    include_time: bool = False,
) -> pl.DataFrame:
    """
    Extract per-frame signalstats metrics from a video into a Polars DataFrame.

    This is a convenience wrapper around :func:`~vidstats.probe.build_command`,
    :func:`~vidstats.probe.run`, and :func:`~vidstats.parse.parse`.

    Parameters
    ----------
    input:
        Path to the input video file.
    metrics:
        List of ffprobe metric names to extract (e.g. ``["YAVG", "SATAVG"]``).
        Defaults to all 25 metrics. See :data:`~vidstats.ALL_METRICS` for valid
        names, and :data:`~vidstats.COLUMN_NAMES` for the output column names
        they map to.
    crop:
        Optional ``(x, y, w, h)`` crop region in pixels, applied before
        metric extraction.
    fps:
        Frames per second used to compute the ``time_s`` column. Only relevant
        when ``include_time=True``. If ``None``, FPS is read from the video
        stream metadata. If that also fails, ``time_s`` is omitted.
    hwaccel:
        Hardware acceleration backend for ffprobe decoding (e.g. ``"cuda"``).
        ``None`` disables hardware acceleration.
    include_time:
        If ``True``, include a ``time_s`` column computed as ``frame / fps``.

    Returns
    -------
    pl.DataFrame
        Columns: ``frame`` (UInt32), optionally ``time_s`` (Float64), then one
        Float32 column per metric using descriptive snake_case names.

    Examples
    --------
    Extract all metrics:

    >>> import vidstats
    >>> df = vidstats.extract("spider_abdomen.mp4")

    Extract a subset of metrics with timestamps:

    >>> df = vidstats.extract(
    ...     "spider_abdomen.mp4",
    ...     metrics=["YAVG", "SATAVG", "HUEMED"],
    ...     include_time=True,
    ... )

    With a crop region and explicit FPS:

    >>> df = vidstats.extract(
    ...     "spider_abdomen.mp4",
    ...     crop=(10, 20, 180, 180),
    ...     fps=25.0,
    ...     include_time=True,
    ... )
    """
    input_path = Path(input)
    selected = metrics if metrics is not None else ALL_METRICS

    resolved_fps: float | None = None
    if include_time:
        resolved_fps = fps if fps is not None else get_fps(input_path)

    cmd = build_command(
        input_path=input_path,
        metrics=selected,
        crop=crop,
        hwaccel=hwaccel,
    )
    stdout = run(cmd)
    return parse(stdout, selected, resolved_fps)