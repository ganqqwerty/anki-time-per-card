# Development

This project uses two runtimes:

- system Python starts `scripts/dev.py`
- Anki's bundled Python runs tests and Python quality tools

The split matters because the add-on runs inside Anki, not inside a repository virtualenv.

## Setup

```bash
python3 scripts/dev.py setup
```

Setup installs Python development tools into Anki's bundled Python, installs frontend dependencies in `webview_ui/`, and creates the local add-on symlink when Anki's `addons21` directory exists.

If Anki Python is not auto-discovered, copy `.env.example` to `.env` and set `ANKI_PYTHON`.

## Build

```bash
python3 scripts/dev.py build
```

The build command compiles the Svelte WebView app into `addon/anki_time_per_card/web/` and byte-compiles the Python add-on code. Generated WebView bundles are ignored because `webview_ui/src/` is the source of truth.

## Link And Run

```bash
python3 scripts/dev.py link-addon
python3 scripts/dev.py run-anki
```

The local add-on ID is `1000000003`. The link command points Anki's `addons21/1000000003` path at `addon/anki_time_per_card/` in this checkout. `run-anki` builds the UI, links the add-on, and launches Anki.

If Anki is already running, quit and relaunch it so add-ons reload from the linked directory.

## Frontend

The WebView app lives in `webview_ui/` and mounts from `window.__INITIAL_STATE__`. Python embeds that state into the Anki WebView shell. Keep the bundle filenames stable because `dialog.py` reads them directly.
