# Spotify Privado

Crea tu propio "Spotify" casero: pega la URL de una playlist de Spotify y esta herramienta
localiza las canciones, las descarga como MP3 con sus etiquetas y carátulas, y las sirve con
[Navidrome](https://www.navidrome.org/), tu servidor de música personal. Luego la escuchas desde
cualquier app compatible con Subsonic.

```
playlist de Spotify ──► scraper (Playwright) ──► yt-dlp ──► tags + carátulas ──► Navidrome ──► tu app
```

*English: self-hosted "Spotify" — paste a Spotify playlist URL, get tagged MP3s with cover art, served by Navidrome. See the quick start below; the UI/logs are in Spanish.*

> **Aviso legal.** Pensado para uso personal con música a la que tengas derecho. Descargar contenido
> con copyright puede incumplir los términos de YouTube/Spotify o la ley de tu país. Eres el único
> responsable de su uso. No está afiliado a Spotify.

## Arranque rápido (Docker)

Necesitas [Docker](https://docs.docker.com/get-docker/).

```bash
git clone https://github.com/TU_USUARIO/spotify-privado.git
cd spotify-privado
cp .env.example .env        # edita APP_PASSWORD
docker compose up -d --build
```

1. Abre **http://localhost:4533** y crea tu usuario de Navidrome.
2. Abre **http://localhost:8501**, entra con `APP_PASSWORD`, pega la URL de una playlist y listo.
3. (Opcional) Pon tu usuario/contraseña de Navidrome en `.env` para que se reescanee al instante;
   si no, Navidrome detecta lo nuevo en ≤5 minutos.

La música queda en `./music/Artista/Álbum/Canción.mp3`.

## Sin Docker (Windows / Linux / macOS)

Requisitos: Python 3.10+ y [ffmpeg](https://ffmpeg.org/) (sin él descarga M4A en vez de MP3).

```bash
python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium

python -m spotifyprivado sync "https://open.spotify.com/playlist/XXXX"   # una playlist
python -m spotifyprivado retag                                            # re-etiquetar biblioteca
APP_PASSWORD=algo python -m spotifyprivado web                            # panel web
```

En Windows también tienes `scripts\install.bat` y `scripts\sync.bat`.

## Escuchar la música

Cualquier cliente Subsonic sirve (apunta a `http://TU_IP:4533`): [Musly](https://github.com/dddevid/musly),
Symfonium, DSub, Feishin, la propia web de Navidrome...

Para escuchar fuera de casa, expón Navidrome con un túnel (Cloudflare Tunnel, Tailscale…). **No
expongas el panel web (8501) a internet sin HTTPS**: la contraseña viaja en una cabecera.

## Configuración

| Variable | Para qué | Por defecto |
|---|---|---|
| `APP_PASSWORD` | Contraseña del panel web (obligatoria) | — |
| `NAVIDROME_URL` / `_USER` / `_PASSWORD` | Forzar reescaneo tras sincronizar | vacío |
| `BATCH_SIZE` | Descargas simultáneas | `3` |
| `MUSIC_DIR` | Carpeta de salida | `music` |

## Limitaciones

- El scraper depende del HTML de la web de Spotify; si lo cambian, habrá que actualizar los selectores en `spotifyprivado/scraper.py`.
- Solo playlists públicas. La coincidencia en YouTube es automática (primer resultado) y a veces falla.

## Licencia

MIT — ver [LICENSE](LICENSE).
