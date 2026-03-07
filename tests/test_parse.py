# Tests for parse.py
# - Empty stdout returns empty DataFrame with correct schema
# - Frame numbers are zero-based sequential integers
# - Metrics parse as Float32 columns using snake_case COLUMN_NAMES
# - time_s column present and correct when fps is provided
# - time_s column absent when fps is None
# - time_s values are frame / fps
# - N/A values become null
# - Blank lines do not crash the parser
# - Column order matches: frame, (time_s,) then metrics in order

import polars as pl
import pytest

from vidstats.metrics import COLUMN_NAMES
from vidstats.parse import parse

METRICS = ["YAVG", "UAVG", "SATAVG"]
COL_NAMES = [COLUMN_NAMES[m] for m in METRICS]


def _make_stdout(rows: list[tuple]) -> str:
    lines = []
    for row in rows:
        parts = ["frame"] + [str(v) for v in row]
        lines.append(",".join(parts))
    return "\n".join(lines)


def test_empty_stdout_returns_empty_dataframe():
    df = parse("", METRICS, fps=None)
    assert len(df) == 0
    assert "frame" in df.columns
    assert "luminance_mean" in df.columns


def test_frame_column_dtype():
    df = parse("", METRICS, fps=None)
    assert df.schema["frame"] == pl.UInt32


def test_metric_columns_dtype():
    stdout = _make_stdout([(100.0, 64.0, 80.0)])
    df = parse(stdout, METRICS, fps=None)
    for col in COL_NAMES:
        assert df.schema[col] == pl.Float32


def test_metric_columns_use_snake_case_names():
    stdout = _make_stdout([(100.0, 64.0, 80.0)])
    df = parse(stdout, METRICS, fps=None)
    for col in COL_NAMES:
        assert col in df.columns
    for m in METRICS:
        assert m not in df.columns


def test_frame_numbers_zero_based():
    rows = [(100.0, 64.0, 80.0), (101.0, 65.0, 81.0), (99.0, 63.0, 79.0)]
    stdout = _make_stdout(rows)
    df = parse(stdout, METRICS, fps=None)
    assert df["frame"].to_list() == [0, 1, 2]


def test_metric_values_parsed_correctly():
    rows = [(128.5, 64.2, 90.1)]
    stdout = _make_stdout(rows)
    df = parse(stdout, METRICS, fps=None)
    assert df["luminance_mean"][0] == pytest.approx(128.5, abs=0.01)
    assert df["chroma_u_mean"][0] == pytest.approx(64.2, abs=0.01)


def test_fps_none_omits_time_column():
    stdout = _make_stdout([(100.0, 64.0, 80.0)])
    df = parse(stdout, METRICS, fps=None)
    assert "time_s" not in df.columns


def test_fps_provided_adds_time_column():
    rows = [(100.0, 64.0, 80.0), (101.0, 65.0, 81.0)]
    stdout = _make_stdout(rows)
    df = parse(stdout, METRICS, fps=25.0)
    assert "time_s" in df.columns
    assert df.schema["time_s"] == pl.Float64


def test_time_s_values_are_frame_over_fps():
    rows = [(100.0, 64.0, 80.0), (101.0, 65.0, 81.0), (99.0, 63.0, 79.0)]
    stdout = _make_stdout(rows)
    df = parse(stdout, METRICS, fps=25.0)
    assert df["time_s"][0] == pytest.approx(0.0 / 25.0)
    assert df["time_s"][1] == pytest.approx(1.0 / 25.0)
    assert df["time_s"][2] == pytest.approx(2.0 / 25.0)


def test_na_values_become_null():
    stdout = "frame,N/A,64.0,80.0"
    df = parse(stdout, METRICS, fps=None)
    assert df["luminance_mean"][0] is None


def test_blank_lines_skipped():
    stdout = "\nframe,100.0,64.0,80.0\n\nframe,101.0,65.0,81.0\n"
    df = parse(stdout, METRICS, fps=None)
    assert len(df) == 2


def test_column_order_without_time():
    stdout = _make_stdout([(100.0, 64.0, 80.0)])
    df = parse(stdout, METRICS, fps=None)
    assert df.columns == ["frame"] + COL_NAMES


def test_column_order_with_time():
    stdout = _make_stdout([(100.0, 64.0, 80.0)])
    df = parse(stdout, METRICS, fps=25.0)
    assert df.columns == ["frame", "time_s"] + COL_NAMES