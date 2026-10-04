import json
import os
import shutil
import sys
from pathlib import Path

MUSIC_DIR = Path(os.environ.get("MUSIC_DIR", "music"))
CONFIG_DIR = Path(os.environ.get("CONFIG_DIR", "config"))
SETTINGS_FILE = CONFIG_DIR / "settings.json"
HAS_FFMPEG = shutil.which("ffmpeg") is not None

# Navidrome es opcional. NAVIDROME_ENABLED lo activa en el panel;
# NAVIDROME_URL/USER/PASSWORD (opcionales) permiten forzar un reescaneo al terminar.
NAVIDROME_ENABLED = os.environ.get("NAVIDROME_ENABLED", "").lower() in ("1", "true", "yes")
NAVIDROME_PORT = os.environ.get("NAVIDROME_PORT", "4533")
NAVIDROME_URL = os.environ.get("NAVIDROME_URL", "").rstrip("/")
NAVIDROME_USER = os.environ.get("NAVIDROME_USER", "")
NAVIDROME_PASSWORD = os.environ.get("NAVIDROME_PASSWORD", "")

QUALITIES = ("best", "320", "256", "192", "128")

# Ajustes editables desde el panel web (se guardan en config/settings.json).
DEFAULT_SETTINGS = {
    "quality": "320",       # kbps del MP3, o "best"
    "batch_size": 3,        # descargas simultáneas
    "covers": True,         # descargar e incrustar carátulas
}


def load_settings() -> dict:
    settings = dict(DEFAULT_SETTINGS)
    settings["batch_size"] = int(os.environ.get("BATCH_SIZE", settings["batch_size"]))
    try:
        settings.update(json.loads(SETTINGS_FILE.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    return settings


def save_settings(new: dict) -> dict:
    """Valida y guarda; ignora claves desconocidas."""
    settings = load_settings()
    if new.get("quality") in QUALITIES:
        settings["quality"] = new["quality"]
    if isinstance(new.get("batch_size"), int):
        settings["batch_size"] = max(1, min(new["batch_size"], 8))
    if isinstance(new.get("covers"), bool):
        settings["covers"] = new["covers"]
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    return settings


def ytdlp_quality(quality: str) -> str:
    return "0" if quality == "best" else f"{quality}K"


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
