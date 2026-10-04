"""Busca cada canción en YouTube y la descarga con yt-dlp."""
import subprocess
from concurrent.futures import ThreadPoolExecutor

from .config import BATCH_SIZE, HAS_FFMPEG, MUSIC_DIR, find_ytdlp
from .log import log
from .util import sanitize

AUDIO_EXTS = (".mp3", ".m4a", ".webm", ".opus", ".ogg", ".mp4")


def _track_dir(track: dict):
    return MUSIC_DIR / sanitize(track["artist"]) / sanitize(track["album"])


def already_downloaded(track: dict) -> bool:
    folder, title = _track_dir(track), sanitize(track["title"])
    return any((folder / f"{title}{ext}").exists() for ext in AUDIO_EXTS)


def download_track(track: dict, idx: int, total: int, ytdlp: str) -> bool:
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
        "--audio-quality", "0",
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
    total, ok = len(tracks), 0
    n_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE

    for start in range(0, total, BATCH_SIZE):
        batch = tracks[start:start + BATCH_SIZE]
        log(f"\n[LOTE {start // BATCH_SIZE + 1}/{n_batches}] ({len(batch)} tracks)\n")
        with ThreadPoolExecutor(max_workers=len(batch)) as pool:
            futures = [
                pool.submit(download_track, t, start + i + 1, total, ytdlp)
                for i, t in enumerate(batch)
            ]
            for f in futures:
                try:
                    ok += bool(f.result())
                except Exception as e:
                    log(f"  [ERROR] {e}")

    log(f"\n[DOWNLOAD] {ok} OK, {total - ok} errores de {total}")
    return ok, total - ok
