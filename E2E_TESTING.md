# E2E Testing

The e2e suite starts a real Anki runtime from Anki's bundled Python. It creates a temporary `ANKI_BASE`, installs the add-on under `addons21/1000000003`, opens the WebView dialog, and verifies that the rendered Svelte UI matches review log rows inserted into the collection.

Run:

```bash
python3 scripts/dev.py test-e2e
```

Parallel sharding is available for larger suites:

```bash
DEV_E2E_JOBS=2 python3 scripts/dev.py test-e2e-parallel
```

The current suite is intentionally small, but it exercises the important integration path: numeric add-on import, generated JS/CSS bundles, Anki WebView rendering, and `revlog` aggregation.
