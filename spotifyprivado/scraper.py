"""Lee una playlist pública de Spotify con un navegador headless (sin API key)."""
import time

from playwright.sync_api import sync_playwright

from .log import log

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

EXTRACT_JS = """() => {
    const rows = document.querySelectorAll('div[data-testid="tracklist-row"]');
    const result = [];
    rows.forEach(row => {
        try {
            const trackLink = row.querySelector('a[data-testid="internal-track-link"]');
            let title = '';
            let track_id = '';
            if (trackLink) {
                title = trackLink.textContent.trim();
                const m = (trackLink.getAttribute('href') || '').match(/\\/track\\/([A-Za-z0-9]+)/);
                if (m) track_id = m[1];
            }
            if (!title) {
                const titleEl = row.querySelector('div[data-testid="tracklist-row-title"]');
                if (titleEl) title = titleEl.textContent.trim();
            }
            const artists = [];
            row.querySelectorAll('a[href*="/artist/"]').forEach(n => {
                const t = n.textContent.trim();
                if (t) artists.push(t);
            });
            if (artists.length === 0) {
                const fb = row.querySelector('span.standalone-ellipsis-one-line');
                if (fb) artists.push(fb.textContent.trim());
            }
            const artist = artists.join(', ') || 'Unknown Artist';
            const albumEl = row.querySelector('a[href*="/album/"]')
                || row.querySelector('[data-testid="tracklist-row-album"]');
            const album = albumEl ? albumEl.textContent.trim() : 'Unknown Album';
            const img = row.querySelector('img');
            const cover_url = img ? img.getAttribute('src') : null;
            result.push({title, artist, album, track_id,
                         uid: track_id || (title + '|||' + artist), cover_url});
        } catch (e) {}
    });
    return result;
}"""

SCROLL_JS = """() => {
    const scroller = document.querySelector('.os-viewport');
    if (scroller) scroller.scrollTop = scroller.scrollHeight;
    const rows = document.querySelectorAll('div[data-testid="tracklist-row"]');
    if (rows.length > 0) rows[rows.length - 1].scrollIntoView({behavior: 'instant', block: 'end'});
}"""


def scrape_spotify(url: str) -> tuple[list[dict], dict]:
    """Devuelve (tracks, covers). Si falla, ([], {}).

    tracks: [{title, artist, album, track_id}]
    covers: {(artista_principal, album): url_cover}
    """
    log(f"[SCRAPE] Abriendo {url} ...")
    seen: set[str] = set()
    tracks: list[dict] = []
    covers: dict[tuple[str, str], str] = {}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )
            page = browser.new_context(user_agent=USER_AGENT).new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_load_state("networkidle", timeout=30000)

            btn = page.query_selector("#onetrust-accept-btn-handler")
            if btn:
                btn.click()
                time.sleep(1)

            try:
                page.wait_for_selector('[data-testid="tracklist-row"]', timeout=15000)
            except Exception:
                log("[SCRAPE] No se encontraron tracks (¿playlist privada o URL incorrecta?).")
                browser.close()
                return [], {}

            # Spotify virtualiza la lista: hay que hacer scroll y acumular lo visible.
            stale_rounds = 0
            for _ in range(1000):
                page.evaluate(SCROLL_JS)
                time.sleep(0.5)

                before = len(tracks)
                for t in page.evaluate(EXTRACT_JS):
                    if t["uid"] not in seen:
                        seen.add(t["uid"])
                        tracks.append({k: t[k] for k in ("title", "artist", "album", "track_id")})
                    key = (t["artist"].split(",")[0].strip(), t["album"])
                    if t.get("cover_url") and key not in covers:
                        covers[key] = t["cover_url"]

                if len(tracks) == before:
                    stale_rounds += 1
                    if stale_rounds >= 15:
                        break
                else:
                    stale_rounds = 0
                    log(f"[SCRAPE] {len(tracks)} tracks (+{len(tracks) - before})")

            browser.close()
    except Exception as e:
        log(f"[SCRAPE] Error: {e}")
        return [], {}

    log(f"[SCRAPE] OK: {len(tracks)} tracks, {len(covers)} covers")
    return tracks, covers
