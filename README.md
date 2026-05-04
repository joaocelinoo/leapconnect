# LeapConnect

[![GitHub Container Registry](https://img.shields.io/badge/ghcr.io-leapconnect-blue?logo=docker)](https://ghcr.io/markoceri/leapconnect)

Web dashboard for monitoring and controlling Leapmotor vehicles via the [leapmotor-api](https://github.com/markoceri/leapmotor-api) Python client.

## Features

- **Live vehicle status**: Battery, range, speed, odometer, temperature, lock status and more
- **Remote controls**: Lock/unlock, trunk, windows, sunshade, climate (A/C, quick cool/heat, defrost), battery preheat, find car
- **Charge limit**: Adjustable charge limit slider
- **Vehicle details**: Doors, windows, tire pressure, climate, connectivity, ignition
- **Location**: OpenStreetMap embedded view with coordinates
- **Mileage & energy**: Delivery history, total mileage
- **Car picture**: Dinamic image reflecting lock status, doors, windows, sunshade, and lights
- **Raw data viewer**: Full JSON inspection for debugging
- **Multi-vehicle**: Tab switching for accounts with multiple vehicles
- **Home Assistant integration**: Optional MQTT export of all vehicle data for smart home
- **Local history recording**: Optional SQLite database to track vehicle data over time.

## Screenshots

| Login | Dashboard | Details |
|:---:|:---:|:---:|
| [![Login](docs/screenshots/login.png)](docs/screenshots/login.png) | [![Dashboard](docs/screenshots/dashboard.png)](docs/screenshots/dashboard.png) | [![Details](docs/screenshots/details.png)](docs/screenshots/details.png) |

| History | Messages | Settings |
|:---:|:---:|:---:|
| [![History](docs/screenshots/history.png)](docs/screenshots/history.png) | [![Messages](docs/screenshots/messages.png)](docs/screenshots/messages.png) | [![Settings](docs/screenshots/settings.png)](docs/screenshots/settings.png) |

## Tested Vehicles

| Model | Status |
|-------|--------|
| T03 | ✅ Tested |
| C10 | 🟡 Should work (same cloud API) |
| B10 | 🟡 Should work (same cloud API) |
| B05 | 🟡 Should work (same cloud API) |

## Requirements

- Docker & Docker Compose (for production)
- [uv](https://docs.astral.sh/uv/) (for local development)
- Leapmotor app certificate files (`.pem`) — [download here](https://github.com/markoceri/leapmotor-certs/archive/refs/tags/v1.0.0.zip)
- A valid Leapmotor account

> **⚠️ Strongly recommended:** Create a separate Leapmotor account and share your vehicle with it, rather than using your primary account. This way, if anything goes wrong (e.g. account suspension), your main account remains unaffected.

## Quick Start (Docker)

### Using the pre-built image

```bash
docker pull ghcr.io/markoceri/leapconnect:latest
```

Create a `docker-compose.yml`:

```yaml
services:
  generate-certs:
    image: alpine:latest
    entrypoint: /bin/sh
    command:
      - -c
      - |
        if [ -f /certs/traefik.crt ] && [ -f /certs/traefik.key ]; then
          echo "Certificates already exist, skipping."
          exit 0
        fi
        apk add --no-cache openssl
        SAN="DNS:localhost,IP:127.0.0.1"
        for ip in $$(hostname -I 2>/dev/null); do SAN="$$SAN,IP:$$ip"; done
        openssl req -x509 -nodes -days 3650 \
          -newkey rsa:2048 \
          -keyout /certs/traefik.key \
          -out /certs/traefik.crt \
          -subj "/CN=leapmotor-webapp" \
          -addext "subjectAltName=$$SAN"
    volumes:
      - ./traefik/certs:/certs
    network_mode: host

  traefik:
    image: traefik:latest
    depends_on:
      generate-certs:
        condition: service_completed_successfully
    command:
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--entrypoints.web.http.redirections.entrypoint.to=websecure"
      - "--entrypoints.web.http.redirections.entrypoint.scheme=https"
      - "--providers.file.filename=/etc/traefik/dynamic.yml"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik/dynamic.yml:/etc/traefik/dynamic.yml:ro
      - ./traefik/certs:/certs:ro
    restart: unless-stopped

  app:
    image: ghcr.io/markoceri/leapconnect:latest
    environment:
      - HISTORY_DB_PATH=/app/data/history.db
      - DATA_DIR=/app/data
    volumes:
      - ./data:/app/data
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.leapmotor.rule=PathPrefix(`/`)"
      - "traefik.http.routers.leapmotor.entrypoints=websecure"
      - "traefik.http.routers.leapmotor.tls=true"
      - "traefik.http.services.leapmotor.loadbalancer.server.port=8099"
    restart: unless-stopped
```

```bash
docker compose up -d
```

The app will be available at **https://localhost**.

### Building from source

```bash
git clone https://github.com/markoceri/leapconnect
cd leapconnect
docker compose up -d --build
```

The app is available at **https://localhost**.

Traefik handles reverse proxying with HTTPS on port 443 and automatic HTTP→HTTPS redirect on port 80. The app container runs internally on port 8099.

Vehicle history data is persisted in a Docker volume (`app-data`).

### HTTPS & Certificates

The Docker Compose setup includes automatic TLS certificate generation. On first `docker compose up`, a one-shot init container generates a self-signed certificate with all local IP addresses in the SAN (Subject Alternative Name), so you can access the app via `https://<server-ip>` without certificate errors.

- Certificates are stored in `traefik/certs/` (git-ignored)
- If certificates already exist, the init container skips generation
- To regenerate (e.g. after an IP change), delete the old certificates and restart:

```bash
rm traefik/certs/traefik.crt traefik/certs/traefik.key
docker compose up -d
```

Alternatively, you can use the standalone script to regenerate certificates with custom IPs or hostnames:

```bash
rm traefik/certs/traefik.crt traefik/certs/traefik.key
./generate-traefik-certs.sh                     # auto-detect local IPs
./generate-traefik-certs.sh 192.168.1.100       # add extra IP
./generate-traefik-certs.sh myhost.local        # add extra hostname
```

## Development

### Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

See [uv installation docs](https://docs.astral.sh/uv/getting-started/installation/) for other methods (Homebrew, Windows, pipx).

### Backend

```bash
uv sync
uv run pre-commit install && uv run pre-commit install --hook-type pre-push
uv run uvicorn main:app --host 0.0.0.0 --port 8099 --reload
```

The API runs at **http://localhost:8099**.

### Tests

```bash
uv run pytest
```

### Code Quality

Pre-commit hooks run automatically:

- **On commit**: trailing whitespace, end-of-file fix, YAML/TOML/JSON validation, ruff lint + format
- **On push**: full pytest suite

To run all checks manually:

```bash
uv run pre-commit run --all-files
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vue dev server runs at **http://localhost:5173** and proxies `/api` calls to the backend.

### Production build (manual)

```bash
cd frontend
npm run build
```

This outputs to `frontend/dist/`. The FastAPI backend will automatically serve the built SPA.

### Versioning

The project uses [bump-my-version](https://github.com/callowayproject/bump-my-version) to manage versions across `pyproject.toml` and `frontend/package.json`.

```bash
uv run bump-my-version bump patch   # 0.1.0 → 0.1.1 (bugfix)
uv run bump-my-version bump minor   # 0.1.0 → 0.2.0 (new feature)
uv run bump-my-version bump major   # 0.1.0 → 1.0.0 (breaking change)
```

Each command updates the version in both files, creates a commit, and tags it `vX.Y.Z`.

**Release workflow:**

1. Commit all changes
2. Update `CHANGELOG.md` (move entries from `[Unreleased]` to a new version section)
3. `uv run bump-my-version bump patch|minor|major`
4. `git push --follow-tags`

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `APP_CERT_PATH` | Yes | Path to the app certificate PEM file |
| `APP_KEY_PATH` | Yes | Path to the app key PEM file |
| `ACCOUNT_P12_PASSWORD` | No | P12 password (usually auto-derived from login) |
| `HISTORY_DB_PATH` | No | SQLite database path (default: `/app/data/history.db`) |

## Login

You will need:
- **Email & Password**: Your Leapmotor account credentials
- **Vehicle PIN** (optional): Required for remote control actions (lock, unlock, climate, etc.)

## Disclaimer

**This is NOT an official Leapmotor product.**

LeapConnect is an independent, community-driven project with no affiliation to Leapmotor International or its subsidiaries. It interacts with Leapmotor's cloud services through unofficial, reverse-engineered APIs.

By using this software you acknowledge that:

- You use LeapConnect **entirely at your own risk**.
- The author(s) accept **no responsibility** for any consequences, including but not limited to account suspension or ban by Leapmotor.
- Vehicle commands are sent over unofficial channels — **use remote controls with caution**.
- The project may stop working at any time if Leapmotor changes its APIs.
