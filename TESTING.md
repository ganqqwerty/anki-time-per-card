# Quality

```bash
python3 scripts/dev.py check
```

`check` runs Python byte-compilation, Ruff, mypy, file-length checks, Bandit, Vulture, Deptry, and Radon. Use `--verbose` before the command to stream tool output live:

```bash
python3 scripts/dev.py --verbose check
```

Long-running subprocesses are guarded by an idle timeout. Override it with:

```bash
python3 scripts/dev.py --idle-timeout 900 check
```
