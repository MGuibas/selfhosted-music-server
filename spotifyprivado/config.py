import os
import shutil
import sys
from pathlib import Path

MUSIC_DIR = Path(os.environ.get("MUSIC_DIR", "music"))
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "3"))
HAS_FFMPEG = shutil.which("ffmpeg") is not None

# Opcional: si se define, se pide a Navidrome que reescanee al terminar.
NAVIDROME_URL = os.environ.get("NAVIDROME_URL", "").rstrip("/")
NAVIDROME_USER = os.environ.get("NAVIDROME_USER", "")
NAVIDROME_PASSWORD = os.environ.get("NAVIDROME_PASSWORD", "")


def find_ytdlp() -> str:
    found = shutil.which("yt-dlp") or shutil.which("yt_dlp")
    if found:
        return found
    for cand in (
        Path(sys.prefix) / "Scripts" / "yt-dlp.exe",
        Path(sys.prefix) / "bin" / "yt-dlp",
    ):
        if cand.exists():
            return str(cand)
    raise RuntimeError("yt-dlp no encontrado. Ejecuta: pip install -r requirements.txt")
