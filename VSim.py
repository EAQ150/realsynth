import json
from operator import itemgetter
import os
import re
import wave
import numpy as np

try:
  from PyQt6.QtCore import QEventLoop, Qt, QThread, pyqtSignal
  from PyQt6.QtWidgets import QApplication, QProgressDialog
  HAS_PYQT6 = True
except ImportError:
  HAS_PYQT6 = False

SAMPLE_RATE = 44100
ROW_HEIGHT = 24
STEP_WIDTH = 20
STEPS_PER_BEAT = 4

DEFAULT_FORMANTS = {
    "a": (660.0, 1720.0, 2410.0),
    "e": (530.0, 1840.0, 2480.0),
    "i": (400.0, 1920.0, 2550.0),
    "o": (520.0, 880.0, 2400.0),
    "u": (640.0, 1190.0, 2390.0),
    "l": (350.0, 1050.0, 2800.0),
    "h": (530.0, 1840.0, 2480.0),
    "あ": (800.0, 1200.0, 2500.0),
    "え": (500.0, 1900.0, 2600.0),
    "い": (300.0, 2300.0, 3000.0),
    "お": (500.0, 900.0, 2500.0),
    "う": (350.0, 1150.0, 2500.0),
}

UNVOICED_CONSONANTS = {"h", "s", "sh", "f", "th", "ch", "ts"}
VOWEL_CHARS = set("aeiouあいうえお")


def is_vowel_token(tok):
  return any(ch in VOWEL_CHARS for ch in tok)


def tokenize_word(raw_word, phonemes):
  raw_word = raw_word.replace("qu", "kw").replace("q", "k")
  raw_word = re.sub(r"c([eiy])", r"s\1", raw_word)
  raw_word = raw_word.replace("c", "k")

  all_keys = set(phonemes.keys()) | set(DEFAULT_FORMANTS.keys())
  ordered_keys = sorted(all_keys, key=len, reverse=True)
  tokens = []
  i = 0
  while i < len(raw_word):
    matched = None
    for key in ordered_keys:
      if raw_word.startswith(key, i):
        matched = key
        break
    if matched:
      if not (tokens and tokens[-1] == matched and not is_vowel_token(matched)):
        tokens.append(matched)
      i += len(matched)
    else:
      i += 1
  return tokens if tokens else ["a"]
def parse_vsim_voicebank(singer_dir):
  config = {
      "voice": (0.8, 1.0, 0.0),
      "wave_mix": (0.4, 0.5, 0.1),
      "upper_formants": (3500.0, 4500.0),
      "tract": 1.0,
      "breath": 0.018,
      "phonemes": {},
  }

  if not singer_dir or not os.path.isdir(singer_dir):
    return config

  vb_file = os.path.join(singer_dir, "voice.v")
  if not os.path.isfile(vb_file):
    return config

  with open(vb_file, "r", encoding="utf-8") as f:
    text = f.read()

  v_match = re.search(r"voice\s*\{([^}]+)\}", text, re.IGNORECASE)
  if v_match:
    nums = [float(x) for x in v_match.group(1).strip().split()]
    if len(nums) >= 3:
      config["voice"] = tuple(nums[:3])
    if len(nums) >= 6:
      s_amt, saw_amt, sq_amt = nums[3:6]
      total = s_amt + saw_amt + sq_amt
      if total > 0:
        config["wave_mix"] = (s_amt / total, saw_amt / total, sq_amt / total)
    if len(nums) >= 8:
      config["upper_formants"] = (nums[6], nums[7])

  for raw_line in text.splitlines():
    line, _, _ = raw_line.partition("#")
    line = line.strip()
    if not line or ":" not in line or line.lower().startswith("voice"):
      continue

    key, vals = line.split(":", 1)
    key = key.strip().lower()
    nums = [float(x) for x in vals.strip().split()]

    if key == "tract" and nums:
      config["tract"] = float(nums.pop(0))
    elif key == "breath" and nums:
      config["breath"] = float(nums.pop(0))
    elif len(nums) >= 6:
      config["phonemes"][key] = {
          "wave": tuple(nums[:3]),
          "formants": tuple(nums[3:6]),
      }
    elif len(nums) >= 3:
      config["phonemes"][key] = {
          "wave": tuple(nums[:3]),
          "formants": None,
      }

  return config


def y_to_hz(y_pos):
  row = y_pos / ROW_HEIGHT
  midi_note = 107.0 - row
  return 440.0 * (2.0 ** ((midi_note - 69.0) / 12.0))
def build_greedy_envelopes(tokens, phonemes, num_samples, duration_sec, tract_scale):
  cons_dur = 0.065
  num_cons = sum(1 for tok in tokens if not is_vowel_token(tok))
  num_vowels = max(1, len(tokens) - num_cons)

  total_cons_time = min(duration_sec * 0.6, num_cons * cons_dur)
  per_cons_time = total_cons_time / max(1, num_cons)
  per_vowel_time = max(0.03, (duration_sec - total_cons_time) / num_vowels)

  centers = []
  cursor = 0.0
  for idx, tok in enumerate(tokens):
    seg_dur = per_vowel_time if is_vowel_token(tok) else per_cons_time
    entry = phonemes.get(tok)

    if tok == "h" and idx + 1 < len(tokens):
      next_tok = tokens[idx + 1]
      next_entry = phonemes.get(next_tok)
      if next_entry and next_entry["formants"]:
        f1, f2, f3 = next_entry["formants"]
      else:
        f1, f2, f3 = DEFAULT_FORMANTS.get(next_tok, (530.0, 1840.0, 2480.0))
    elif entry and entry["formants"]:
      f1, f2, f3 = entry["formants"]
    else:
      f1, f2, f3 = DEFAULT_FORMANTS.get(tok, (660.0, 1720.0, 2410.0))

    p_amp, p_freq_mult, p_phi = entry["wave"] if entry else (0.7, 1.0, 0.0)
    scale = max(0.4, p_freq_mult * tract_scale)

    v_gain = 0.0 if tok in UNVOICED_CONSONANTS else (0.65 if not is_vowel_token(tok) else 1.0)
    b_gain = 0.25 if tok in UNVOICED_CONSONANTS else 0.0

    center_sample = int(((cursor + seg_dur * 0.5) / duration_sec) * num_samples)
    centers.append((center_sample, f1 * scale, f2 * scale, f3 * scale, v_gain, b_gain, p_amp, p_phi))
    cursor += seg_dur

  first_c = centers[0]
  last_c = centers[-1]
  padded = [first_c] + centers + [last_c]

  idx_pts = [0] + list(map(itemgetter(0), centers)) + [num_samples - 1]
  x = np.arange(num_samples)

  f1_arr = np.interp(x, idx_pts, list(map(itemgetter(1), padded)))
  f2_arr = np.interp(x, idx_pts, list(map(itemgetter(2), padded)))
  f3_arr = np.interp(x, idx_pts, list(map(itemgetter(3), padded)))
  v_gain = np.interp(x, idx_pts, list(map(itemgetter(4), padded)))
  b_gain = np.interp(x, idx_pts, list(map(itemgetter(5), padded)))
  amp_arr = np.interp(x, idx_pts, list(map(itemgetter(6), padded)))
  phi_arr = np.interp(x, idx_pts, list(map(itemgetter(7), padded)))

  return f1_arr, f2_arr, f3_arr, v_gain, b_gain, amp_arr, phi_arr
def _render_project_core(project_data, output_wav="render_output.wav", bpm=120.0, progress_callback=None):
  if isinstance(project_data, str):
    with open(project_data, "r", encoding="utf-8") as f:
      project_data = json.load(f)

  singer_info = project_data.get("singer", {})
  singer_dir = singer_info.get("singerdir", "")
  master_vol = singer_info.get("volume", 70) / 100.0
  clarity = singer_info.get("clarity", 70) / 100.0

  vb_config = parse_vsim_voicebank(singer_dir)
  notes = project_data.get("notes", [])
  transitions = project_data.get("transitions", [])

  if not notes:
    return None

  sec_per_step = (60.0 / bpm) / STEPS_PER_BEAT
  max_end_step = max((n["x"] + n["width"]) / STEP_WIDTH for n in notes)
  total_samples = int((max_end_step * sec_per_step + 0.5) * SAMPLE_RATE)

  def update_bar(pct):
    if progress_callback:
      progress_callback(pct)

  update_bar(5)

  freq_curve = np.full(total_samples, 220.0, dtype=np.float64)
  f1_curve = np.full(total_samples, 660.0, dtype=np.float64)
  f2_curve = np.full(total_samples, 1720.0, dtype=np.float64)
  f3_curve = np.full(total_samples, 2410.0, dtype=np.float64)

  active_gate = np.zeros(total_samples, dtype=np.float64)
  v_gain = np.zeros(total_samples, dtype=np.float64)
  b_gain = np.zeros(total_samples, dtype=np.float64)
  amp_curve = np.full(total_samples, 0.7, dtype=np.float64)
  phi_curve = np.zeros(total_samples, dtype=np.float64)
  vib_env = np.zeros(total_samples, dtype=np.float64)

  tone_drive = np.full(total_samples, 1.0, dtype=np.float64)
  tone_gain = np.full(total_samples, 1.0, dtype=np.float64)
  whisper_mix = np.zeros(total_samples, dtype=np.float64)

  v_amp, v_freq_mult, v_phi = vb_config["voice"]
  sine_amt, saw_amt, sq_amt = vb_config["wave_mix"]
  f4_base, f5_base = vb_config["upper_formants"]
  tract_scale = vb_config.get("tract", 1.0)
  breath_amt = vb_config.get("breath", 0.018)
  phonemes = vb_config["phonemes"]

  indexed_notes = sorted(enumerate(notes), key=lambda item: item[1]["x"])
  note_spans = {}
  VOICELESS_STOPS = {"t", "k", "p"}
  VOICED_STOPS = {"d", "b", "g"}
  ALL_STOPS = VOICELESS_STOPS | VOICED_STOPS

  for orig_idx, note in indexed_notes:
    start_sec = (note["x"] / STEP_WIDTH) * sec_per_step
    dur_sec = max(0.05, (note["width"] / STEP_WIDTH) * sec_per_step)
    s0 = int(start_sec * SAMPLE_RATE)
    s1 = min(total_samples, s0 + int(dur_sec * SAMPLE_RATE))
    n_len = s1 - s0
    if n_len <= 0:
      continue

    note_spans[orig_idx] = (s0, s1)
    freq_curve[s0:s1] = y_to_hz(note["y"])
    active_gate[s0:s1] = 1.0

    t_local = np.arange(n_len) / SAMPLE_RATE
    vib_env[s0:s1] = np.clip((t_local - 0.25) / 0.2, 0.0, 1.0)

    raw_word = note.get("word", "a").strip().lower()
    raw_word = raw_word.replace("qu", "kw").replace("q", "k")
    raw_word = re.sub(r"c([eiy])", r"s\1", raw_word)
    raw_word = raw_word.replace("c", "k")

    tokens = tokenize_word(raw_word, phonemes)
    f1, f2, f3, vg, bg, amp, phi = build_greedy_envelopes(
        tokens, phonemes, n_len, dur_sec, tract_scale
    )

    for tok_i, tok in enumerate(tokens):
      if tok in ALL_STOPS:
        seg_start = int((tok_i / max(1, len(tokens))) * min(n_len, int(0.08 * SAMPLE_RATE)))
        seg_end = min(n_len, seg_start + int(0.045 * SAMPLE_RATE))
        if seg_end > seg_start:
          bg[seg_start:seg_end] = 0.0

    first_tok = tokens[0]
    if first_tok in ALL_STOPS:
      stop_len = min(n_len // 3, int(0.026 * SAMPLE_RATE))
      rel_len = min(n_len // 3, int(0.020 * SAMPLE_RATE))
      if stop_len > 4:
        hold_gain = 0.02 if first_tok in VOICELESS_STOPS else 0.30
        vg[:stop_len] = hold_gain
        bg[:stop_len] = 0.0
        if rel_len > 2 and stop_len + rel_len < n_len:
          vg[stop_len : stop_len + rel_len] = np.linspace(hold_gain, 1.0, rel_len)
          bg[stop_len : stop_len + rel_len] = 0.0

    f1_curve[s0:s1] = f1
    f2_curve[s0:s1] = f2
    f3_curve[s0:s1] = f3
    v_gain[s0:s1] = vg
    b_gain[s0:s1] = bg
    amp_curve[s0:s1] = amp
    phi_curve[s0:s1] = phi

    tone = note.get("tone", "Normal")
    if tone == "Yell":
      tone_drive[s0:s1] = 2.2
      tone_gain[s0:s1] = 1.15
    elif tone == "Soft":
      tone_gain[s0:s1] = 0.6
    elif tone == "Whisper":
      tone_gain[s0:s1] = 0.2
      whisper_mix[s0:s1] = 0.18

  for tr in transitions:
    from_idx = tr.get("from_note")
    to_idx = tr.get("to_note")
    if from_idx not in note_spans or to_idx not in note_spans:
      continue

    from_s0, from_s1 = note_spans[from_idx]
    to_s0, to_s1 = note_spans[to_idx]
    start_hz = y_to_hz(notes[from_idx]["y"])
    end_hz = y_to_hz(notes[to_idx]["y"])
    is_curve = tr.get("mode") == "curve"

    if to_s0 > from_s1:
      g0, g1 = from_s1, to_s0
      g_len = g1 - g0
      u = np.linspace(0.0, 1.0, g_len)
      blend = 0.5 * (1.0 - np.cos(np.pi * u)) if is_curve else u

      freq_curve[g0:g1] = start_hz + (end_hz - start_hz) * blend
      active_gate[g0:g1] = 1.0
      vib_env[g0:g1] = 0.0

      f1_curve[g0:g1] = np.linspace(f1_curve[from_s1 - 1], f1_curve[to_s0], g_len)
      f2_curve[g0:g1] = np.linspace(f2_curve[from_s1 - 1], f2_curve[to_s0], g_len)
      f3_curve[g0:g1] = np.linspace(f3_curve[from_s1 - 1], f3_curve[to_s0], g_len)
      v_gain[g0:g1] = np.linspace(v_gain[from_s1 - 1], v_gain[to_s0], g_len)
      b_gain[g0:g1] = np.linspace(b_gain[from_s1 - 1], b_gain[to_s0], g_len)
      amp_curve[g0:g1] = np.linspace(amp_curve[from_s1 - 1], amp_curve[to_s0], g_len)
      phi_curve[g0:g1] = np.linspace(phi_curve[from_s1 - 1], phi_curve[to_s0], g_len)
      tone_drive[g0:g1] = np.linspace(tone_drive[from_s1 - 1], tone_drive[to_s0], g_len)
      tone_gain[g0:g1] = np.linspace(tone_gain[from_s1 - 1], tone_gain[to_s0], g_len)
      whisper_mix[g0:g1] = np.linspace(whisper_mix[from_s1 - 1], whisper_mix[to_s0], g_len)
    else:
      glide_len = min(to_s1 - to_s0, int(0.12 * SAMPLE_RATE))
      if glide_len > 1:
        u = np.linspace(0.0, 1.0, glide_len)
        blend = 0.5 * (1.0 - np.cos(np.pi * u)) if is_curve else u
        freq_curve[to_s0 : to_s0 + glide_len] = start_hz + (end_hz - start_hz) * blend

  coart_len = max(1, int(0.035 * SAMPLE_RATE))
  coart_kernel = np.ones(coart_len) / coart_len
  f1_curve = np.convolve(f1_curve, coart_kernel, mode="same")
  f2_curve = np.convolve(f2_curve, coart_kernel, mode="same")
  f3_curve = np.convolve(f3_curve, coart_kernel, mode="same")
  v_gain = np.convolve(v_gain, coart_kernel, mode="same")
  b_gain = np.convolve(b_gain, coart_kernel, mode="same")
  amp_curve = np.convolve(amp_curve, coart_kernel, mode="same")
  phi_curve = np.convolve(phi_curve, coart_kernel, mode="same")

  pitch_smooth_len = max(1, int(0.015 * SAMPLE_RATE))
  freq_curve = np.convolve(freq_curve, np.ones(pitch_smooth_len) / pitch_smooth_len, mode="same")

  ramp_len = max(1, int(0.008 * SAMPLE_RATE))
  smooth_gate = np.convolve(active_gate, np.ones(ramp_len) / ramp_len, mode="same")

  update_bar(20)
  rng = np.random.default_rng()
  jitter_kernel = np.ones(max(1, int(0.012 * SAMPLE_RATE))) / max(1, int(0.012 * SAMPLE_RATE))
  jitter = np.convolve(rng.normal(0.0, 1.0, total_samples), jitter_kernel, mode="same") * 0.004

  t_sec = np.arange(total_samples) / SAMPLE_RATE
  vib_rate = 5.3 + 0.35 * np.sin(2.0 * np.pi * 0.7 * t_sec)
  vib_phase = 2.0 * np.pi * np.cumsum(vib_rate) / SAMPLE_RATE
  vibrato = 0.007 * vib_env * np.sin(vib_phase)

  eff_mult = max(0.1, v_freq_mult)
  f0_curve = freq_curve * eff_mult * (1.0 + jitter + vibrato)
  base_phase = 2.0 * np.pi * np.cumsum(f0_curve) / SAMPLE_RATE

  shimmer = 1.0 + np.convolve(rng.normal(0.0, 0.035, total_samples), jitter_kernel, mode="same")

  hb1, hb2, hb3, hb4, hb5 = 45.0, 65.0, 90.0, 130.0, 170.0
  f4_scaled = np.float32(f4_base * tract_scale)
  f5_scaled = np.float32(f5_base * tract_scale)

  active_idx = np.flatnonzero(smooth_gate > 1e-4)
  voiced = np.zeros(total_samples, dtype=np.float32)

  if active_idx.size > 0:
    f0_act = f0_curve[active_idx].astype(np.float32)
    f1_act = f1_curve[active_idx].astype(np.float32)
    f2_act = f2_curve[active_idx].astype(np.float32)
    f3_act = f3_curve[active_idx].astype(np.float32)
    bp_act = base_phase[active_idx].astype(np.float32)
    phi_act = phi_curve[active_idx].astype(np.float32)

    step_phasor = np.exp(1j * bp_act).astype(np.complex64)
    curr_phasor = step_phasor.copy()
    phi_step = np.exp(1j * phi_act).astype(np.complex64)
    curr_phi = phi_step.copy()
    v_phi_phasor = np.complex64(np.exp(1j * v_phi))

    pitch_ratio = np.clip(f0_act / np.float32(220.0), 0.5, 2.0)
    age_lock = pitch_ratio ** np.float32(0.08)
    f1_eff = f1_act * age_lock
    f2_eff = f2_act * age_lock
    f3_eff = f3_act * age_lock

    bw_scale = np.float32(1.15) - np.float32(0.15) * pitch_ratio
    inv_hb1 = np.float32(1.0) / (np.float32(hb1) * bw_scale)
    inv_hb2 = np.float32(1.0) / (np.float32(hb2) * bw_scale)
    inv_hb3 = np.float32(1.0 / hb3)
    inv_hb4 = np.float32(1.0 / hb4)
    inv_hb5 = np.float32(1.0 / hb5)

    tilt = np.float32(0.95) + np.float32(0.30) * np.clip(
        (np.float32(330.0) - f0_act) / np.float32(220.0), 0.0, 1.0
    )

    voiced_act = np.zeros(active_idx.size, dtype=np.float32)
    min_f0 = float(np.min(f0_act))
    max_h = min(64, int(16000.0 / max(40.0, min_f0)))

    sine_f = np.float32(sine_amt)
    saw_f = np.float32(saw_amt)
    sq_f = np.float32(sq_amt)
    clarity_w = np.float32(0.20 + 0.25 * clarity)
    nyq_limit = np.float32(SAMPLE_RATE * 0.45)

    def fast_res(f_hz, f_c, inv_hb):
      u = (f_hz - f_c) * inv_hb
      u2 = u * u
      mag = np.float32(1.0) / np.sqrt(np.float32(1.0) + u2)
      phase = (np.float32(-1.5707963) * u) / (
          np.float32(1.0) + np.abs(u) + np.float32(0.28) * u2
      )
      return mag, phase

    for h in range(1, max_h + 1):
      if h % 4 == 0:
        update_bar(20 + int((h / max_h) * 70))

      h_f = np.float32(h)
      h_hz = f0_act * h_f
      nyq_mask = h_hz < nyq_limit
      if not np.any(nyq_mask):
        break

      h_sine = sine_f if h == 1 else np.float32(0.0)
      h_pow = h_f ** (-tilt)
      glottal_gain = h_sine + (saw_f + (sq_f if (h & 1) else np.float32(0.0))) * h_pow

      m1, p1 = fast_res(h_hz, f1_eff, inv_hb1)
      m2, p2 = fast_res(h_hz, f2_eff, inv_hb2)
      m3, p3 = fast_res(h_hz, f3_eff, inv_hb3)
      m4, p4 = fast_res(h_hz, f4_scaled, inv_hb4)
      m5, p5 = fast_res(h_hz, f5_scaled, inv_hb5)

      cascade_mag = (m1 * m2 * m3 * m4 * m5) * np.float32(18.0)
      parallel_mag = (
          np.float32(0.35) * m1
          + np.float32(0.30) * m2
          + clarity_w * m3
          + np.float32(0.15) * m4
          + np.float32(0.10) * m5
      )
      total_mag = np.float32(0.65) * cascade_mag + np.float32(0.35) * parallel_mag

      total_phase = p1 + p2 + p3 + p4 + p5 + np.float32(-0.35 * np.log(h))
      res_phasor = np.cos(total_phase) + 1j * np.sin(total_phase)

      full_phasor = curr_phasor * curr_phi * v_phi_phasor * res_phasor
      voiced_act += np.where(
          nyq_mask, glottal_gain * total_mag * full_phasor.imag, np.float32(0.0)
      )

      curr_phasor *= step_phasor
      curr_phi *= phi_step

    voiced[active_idx] = voiced_act * shimmer[active_idx].astype(np.float32)

  update_bar(92)
  glottal_pulse_env = 0.5 + 0.5 * np.sin(base_phase)
  raw_asp = rng.normal(0.0, 0.25, total_samples)
  p_f2 = 2.0 * np.pi * np.cumsum(f2_curve) / SAMPLE_RATE
  p_f3 = 2.0 * np.pi * np.cumsum(f3_curve) / SAMPLE_RATE
  band_noise = (
      np.convolve(raw_asp * np.cos(p_f2), np.ones(16) / 16.0, mode="same") * np.cos(p_f2)
      + np.convolve(raw_asp * np.cos(p_f3), np.ones(12) / 12.0, mode="same") * np.cos(p_f3)
  )
  formant_asp = band_noise * (0.45 + 0.55 * glottal_pulse_env)

  combined = (voiced * v_gain * v_amp * (0.6 + amp_curve)) + (formant_asp * b_gain)
  combined *= smooth_gate
  combined += np.random.normal(0.0, breath_amt * 0.08, total_samples) * smooth_gate

  combined = np.tanh(combined * tone_drive) * tone_gain
  combined += np.random.normal(0.0, 1.0, total_samples) * whisper_mix * smooth_gate

  peak = np.max(np.abs(combined))
  if peak > 0:
    combined = (combined / peak) * master_vol * 0.9

  pcm_data = np.int16(np.clip(combined, -1.0, 1.0) * 32767)

  with wave.open(output_wav, "w") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(pcm_data.tobytes())

  update_bar(100)
  return output_wav


def render_project(project_data, output_wav="render_output.wav", bpm=120.0, progress_callback=None):
  if not HAS_PYQT6 or QApplication.instance() is None:
    return _render_project_core(project_data, output_wav, bpm, progress_callback)

  class _VSimThread(QThread):
    prog = pyqtSignal(int)
    done = pyqtSignal(object)

    def run(self):
      res = _render_project_core(project_data, output_wav, bpm, self.prog.emit)
      self.done.emit(res)

  parent_win = QApplication.activeWindow()
  dlg = QProgressDialog("Rendering VSim vocals...", None, 0, 100, parent_win)
  dlg.setWindowTitle("VSim")
  dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
  dlg.setMinimumDuration(0)
  dlg.setAutoClose(True)
  dlg.setValue(0)
  dlg.show()

  loop = QEventLoop()
  worker = _VSimThread()
  result_holder = []

  def on_prog(val):
    dlg.setValue(val)
    if progress_callback:
      progress_callback(val)

  def on_done(res):
    result_holder.append(res)
    dlg.close()
    loop.quit()

  worker.prog.connect(on_prog)
  worker.done.connect(on_done)
  worker.start()
  loop.exec()
  worker.wait()

  return result_holder[0] if result_holder else None
