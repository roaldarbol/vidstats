from __future__ import annotations

import shutil
import subprocess


def detect_hwaccel() -> str | None:
    """
    Probe ffprobe for available hardware acceleration backends.

    Returns the backend name (e.g. ``"cuda"``) if CUDA is available,
    otherwise ``None``. Only accelerates the decode stage; signalstats
    itself runs on CPU regardless. Most useful for large or high-fps videos.
    """
    if shutil.which("ffprobe") is None:
        return None

    try:
        result = subprocess.run(
            ["ffprobe", "-hwaccels"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        backends = result.stdout.lower().splitlines()
        if any("cuda" in line for line in backends):
            return "cuda"
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return None
