"""Uso:
    python -m spotifyprivado sync <URL> [<URL>...] [--yes]
    python -m spotifyprivado retag
    python -m spotifyprivado web
"""
import sys

from .config import MUSIC_DIR
from .downloader import download_batch
from .log import log
from .navidrome import scan_navidrome
from .scraper import scrape_spotify
from .tagging import apply_tags_and_covers

USAGE = __doc__


def sync(args: list[str]) -> int:
    auto = "--yes" in args or "-y" in args
    urls = [a for a in args if not a.startswith("-")]
    if not urls:
        url = input("Pega la URL de la playlist de Spotify: ").strip()
        urls = [url] if url else []
    if not urls:
        print(USAGE)
        return 1

    print(f"\n[1/4] Leyendo {len(urls)} playlist(s)...")
    tracks, covers, seen = [], {}, set()
    for url in urls:
        found, found_covers = scrape_spotify(url)
        covers.update(found_covers)
        for track in found:
            key = track["track_id"] or (track["title"], track["artist"])
            if key not in seen:
                seen.add(key)
                tracks.append(track)
    if not tracks:
        print("No se extrajeron tracks.")
        return 1

    print(f"\n  → {len(tracks)} tracks, {len(covers)} carátulas")
    if not auto and input("Descargar? (s/n): ").strip().lower() not in ("s", "si", "y", "yes"):
        print("Cancelado.")
        return 0

    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    print("\n[2/4] Descargando...")
    ok, fail = download_batch(tracks)
    print("\n[3/4] Etiquetando y aplicando carátulas...")
    apply_tags_and_covers(covers)
    print("\n[4/4] Navidrome...")
    scan_navidrome()
    log(f"\nHecho: {ok} descargados, {fail} errores")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(USAGE)
        return 1
    cmd, rest = sys.argv[1], sys.argv[2:]
    if cmd == "sync":
        return sync(rest)
    if cmd == "retag":
        apply_tags_and_covers()
        scan_navidrome()
        return 0
    if cmd == "web":
        from .web import run_server
        run_server()
        return 0
    print(USAGE)
    return 1


if __name__ == "__main__":
    sys.exit(main())
