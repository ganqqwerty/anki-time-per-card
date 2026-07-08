# Anki Time Per Card

Anki Time Per Card is a small local Anki add-on that shows the average time spent per distinct card reviewed during today's local Anki session.

The project is intentionally scaffolded around the developer loop:

- build Python add-on code and a Svelte WebView bundle
- link the add-on into Anki as a numeric local add-on
- launch Anki with the linked add-on
- run unit tests, frontend tests, and real-Anki e2e tests
- run quality checks from one `scripts/dev.py` entrypoint

## Quick Start

```bash
python3 scripts/dev.py setup
python3 scripts/dev.py build
python3 scripts/dev.py link-addon
python3 scripts/dev.py run-anki
```

In Anki, open `Tools -> Average Time Per Card Today`.

## Common Commands

```bash
python3 scripts/dev.py test
python3 scripts/dev.py test-svelte
python3 scripts/dev.py test-e2e
python3 scripts/dev.py check
python3 scripts/dev.py info
```

The Python commands run through Anki's bundled Python so tests see the same `anki`, `aqt`, and Qt packages used by the add-on at runtime.
