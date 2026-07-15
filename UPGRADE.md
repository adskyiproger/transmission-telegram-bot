# Upgrade notes

## Required configuration changes

- Configure `bot.super_user`, `SUPER_USER`, or `--super-user`. The first person
  to contact a fresh bot is no longer promoted automatically.
- Docker Compose requires `TOKEN`, `SUPER_USER`, `TRANSMISSION_USER`, and
  `TRANSMISSION_PASSWORD` in the environment or an `.env` file.
- Proxy TLS verification now defaults to enabled. For an intercepting proxy,
  install its CA certificate instead of disabling verification. The temporary
  compatibility switch is `proxy.verify_tls: false`.

## Runtime and dependency changes

- The container runtime is Python 3.14.6 on Debian Bookworm.
- `python-telegram-bot` is upgraded from 21.10 to 22.8.
- The lockfile is generated with Python 3.14 and current stable direct
  dependencies.
- The unrelated `cookiejar`, dummy `bs4`, and unused `mechanize` packages are
  removed. Use the direct `beautifulsoup4` dependency.
- `Dockerfile.nas` is removed. Mount configuration at
  `/usr/src/app/config/torrentino.yaml`; do not embed secrets in images.

## Data compatibility

New download-history entries use JSON Lines so torrent names may safely contain
commas. Existing comma-separated entries are still read on a best-effort basis.
Back up `download.log` before the first deployment of this release.

## Recommended rollout

1. Back up `config/torrentino.yaml` and `download.log`.
2. Set the required environment variables and run `docker compose config`.
3. Pull/build the new images and start a staging bot against a non-production
   Transmission instance.
4. Verify `/help`, search, torrent upload, magnet addition, start/stop/delete,
   user invitation, completion notification, and clean shutdown.
5. Deploy to production and monitor bot and Transmission logs.

## Local verification

```shell
pipenv sync --dev
pipenv run pytest
pipenv run black --check lib models tests torrentino.py
pipenv run flake8
pipenv run mypy lib models tests torrentino.py
XDG_CACHE_HOME=/tmp/pip-audit-cache pipenv run pip-audit
docker build -t transmission-telegram-bot .
```
