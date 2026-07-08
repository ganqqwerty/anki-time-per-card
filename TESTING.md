# Testing And Quality

Run unit tests:

```bash
python3 scripts/dev.py test
```

Run frontend validation:

```bash
python3 scripts/dev.py test-svelte
```

Run real-Anki e2e tests:

```bash
python3 scripts/dev.py test-e2e
```

Run the full quality pipeline:

```bash
python3 scripts/dev.py check
```

`check` runs the WebView build, Ruff, mypy, file-length checks, Bandit, Vulture, Deptry, Radon, Python tests, coverage, and frontend validation. Use `--verbose` before the command to stream tool output live:

```bash
python3 scripts/dev.py --verbose check
```

Long-running subprocesses are guarded by an idle timeout. Override it with:

```bash
python3 scripts/dev.py --idle-timeout 900 test-e2e
```
