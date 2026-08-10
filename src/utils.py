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
  plt.style.use("dark_background")
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
  x_array = np.array(list(cases.keys()), dtype = float)
  y_array = np.array(list(cases.values()), dtype = float)
  y_array = np.nan_to_num(
    y_array,
    nan = 0,
    posinf = 100,
    neginf = -100,
  )
  y_min = np.min(y_array)
  y_max = np.max(y_array)

  if y_max == y_min:
    y_normalized = np.full_like(y_array, 0.5)
  else:
    y_normalized = (y_array - y_min) / (y_max - y_min)

  x_diffs = np.diff(x_array, prepend = x_array[0])
  x_diffs = np.abs(x_diffs)

  if len(x_diffs) > 1:
    x_min = np.min(x_diffs[1:])
    x_max = np.max(x_diffs[1:])
  else:
    x_min = x_max = 0

  if x_max == x_min:
    durations = np.full(len(x_array), 0.5)
  else:
    durations = 0.25 + (
      (x_diffs - x_min) / (x_max - x_min)
    ) * 0.75

  allowed_durations = np.array([0.25, 0.5, 0.75, 1.0, 1.5, 2.0])
  durations = np.array([
    allowed_durations[
      np.argmin(np.abs(allowed_durations - d))
    ]
    for d in durations
  ])

  LOW_NOTE = 60
  HIGH_NOTE = 84

  midi_notes = (
    LOW_NOTE +
    y_normalized * (HIGH_NOTE - LOW_NOTE)
  ).astype(int)

  scale = np.array([0, 2, 4, 5, 7, 9, 11])

  def snap_to_scale(midi: int) -> int:
    octave = midi // 12
    pitch_class = midi % 12

    closest = scale[np.argmin(
      np.abs(scale - pitch_class)
    )]

    if closest < pitch_class and pitch_class - closest > 6:
      octave += 1

    return octave * 12 + closest

  midi_notes = np.array([
    snap_to_scale(int(note))
    for note in midi_notes
  ])

  score = music.stream.Score()
  melody = music.stream.Part()
  melody.append(instru)
  melody.append(
    music.tempo.MetronomeMark(number = bpm)
  )

  for i, (pitch, duration) in enumerate(zip(midi_notes, durations)):
    n = music.note.Note(midi = int(pitch))
    n.quarterLength = float(duration)

    if i == 0:
      movement = 0
    else:
      movement = abs(
        int(midi_notes[i]) -
        int(midi_notes[i - 1])
      )

    velocity = 80 + min(movement * 2, 25)
    n.volume.velocity = int(
      np.clip(velocity, 55, 110)
    )
    melody.append(n)
  score.append(melody)

  bass = music.stream.Part()
  bass_instrument = music.instrument.AcousticBass()
  bass.append(bass_instrument)

  for i in range(0, len(midi_notes), 4):
    pitch = midi_notes[i]

    bass_pitch = max(36, int(pitch) - 24)

    n = music.note.Note(midi = bass_pitch)
    n.quarterLength = 2.0
    n.volume.velocity = 28

    bass.append(n)

  score.append(bass)

  pad = music.stream.Part()
  pad_instrument = music.instrument.Viola()
  pad.append(pad_instrument)

  for i in range(0, len(midi_notes), 4):
    root = int(midi_notes[i])
    chord = music.chord.Chord([root, root + 4, root + 7])
    chord.quarterLength = 2.0
    for note in chord.notes:
      note.volume.velocity = 18
    pad.append(chord)
  score.append(pad)

  with tempfile.NamedTemporaryFile(suffix = ".mid") as temp:
    score.write("midi", fp = temp.name)
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
