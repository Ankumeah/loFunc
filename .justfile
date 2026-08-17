default: run

[linux, macos]
run *opts:
  .venv/bin/python src/main.py {{opts}}
