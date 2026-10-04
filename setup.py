#!/usr/bin/env python3
"""Asistente de instalación: pregunta lo básico, genera .env y arranca todo con Docker.

Uso:  python setup.py
Solo usa la librería estándar de Python 3.8+.
"""
import secrets
import shutil
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
ENV_FILE = ROOT / ".env"


def ask(question: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    return input(f"{question}{suffix}: ").strip() or default


def ask_yes(question: str, default: bool) -> bool:
    answer = ask(f"{question} (s/n)", "s" if default else "n").lower()
    return answer in ("s", "si", "sí", "y", "yes")


def local_ips() -> list[str]:
    ips = []
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))  # no envía nada; solo elige la interfaz de red
            ips.append(s.getsockname()[0])
    except OSError:
        pass
    return ips or ["localhost"]


def read_env() -> dict:
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
    return env


def main() -> int:
    print("=== Spotify Privado: instalación ===\n")

    if not shutil.which("docker"):
        print("No encuentro Docker. Instálalo desde https://docs.docker.com/get-docker/ y vuelve a ejecutar esto.")
        print("(Sin Docker también puedes usarlo: mira la sección 'Sin Docker' del README.)")
        return 1
    if subprocess.run(["docker", "info"], capture_output=True).returncode != 0:
        print("Docker está instalado pero no está en marcha. Ábrelo (Docker Desktop) y reintenta.")
        return 1

    old = read_env()
    if old and not ask_yes(f"Ya existe {ENV_FILE.name}. ¿Reconfigurar?", False):
        env = old
    else:
        generated = secrets.token_urlsafe(9)
        env = {
            "APP_PASSWORD": ask("Contraseña del panel web", old.get("APP_PASSWORD", generated)),
            "MUSIC_PATH": ask(
                "Carpeta para guardar la música (ruta completa, ej. D:/Musica)", old.get("MUSIC_PATH", "./music")
            ).replace("\\", "/"),
            "WEB_PORT": ask("Puerto del panel web", old.get("WEB_PORT", "8501")),
        }
        if ask_yes("¿Quieres Navidrome (servidor para escuchar la música desde el móvil/otras apps)?", True):
            env["COMPOSE_PROFILES"] = "navidrome"
            env["NAVIDROME_ENABLED"] = "1"
            env["NAVIDROME_PORT"] = ask("Puerto de Navidrome", old.get("NAVIDROME_PORT", "4533"))
            for key in ("NAVIDROME_USER", "NAVIDROME_PASSWORD"):
                if old.get(key):
                    env[key] = old[key]
            for key in ("NAVIDROME_USER", "NAVIDROME_PASSWORD"):
                if old.get(key):
                    env[key] = old[key]
        ENV_FILE.write_text("".join(f"{k}={v}\n" for k, v in env.items()), encoding="utf-8")
        print(f"\nGuardado {ENV_FILE.name}.")

    music = Path(env.get("MUSIC_PATH", "./music"))
    if not music.is_absolute():
        music = ROOT / music
    music.mkdir(parents=True, exist_ok=True)

    print("\nConstruyendo y arrancando (la primera vez tarda unos minutos)...\n")
    if subprocess.run(["docker", "compose", "up", "-d", "--build"], cwd=ROOT).returncode != 0:
        print("\nAlgo falló al arrancar. Revisa el mensaje de arriba.")
        return 1

    ips = local_ips()
    web, nav = env.get("WEB_PORT", "8501"), env.get("NAVIDROME_PORT", "4533")
    print("\n=== ¡Listo! ===")
    print(f"Panel web (pega aquí tus playlists):  http://localhost:{web}")
    if env.get("NAVIDROME_ENABLED"):
        print(f"Navidrome (crea tu usuario al entrar): http://localhost:{nav}")
        print("\nPara conectar el móvil u otra app (misma WiFi), usa como servidor:")
        for ip in ips:
            print(f"  http://{ip}:{nav}")
    else:
        print("Sin Navidrome: la música se guardará en", music)
    print("\nLa contraseña del panel está en el archivo .env (APP_PASSWORD).")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(1)
