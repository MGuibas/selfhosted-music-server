"""Pide a Navidrome que reescanee la biblioteca (API Subsonic)."""
import requests

from .config import NAVIDROME_ENABLED, NAVIDROME_PASSWORD, NAVIDROME_URL, NAVIDROME_USER
from .log import log


def scan_navidrome() -> None:
    if not NAVIDROME_ENABLED:
        log("[SCAN] Navidrome desactivado: solo se descarga la música.")
        return
    if not NAVIDROME_URL or not NAVIDROME_USER:
        log("[SCAN] Sin reescaneo forzado: Navidrome detectará lo nuevo en su próximo escaneo (≤5 min).")
        return
    try:
        resp = requests.get(
            f"{NAVIDROME_URL}/rest/startScan",
            params={
                "u": NAVIDROME_USER,
                "p": NAVIDROME_PASSWORD,
                "v": "1.16.1",
                "c": "spotifyprivado",
                "f": "json",
            },
            timeout=15,
        )
        status = resp.json()["subsonic-response"]["status"]
        log("[SCAN] Scan completado." if status == "ok" else f"[SCAN] Navidrome respondió: {status}")
    except Exception as e:
        log(f"[SCAN] Error: {e}")
