#!/usr/bin/env sh
set -eu

python - <<'PY'
from pathlib import Path

root = Path.cwd()
tests_dir = root / "tests"
tests_dir.mkdir(exist_ok=True)
(tests_dir / "__init__.py").touch()
PY
