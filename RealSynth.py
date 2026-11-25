import json
import math
import os
from pathlib import Path
import shutil
import sys
import zipfile
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import *
import VSim
import webbrowser

base_dir = Path(__file__).resolve().parent
pencil_path = str(base_dir / "assets" / "images" / "pencil.svg")
eraser_path = str(base_dir / "assets" / "images" / "eraser.svg")
select_path = str(base_dir / "assets" / "images" / "select.svg")
pan_path = str(base_dir / "assets" / "images" / "pan.svg")
link_path = str(base_dir / "assets" / "images" / "link.svg")
icon_path = base_dir / "logo.png"

app = QApplication(sys.argv)
app.setWindowIcon(QIcon(str(icon_path)))

CONFIG_PATH = os.path.join(os.path.expanduser("~"), "RealSynth", "config.json")

DEFAULT_CONFIG = {
    "singers_dir": os.path.join(os.path.expanduser("~"), "RealSynth", "Singers"),
    "default_bpm": 120,
    "master_volume": 100,
    "default_word": "a",
    "auto_extend_timeline": True,
    "bg_color": "#18181b",
    "surface_color": "#27272a",
    "border_color": "#3f3f46",
    "text_color": "#f4f4f5",
    "accent_color": "#3b82f6",
    "note_color": "#5555ff",
    "playhead_color": "#ff4455",
}

THEME_PRESETS = {
    "Midnight Blue (Default)": {
        "bg_color": "#18181b",
        "surface_color": "#27272a",
        "border_color": "#3f3f46",
        "text_color": "#f4f4f5",
        "accent_color": "#1048ff",
        "note_color": "#1048ff",
        "playhead_color": "#ff4455",
    },
    "Emerald Synth": {
        "bg_color": "#121716",
        "surface_color": "#1e2624",
        "border_color": "#313e3b",
        "text_color": "#ecfdf5",
        "accent_color": "#10b981",
        "note_color": "#059669",
        "playhead_color": "#f59e0b",
    },
    "Crimson Studio": {
        "bg_color": "#181416",
        "surface_color": "#261f22",
        "border_color": "#3f3238",
        "text_color": "#fff1f2",
        "accent_color": "#e11d48",
        "note_color": "#be123c",
        "playhead_color": "#38bdf8",
    },
    "Violet Neon": {
        "bg_color": "#15131c",
        "surface_color": "#211e2c",
        "border_color": "#363147",
        "text_color": "#f5f3ff",
        "accent_color": "#8b5cf6",
        "note_color": "#7c3aed",
        "playhead_color": "#00e08f",
    },
    "First Snow": {
            "bg_color": "#13181c",
            "surface_color": "#1e252c",
            "border_color": "#313D47",
            "text_color": "#f5f3ff",
            "accent_color": "#217bb7",
            "note_color": "#6dbee7",
            "playhead_color": "#AC302C",
        },
    "The Void": {
            "bg_color": "#000000",
            "surface_color": "#000000",
            "border_color": "#111111",
            "text_color": "#f5f3ff",
            "accent_color": "#333333",
            "note_color": "#222222",
            "playhead_color": "#ffffff",
        },
}


def load_config():
  if os.path.isfile(CONFIG_PATH):
    try:
      with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return {**DEFAULT_CONFIG, **json.load(f)}
    except Exception:
      pass
  return DEFAULT_CONFIG.copy()


def save_config(cfg):
  os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
  with open(CONFIG_PATH, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2)
def build_stylesheet_part_a(
    bg, surface, border, text, accent, accent_hover, accent_pressed, accent_light
):
  return f"""
QWidget {{
    background-color: {bg};
    color: {text};
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 14px;
}}

QMenuBar {{
    background-color: {bg};
    color: {text};
    border-bottom: 1px solid {surface};
    padding: 2px;
}}

QMenuBar::item {{
    background: transparent;
    padding: 4px 10px;
    border-radius: 4px;
}}

QMenuBar::item:selected {{
    background-color: {surface};
}}

QMenu {{
    background-color: {surface};
    color: {text};
    border: 1px solid {border};
    padding: 4px;
}}

QMenu::item {{
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {accent};
    color: #ffffff;
}}

QPushButton {{
    background-color: {accent};
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: bold;
    outline: none;
}}

QPushButton:hover {{
    background-color: {accent_hover};
}}

QPushButton:pressed {{
    background-color: {accent_pressed};
}}

QPushButton:checked {{
    background-color: {accent_pressed};
    border: 1px solid {accent_light};
}}

QPushButton:checked:hover {{
    background-color: {accent_hover};
}}

QPushButton:disabled {{
    background-color: {surface};
    color: #71717a;
}}

QWidget#toolbar QPushButton {{
    background-color: {surface};
    padding: 4px 8px;
    min-width: 24px;
    min-height: 22px;
}}

QWidget#toolbar QPushButton:hover {{
    background-color: {border};
}}

QWidget#toolbar QPushButton:pressed {{
    background-color: {accent_pressed};
}}

QWidget#toolbar QPushButton:checked {{
    background-color: {accent};
    border: 1px solid {accent_light};
}}

QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {{
    background-color: {surface};
    color: {text};
    border: 1px solid {border};
    border-radius: 4px;
    padding: 6px 10px;
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QComboBox:focus, QComboBox:on {{
    border: 1px solid {accent};
}}
"""

def build_stylesheet_part_b(bg, surface, border, text, accent, accent_light):
  up_svg = (
      "data:image/svg+xml;utf8,"
      "<svg xmlns='http://w3.org' width='10' height='10' "
      "viewBox='0 0 10 10' fill='none' stroke='%23a1a1aa' "
      "stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'>"
      "<polyline points='2,6.5 5,3.5 8,6.5'/></svg>"
  )
  up_hover_svg = up_svg.replace("%23a1a1aa", "%23f4f4f5")
  down_svg = (
      "data:image/svg+xml;utf8,"
      "<svg xmlns='http://w3.org' width='10' height='10' "
      "viewBox='0 0 10 10' fill='none' stroke='%23a1a1aa' "
      "stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'>"
      "<polyline points='2,3.5 5,6.5 8,3.5'/></svg>"
  )
  down_hover_svg = down_svg.replace("%23a1a1aa", "%23f4f4f5")
  combo_svg = (
      "data:image/svg+xml;utf8,"
      "<svg xmlns='http://w3.org' width='12' height='12' "
      "viewBox='0 0 12 12' fill='none' stroke='%23a1a1aa' "
      "stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'>"
      "<polyline points='2.5,4.5 6,8 9.5,4.5'/></svg>"
  )
  combo_hover_svg = combo_svg.replace("%23a1a1aa", "%23f4f4f5")

  return f"""
QSpinBox {{
    padding: 4px 8px;
}}

QSpinBox::up-button, QSpinBox::down-button {{
    subcontrol-origin: border;
    width: 18px;
    border: none;
    background: transparent;
}}

QSpinBox::up-arrow {{
    image: url("{up_svg}");
    width: 10px;
    height: 10px;
}}

QSpinBox::up-arrow:hover {{
    image: url("{up_hover_svg}");
}}

QSpinBox::down-arrow {{
    image: url("{down_svg}");
    width: 10px;
    height: 10px;
}}

QSpinBox::down-arrow:hover {{
    image: url("{down_hover_svg}");
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border: none;
    background: transparent;
}}

QComboBox::down-arrow {{
    image: url("{combo_svg}");
    width: 12px;
    height: 12px;
}}

QComboBox::down-arrow:hover {{
    image: url("{combo_hover_svg}");
}}

QComboBox QAbstractItemView {{
    background-color: {surface};
    color: {text};
    border: 1px solid {border};
    selection-background-color: {accent};
    selection-color: #ffffff;
    outline: 0px;
}}

QListWidget {{
    background-color: {surface};
    color: {text};
    border: 1px solid {border};
    border-radius: 4px;
    outline: 0px;
}}

QListWidget::item {{
    padding: 6px;
}}

QListWidget::item:selected {{
    background-color: {accent};
    color: #ffffff;
}}

QSlider::groove:horizontal {{
    height: 4px;
    background: {border};
    border-radius: 2px;
}}

QSlider::sub-page:horizontal {{
    background: {accent};
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background: {text};
    border: none;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}

QSlider::handle:horizontal:hover {{
    background: {accent_light};
}}

QCheckBox, QRadioButton {{
    spacing: 8px;
}}

QCheckBox::indicator, QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    background-color: {surface};
    border: 1px solid #52525b;
}}

QCheckBox::indicator {{
    border-radius: 3px;
}}

QRadioButton::indicator {{
    border-radius: 9px;
}}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background-color: {accent};
    border: 1px solid {accent};
}}

QTabWidget::pane {{
    border: 1px solid {surface};
    background-color: {bg};
}}

QTabBar::tab {{
    background-color: {surface};
    color: #a1a1aa;
    padding: 8px 16px;
    border: none;
}}

QTabBar::tab:selected {{
    background-color: {bg};
    color: {text};
    border-bottom: 2px solid {accent};
}}

QGroupBox {{
    color: {text};
    border: 1px solid {border};
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 10px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}}

QScrollBar:vertical {{
    background: {bg};
    width: 10px;
    margin: 0px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background: {border};
    border-radius: 5px;
    min-height: 20px;
    border: none;
}}

QScrollBar::handle:vertical:hover {{
    background: #52525b;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    background: none;
    border: none;
    height: 0px;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
    border: none;
}}

QScrollBar:horizontal {{
    background: {bg};
    height: 10px;
    margin: 0px;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background: {border};
    border-radius: 5px;
    min-width: 20px;
    border: none;
}}

QScrollBar::handle:horizontal:hover {{
    background: #52525b;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    background: none;
    border: none;
    width: 0px;
}}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
    border: none;
}}

QAbstractScrollArea::corner {{
    background: {bg};
    border: none;
}}
"""


def apply_theme(cfg):
  bg = cfg["bg_color"]
  surface = cfg["surface_color"]
  border = cfg["border_color"]
  text = cfg["text_color"]
  accent = cfg["accent_color"]

  accent_q = QColor(accent)
  accent_hover = accent_q.darker(115).name()
  accent_pressed = accent_q.darker(135).name()
  accent_light = accent_q.lighter(125).name()

  app.setStyle("Fusion")
  qss = build_stylesheet_part_a(
      bg, surface, border, text, accent, accent_hover, accent_pressed, accent_light
  )
  qss += build_stylesheet_part_b(bg, surface, border, text, accent, accent_light)
  app.setStyleSheet(qss)


app_config = load_config()
SINGERS_ROOT = app_config["singers_dir"]
os.makedirs(SINGERS_ROOT, exist_ok=True)
apply_theme(app_config)
def save_project():
  file_path, _ = QFileDialog.getSaveFileName(
      maindaw,
      "Save RealSynth Project",
      "untitled.json",
      "RealSynth Project (*.json);;All Files (*)",
  )
  if not file_path:
    return

  notes = [item for item in roll_scene.items() if isinstance(item, NoteItem)]
  notes.sort(key=lambda n: (n.x(), n.y()))
  note_to_idx = {note: i for i, note in enumerate(notes)}

  notes_data = []
  for note in notes:
    notes_data.append({
        "x": note.x(),
        "y": note.y(),
        "width": note.rect().width(),
        "word": note.word,
        "tone": note.tone,
    })

  transitions = [
      item for item in roll_scene.items() if isinstance(item, TransitionLine)
  ]
  transitions_data = []
  for t in transitions:
    if t.note_a in note_to_idx and t.note_b in note_to_idx:
      transitions_data.append({
          "from_note": note_to_idx[t.note_a],
          "to_note": note_to_idx[t.note_b],
          "mode": t.mode,
      })

  project_data = {
      "version": "0.0.1",
      "singer": {
          "singerdir": current_singer_dir,
          "language": singerlang.currentText(),
          "method": singermethod.currentText(),
          "volume": singervol.value(),
          "clarity": singerclar.value(),
      },
      "notes": notes_data,
      "transitions": transitions_data,
  }

  with open(file_path, "w", encoding="utf-8") as f:
    json.dump(project_data, f, indent=2)
  maindaw.setWindowTitle(f"RealSynth v0.0.1 Alpha - {file_path}")


def open_project():
  file_path, _ = QFileDialog.getOpenFileName(
      maindaw,
      "Open RealSynth Project",
      "",
      "RealSynth Project (*.json);;All Files (*)",
  )
  if not file_path:
    return

  with open(file_path, "r", encoding="utf-8") as f:
    project_data = json.load(f)

  for item in list(roll_scene.items()):
    if isinstance(item, (NoteItem, TransitionLine)):
      roll_scene.removeItem(item)

  singer = project_data.get("singer", {})
  apply_voicebank(singer.get("singerdir", ""))
  if "language" in singer:
    singerlang.setCurrentText(singer["language"])
  if "method" in singer:
    singermethod.setCurrentText(singer["method"])
  if "volume" in singer:
    singervol.setValue(singer["volume"])
  if "clarity" in singer:
    singerclar.setValue(singer["clarity"])

  notes_data = project_data.get("notes", [])
  if notes_data:
    max_x = max(n["x"] + n["width"] for n in notes_data)
    needed_steps = int(max_x // STEP_WIDTH) + 32
    if needed_steps > drawn_steps:
      extend_timeline(needed_steps)

  created_notes = []
  for n in notes_data:
    note = NoteItem(
        n["x"],
        n["y"],
        n["width"],
        ROW_HEIGHT,
        word=n.get("word", app_config["default_word"]),
        tone=n.get("tone", "Normal"),
    )
    roll_scene.addItem(note)
    created_notes.append(note)

  for t in project_data.get("transitions", []):
    idx_a = t["from_note"]
    idx_b = t["to_note"]
    if 0 <= idx_a < len(created_notes) and 0 <= idx_b < len(created_notes):
      note_a = created_notes[idx_a]
      note_b = created_notes[idx_b]
      line = TransitionLine(note_a, note_b, mode=t.get("mode", "curve"))
      roll_scene.addItem(line)
      note_a.transitions.append(line)
      note_b.transitions.append(line)

  refresh_note_inspector()
  maindaw.setWindowTitle(f"RealSynth v0.0.1 Alpha - {file_path}")


def apply_voicebank(singer_folder):
  global current_singer_dir
  if not singer_folder or not os.path.isdir(singer_folder):
    current_singer_dir = ""
    singerlabel.setText("No Singer")
    singerportraitframe.setPixmap(QPixmap())
    return

  current_singer_dir = singer_folder
  singer_name = os.path.basename(os.path.normpath(singer_folder))
  singerlabel.setText(singer_name)

  icon_path = os.path.join(singer_folder, "singericon.png")
  if os.path.isfile(icon_path):
    singerportraitframe.setPixmap(QPixmap(icon_path))
  else:
    singerportraitframe.setPixmap(QPixmap())


def load_voicebank():
  choice = QMessageBox.question(
      maindaw,
      "Install / Load Voicebank",
      "Install from a .zip file?\n\nClick 'Yes' for a .zip archive, or 'No' to select a singer folder.",
      QMessageBox.StandardButton.Yes
      | QMessageBox.StandardButton.No
      | QMessageBox.StandardButton.Cancel,
  )
  if choice == QMessageBox.StandardButton.Cancel:
    return

  if choice == QMessageBox.StandardButton.Yes:
    zip_path, _ = QFileDialog.getOpenFileName(
        maindaw, "Select Voicebank ZIP", "", "ZIP Archives (*.zip)"
    )
    if not zip_path:
      return
    singer_name = os.path.splitext(os.path.basename(zip_path))[0]
    dest_dir = os.path.join(SINGERS_ROOT, singer_name)
    os.makedirs(dest_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
      zf.extractall(dest_dir)
    nested = os.path.join(dest_dir, singer_name)
    if os.path.isdir(nested):
      dest_dir = nested
  else:
    src_dir = QFileDialog.getExistingDirectory(
        maindaw, "Select Singer Folder"
    )
    if not src_dir:
      return
    singer_name = os.path.basename(os.path.normpath(src_dir))
    dest_dir = os.path.join(SINGERS_ROOT, singer_name)
    if os.path.abspath(src_dir) != os.path.abspath(dest_dir):
      shutil.copytree(src_dir, dest_dir, dirs_exist_ok=True)

  apply_voicebank(dest_dir)
  QMessageBox.information(
      maindaw,
      "Voicebank Installed",
      f"Installed '{singer_name}' to:\n{dest_dir}",
  )


project_data = {}
current_singer_dir = ""
NOTES = ["B", "A#", "A", "G#", "G", "F#", "F", "E", "D#", "D", "C#", "C"]
ROW_HEIGHT = 24
TOTAL_ROWS = 84
STEP_WIDTH = 20
STEPS_PER_BEAT = 4
STEPS_PER_BAR = 16
TOTAL_STEPS = 128
ROLL_WIDTH = TOTAL_STEPS * STEP_WIDTH
drawn_steps = 0
RESIZE_MARGIN = 8
class TransitionLine(QGraphicsPathItem):

  def __init__(self, note_a, note_b, mode="curve"):
    super().__init__()
    self.note_a = note_a
    self.note_b = note_b
    self.mode = mode
    self.setZValue(1)
    self.setCursor(Qt.CursorShape.PointingHandCursor)
    self.update_path()

  def update_path(self):
    x1 = self.note_a.x() + self.note_a.rect().width()
    y1 = self.note_a.y() + (self.note_a.rect().height() / 2)
    x2 = self.note_b.x()
    y2 = self.note_b.y() + (self.note_b.rect().height() / 2)

    path = QPainterPath(QPointF(x1, y1))

    if self.mode == "curve":
      mid_x = (x1 + x2) / 2
      path.cubicTo(QPointF(mid_x, y1), QPointF(mid_x, y2), QPointF(x2, y2))
      pen = QPen(QColor("#00e08f"), 2.5)
    else:
      path.lineTo(QPointF(x2, y2))
      pen = QPen(QColor("#ffaa00"), 2.5, Qt.PenStyle.DashLine)

    self.setPen(pen)
    self.setPath(path)

  def shape(self):
    stroker = QPainterPathStroker()
    stroker.setWidth(10)
    return stroker.createStroke(self.path())

  def toggle_mode(self):
    self.mode = "line" if self.mode == "curve" else "curve"
    self.update_path()


class NoteItem(QGraphicsRectItem):

  def __init__(self, x, y, width, height, word="a", tone="Normal"):
    super().__init__(0, 0, width, height)
    self.word = word
    self.tone = tone
    self.resizing = False
    self.transitions = []

    self.setPos(x, y)
    self.setPen(QPen(QColor(app_config["note_color"])))
    self.setBrush(QBrush(QColor(app_config["note_color"])))
    self.setData(0, "note")

    self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
    self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
    self.setFlag(
        QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True
    )
    self.setAcceptHoverEvents(True)

    self.label = QGraphicsSimpleTextItem(self.word, self)
    self.label.setBrush(QBrush(QColor("#ffffff")))
    self.label.setPos(5, 3)

  def set_word(self, new_word):
    self.word = new_word
    self.label.setText(new_word)

  def get_pitch_name(self):
    row = int(round(self.y() / ROW_HEIGHT))
    row = max(0, min(row, TOTAL_ROWS - 1))
    note_name = NOTES[row % 12]
    octave = 7 - (row // 12)
    return f"{note_name}{octave}"

  def hoverMoveEvent(self, event):
    if event.pos().x() >= self.rect().width() - RESIZE_MARGIN:
      self.setCursor(Qt.CursorShape.SizeHorCursor)
    else:
      self.setCursor(Qt.CursorShape.ArrowCursor)
    super().hoverMoveEvent(event)

  def mousePressEvent(self, event):
    if event.button() == Qt.MouseButton.LeftButton:
      if event.pos().x() >= self.rect().width() - RESIZE_MARGIN:
        self.resizing = True
        self.setSelected(True)
        event.accept()
        return
    super().mousePressEvent(event)

  def mouseMoveEvent(self, event):
    if self.resizing:
      raw_width = event.pos().x()
      snapped_width = max(
          STEP_WIDTH, round(raw_width / STEP_WIDTH) * STEP_WIDTH
      )
      self.setRect(0, 0, snapped_width, self.rect().height())
      for t in self.transitions:
        t.update_path()
      event.accept()
      return
    super().mouseMoveEvent(event)

  def mouseReleaseEvent(self, event):
    if self.resizing:
      self.resizing = False
      for t in self.transitions:
        t.update_path()
      event.accept()
      return
    super().mouseReleaseEvent(event)

  def itemChange(self, change, value):
    if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
      snapped_x = max(0, round(value.x() / STEP_WIDTH) * STEP_WIDTH)
      max_y = (TOTAL_ROWS - 1) * ROW_HEIGHT
      snapped_y = max(0, min(round(value.y() / ROW_HEIGHT) * ROW_HEIGHT, max_y))
      return QPointF(snapped_x, snapped_y)

    if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
      for t in self.transitions:
        t.update_path()
      if self.scene() and hasattr(self.scene(), "on_note_updated"):
        self.scene().on_note_updated(self)

    return super().itemChange(change, value)


class PianoRollScene(QGraphicsScene):

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.active_tool = "Select"

  def connect_selected_notes(self):
    selected_notes = [
        item for item in self.selectedItems() if isinstance(item, NoteItem)
    ]
    if len(selected_notes) != 2:
      return

    note_a, note_b = sorted(selected_notes, key=lambda n: n.x())

    for existing in note_a.transitions:
      if existing.note_a is note_a and existing.note_b is note_b:
        return

    line = TransitionLine(note_a, note_b, mode="curve")
    self.addItem(line)
    note_a.transitions.append(line)
    note_b.transitions.append(line)

  def remove_note_and_transitions(self, note):
    for t in list(note.transitions):
      if t in t.note_a.transitions:
        t.note_a.transitions.remove(t)
      if t in t.note_b.transitions:
        t.note_b.transitions.remove(t)
      if t.scene() == self:
        self.removeItem(t)
    self.removeItem(note)

  def mousePressEvent(self, event):
    pos = event.scenePos()
    if event.button() == Qt.MouseButton.LeftButton:
      clicked_item = self.itemAt(pos, QTransform())

      if isinstance(clicked_item, TransitionLine):
        if self.active_tool == "Eraser":
          clicked_item.note_a.transitions.remove(clicked_item)
          clicked_item.note_b.transitions.remove(clicked_item)
          self.removeItem(clicked_item)
        else:
          clicked_item.toggle_mode()
        event.accept()
        return

      if self.active_tool == "Pencil":
        snap_x = (int(pos.x()) // STEP_WIDTH) * STEP_WIDTH
        snap_y = (int(pos.y()) // ROW_HEIGHT) * ROW_HEIGHT
        default_width = STEP_WIDTH * STEPS_PER_BEAT
        note = NoteItem(
            snap_x,
            snap_y,
            default_width,
            ROW_HEIGHT,
            word=app_config["default_word"],
        )
        self.addItem(note)
        return

      elif self.active_tool == "Eraser":
        if clicked_item and not isinstance(clicked_item, NoteItem):
          clicked_item = clicked_item.parentItem()
        if isinstance(clicked_item, NoteItem):
          self.remove_note_and_transitions(clicked_item)
          return

    super().mousePressEvent(event)


class ClickablePortrait(QLabel):
  clicked = pyqtSignal()

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.setCursor(Qt.CursorShape.PointingHandCursor)
    self.setToolTip("Click to select or install a voicebank")

  def mousePressEvent(self, event):
    if event.button() == Qt.MouseButton.LeftButton:
      self.clicked.emit()
    super().mousePressEvent(event)


class VoicebankSelectorDialog(QDialog):

  def __init__(self, parent=None):
    super().__init__(parent)
    self.setWindowTitle("Select Voicebank")
    self.resize(360, 420)
    self.selected_singer_dir = None

    layout = QVBoxLayout(self)

    info = QLabel("Installed Singers:")
    info.setStyleSheet("font-weight: bold;")
    layout.addWidget(info)

    self.list_widget = QListWidget()
    self.list_widget.setIconSize(QSize(48, 48))
    self.list_widget.itemDoubleClicked.connect(self.accept_selection)
    layout.addWidget(self.list_widget)

    btn_row = QHBoxLayout()
    install_btn = QPushButton("Install New Singer...")
    select_btn = QPushButton("Load Selected")
    cancel_btn = QPushButton("Cancel")

    install_btn.clicked.connect(self.install_new)
    select_btn.clicked.connect(self.accept_selection)
    cancel_btn.clicked.connect(self.reject)

    btn_row.addWidget(install_btn)
    btn_row.addStretch()
    btn_row.addWidget(select_btn)
    btn_row.addWidget(cancel_btn)
    layout.addLayout(btn_row)

    self.populate_singers()

  def populate_singers(self):
    self.list_widget.clear()
    if not os.path.isdir(SINGERS_ROOT):
      return
    for name in sorted(os.listdir(SINGERS_ROOT)):
      folder = os.path.join(SINGERS_ROOT, name)
      if os.path.isdir(folder):
        item = QListWidgetItem(name)
        item.setData(Qt.ItemDataRole.UserRole, folder)
        icon_path = os.path.join(folder, "singericon.png")
        if os.path.isfile(icon_path):
          item.setIcon(QIcon(icon_path))
        self.list_widget.addItem(item)

  def install_new(self):
    load_voicebank()
    self.populate_singers()

  def accept_selection(self):
    item = self.list_widget.currentItem()
    if item:
      self.selected_singer_dir = item.data(Qt.ItemDataRole.UserRole)
      self.accept()
class ColorWheelPicker(QWidget):
  colorChanged = pyqtSignal(str)

  def __init__(self, hex_color="#3b82f6", parent=None):
    super().__init__(parent)
    self._hue = 0.0
    self._sat = 1.0
    self._val = 1.0
    self._wheel_pixmap = None

    layout = QVBoxLayout(self)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10)

    self.wheel_area = QWidget()
    self.wheel_area.setFixedSize(170, 170)
    self.wheel_area.paintEvent = self._paint_wheel
    self.wheel_area.mousePressEvent = self._mouse_wheel
    self.wheel_area.mouseMoveEvent = self._mouse_wheel
    self.wheel_area.setCursor(Qt.CursorShape.CrossCursor)
    layout.addWidget(self.wheel_area, alignment=Qt.AlignmentFlag.AlignCenter)

    val_row = QHBoxLayout()
    val_row.addWidget(QLabel("Brightness:"))
    self.val_slider = QSlider(Qt.Orientation.Horizontal)
    self.val_slider.setRange(0, 100)
    self.val_slider.setValue(100)
    self.val_slider.valueChanged.connect(self._on_val_changed)
    val_row.addWidget(self.val_slider)
    layout.addLayout(val_row)

    hex_row = QHBoxLayout()
    self.preview_box = QLabel()
    self.preview_box.setFixedSize(28, 28)
    self.hex_input = QLineEdit()
    self.hex_input.setMaxLength(7)
    self.hex_input.setPlaceholderText("#RRGGBB")
    self.hex_input.textEdited.connect(self._on_hex_edited)

    dialog_btn = QPushButton("System Picker...")
    dialog_btn.clicked.connect(self._open_system_dialog)

    hex_row.addWidget(self.preview_box)
    hex_row.addWidget(self.hex_input)
    hex_row.addWidget(dialog_btn)
    layout.addLayout(hex_row)

    self.set_color(hex_color, emit=False)

  def _build_wheel_pixmap(self, size):
    img = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    cx = size / 2.0
    cy = size / 2.0
    radius = (size / 2.0) - 4.0

    for y in range(size):
      for x in range(size):
        dx = x - cx
        dy = y - cy
        dist = math.hypot(dx, dy)
        if dist <= radius:
          hue = (math.degrees(math.atan2(-dy, dx)) + 360.0) % 360.0
          sat = min(1.0, dist / radius)
          c = QColor.fromHsvF(hue / 360.0, sat, 1.0)
          img.setPixelColor(x, y, c)
    return QPixmap.fromImage(img)

  def _paint_wheel(self, event):
    size = self.wheel_area.width()
    if self._wheel_pixmap is None or self._wheel_pixmap.width() != size:
      self._wheel_pixmap = self._build_wheel_pixmap(size)

    painter = QPainter(self.wheel_area)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.drawPixmap(0, 0, self._wheel_pixmap)

    cx = size / 2.0
    cy = size / 2.0
    radius = (size / 2.0) - 4.0
    angle = math.radians(self._hue * 360.0)
    px = cx + math.cos(angle) * (self._sat * radius)
    py = cy - math.sin(angle) * (self._sat * radius)

    painter.setPen(QPen(QColor("#000000"), 3))
    painter.drawEllipse(QPointF(px, py), 6, 6)
    painter.setPen(QPen(QColor("#ffffff"), 2))
    painter.drawEllipse(QPointF(px, py), 6, 6)

  def _mouse_wheel(self, event):
    if not (event.buttons() & Qt.MouseButton.LeftButton):
      return
    size = self.wheel_area.width()
    cx = size / 2.0
    cy = size / 2.0
    radius = (size / 2.0) - 4.0
    dx = event.position().x() - cx
    dy = event.position().y() - cy
    dist = math.hypot(dx, dy)

    self._hue = ((math.degrees(math.atan2(-dy, dx)) + 360.0) % 360.0) / 360.0
    self._sat = min(1.0, dist / radius)
    self._sync_ui(emit=True)

  def _on_val_changed(self, val):
    self._val = val / 100.0
    self._sync_ui(emit=True)

  def _on_hex_edited(self, text):
    if len(text) == 7 and QColor.isValidColorName(text):
      self.set_color(text, emit=True)

  def _open_system_dialog(self):
    chosen = QColorDialog.getColor(
        QColor(self.current_hex()), self, "Pick Color"
    )
    if chosen.isValid():
      self.set_color(chosen.name(), emit=True)

  def current_hex(self):
    return QColor.fromHsvF(self._hue, self._sat, self._val).name()

  def set_color(self, hex_color, emit=True):
    c = QColor(hex_color)
    if not c.isValid():
      return
    h, s, v, _ = c.getHsvF()
    self._hue = max(0.0, h)
    self._sat = max(0.0, s)
    self._val = max(0.0, v)
    self.val_slider.blockSignals(True)
    self.val_slider.setValue(int(round(self._val * 100)))
    self.val_slider.blockSignals(False)
    self._sync_ui(emit=emit)

  def _sync_ui(self, emit=True):
    hex_str = self.current_hex()
    self.hex_input.blockSignals(True)
    self.hex_input.setText(hex_str.upper())
    self.hex_input.blockSignals(False)
    self.preview_box.setStyleSheet(
        f"background-color: {hex_str}; border: 1px solid #52525b; border-radius: 4px;"
    )
    self.wheel_area.update()
    if emit:
      self.colorChanged.emit(hex_str)
class PreferencesDialog(QDialog):

  def __init__(self, parent=None):
    super().__init__(parent)
    self.setWindowTitle("Preferences")
    self.resize(500, 380)

    layout = QVBoxLayout(self)
    tabs = QTabWidget()

    general_tab = QWidget()
    general_form = QFormLayout(general_tab)

    self.bpm_input = QSpinBox()
    self.bpm_input.setRange(40, 300)
    self.bpm_input.setValue(app_config["default_bpm"])

    self.word_input = QLineEdit(app_config["default_word"])

    self.auto_extend_chk = QCheckBox("Automatically extend timeline on scroll")
    self.auto_extend_chk.setChecked(app_config["auto_extend_timeline"])

    general_form.addRow("Default BPM:", self.bpm_input)
    general_form.addRow("Default Note Lyric:", self.word_input)
    general_form.addRow("", self.auto_extend_chk)

    colors_tab = QWidget()
    colors_main = QHBoxLayout(colors_tab)

    left_col = QVBoxLayout()
    self.preset_box = QComboBox()
    self.preset_box.addItem("Custom")
    self.preset_box.addItems(list(THEME_PRESETS.keys()))
    self.preset_box.currentTextChanged.connect(self.apply_preset)
    left_col.addWidget(self.preset_box)

    self.color_roles = [
        ("accent_color", "Accent Color"),
        ("bg_color", "Window Background"),
        ("surface_color", "Controls / Inputs"),
        ("border_color", "Borders / Handles"),
        ("text_color", "Text Color"),
        ("note_color", "Piano Roll Notes"),
        ("playhead_color", "Playhead Line"),
    ]
    self.pending_colors = {
        key: app_config[key] for key, _ in self.color_roles
    }

    self.role_list = QListWidget()
    self.role_list.setIconSize(QSize(16, 16))
    for key, label in self.color_roles:
      item = QListWidgetItem(label)
      item.setData(Qt.ItemDataRole.UserRole, key)
      self.role_list.addItem(item)
    self.refresh_role_swatches()

    self.wheel_picker = ColorWheelPicker(self.pending_colors["accent_color"])
    self.wheel_picker.colorChanged.connect(self.on_wheel_color_changed)
    self.role_list.currentRowChanged.connect(self.on_role_selected)
    self.role_list.setCurrentRow(0)

    left_col.addWidget(self.role_list)
    colors_main.addLayout(left_col, 1)
    colors_main.addWidget(self.wheel_picker, 1)

    paths_tab = QWidget()
    paths_form = QFormLayout(paths_tab)

    self.vol_slider = QSlider(Qt.Orientation.Horizontal)
    self.vol_slider.setRange(0, 100)
    self.vol_slider.setValue(app_config["master_volume"])

    dir_row = QHBoxLayout()
    self.singers_dir_input = QLineEdit(app_config["singers_dir"])
    browse_btn = QPushButton("Browse...")
    browse_btn.clicked.connect(self.browse_singers_dir)
    dir_row.addWidget(self.singers_dir_input)
    dir_row.addWidget(browse_btn)

    paths_form.addRow("Master Output Volume:", self.vol_slider)
    paths_form.addRow("Voicebanks Folder:", dir_row)

    tabs.addTab(general_tab, "General")
    tabs.addTab(colors_tab, "Colors")
    tabs.addTab(paths_tab, "Audio && Paths")
    layout.addWidget(tabs)

    btn_row = QHBoxLayout()
    reset_btn = QPushButton("Reset Defaults")
    save_btn = QPushButton("Save")
    cancel_btn = QPushButton("Cancel")

    reset_btn.clicked.connect(self.reset_defaults)
    save_btn.clicked.connect(self.apply_and_accept)
    cancel_btn.clicked.connect(self.reject)

    btn_row.addWidget(reset_btn)
    btn_row.addStretch()
    btn_row.addWidget(save_btn)
    btn_row.addWidget(cancel_btn)
    layout.addLayout(btn_row)

  def refresh_role_swatches(self):
    for i, (key, _) in enumerate(self.color_roles):
      pix = QPixmap(16, 16)
      pix.fill(QColor(self.pending_colors[key]))
      self.role_list.item(i).setIcon(QIcon(pix))

  def on_role_selected(self, row):
    if 0 <= row < len(self.color_roles):
      key = self.color_roles[row][0]
      self.wheel_picker.set_color(self.pending_colors[key], emit=False)

  def on_wheel_color_changed(self, hex_str):
    row = self.role_list.currentRow()
    if 0 <= row < len(self.color_roles):
      key = self.color_roles[row][0]
      self.pending_colors[key] = hex_str
      self.refresh_role_swatches()

  def apply_preset(self, preset_name):
    if preset_name in THEME_PRESETS:
      self.pending_colors.update(THEME_PRESETS[preset_name])
      self.refresh_role_swatches()
      self.on_role_selected(self.role_list.currentRow())

  def browse_singers_dir(self):
    folder = QFileDialog.getExistingDirectory(
        self, "Select Voicebanks Folder", self.singers_dir_input.text()
    )
    if folder:
      self.singers_dir_input.setText(folder)

  def reset_defaults(self):
    self.bpm_input.setValue(DEFAULT_CONFIG["default_bpm"])
    self.word_input.setText(DEFAULT_CONFIG["default_word"])
    self.auto_extend_chk.setChecked(DEFAULT_CONFIG["auto_extend_timeline"])
    self.vol_slider.setValue(DEFAULT_CONFIG["master_volume"])
    self.singers_dir_input.setText(DEFAULT_CONFIG["singers_dir"])
    for key, _ in self.color_roles:
      self.pending_colors[key] = DEFAULT_CONFIG[key]
    self.refresh_role_swatches()
    self.on_role_selected(self.role_list.currentRow())

  def apply_and_accept(self):
    global SINGERS_ROOT
    app_config["default_bpm"] = self.bpm_input.value()
    app_config["default_word"] = self.word_input.text().strip() or "a"
    app_config["auto_extend_timeline"] = self.auto_extend_chk.isChecked()
    app_config["master_volume"] = self.vol_slider.value()
    app_config["singers_dir"] = self.singers_dir_input.text().strip()
    app_config.update(self.pending_colors)

    SINGERS_ROOT = app_config["singers_dir"]
    os.makedirs(SINGERS_ROOT, exist_ok=True)
    audio_output.setVolume(app_config["master_volume"] / 100.0)

    apply_theme(app_config)
    refresh_canvas_colors()
    save_config(app_config)
    self.accept()

class HelpDialog(QDialog):

  def __init__(self, parent=None):
    super().__init__(parent)
    self.setWindowTitle("Help")
    self.resize(500, 380)

    helpwindow = QVBoxLayout(self)
    tabs = QTabWidget()

    # --- Tab 1: Tools (Scrollable) ---
    tab1_scroll = QScrollArea()
    tab1_scroll.setWidgetResizable(True)
    tab1_scroll.setFrameShape(QScrollArea.Shape.NoFrame)

    tab1_content = QWidget()
    tab1_layout = QVBoxLayout(tab1_content)

    helptext = QLabel()
    helptext.setAlignment(Qt.AlignmentFlag.AlignTop)
    helptext.setWordWrap(True)
    helptext.setText("""
            There are 5 essential tools in RealSynth that you need to know about: Select, Pencil, Eraser, Pan, and Link tools. This page goes over the uses of each of them.

            Select: This tool lets you select, move, and edit one or more notes. You can't bulk edit notes, so you'll have to edit them individually.

            Pencil: This tool lets you create notes wherever you click.

            Eraser: This tool erases the topmost note in the clicked spot.

            Pan: This tool lets you drag on the board to shift your view. It's incredibly essential.

            Link: This is not a separate tool, but pressing this button will link two selected notes together. Pressing the newly made link will change it from a linear link to a curve link and vice versa.
        """)

    tab1_layout.addWidget(helptext)
    tab1_scroll.setWidget(tab1_content)

    tab2 = QWidget()
    tab2_layout = QVBoxLayout(tab2)

    tabs.addTab(tab1_scroll, "Tools")
    tabs.addTab(tab2, "Other")
    helpwindow.addWidget(tabs)

    

maindaw = QMainWindow()
maindaw.setWindowTitle("RealSynth v0.0.1 Beta")
maindaw.resize(1000, 500)

pickmegirl = QWidget(maindaw)
maindaw.setCentralWidget(pickmegirl)
mainlayout = QHBoxLayout(pickmegirl)
vbarea = QWidget()

menubar = maindaw.menuBar()

filemenu = menubar.addMenu("File")
openproject = QAction("Open Project", maindaw)
filemenu.addAction(openproject)
saveproject = QAction("Save Project", maindaw)
filemenu.addAction(saveproject)
loadvoicebank = QAction("Load Voicebank", maindaw)
filemenu.addAction(loadvoicebank)
export_action = filemenu.addAction("Export as WAV")
export_action.setShortcut("Ctrl+E")
quitapp = QAction("Quit App", maindaw)
filemenu.addAction(quitapp)

editmenu = menubar.addMenu("Edit")
preferences = QAction("Preferences", maindaw)
editmenu.addAction(preferences)

helpmenu = menubar.addMenu("Help")
openhelp = QAction("Open Help", maindaw)
helpmenu.addAction(openhelp)

moremenu = menubar.addMenu("More")
viewgithub = QAction("View GitHub Repository", maindaw)
moremenu.addAction(viewgithub)

mainlayout.setContentsMargins(0, 0, 0, 0)
mainlayout.setSpacing(0)
mainlayout.addWidget(vbarea)
vbarea.setFixedWidth(250)

vblayout = QVBoxLayout(vbarea)
singerlabel = QLabel("No Singer")
singerlabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
singerlabel.setStyleSheet("font-size:20px")
singerportrait = QPixmap(current_singer_dir)
singerportraitframe = ClickablePortrait()
singerportraitframe.setScaledContents(True)
singerportraitframe.setFixedSize(150, 150)
singerportraitframe.setPixmap(singerportrait)
singerportraitframe.setStyleSheet("border: 2px solid #55555a;")
singerlang = QComboBox()
singerlang.addItems(["English", "Japanese"])
singermethod = QComboBox()
singermethod.addItems(["VSim"])
singeroptions = QFormLayout()
singervol = QSlider(Qt.Orientation.Horizontal)
singervol.setRange(0, 100)
singervol.setValue(70)
singerclar = QSlider(Qt.Orientation.Horizontal)
singerclar.setRange(0, 100)
singerclar.setValue(70)
singeroptions.addRow("Language:", singerlang)
singeroptions.addRow("Method:", singermethod)
singeroptions.addRow("Volume", singervol)
singeroptions.addRow("Clarity", singerclar)

note_box = QGroupBox("Selected Note")
note_form = QFormLayout(note_box)
note_word_input = QLineEdit()
note_word_input.setPlaceholderText("Type word/phoneme...")
note_pitch_label = QLabel("--")
note_pitch_label.setStyleSheet("color: #00e08f; font-weight: bold;")
note_tone_box = QComboBox()
note_tone_box.addItems(["Normal", "Yell", "Soft", "Whisper"])

note_form.addRow("Word / Phoneme:", note_word_input)
note_form.addRow("Pitch:", note_pitch_label)
note_form.addRow("Tone:", note_tone_box)
vblayout.addWidget(singerlabel)
vblayout.addWidget(singerportraitframe, alignment=Qt.AlignmentFlag.AlignCenter)
vblayout.addLayout(singeroptions)
vblayout.addWidget(note_box)
vblayout.addStretch()

tool_group = QButtonGroup(maindaw)
tool_group.setExclusive(True)
select_btn = QPushButton("")
select_btn.setIcon(QIcon(select_path))
pencil_btn = QPushButton("")
pencil_btn.setIcon(QIcon(pencil_path))
eraser_btn = QPushButton("")
eraser_btn.setIcon(QIcon(eraser_path))
pan_btn = QPushButton("")
pan_btn.setIcon(QIcon(pan_path))
link_btn = QPushButton("")
link_btn.setIcon(QIcon(link_path))

toolbar_box = QWidget()
toolbar_box.setObjectName("toolbar")
toolbar_box.setFixedHeight(38)
toolbar_row = QHBoxLayout(toolbar_box)
toolbar_row.setContentsMargins(8, 4, 8, 4)
toolbar_row.setSpacing(6)

play_btn = QPushButton(
    maindaw.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay), ""
)
pause_btn = QPushButton(
    maindaw.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause), ""
)
stop_btn = QPushButton(
    maindaw.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop), ""
)
toolbar_row.addWidget(play_btn)
toolbar_row.addWidget(pause_btn)
toolbar_row.addWidget(stop_btn)
toolbar_row.addSpacing(20)

bpm_label = QLabel("BPM:")
bpm_spin = QSpinBox()
bpm_spin.setRange(40, 300)
bpm_spin.setValue(app_config["default_bpm"])

toolbar_row.addWidget(bpm_label)
toolbar_row.addWidget(bpm_spin)

for btn in (select_btn, pencil_btn, eraser_btn, pan_btn):
  btn.setCheckable(True)
  tool_group.addButton(btn)
  toolbar_row.addWidget(btn)

toolbar_row.addWidget(link_btn)

select_btn.setChecked(True)
toolbar_row.addStretch()

keys_scene = QGraphicsScene()
keys_scene.setSceneRect(0, 0, 60, ROW_HEIGHT * TOTAL_ROWS)
for row in range(TOTAL_ROWS):
  y = row * ROW_HEIGHT
  color = (
      QBrush(QColor("#3a3a42")) if row % 2 == 0 else QBrush(QColor("#484852"))
  )
  keys_scene.addRect(0, y, 60, ROW_HEIGHT, QPen(Qt.PenStyle.NoPen), color)
  note_name = NOTES[row % 12]
  octave = 7 - (row // 12)
  label = keys_scene.addText(f"{note_name}{octave}")
  label.setDefaultTextColor(QColor("#e0e0e0"))
  label.setPos(8, y)

keys_view = QGraphicsView(keys_scene)
keys_view.setFixedWidth(60)
keys_view.setStyleSheet("background-color: #2f2f35; border: none;")
keys_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
keys_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

roll_scene = PianoRollScene()
roll_scene.setSceneRect(0, 0, ROLL_WIDTH, ROW_HEIGHT * TOTAL_ROWS)

ruler_scene = QGraphicsScene()
ruler_scene.setSceneRect(0, 0, ROLL_WIDTH, 24)
ruler_view = QGraphicsView(ruler_scene)
ruler_view.setFixedHeight(24)
ruler_view.setStyleSheet("background-color: #222227; border: none;")
ruler_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
ruler_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

roll_view = QGraphicsView(roll_scene)
roll_view.setStyleSheet("border: none;")
roll_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
roll_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
roll_view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
def set_tool(tool_name):
  roll_scene.active_tool = tool_name
  if tool_name == "Pan":
    roll_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
  elif tool_name == "Select":
    roll_view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
  else:
    roll_view.setDragMode(QGraphicsView.DragMode.NoDrag)


select_btn.clicked.connect(lambda: set_tool("Select"))
pencil_btn.clicked.connect(lambda: set_tool("Pencil"))
eraser_btn.clicked.connect(lambda: set_tool("Eraser"))
pan_btn.clicked.connect(lambda: set_tool("Pan"))
link_btn.clicked.connect(lambda: roll_scene.connect_selected_notes())

link_shortcut = QShortcut(QKeySequence("L"), maindaw)
link_shortcut.activated.connect(roll_scene.connect_selected_notes)

roll_view.verticalScrollBar().valueChanged.connect(
    keys_view.verticalScrollBar().setValue
)
keys_view.verticalScrollBar().valueChanged.connect(
    roll_view.verticalScrollBar().setValue
)


def open_voicebank_selector():
  dlg = VoicebankSelectorDialog(maindaw)
  if dlg.exec() == QDialog.DialogCode.Accepted and dlg.selected_singer_dir:
    apply_voicebank(dlg.selected_singer_dir)


singerportraitframe.clicked.connect(open_voicebank_selector)


def refresh_note_inspector(note=None):
  if note is None:
    selected = roll_scene.selectedItems()
    note = selected[0] if selected else None

  if isinstance(note, NoteItem):
    note_word_input.blockSignals(True)
    note_tone_box.blockSignals(True)
    note_word_input.setText(note.word)
    note_pitch_label.setText(note.get_pitch_name())
    note_tone_box.setCurrentText(note.tone)
    note_word_input.blockSignals(False)
    note_tone_box.blockSignals(False)
  else:
    note_word_input.clear()
    note_pitch_label.setText("--")
    note_tone_box.setCurrentIndex(0)


roll_scene.selectionChanged.connect(refresh_note_inspector)
roll_scene.on_note_updated = refresh_note_inspector


def apply_word_edit(text):
  selected = roll_scene.selectedItems()
  if selected and isinstance(selected[0], NoteItem):
    selected[0].set_word(text)


def apply_tone_edit(text):
  selected = roll_scene.selectedItems()
  if selected and isinstance(selected[0], NoteItem):
    selected[0].tone = text


note_word_input.textChanged.connect(apply_word_edit)
note_tone_box.currentTextChanged.connect(apply_tone_edit)

dawcontainer = QWidget()
dawlayout = QVBoxLayout(dawcontainer)
dawlayout.setContentsMargins(0, 0, 0, 0)
dawlayout.setSpacing(0)

views_row = QHBoxLayout()
views_row.setContentsMargins(0, 0, 0, 0)
views_row.setSpacing(0)
views_row.addWidget(roll_view)
views_row.addWidget(keys_view)

shared_hbar = QScrollBar(Qt.Orientation.Horizontal)
roll_view.horizontalScrollBar().rangeChanged.connect(shared_hbar.setRange)
shared_hbar.valueChanged.connect(roll_view.horizontalScrollBar().setValue)
roll_view.horizontalScrollBar().valueChanged.connect(shared_hbar.setValue)
roll_view.horizontalScrollBar().valueChanged.connect(
    ruler_view.horizontalScrollBar().setValue
)


def extend_timeline(new_total_steps):
  global drawn_steps
  if new_total_steps <= drawn_steps:
    return

  new_width = new_total_steps * STEP_WIDTH
  roll_scene.setSceneRect(0, 0, new_width, ROW_HEIGHT * TOTAL_ROWS)
  ruler_scene.setSceneRect(0, 0, new_width, 24)

  start_x = drawn_steps * STEP_WIDTH
  chunk_width = (new_total_steps - drawn_steps) * STEP_WIDTH
  for row in range(TOTAL_ROWS):
    y = row * ROW_HEIGHT
    color = (
        QBrush(QColor("#28282e")) if row % 2 == 0 else QBrush(QColor("#303036"))
    )
    bg = roll_scene.addRect(
        start_x, y, chunk_width, ROW_HEIGHT, QPen(Qt.PenStyle.NoPen), color
    )
    bg.setZValue(-2)
    bg.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

  for step in range(drawn_steps, new_total_steps):
    x = step * STEP_WIDTH
    if step % STEPS_PER_BAR == 0:
      pen = QPen(QColor("#555564"))
    elif step % STEPS_PER_BEAT == 0:
      pen = QPen(QColor("#3e3e48"))
    else:
      pen = QPen(QColor("#2f2f37"))
    line = roll_scene.addLine(x, 0, x, ROW_HEIGHT * TOTAL_ROWS, pen)
    line.setZValue(-1)
    line.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

    if step % STEPS_PER_BAR == 0:
      bar_num = (step // STEPS_PER_BAR) + 1
      ruler_scene.addLine(x, 0, x, 24, QPen(QColor("#888899")))
      txt = ruler_scene.addText(str(bar_num))
      txt.setDefaultTextColor(QColor("#e0e0e0"))
      txt.setPos(x + 3, 0)
    elif step % STEPS_PER_BEAT == 0:
      bar_num = (step // STEPS_PER_BAR) + 1
      beat_num = ((step % STEPS_PER_BAR) // STEPS_PER_BEAT) + 1
      ruler_scene.addLine(x, 10, x, 24, QPen(QColor("#666677")))
      txt = ruler_scene.addText(f"{bar_num}.{beat_num}")
      txt.setDefaultTextColor(QColor("#9999aa"))
      txt.setPos(x + 2, 2)
    else:
      ruler_scene.addLine(x, 17, x, 24, QPen(QColor("#484854")))

  drawn_steps = new_total_steps


extend_timeline(128)


def check_infinite_scroll(val):
  if not app_config["auto_extend_timeline"]:
    return
  if shared_hbar.maximum() > 0 and val >= shared_hbar.maximum() - 300:
    extend_timeline(drawn_steps + 64)


shared_hbar.valueChanged.connect(check_infinite_scroll)

roll_view.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
ruler_view.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
keys_view.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

dawlayout.addWidget(toolbar_box)
dawlayout.addWidget(ruler_view)
dawlayout.addLayout(views_row)
dawlayout.addWidget(shared_hbar)
mainlayout.addWidget(dawcontainer)

playhead_roll = roll_scene.addLine(
    0,
    0,
    0,
    ROW_HEIGHT * TOTAL_ROWS,
    QPen(QColor(app_config["playhead_color"]), 2),
)
playhead_roll.setZValue(10)

playhead_ruler = ruler_scene.addLine(
    0, 0, 0, 24, QPen(QColor(app_config["playhead_color"]), 2)
)
playhead_ruler.setZValue(10)


def refresh_canvas_colors():
  note_brush = QBrush(QColor(app_config["note_color"]))
  for item in roll_scene.items():
    if isinstance(item, NoteItem):
      item.setBrush(note_brush)
  playhead_pen = QPen(QColor(app_config["playhead_color"]), 2)
  playhead_roll.setPen(playhead_pen)
  playhead_ruler.setPen(playhead_pen)
audio_output = QAudioOutput()
audio_output.setVolume(app_config["master_volume"] / 100.0)
media_player = QMediaPlayer()
media_player.setAudioOutput(audio_output)

is_paused = False
temp_wav_path = os.path.join(
    os.path.expanduser("~"), "RealSynth", "preview.wav"
)


def get_current_project_dict():
  notes = [item for item in roll_scene.items() if isinstance(item, NoteItem)]
  notes.sort(key=lambda n: (n.x(), n.y()))
  note_to_idx = {note: i for i, note in enumerate(notes)}

  notes_data = [
      {
          "x": n.x(),
          "y": n.y(),
          "width": n.rect().width(),
          "word": n.word,
          "tone": n.tone,
      }
      for n in notes
  ]

  transitions = [
      item for item in roll_scene.items() if isinstance(item, TransitionLine)
  ]
  transitions_data = [
      {
          "from_note": note_to_idx[t.note_a],
          "to_note": note_to_idx[t.note_b],
          "mode": t.mode,
      }
      for t in transitions
      if t.note_a in note_to_idx and t.note_b in note_to_idx
  ]

  return {
      "singer": {
          "singerdir": current_singer_dir,
          "language": singerlang.currentText(),
          "method": singermethod.currentText(),
          "volume": singervol.value(),
          "clarity": singerclar.value(),
      },
      "notes": notes_data,
      "transitions": transitions_data,
  }


playhead_timer = QTimer()
playhead_timer.setInterval(16)


def update_playhead():
  if media_player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
    return
  pos_ms = media_player.position()
  bpm = bpm_spin.value()
  px_per_sec = (bpm / 60.0) * STEPS_PER_BEAT * STEP_WIDTH
  x_pos = (pos_ms / 1000.0) * px_per_sec

  playhead_roll.setLine(x_pos, 0, x_pos, ROW_HEIGHT * TOTAL_ROWS)
  playhead_ruler.setLine(x_pos, 0, x_pos, 24)


playhead_timer.timeout.connect(update_playhead)


def on_media_status_changed(status):
  if status == QMediaPlayer.MediaStatus.EndOfMedia:
    stop_playback()


media_player.mediaStatusChanged.connect(on_media_status_changed)


def start_playback():
  global is_paused
  if is_paused:
    is_paused = False
    media_player.play()
    playhead_timer.start()
    return

  media_player.stop()
  media_player.setSource(QUrl())

  project_data = get_current_project_dict()
  if not project_data["notes"]:
    return

  rendered = VSim.render_project(
      project_data, output_wav=temp_wav_path, bpm=bpm_spin.value()
  )
  if rendered and os.path.isfile(rendered):
    media_player.setSource(QUrl.fromLocalFile(rendered))
    media_player.play()
    playhead_timer.start()


def export_audio():
  current_project = get_current_project_dict()
  if not current_project.get("notes"):
    QMessageBox.warning(
        maindaw, "Empty Project", "Add some notes before exporting."
    )
    return

  save_path, _ = QFileDialog.getSaveFileName(
      maindaw,
      "Export Rendered Audio",
      "output.wav",
      "WAV Audio (*.wav);;All Files (*)",
  )
  if not save_path:
    return

  if not save_path.lower().endswith(".wav"):
    save_path += ".wav"

  rendered = VSim.render_project(
      current_project,
      output_wav=save_path,
      bpm=bpm_spin.value(),
  )

  if rendered:
    QMessageBox.information(
        maindaw,
        "Export Complete",
        f"Successfully exported wav to:\n{rendered}",
    )

def pause_playback():
  global is_paused
  if media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
    media_player.pause()
    playhead_timer.stop()
    is_paused = True


def stop_playback():
  global is_paused
  is_paused = False
  media_player.stop()
  playhead_timer.stop()
  playhead_roll.setLine(0, 0, 0, ROW_HEIGHT * TOTAL_ROWS)
  playhead_ruler.setLine(0, 0, 0, 24)


def open_preferences():
  dlg = PreferencesDialog(maindaw)
  dlg.exec()

def open_help():
  dlg = HelpDialog(maindaw)
  dlg.exec()

def open_github():
  webbrowser.open("https://github.com/EAQ150/realsynth")

def quit_app():
  sys.exit()

play_btn.clicked.connect(start_playback)
pause_btn.clicked.connect(pause_playback)
stop_btn.clicked.connect(stop_playback)

saveproject.setShortcut(QKeySequence("Ctrl+S"))
openproject.setShortcut(QKeySequence("Ctrl+O"))
loadvoicebank.setShortcut(QKeySequence("Ctrl+L"))
preferences.setShortcut(QKeySequence("Ctrl+,"))
openhelp.setShortcut(QKeySequence("Ctrl+H"))
saveproject.triggered.connect(save_project)
openproject.triggered.connect(open_project)
loadvoicebank.triggered.connect(load_voicebank)
export_action.triggered.connect(export_audio)
quitapp.triggered.connect(quit_app)
preferences.triggered.connect(open_preferences)
openhelp.triggered.connect(open_help)
viewgithub.triggered.connect(open_github)

maindaw.show()
sys.exit(app.exec())
