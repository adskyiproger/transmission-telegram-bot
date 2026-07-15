# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.4.0] - 2026-07-15

See the [1.4.0 release and migration notes](docs/releases/v1.4.0.md).

### Added

- Required explicit administrator configuration through `bot.super_user`,
  `SUPER_USER`, or `--super-user`.
- Regression tests for authorization, configuration, tracker downloads,
  torrent metainfo uploads, browser escaping, history, and utility functions.
- Python 3.14 CI jobs for tests, formatting, linting, static typing, dependency
  auditing, and container builds.
- Container and Transmission health checks.
- Bounded and expiring search-result caching.
- Configurable maximum tracker torrent size through `bot.max_torrent_size`.
- Structured JSON Lines download-history records with best-effort support for
  reading the legacy format.

### Changed

- Upgraded the container runtime from Python 3.13 to Python 3.14.6.
- Upgraded `python-telegram-bot` from 21.10 to 22.8.
- Upgraded Beautiful Soup, Requests, lxml, PyYAML, Pillow/qrcode, pydash, and
  development tools to their current stable releases.
- Pinned the bundled Transmission deployment to
  `lscr.io/linuxserver/transmission:4.1.1-r1-ls345`.
- Moved blocking tracker and Transmission operations away from Telegram's
  asynchronous event loop.
- Replaced the unmanaged Transmission monitoring thread with an
  application-owned asynchronous task and clean shutdown handling.
- Reused a single Transmission RPC client instead of creating one per action.
- Moved bot-command synchronization into Telegram application startup.
- Changed invitation tokens to cryptographically secure, single-use tokens
  with a 15-minute lifetime.
- Changed downloaded local torrent handling to pass metainfo to Transmission
  instead of exposing temporary paths as server-side filenames.
- Consolidated container builds into one hardened `Dockerfile`.
- Changed Docker dependency installation to use the lockfile directly in the
  system environment without a runtime Pipenv dependency.

### Fixed

- Prevented the first Telegram user contacting a fresh deployment from
  automatically becoming administrator.
- Prevented tracker usernames and passwords from appearing in debug logs.
- Prevented environment and CLI secrets from being persisted into YAML.
- Restored TLS certificate verification when tracker proxies are enabled.
- Fixed unsafe and colliding temporary torrent filenames and ensured temporary
  torrent and QR files are removed.
- Fixed local `.torrent` uploads failing with Transmission's
  `unrecognized info` response.
- Added URL encoding and HTTP status checks to tracker requests.
- Escaped tracker-provided values before rendering Telegram HTML.
- Validated download-directory callback values against configured directories.
- Fixed process exit status and exception logging for startup/runtime failures.
- Fixed deprecated logging calls and a tracker error-log argument mix-up.

### Removed

- Removed the unrelated `cookiejar` package.
- Removed the dummy `bs4` package in favor of the direct `beautifulsoup4`
  dependency.
- Removed the unused `mechanize` dependency.
- Removed `Dockerfile.nas`; configuration must be mounted or provided through
  environment variables rather than embedded in an image.
- Removed default `test` Transmission credentials from example configuration.

### Security

- Deny access when no explicit administrator is configured.
- Keep TLS verification enabled by default when using a proxy.
- Redact secrets from logs and avoid persisting runtime secrets.
- Validate untrusted tracker output, callback values, downloads, and temporary
  file handling.

[Unreleased]: https://github.com/adskyiproger/transmission-telegram-bot/compare/v1.4.0...HEAD
[1.4.0]: https://github.com/adskyiproger/transmission-telegram-bot/compare/v1.3.4...v1.4.0
