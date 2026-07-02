default: run

[linux, macos]
run *opts:
  #! /bin/sh

  echo "==> python src/main.py {{opts}}"
  .venv/bin/python src/main.py {{opts}}
