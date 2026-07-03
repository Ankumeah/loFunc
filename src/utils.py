import sympy.parsing.sympy_parser as sy_parser
import matplotlib.pyplot as plt
import music21 as music
import numpy as np
import scipy.io.wavfile as wavfile
import pretty_midi as midi

from io import BytesIO
import tempfile

def gen_points(expr: str, cases: dict[float, float]) -> list[str]:
  errors: list[str] = []

  for x in cases.keys():
    try:
      cases[x] = float(sy_parser.parse_expr(expr, local_dict = { "x": x }))
    except TypeError:
      errors.append(f"Skipping f({x}) as it cannot be represent as a constant real number")
    except OverflowError:
      errors.append(f"Skipping f({x}) as it is too large")

  return errors

def gen_graph(expr: str, cases: dict[float, float]) -> bytes:
  plt.figure()
  plt.plot(list(cases.keys()), list(cases.values()), marker = "o", linewidth = 2, markersize = 6)
  plt.xlabel("x")
  plt.ylabel("f(x)")
  plt.title(expr)
  plt.grid(True)

  with BytesIO() as buf:
    plt.savefig(buf, format = "webp")
    plt.close()
    return buf.getvalue()

def gen_midi(cases: dict[float, float], bpm: int, instrument: str) -> bytes:
  instru = music.instrument.fromString(instrument)

  x_array: np.ndarray = np.array(list(cases.keys()), dtype = float)
  y_array: np.ndarray = np.array(list(cases.values()), dtype = float)
  y_array = np.nan_to_num(y_array, nan = 0, posinf = 100, neginf = -100)
  y_min: float = np.min(y_array)
  y_max: float = np.max(y_array)

  if y_max ==  y_min:
    y_normalized: np.ndarray = np.ones_like(y_array) * 0.5
  else:
    y_normalized = (y_array - y_min) / (y_max - y_min)

  midi_notes: np.ndarray = (y_normalized * 127).astype(int)
  x_diffs: np.ndarray = np.diff(x_array, prepend = x_array[0])
  x_diffs = np.abs(x_diffs)
  x_min: float = np.min(x_diffs)
  x_max: float = np.max(x_diffs)
  if x_max ==  x_min:
    note_durations: np.ndarray = np.ones_like(x_diffs) * 0.5
  else:
    note_durations = 0.25 + (x_diffs - x_min) / (x_max - x_min) * 1.75

  s = music.stream.Score()
  part = music.stream.Part()
  part.append(instru)
  part.append(music.tempo.MetronomeMark(number = bpm))

  for midi_pitch, duration in zip(midi_notes, note_durations):
    n = music.note.Note(midi = int(midi_pitch))
    n.quarterLength = duration
    part.append(n)

  s.append(part)

  with tempfile.NamedTemporaryFile(suffix = ".mid") as temp:
    s.write("midi", fp = temp.name)
    temp.seek(0)
    return temp.read()

def midi_to_wav(midi_bytes: bytes, fs: int = 44100) -> bytes:
  pm = midi.PrettyMIDI(BytesIO(midi_bytes))
  audio = pm.fluidsynth(fs=fs)

  audio = np.clip(audio, -1.0, 1.0)
  audio_int16 = (audio * 32767).astype(np.int16)

  buf = BytesIO()
  wavfile.write(buf, fs, audio_int16)
  return buf.getvalue()
