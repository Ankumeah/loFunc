import flask

import utils

import base64

api = flask.Flask(__name__)

@api.route("/gen", methods = ["POST"])
def gen_points():
  body = flask.request.get_json(silent = False)
  feilds = { "expr": str, "cases": list, "instrument": str , "bpm": int}
  for feild in feilds:
    if not isinstance(body.get(feild), feilds[feild]):
      return { "error": f"expected {feild} of type {feilds[feild]}" }
  expr = body["expr"]
  cases: dict[float, float] = { case: 0 for case in body["cases"] }
  bpm = body["bpm"]
  instrument = body["instrument"]

  errors = utils.gen_points(expr, cases)
  image = utils.gen_graph(expr, cases)
  mid = utils.gen_midi(cases, bpm, instrument)
  aud = utils.midi_to_wav(mid)

  image = base64.b64encode(image).decode("utf-8")
  aud = base64.b64encode(aud).decode("utf-8")

  return {
    "image": image,
    "aud": aud,
    "errors": errors
  }

@api.route("/", methods = ["GET"])
def index():
  return flask.render_template("index.html")

if __name__ == "__main__":
  api.run(debug = True)
