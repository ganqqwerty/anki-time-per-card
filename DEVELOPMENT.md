# Development

This project uses two runtimes:

- system Python starts `scripts/dev.py`
- Anki's bundled Python runs Python build and quality tools

The split matters because the add-on runs inside Anki, not inside a repository virtualenv.

## Setup

```bash
python3 scripts/dev.py setup
```

Setup installs Python development tools into Anki's bundled Python and creates the local add-on symlink when Anki's `addons21` directory exists.

If Anki Python is not auto-discovered, copy `.env.example` to `.env` and set `ANKI_PYTHON`.

## Build

```bash
python3 scripts/dev.py build
```

The build command byte-compiles the Python add-on and development scripts through Anki's bundled Python.

## Link And Run

```bash
python3 scripts/dev.py link-addon
python3 scripts/dev.py run-anki
```

The local add-on ID is `1000000003`. The link command points Anki's `addons21/1000000003` path at `addon/anki_time_per_card/` in this checkout. `run-anki` builds Python, links the add-on, and launches Anki.

If Anki is already running, quit and relaunch it so add-ons reload from the linked directory.
