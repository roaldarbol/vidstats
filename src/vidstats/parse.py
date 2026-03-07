from __future__ import annotations

import polars as pl

from .metrics import COLUMN_NAMES

_NA_VALUES = {"N/A", "n/a", "", "nan"}


def _safe_float(value: str) -> float | None:
    if value.strip() in _NA_VALUES:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse(
    stdout: str,
    metrics: list[str],
    fps: float | None,
) -> pl.DataFrame:
    """
    Parse ffprobe CSV stdout into a Polars DataFrame.

    The CSV rows have the structure::

        frame,<metric1>,<metric2>,...

    Column 0 is always the literal string ``"frame"`` (ffprobe section name)
    and is discarded. Frame numbers are assigned as a zero-based integer index.
    Metric columns are named using descriptive snake_case names from
    :data:`~vidstats.metrics.COLUMN_NAMES`.

    If ``fps`` is provided, a ``time_s`` column is computed as
    ``frame / fps``. If ``fps`` is ``None``, the column is omitted.

    Parameters
    ----------
    stdout:
        Raw stdout string from ffprobe.
    metrics:
        Ordered list of ffprobe metric names matching the order in the
        ffprobe command.
    fps:
        Frames per second used to compute ``time_s``. Pass ``None`` to
        omit the timestamp column.

    Returns
    -------
    pl.DataFrame
        Columns: ``frame`` (UInt32), optionally ``time_s`` (Float64),
        then one Float32 column per metric using descriptive snake_case names.
    """
    frame_nums: list[int] = []
    metric_cols: dict[str, list[float | None]] = {m: [] for m in metrics}

    for frame_num, line in enumerate(stdout.splitlines()):
        line = line.strip()
        if not line:
            continue

        parts = line.split(",")
        # parts[0] == "frame" (section label), always discard
        offset = 1

        frame_nums.append(frame_num)

        for metric in metrics:
            val = parts[offset] if len(parts) > offset else None
            metric_cols[metric].append(_safe_float(val) if val is not None else None)
            offset += 1

    schema: dict[str, pl.Series] = {
        "frame": pl.Series("frame", frame_nums, dtype=pl.UInt32),
    }

    if fps is not None:
        time_s = [n / fps for n in frame_nums]
        schema["time_s"] = pl.Series("time_s", time_s, dtype=pl.Float64)

    for metric, values in metric_cols.items():
        col_name = COLUMN_NAMES[metric]
        schema[col_name] = pl.Series(col_name, values, dtype=pl.Float32)

    return pl.DataFrame(schema)