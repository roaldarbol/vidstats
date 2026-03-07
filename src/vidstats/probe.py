from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class FFprobeNotFoundError(RuntimeError):
    pass


class FFprobeError(RuntimeError):
    pass


def _check_ffprobe() -> None:
    if shutil.which("ffprobe") is None:
        raise FFprobeNotFoundError(
            "ffprobe not found on PATH. "
            "Install ffmpeg (e.g. `conda install -c conda-forge ffmpeg`)."
        )


def _build_filter_graph(input_path: Path, crop: tuple[int, int, int, int] | None) -> str:
    """
    Construct the lavfi filter graph string.

    Crop tuple is (x, y, w, h) in pixels. ffmpeg crop filter takes w:h:x:y.
    """
    graph = f"movie={input_path.as_posix()}"
    if crop is not None:
        x, y, w, h = crop
        graph += f",crop={w}:{h}:{x}:{y}"
    graph += ",signalstats=stat=tout+vrep+brng"
    return graph


def get_fps(input_path: Path) -> float | None:
    """
    Return the frame rate of the first video stream as a float, or ``None``
    if it cannot be determined.

    Parameters
    ----------
    input_path:
        Path to the video file.

    Returns
    -------
    float | None
        Frames per second, or ``None`` if the stream metadata is absent or
        unparseable.
    """
    _check_ffprobe()
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-select_streams", "v:0",
            "-show_entries", "stream=r_frame_rate",
            "-print_format", "default=noprint_wrappers=1:nokey=1",
            str(input_path),
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    raw = result.stdout.strip()  # e.g. "25/1" or "30000/1001"
    try:
        num, den = raw.split("/")
        fps = float(num) / float(den)
        if fps <= 0:
            return None
        return fps
    except Exception:
        return None


def build_command(
    input_path: Path,
    metrics: list[str],
    crop: tuple[int, int, int, int] | None,
    hwaccel: str | None,
) -> list[str]:
    """
    Build the ffprobe command to extract signalstats metrics per frame.

    Parameters
    ----------
    input_path:
        Path to the input video file.
    metrics:
        Signalstats metric names (without the ``lavfi.signalstats.`` prefix).
    crop:
        Optional (x, y, w, h) crop region in pixels, applied before signalstats.
    hwaccel:
        Hardware acceleration backend name (e.g. ``"cuda"``), or ``None``.

    Returns
    -------
    list[str]
        Command as a list of arguments suitable for ``subprocess``.
    """
    _check_ffprobe()

    cmd: list[str] = ["ffprobe"]

    if hwaccel:
        cmd += ["-hwaccel", hwaccel]

    cmd += ["-f", "lavfi", "-i", _build_filter_graph(input_path, crop)]

    tags = ",".join(f"lavfi.signalstats.{m}" for m in metrics)

    cmd += [
        "-show_entries", f"frame_tags={tags}",
        "-print_format", "csv",
        "-v", "quiet",
    ]

    return cmd


def run(cmd: list[str]) -> str:
    """
    Execute the ffprobe command and return stdout as a string.

    Raises
    ------
    FFprobeError
        If ffprobe exits with a non-zero return code.
    """
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise FFprobeError(
            f"ffprobe exited with code {result.returncode}.\n"
            f"stderr: {result.stderr.strip()}"
        )
    return result.stdout