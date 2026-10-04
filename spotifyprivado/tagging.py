"""Etiquetas ID3 y carátulas (Spotify -> iTunes como respaldo)."""
import requests
from mutagen.easyid3 import EasyID3
from mutagen.id3 import APIC
from mutagen.mp3 import MP3

from .config import MUSIC_DIR
from .log import log


def parse_artists(folder_name: str) -> tuple[str, list[str]]:
    """'Artista, Feat1, Feat2' -> ('Artista', ['Feat1', 'Feat2'])."""
    parts = [p.strip() for p in folder_name.split(",")]
    return parts[0], parts[1:]


def get_itunes_cover(artist: str, album: str) -> str | None:
    try:
        resp = requests.get(
            "https://itunes.apple.com/search",
            params={"term": f"{artist} {album}", "entity": "album", "limit": 1},
            timeout=10,
        )
        results = resp.json().get("results", []) if resp.status_code == 200 else []
        if results and results[0].get("artworkUrl100"):
            return results[0]["artworkUrl100"].replace("100x100bb", "1200x1200bb")
    except Exception:
        pass
    return None


def download_cover(url: str) -> bytes | None:
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200 and len(resp.content) > 1000:
            return resp.content
    except Exception:
        pass
    return None


def embed_cover(mp3_path, data: bytes) -> bool:
    try:
        audio = MP3(str(mp3_path))
        if audio.tags is None:
            audio.add_tags()
        mime = "image/png" if data[:4] == b"\x89PNG" else "image/jpeg"
        audio.tags["APIC"] = APIC(encoding=3, mime=mime, type=3, desc="Cover", data=data)
        audio.save()
        return True
    except Exception as e:
        log(f"    [APIC ERROR] {e}")
        return False


def apply_tags_and_covers(covers: dict | None = None) -> None:
    """Recorre music/Artista/Album/*.mp3, corrige tags y pone la carátula."""
    covers = covers or {}
    mp3s = list(MUSIC_DIR.rglob("*.mp3"))
    if not mp3s:
        log("[TAGS] No hay MP3s para procesar.")
        return

    log(f"[TAGS] Procesando {len(mp3s)} MP3s...")
    seen_albums: set = set()

    for mp3 in mp3s:
        parts = mp3.relative_to(MUSIC_DIR).parts
        if len(parts) < 3:
            continue
        principal, feats = parse_artists(parts[0])

        try:
            tags = EasyID3(str(mp3))
        except Exception:
            tags = EasyID3()
        title = tags.get("title", [mp3.stem])[0]
        album = tags.get("album", [parts[1]])[0]
        if feats and "feat." not in title.lower() and "ft." not in title.lower():
            title = f"{title} (feat. {', '.join(feats)})"
        tags["title"] = title
        tags["artist"] = principal
        tags["albumartist"] = principal
        tags["album"] = album
        tags.save(str(mp3))

        album_dir = mp3.parent
        cover_file = album_dir / "cover.jpg"
        if album_dir not in seen_albums:
            seen_albums.add(album_dir)
            if not cover_file.exists():
                url = next(
                    (u for (_, a), u in covers.items() if a.lower() == album.lower()), None
                ) or get_itunes_cover(principal, album)
                data = download_cover(url) if url else None
                if data:
                    cover_file.write_bytes(data)
                    log(f"  [COVER] {principal} - {album}")
        if cover_file.exists():
            embed_cover(mp3, cover_file.read_bytes())

        log(f"  [OK] {principal} - {title}")
