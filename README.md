# Spotify Privado

Tu propio "Spotify" casero. Pegas la URL de una playlist de Spotify y esta herramienta
descarga las canciones en MP3 con sus etiquetas y carátulas. Opcionalmente las sirve con
[Navidrome](https://www.navidrome.org/) para que las escuches desde el móvil con una app tipo Spotify.

```
playlist de Spotify ─► scraper ─► yt-dlp ─► MP3 + tags + carátula ─► carpeta de música ─► (Navidrome) ─► tu app
```

**Tú eliges:** solo descargar la música a una carpeta, o descargar *y* tener tu servidor de streaming.

> **Aviso legal.** Pensado para uso personal con música a la que tengas derecho. Descargar contenido con
> copyright puede incumplir los términos de YouTube/Spotify o la ley de tu país. Eres el único responsable
> de su uso. Proyecto no afiliado a Spotify.
>
> *English: self-hosted playlist downloader + optional Navidrome streaming server. Run `python setup.py`; the UI is in Spanish.*

---

## Instalación en 3 pasos

**Necesitas:** [Docker](https://docs.docker.com/get-docker/) (en Windows/Mac, Docker Desktop abierto) y Python 3 solo para el asistente.

```bash
git clone https://github.com/TU_USUARIO/spotify-privado.git
cd spotify-privado
python setup.py
```

El asistente te pregunta:

| Pregunta | Para qué |
|---|---|
| Contraseña del panel | Protege el panel web |
| Carpeta de música | Dónde se guardan los MP3 (p. ej. `D:/Musica`) |
| Puertos | Déjalos por defecto salvo que estén ocupados |
| ¿Quieres Navidrome? | Sí = servidor para escuchar en el móvil; No = solo descarga |

Al terminar te muestra las direcciones, incluida **la IP de tu PC** para conectar el móvil.
La primera vez tarda unos minutos (construye la imagen).

Después abre **http://localhost:8501**, entra con tu contraseña, pega una o varias playlists
(una URL por línea) y pulsa **Descargar**.

> Solo funcionan **playlists públicas**. En Spotify: playlist → `···` → Compartir → Copiar enlace.

## El panel web

- **Descargar:** pega una o varias playlists y verás el progreso en directo.
- **Ajustes:** calidad del MP3 (128–320 kbps o máxima), descargas simultáneas y carátulas sí/no. Se guardan solos.
- **Biblioteca:** cuántas canciones y artistas llevas y, si activaste Navidrome, la dirección para conectar tus apps.

La música queda en `TU_CARPETA/Artista/Álbum/Canción.mp3`. Las canciones ya descargadas se saltan, así que puedes
repetir una playlist para añadir solo las nuevas.

## Navidrome (opcional)

[Navidrome](https://www.navidrome.org/) es un servidor de música: lee tu carpeta y la sirve por red.

1. Abre **http://localhost:4533** (o el puerto que elegiste).
2. La primera vez te pide crear un usuario administrador: invéntate usuario y contraseña.
3. Tras cada descarga, Navidrome detecta lo nuevo en ≤5 minutos. Si quieres que sea instantáneo, añade
   `NAVIDROME_USER` y `NAVIDROME_PASSWORD` a `.env` y ejecuta `docker compose up -d`.

¿No lo quisiste al principio? Ejecuta `python setup.py` otra vez y responde que sí (o al revés para quitarlo).

## Escuchar en el móvil / PC (apps)

Cualquier app compatible con **Subsonic/Navidrome** sirve:
[Musly](https://github.com/dddevid/musly), Symfonium, DSub, Substreamer, Feishin…

En la app, añade un servidor con:

- **Tipo:** Subsonic / Navidrome
- **Dirección:** `http://IP_DE_TU_PC:4533` (la IP que te mostró `setup.py`; el panel web también la indica)
- **Usuario y contraseña:** los que creaste en Navidrome

El móvil y el PC deben estar en la **misma WiFi**. Si no conecta, revisa que el firewall del PC permita el puerto 4533.

### Escuchar fuera de casa

Necesitas que tu PC sea accesible desde internet. Lo más sencillo y seguro:

- **[Tailscale](https://tailscale.com/)**: instálalo en el PC y en el móvil y usa la IP de Tailscale como dirección. Sin abrir puertos.
- **Cloudflare Tunnel**: expón solo Navidrome (puerto 4533) con HTTPS.

> **No expongas el panel web (8501) a internet sin HTTPS**: la contraseña viaja en una cabecera. Expón solo Navidrome.

## Sin Docker

Requisitos: Python 3.10+ y [ffmpeg](https://ffmpeg.org/) (sin él descarga M4A en vez de MP3).

```bash
python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium

python -m spotifyprivado sync "https://open.spotify.com/playlist/XXXX"   # descargar playlist(s)
python -m spotifyprivado retag                                            # re-etiquetar la biblioteca
APP_PASSWORD=algo MUSIC_DIR=/ruta/musica python -m spotifyprivado web    # panel web
```

En Windows también puedes usar `scripts\install.bat` y `scripts\sync.bat`. Para Navidrome sin Docker,
sigue su [guía de instalación](https://www.navidrome.org/docs/installation/) y apúntalo a tu carpeta de música.

## Configuración avanzada (`.env`)

| Variable | Para qué | Por defecto |
|---|---|---|
| `APP_PASSWORD` | Contraseña del panel (obligatoria) | — |
| `MUSIC_PATH` | Carpeta de música (Docker) | `./music` |
| `WEB_PORT` | Puerto del panel | `8501` |
| `COMPOSE_PROFILES=navidrome` + `NAVIDROME_ENABLED=1` | Activa Navidrome | desactivado |
| `NAVIDROME_PORT` | Puerto de Navidrome | `4533` |
| `NAVIDROME_USER` / `NAVIDROME_PASSWORD` | Reescaneo instantáneo tras descargar | vacío |

Calidad, simultáneas y carátulas se cambian desde el panel (se guardan en `config/settings.json`).

## Problemas frecuentes

- **"No se extrajeron tracks"**: la playlist es privada o la URL es incorrecta. Hazla pública.
- **Puerto ocupado** (`port is already allocated`): cambia `WEB_PORT`/`NAVIDROME_PORT` en `.env` y ejecuta `docker compose up -d`.
- **No aparece música en Navidrome**: espera 5 minutos, o mira que `MUSIC_PATH` apunte a la carpeta correcta.
- **El móvil no conecta**: misma WiFi, IP correcta (no `localhost`) y puerto 4533 abierto en el firewall.
- **Algunas canciones fallan o son otra versión**: la búsqueda en YouTube es automática (primer resultado). Es una limitación conocida.
- **Dejó de leer la playlist**: Spotify cambió su web; hay que actualizar los selectores en `spotifyprivado/scraper.py`.
- **Ver logs**: `docker compose logs -f web`.

## Actualizar / desinstalar

```bash
git pull && docker compose up -d --build     # actualizar
docker compose down                          # parar (tu música no se borra)
```

## Licencia

MIT — ver [LICENSE](LICENSE).
