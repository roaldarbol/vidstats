# Tests for probe.py
# - build_command returns a list starting with "ffprobe"
# - build_command includes -f lavfi and -i
# - build_command injects crop filter when crop is provided
# - build_command omits crop filter when crop is None
# - build_command includes hwaccel flags when hwaccel is set
# - build_command omits hwaccel flags when hwaccel is None
# - build_command never includes pkt_pts_time (time handled via fps in parse)
# - build_command includes all requested metric tags
# - get_fps returns None when ffprobe output is unparseable
# - _check_ffprobe raises FFprobeNotFoundError when ffprobe is absent

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vidstats.probe import FFprobeNotFoundError, build_command, get_fps

VIDEO = Path("spider.mp4")
METRICS = ["YAVG", "UAVG"]


def test_command_starts_with_ffprobe():
    cmd = build_command(VIDEO, METRICS, None, None)
    assert cmd[0] == "ffprobe"


def test_command_includes_lavfi():
    cmd = build_command(VIDEO, METRICS, None, None)
    assert "-f" in cmd
    assert "lavfi" in cmd


def test_command_includes_input_flag():
    cmd = build_command(VIDEO, METRICS, None, None)
    assert "-i" in cmd


def test_no_crop_filter():
    cmd = build_command(VIDEO, METRICS, None, None)
    i_idx = cmd.index("-i")
    filter_graph = cmd[i_idx + 1]
    assert "crop" not in filter_graph


def test_crop_filter_injected():
    cmd = build_command(VIDEO, METRICS, (10, 20, 200, 200), None)
    i_idx = cmd.index("-i")
    filter_graph = cmd[i_idx + 1]
    assert "crop=200:200:10:20" in filter_graph


def test_crop_filter_before_signalstats():
    cmd = build_command(VIDEO, METRICS, (0, 0, 100, 100), None)
    i_idx = cmd.index("-i")
    filter_graph = cmd[i_idx + 1]
    crop_pos = filter_graph.index("crop")
    sig_pos = filter_graph.index("signalstats")
    assert crop_pos < sig_pos


def test_hwaccel_flags_present():
    cmd = build_command(VIDEO, METRICS, None, "cuda")
    assert "-hwaccel" in cmd
    assert "cuda" in cmd


def test_hwaccel_flags_absent():
    cmd = build_command(VIDEO, METRICS, None, None)
    assert "-hwaccel" not in cmd


def test_no_pkt_pts_time_in_command():
    cmd = build_command(VIDEO, METRICS, None, None)
    assert "pkt_pts_time" not in " ".join(cmd)


def test_metric_tags_present():
    cmd = build_command(VIDEO, METRICS, None, None)
    joined = " ".join(cmd)
    for m in METRICS:
        assert f"lavfi.signalstats.{m}" in joined


def test_ffprobe_not_found_raises():
    with patch("shutil.which", return_value=None):
        with pytest.raises(FFprobeNotFoundError):
            build_command(VIDEO, METRICS, None, None)


def test_get_fps_returns_none_on_bad_output():
    mock_result = MagicMock()
    mock_result.stdout = "not/a/valid/fraction"
    with patch("subprocess.run", return_value=mock_result):
        with patch("shutil.which", return_value="/usr/bin/ffprobe"):
            result = get_fps(VIDEO)
    assert result is None


def test_get_fps_returns_none_on_empty_output():
    mock_result = MagicMock()
    mock_result.stdout = ""
    with patch("subprocess.run", return_value=mock_result):
        with patch("shutil.which", return_value="/usr/bin/ffprobe"):
            result = get_fps(VIDEO)
    assert result is None


def test_get_fps_parses_fraction():
    mock_result = MagicMock()
    mock_result.stdout = "30000/1001\n"
    with patch("subprocess.run", return_value=mock_result):
        with patch("shutil.which", return_value="/usr/bin/ffprobe"):
            result = get_fps(VIDEO)
    assert result == pytest.approx(29.97, abs=0.01)


def test_get_fps_parses_integer_fraction():
    mock_result = MagicMock()
    mock_result.stdout = "25/1\n"
    with patch("subprocess.run", return_value=mock_result):
        with patch("shutil.which", return_value="/usr/bin/ffprobe"):
            result = get_fps(VIDEO)
    assert result == pytest.approx(25.0)