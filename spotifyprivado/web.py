"""Panel web mínimo protegido con contraseña para lanzar sincronizaciones."""
import hmac
import json
import os
import re
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .config import (
    HAS_FFMPEG,
    MUSIC_DIR,
    NAVIDROME_ENABLED,
    NAVIDROME_PORT,
    QUALITIES,
    load_settings,
    save_settings,
)

PORT = int(os.environ.get("PORT", 8501))
LOG_FILE = Path(os.environ.get("WEB_LOG_FILE", "web_task.log"))
INDEX_HTML = (Path(__file__).parent / "static" / "index.html").read_bytes()
PLAYLIST_RE = re.compile(r"^https://open\.spotify\.com/(intl-[a-z]+/)?playlist/[A-Za-z0-9]+(\?.*)?$")

_proc: subprocess.Popen | None = None
_lock = threading.Lock()


def _password() -> str:
    pwd = os.environ.get("APP_PASSWORD", "")
    if not pwd:
        sys.exit("Define APP_PASSWORD (ver .env.example) antes de arrancar el panel web.")
    return pwd


def job_running() -> bool:
    with _lock:
        return _proc is not None and _proc.poll() is None


def start_job(urls: list[str]) -> None:
    global _proc
    with _lock:
        with open(LOG_FILE, "w", encoding="utf-8") as fp:
            _proc = subprocess.Popen(
                [sys.executable, "-m", "spotifyprivado", "sync", *urls, "--yes"],
                stdout=fp,
                stderr=subprocess.STDOUT,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )


_lib_cache = {"t": 0.0, "value": {"tracks": 0, "artists": 0}}


def library_stats() -> dict:
    """Cuenta canciones/artistas (cacheado 5 s para no recorrer el disco en cada petición)."""
    if time.time() - _lib_cache["t"] > 5:
        tracks = [p for ext in ("mp3", "m4a") for p in MUSIC_DIR.rglob(f"*.{ext}")] if MUSIC_DIR.exists() else []
        artists = {p.relative_to(MUSIC_DIR).parts[0] for p in tracks}
        _lib_cache.update(t=time.time(), value={"tracks": len(tracks), "artists": len(artists)})
    return _lib_cache["value"]


STAGES = (  # (marcador en el log, etapa, progreso mínimo)
    ("[1/4]", 1, 20),
    ("[2/4]", 2, 55),
    ("[3/4]", 3, 80),
    ("[4/4]", 4, 95),
    ("Hecho:", 4, 100),
)


def read_progress() -> tuple[str, int, int]:
    try:
        lines = LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return "", 1, 0
    stage, progress = 1, 5
    for line in lines:
        for marker, s, p in STAGES:
            if marker in line:
                stage, progress = s, max(progress, p)
    return "\n".join(lines[-40:]), stage, progress


def make_handler(password: str):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def authed(self) -> bool:
            return hmac.compare_digest(self.headers.get("Authorization", ""), password)

        def send_json(self, data, status=200):
            body = json.dumps(data).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/":
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(INDEX_HTML)))
                self.end_headers()
                self.wfile.write(INDEX_HTML)
            elif self.path == "/api/config":
                if not self.authed():
                    return self.send_json({"error": "Unauthorized"}, 401)
                self.send_json({
                    "settings": load_settings(),
                    "qualities": QUALITIES,
                    "ffmpeg": HAS_FFMPEG,
                    "navidrome": NAVIDROME_ENABLED,
                    "navidrome_port": NAVIDROME_PORT,
                    "library": library_stats(),
                })
            elif self.path == "/api/status":
                if not self.authed():
                    return self.send_json({"error": "Unauthorized"}, 401)
                logs, stage, progress = read_progress()
                self.send_json({
                    "running": job_running(),
                    "has_logs": bool(logs),
                    "logs": logs,
                    "stage": stage,
                    "progress": progress,
                })
            else:
                self.send_error(404)

        def do_POST(self):
            try:
                length = min(int(self.headers.get("Content-Length", 0)), 65536)
                data = json.loads(self.rfile.read(length) or b"{}")
            except ValueError:
                data = {}

            if self.path == "/api/login":
                if hmac.compare_digest(str(data.get("password", "")), password):
                    self.send_json({"success": True})
                else:
                    self.send_json({"error": "Wrong password"}, 401)
            elif self.path == "/api/start":
                if not self.authed():
                    return self.send_json({"error": "Unauthorized"}, 401)
                if job_running():
                    return self.send_json({"error": "Ya hay una descarga en curso"}, 400)
                urls = [u.strip() for u in data.get("urls", []) if isinstance(u, str) and u.strip()]
                if not urls or not all(PLAYLIST_RE.match(u) for u in urls):
                    return self.send_json({"error": "Pega URLs de playlist de open.spotify.com (una por línea)"}, 400)
                start_job(urls[:20])
                self.send_json({"success": True})
            elif self.path == "/api/settings":
                if not self.authed():
                    return self.send_json({"error": "Unauthorized"}, 401)
                self.send_json({"settings": save_settings(data)})
            else:
                self.send_error(404)

    return Handler


def run_server() -> None:
    password = _password()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), make_handler(password))
    print(f"Panel web en http://0.0.0.0:{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
