from __future__ import annotations

from pathlib import Path

import polars as pl


# Maps file extension -> Polars write method name.
EXTENSION_MAP: dict[str, str] = {
    ".parquet": "parquet",
    ".csv":     "csv",
    ".tsv":     "csv",
    ".ipc":     "ipc",
    ".arrow":   "ipc",
    ".feather": "ipc",
    ".ndjson":  "ndjson",
    ".jsonl":   "ndjson",
}

SUPPORTED_FORMATS: list[str] = sorted(set(EXTENSION_MAP.values()))


def infer_format(path: Path, override: str | None) -> str:
    """
    Resolve the output format from the file extension or an explicit override.

    Parameters
    ----------
    path:
        Output file path. Extension is used when ``override`` is ``None``.
    override:
        Explicit format name (e.g. ``"csv"``). Must be in
        :data:`SUPPORTED_FORMATS` if provided.

    Returns
    -------
    str
        Resolved format name.

    Raises
    ------
    ValueError
        If the extension is unsupported or the override is not recognised.
    """
    if override is not None:
        if override not in SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format '{override}'. "
                f"Choose from: {', '.join(SUPPORTED_FORMATS)}."
            )
        return override

    ext = path.suffix.lower()
    if ext not in EXTENSION_MAP:
        raise ValueError(
            f"Cannot infer format from extension '{ext}'. "
            f"Supported extensions: {', '.join(sorted(EXTENSION_MAP))}. "
            f"Use --format to override."
        )
    return EXTENSION_MAP[ext]


def write(df: pl.DataFrame, path: Path, fmt: str) -> None:
    """
    Write a Polars DataFrame to ``path`` in the given format.

    Parameters
    ----------
    df:
        DataFrame to write.
    path:
        Destination file path. Parent directories are created if needed.
    fmt:
        Format name as returned by :func:`infer_format`.

    Raises
    ------
    ValueError
        If ``fmt`` is not recognised.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    match fmt:
        case "parquet":
            df.write_parquet(path)
        case "csv":
            separator = "\t" if path.suffix.lower() == ".tsv" else ","
            df.write_csv(path, separator=separator)
        case "ipc":
            df.write_ipc(path)
        case "ndjson":
            df.write_ndjson(path)
        case _:
            raise ValueError(f"Unknown format: '{fmt}'.")
