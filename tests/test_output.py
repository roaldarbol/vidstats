# Tests for output.py
# - infer_format resolves known extensions correctly
# - infer_format raises ValueError for unknown extensions
# - infer_format respects override argument
# - infer_format raises ValueError for invalid override
# - write produces a file at the specified path for each format
# - TSV separator is used when extension is .tsv


import polars as pl
import pytest

from vidstats.output import SUPPORTED_FORMATS, infer_format, write


@pytest.fixture
def simple_df() -> pl.DataFrame:
    return pl.DataFrame({
        "frame": pl.Series([0, 1, 2], dtype=pl.UInt32),
        "YAVG": pl.Series([100.0, 105.0, 98.0], dtype=pl.Float32),
    })


@pytest.mark.parametrize("ext,expected", [
    (".parquet", "parquet"),
    (".csv",     "csv"),
    (".tsv",     "csv"),
    (".ipc",     "ipc"),
    (".arrow",   "ipc"),
    (".feather", "ipc"),
    (".ndjson",  "ndjson"),
    (".jsonl",   "ndjson"),
])
def test_infer_format_extensions(ext, expected, tmp_path):
    p = tmp_path / f"output{ext}"
    assert infer_format(p, None) == expected


def test_infer_format_unknown_extension(tmp_path):
    with pytest.raises(ValueError, match="Cannot infer format"):
        infer_format(tmp_path / "output.xyz", None)


def test_infer_format_override_valid(tmp_path):
    p = tmp_path / "output.xyz"
    assert infer_format(p, "csv") == "csv"


def test_infer_format_override_invalid(tmp_path):
    p = tmp_path / "output.csv"
    with pytest.raises(ValueError, match="Unsupported format"):
        infer_format(p, "excel")


def test_supported_formats_nonempty():
    assert len(SUPPORTED_FORMATS) > 0


@pytest.mark.parametrize("fmt,ext", [
    ("parquet", ".parquet"),
    ("csv",     ".csv"),
    ("ipc",     ".ipc"),
    ("ndjson",  ".ndjson"),
])
def test_write_creates_file(simple_df, tmp_path, fmt, ext):
    p = tmp_path / f"out{ext}"
    write(simple_df, p, fmt)
    assert p.exists()
    assert p.stat().st_size > 0


def test_write_csv_roundtrip(simple_df, tmp_path):
    p = tmp_path / "out.csv"
    write(simple_df, p, "csv")
    loaded = pl.read_csv(p)
    assert loaded.shape == simple_df.shape


def test_write_parquet_roundtrip(simple_df, tmp_path):
    p = tmp_path / "out.parquet"
    write(simple_df, p, "parquet")
    loaded = pl.read_parquet(p)
    assert loaded.shape == simple_df.shape


def test_write_creates_parent_dirs(simple_df, tmp_path):
    p = tmp_path / "a" / "b" / "out.csv"
    write(simple_df, p, "csv")
    assert p.exists()


def test_write_tsv_uses_tab_separator(simple_df, tmp_path):
    p = tmp_path / "out.tsv"
    write(simple_df, p, "csv")
    content = p.read_text()
    assert "\t" in content
