# Tests for api.py
# - extract() returns a DataFrame
# - extract() with no arguments uses ALL_METRICS
# - extract() with metrics subset only returns those columns
# - extract() with include_time=False omits time_s
# - extract() with include_time=True and fps provided adds time_s
# - extract() with include_time=True and no fps calls get_fps
# - extract() passes crop to build_command
# - extract() passes hwaccel to build_command
# - extract() accepts str and Path input

from pathlib import Path
from unittest.mock import patch

import polars as pl
import pytest

from vidstats.api import extract
from vidstats.metrics import ALL_METRICS, COLUMN_NAMES

MOCK_STDOUT = "frame,128.0,64.0\nframe,130.0,65.0\n"
METRICS = ["YAVG", "UAVG"]
COL_NAMES = [COLUMN_NAMES[m] for m in METRICS]


@pytest.fixture
def mock_pipeline():
    """Mock build_command, run, and get_fps so no ffprobe is needed."""
    with (
        patch("vidstats.api.build_command", return_value=["ffprobe"]) as mock_cmd,
        patch("vidstats.api.run", return_value=MOCK_STDOUT) as mock_run,
        patch("vidstats.api.get_fps", return_value=25.0) as mock_fps,
    ):
        yield mock_cmd, mock_run, mock_fps


def test_extract_returns_dataframe(mock_pipeline):
    df = extract("spider.mp4", metrics=METRICS)
    assert isinstance(df, pl.DataFrame)


def test_extract_default_metrics(mock_pipeline):
    mock_cmd, mock_run, _ = mock_pipeline
    # Override stdout to have enough columns for ALL_METRICS
    mock_run.return_value = "frame," + ",".join(["1.0"] * len(ALL_METRICS)) + "\n"
    df = extract("spider.mp4")
    assert set(COLUMN_NAMES[m] for m in ALL_METRICS).issubset(set(df.columns))


def test_extract_metric_subset_columns(mock_pipeline):
    df = extract("spider.mp4", metrics=METRICS)
    for col in COL_NAMES:
        assert col in df.columns


def test_extract_no_time_column_by_default(mock_pipeline):
    df = extract("spider.mp4", metrics=METRICS)
    assert "time_s" not in df.columns


def test_extract_include_time_with_fps(mock_pipeline):
    mock_cmd, _, _ = mock_pipeline
    df = extract("spider.mp4", metrics=METRICS, include_time=True, fps=25.0)
    assert "time_s" in df.columns


def test_extract_include_time_calls_get_fps(mock_pipeline):
    _, _, mock_fps = mock_pipeline
    extract("spider.mp4", metrics=METRICS, include_time=True)
    mock_fps.assert_called_once()


def test_extract_explicit_fps_skips_get_fps(mock_pipeline):
    _, _, mock_fps = mock_pipeline
    extract("spider.mp4", metrics=METRICS, include_time=True, fps=30.0)
    mock_fps.assert_not_called()


def test_extract_passes_crop(mock_pipeline):
    mock_cmd, _, _ = mock_pipeline
    extract("spider.mp4", metrics=METRICS, crop=(10, 20, 100, 100))
    call_kwargs = mock_cmd.call_args
    assert call_kwargs.kwargs["crop"] == (10, 20, 100, 100)


def test_extract_passes_hwaccel(mock_pipeline):
    mock_cmd, _, _ = mock_pipeline
    extract("spider.mp4", metrics=METRICS, hwaccel="cuda")
    call_kwargs = mock_cmd.call_args
    assert call_kwargs.kwargs["hwaccel"] == "cuda"


def test_extract_accepts_str_input(mock_pipeline):
    df = extract("spider.mp4", metrics=METRICS)
    assert isinstance(df, pl.DataFrame)


def test_extract_accepts_path_input(mock_pipeline):
    df = extract(Path("spider.mp4"), metrics=METRICS)
    assert isinstance(df, pl.DataFrame)