# Quality

```bash
python3 scripts/dev.py check
```

`check` runs unit tests, Python byte-compilation, Ruff, mypy, file-length checks, Bandit, Vulture, Deptry, and Radon. The tests cover scheduler-day aggregation, period comparisons, radio-button interaction wiring, and generated statistics markup.

Run only the unit tests with:

```bash
python3 scripts/dev.py test
```

Use `--verbose` before a command to stream tool output live:

```bash
python3 scripts/dev.py --verbose check
```

Long-running subprocesses are guarded by an idle timeout. Override it with:

```bash
python3 scripts/dev.py --idle-timeout 900 check
```
