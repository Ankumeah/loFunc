import sympy.parsing.sympy_parser as sy_parser
import matplotlib.pyplot as plt
import rich.console as c

import sys

def main(con: c.Console):
  expr: str = con.input("[green]f(x) = [/green]")

  cases: dict[float, float] = {}
  for i in range(0, 11):
    cases[i] = 0

  gen_points(expr, cases, con)
  gen_graph(expr, cases, "src/img.jpg", con)

def gen_points(expr: str, cases: dict[float, float], con: c.Console) -> None:
  for x in cases.keys():
    try:
      cases[x] = float(sy_parser.parse_expr(expr, local_dict = { "x": x }))
    except TypeError:
      con.print(f"[red]Skipping f({x}) as it cannot be represent as a constant real number[/red]")
    except OverflowError:
      con.print(f"[red]Skipping f({x}) as it is too large[/red]")

def gen_graph(expr: str, cases: dict[float, float], save_path: str, con: c.Console) -> None:
  plt.plot(list(cases.keys()), list(cases.values()), marker = "o", linewidth = 2, markersize = 6)
  plt.xlabel("x")
  plt.ylabel("f(x)")
  plt.title(expr)
  plt.grid(True)
  plt.savefig(save_path)

  con.print(f"[green]Saved graph to {save_path}[/green]")

if __name__ == "__main__":
  con = c.Console()

  try:
    main(con)
  except KeyboardInterrupt:
    con.print()
    con.print("[green]Bye![/green]")
    sys.exit()
