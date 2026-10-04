"""Busca cada canción en YouTube y la descarga con yt-dlp."""
import subprocess
from concurrent.futures import ThreadPoolExecutor

from .config import HAS_FFMPEG, MUSIC_DIR, find_ytdlp, load_settings, ytdlp_quality
from .log import log
from .util import sanitize

AUDIO_EXTS = (".mp3", ".m4a", ".webm", ".opus", ".ogg", ".mp4")


def _track_dir(track: dict):
    return MUSIC_DIR / sanitize(track["artist"]) / sanitize(track["album"])


def already_downloaded(track: dict) -> bool:
    folder, title = _track_dir(track), sanitize(track["title"])
    return any((folder / f"{title}{ext}").exists() for ext in AUDIO_EXTS)


def download_track(track: dict, idx: int, total: int, ytdlp: str, quality: str) -> bool:
    label = f"{track['artist']} - {track['title']}"
    if already_downloaded(track):
        log(f"  [{idx}/{total}] YA: {label}")
        return True

    out_dir, title = _track_dir(track), sanitize(track["title"])
    out_dir.mkdir(parents=True, exist_ok=True)
    ext = ".mp3" if HAS_FFMPEG else ".m4a"

    cmd = [
        ytdlp,
        "--extract-audio",
        "--audio-quality", ytdlp_quality(quality),
        "--audio-format", ext[1:],
        "--format", "bestaudio/best",
        "--no-playlist",
        "--retries", "3",
        "--fragment-retries", "3",
        "--no-warnings",
        "-o", str(out_dir / f"{title}.%(ext)s"),
        f"ytsearch1:{label}",
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        pass

    for found in AUDIO_EXTS:
        candidate = out_dir / f"{title}{found}"
        if candidate.exists():
            if found != ext:
                candidate.rename(out_dir / f"{title}{ext}")
            log(f"  [{idx}/{total}] OK: {label}")
            return True

    log(f"  [{idx}/{total}] ERROR: {label}")
    return False


def download_batch(tracks: list[dict]) -> tuple[int, int]:
    ytdlp = find_ytdlp()
    cfg = load_settings()
    quality, batch_size = cfg["quality"], cfg["batch_size"]
    log(f"[DOWNLOAD] Calidad: {quality}, simultáneas: {batch_size}")
    total, ok = len(tracks), 0
    n_batches = (total + batch_size - 1) // batch_size

    for start in range(0, total, batch_size):
        batch = tracks[start:start + batch_size]
        log(f"\n[LOTE {start // batch_size + 1}/{n_batches}] ({len(batch)} tracks)\n")
        with ThreadPoolExecutor(max_workers=len(batch)) as pool:
            futures = [
                pool.submit(download_track, t, start + i + 1, total, ytdlp, quality)
                for i, t in enumerate(batch)
            ]
            for f in futures:
                try:
                    ok += bool(f.result())
                except Exception as e:
                    log(f"  [ERROR] {e}")

    log(f"\n[DOWNLOAD] {ok} OK, {total - ok} errores de {total}")
    return ok, total - ok
