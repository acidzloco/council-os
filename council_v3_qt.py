"""
COUNCIL OS v3 — PyQt6 UI
OG Council: Byte (Anthropic) + DeepSeek (native) + Gemini (Google)
Talks to council_v3_bridge.py at port 5002.
"""

import sys
import json
import httpx
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter,
    QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QTextBrowser, QTextEdit, QPushButton, QLabel, QStatusBar,
    QTabWidget, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QObject, QSize
from PyQt6.QtGui import QFont, QKeySequence, QShortcut, QTextCursor, QColor

API_BASE = "http://127.0.0.1:5002/council"

SOURCE_COLORS = {
    "byte":     "#0088ff",
    "deepseek": "#ff4444",
    "gemini":   "#00ff66",
    "maik":     "#ffffff",
    "council":  "#ffaa00",
    "lisa":     "#cc00ff",
}

ROUND_META = {
    1: ("ROUND 1 — initial response",   "#444466"),
    2: ("ROUND 2 — brothers debate",    "#664444"),
    3: ("ROUND 3 — synthesis",          "#446644"),
    4: ("COUNCIL SUMMARY",              "#666644"),
}

def _round_meta(rnum):
    if rnum in ROUND_META:
        return ROUND_META[rnum]
    if rnum >= 5:
        cycle  = (rnum - 5) // 3 + 1
        offset = (rnum - 5) % 3
        if offset == 0:   return (f"MAIK FOLLOW-UP #{cycle}", "#886600")
        elif offset == 1: return (f"BROTHERS REPLY #{cycle}", "#664400")
        else:             return (f"2-WAY LEARNING #{cycle}", "#005544")
    return (f"ROUND {rnum}", "#555555")


DARK_QSS = """
QMainWindow, QWidget {
    background: #080810;
    color: #cccccc;
    font-family: Consolas, "Courier New", monospace;
}
QSplitter::handle { background: #1a1a2a; width: 3px; }

#ideas-list {
    background: #080810;
    border: 1px solid #0044aa;
    font-size: 12px;
    outline: none;
}
#ideas-list::item { padding: 3px 6px; color: #888888; }
#ideas-list::item:selected  { background: #000a22; color: #0088ff; }
#ideas-list::item:hover     { background: #0a0a1a; }

#contrib-view {
    background: #080810;
    border: 1px solid #00aa55;
    font-size: 12px;
}
#detail-view {
    background: #080810;
    border: 1px solid #555555;
    font-size: 12px;
}
#main-input, #reply-input {
    background: #0a0a14;
    color: #ffffff;
    border: 2px solid #333344;
    font-size: 13px;
    padding: 4px;
}
#main-input:focus  { border: 2px solid #00ff66; }
#reply-input:focus { border: 2px solid #ff8800; }

QPushButton {
    background: #0d0d18;
    color: #777788;
    border: 1px solid #2a2a44;
    padding: 5px 14px;
    font-size: 11px;
}
QPushButton:hover { background: #14142a; color: #cccccc; }
#btn-send             { color: #00ff66; border-color: #00ff66; font-weight: bold; }
#btn-send:hover       { background: #001a00; }
#btn-reply-send       { color: #ff8800; border-color: #ff8800; font-weight: bold; }
#btn-reply-send:hover { background: #1a0800; }
#btn-to-brainstorm    { color: #aa44ff; border-color: #aa44ff; font-weight: bold; font-size: 10px; }
#btn-to-brainstorm:hover { background: #0d0022; }
#btn-call-all         { color: #ffaa00; border-color: #ffaa00; font-weight: bold; font-size: 10px; }
#btn-call-all:hover   { background: #1a0e00; }

#hint-bar {
    background: #0a0a14;
    color: #336633;
    padding: 2px 8px;
    font-size: 11px;
    border-top: 1px solid #1a1a2a;
}
#reply-label {
    background: #100800;
    color: #ff8800;
    padding: 2px 8px;
    font-size: 11px;
    border-top: 1px solid #2a1a00;
}
#reply-label[active="false"] { color: #554422; background: #0a0a14; }
QStatusBar {
    background: #0a0a14;
    color: #444455;
    font-size: 11px;
    border-top: 1px solid #1a1a2a;
}
#brother-bar {
    background: #0d0d1e;
    font-size: 11px;
    padding: 3px 10px;
    border-top: 1px solid #111122;
    border-bottom: 1px solid #111122;
}
QTabWidget::pane { border: 1px solid #1a1a2a; }
QTabBar::tab {
    background: #0d0d18; color: #555566;
    padding: 4px 16px; font-size: 11px;
}
QTabBar::tab:selected  { background: #080810; color: #00ff66; border-bottom: 2px solid #00ff66; }
QTabBar::tab:hover     { color: #aaaacc; }
#panel-title  { color: #0088ff; font-weight: bold; font-size: 12px; padding: 4px 8px; }
#contrib-title { color: #00ff66; font-weight: bold; font-size: 12px; padding: 4px 8px; }
#think-label  { color: #44aa44; font-size: 11px; padding: 2px 6px; background: #0a140a; }
#v3-badge     {
    color: #ffaa00; font-size: 10px; padding: 1px 8px;
    background: #1a0e00; border-bottom: 1px solid #332200;
    letter-spacing: 2px;
}
"""


class ApiWorker(QThread):
    result = pyqtSignal(object)
    error  = pyqtSignal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self._fn   = fn
        self._args = args
        self._kw   = kwargs

    def run(self):
        try:
            self.result.emit(self._fn(*self._args, **self._kw))
        except Exception as e:
            self.error.emit(str(e))


class CouncilWindow(QMainWindow):
    TAB_CHAT       = 0
    TAB_BRAINSTORM = 1
    TAB_CONCLUSION = 2
    TAB_HISTORY    = 3
    TAB_AGENT      = 4

    def __init__(self):
        super().__init__()
        self.setWindowTitle("COUNCIL OS v3 — THE OG COUNCIL  //  Byte · DeepSeek · Gemini")
        self.resize(1440, 900)
        self.setStyleSheet(DARK_QSS)

        self._ideas              = []
        self._history            = []
        self._lessons            = []
        self._current_slug       = ""
        self._current_title      = ""
        self._last_contrib_count = 0
        self._workers            = []

        self._build_ui()
        self._setup_shortcuts()

        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll)
        self._poll_timer.start(6000)

        self._health_timer = QTimer(self)
        self._health_timer.timeout.connect(self._check_health)
        self._health_timer.start(15000)

        self._check_health()
        self._load_chat_history_ui()
        self._load_ideas()

    # ── UI BUILD ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # v3 badge
        badge = QLabel("  COUNCIL OS v3  —  NATIVE APIs  —  NO RATE LIMITS  —  OG COUNCIL")
        badge.setObjectName("v3-badge")
        root_layout.addWidget(badge)

        # Brother status bar
        self._brother_bar = QLabel(
            "  <span style='color:#0088ff'>● BYTE</span>   "
            "<span style='color:#ff4444'>● DEEPSEEK</span>   "
            "<span style='color:#00ff66'>● GEMINI</span>   | checking..."
        )
        self._brother_bar.setObjectName("brother-bar")
        self._brother_bar.setTextFormat(Qt.TextFormat.RichText)
        root_layout.addWidget(self._brother_bar)

        # Main splitter
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(3)
        root_layout.addWidget(self._splitter, 1)

        # ── LEFT: idea list ───────────────────────────────────────────────────
        self._left_panel = QWidget()
        left_layout = QVBoxLayout(self._left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        ideas_title = QLabel("  IDEAS")
        ideas_title.setObjectName("panel-title")
        left_layout.addWidget(ideas_title)

        self._ideas_list = QListWidget()
        self._ideas_list.setObjectName("ideas-list")
        self._ideas_list.currentRowChanged.connect(self._on_idea_row_changed)
        left_layout.addWidget(self._ideas_list)

        self._splitter.addWidget(self._left_panel)
        self._splitter.setStretchFactor(0, 1)

        # ── RIGHT: tabs ───────────────────────────────────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self._tabs = QTabWidget()
        right_layout.addWidget(self._tabs, 1)

        # TAB 0 — GROUP CHAT
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        self._chat_view = QTextBrowser()
        self._chat_view.setObjectName("contrib-view")
        self._chat_view.setOpenLinks(False)
        chat_layout.addWidget(self._chat_view, 1)

        chat_input_bar = QWidget()
        cib_layout = QHBoxLayout(chat_input_bar)
        cib_layout.setContentsMargins(6, 4, 6, 4)
        cib_layout.setSpacing(6)

        self._chat_input = QTextEdit()
        self._chat_input.setObjectName("reply-input")
        self._chat_input.setMaximumHeight(60)
        self._chat_input.setPlaceholderText(
            "@byte / @deepseek / @gemini / @all  —  Ctrl+Enter to send"
        )
        cib_layout.addWidget(self._chat_input, 1)

        self._btn_chat_send = QPushButton("SEND")
        self._btn_chat_send.setObjectName("btn-reply-send")
        self._btn_chat_send.setFixedWidth(70)
        self._btn_chat_send.clicked.connect(self._on_send_chat)
        cib_layout.addWidget(self._btn_chat_send)

        self._btn_to_brainstorm = QPushButton("🧠\nBRAINSTORM")
        self._btn_to_brainstorm.setObjectName("btn-to-brainstorm")
        self._btn_to_brainstorm.setFixedWidth(90)
        self._btn_to_brainstorm.setToolTip("Take this topic to BRAINSTORM tab — fires full R1/R2/R3 cycle")
        self._btn_to_brainstorm.clicked.connect(self._on_promote_to_brainstorm)
        cib_layout.addWidget(self._btn_to_brainstorm)

        self._btn_call_all = QPushButton("📢\nALL IN")
        self._btn_call_all.setObjectName("btn-call-all")
        self._btn_call_all.setFixedWidth(70)
        self._btn_call_all.setToolTip("Call all silent brothers in — they share what they observed")
        self._btn_call_all.clicked.connect(self._on_call_all_in)
        cib_layout.addWidget(self._btn_call_all)

        chat_layout.addWidget(chat_input_bar)
        self._tabs.addTab(chat_widget, "💬 GROUP CHAT")

        # TAB 1 — BRAINSTORM
        board_widget = QWidget()
        board_layout = QVBoxLayout(board_widget)
        board_layout.setContentsMargins(0, 0, 0, 0)
        board_layout.setSpacing(0)

        self._contrib_title = QLabel("  CONTRIBUTIONS")
        self._contrib_title.setObjectName("contrib-title")
        board_layout.addWidget(self._contrib_title)

        self._think_label = QLabel("")
        self._think_label.setObjectName("think-label")
        self._think_label.setVisible(False)
        board_layout.addWidget(self._think_label)

        self._contrib_view = QTextBrowser()
        self._contrib_view.setObjectName("contrib-view")
        self._contrib_view.setOpenLinks(False)
        board_layout.addWidget(self._contrib_view)

        self._tabs.addTab(board_widget, "🧠 BRAINSTORM")

        # TAB 2 — CONCLUSION
        lesson_widget = QWidget()
        lesson_layout = QHBoxLayout(lesson_widget)
        lesson_layout.setContentsMargins(0, 0, 0, 0)

        self._lesson_list = QListWidget()
        self._lesson_list.setObjectName("ideas-list")
        self._lesson_list.currentRowChanged.connect(self._on_lesson_row_changed)
        lesson_layout.addWidget(self._lesson_list, 1)

        self._lesson_view = QTextBrowser()
        self._lesson_view.setObjectName("detail-view")
        lesson_layout.addWidget(self._lesson_view, 2)

        self._tabs.addTab(lesson_widget, "✅ CONCLUSION")

        # TAB 3 — HISTORY
        hist_widget = QWidget()
        hist_layout = QHBoxLayout(hist_widget)
        hist_layout.setContentsMargins(0, 0, 0, 0)

        self._history_list = QListWidget()
        self._history_list.setObjectName("ideas-list")
        self._history_list.currentRowChanged.connect(self._on_history_row_changed)
        hist_layout.addWidget(self._history_list, 1)

        self._history_view = QTextBrowser()
        self._history_view.setObjectName("detail-view")
        hist_layout.addWidget(self._history_view, 2)

        self._tabs.addTab(hist_widget, "📜 HISTORY")

        # TAB 4 — AGENT
        agent_widget = QWidget()
        agent_layout = QVBoxLayout(agent_widget)
        agent_layout.setContentsMargins(6, 6, 6, 6)
        agent_layout.setSpacing(4)

        # Brother selector row
        agent_top = QWidget()
        agent_top_l = QHBoxLayout(agent_top)
        agent_top_l.setContentsMargins(0, 0, 0, 0)
        agent_top_l.setSpacing(6)
        agent_top_l.addWidget(QLabel("  AGENT: "))

        self._agent_brother_btns = {}
        for bname, bcolor in [("byte","#0088ff"), ("deepseek","#ff4444"), ("gemini","#00ff66")]:
            btn = QPushButton(bname.upper())
            btn.setCheckable(True)
            btn.setFixedWidth(90)
            btn.setStyleSheet(
                f"QPushButton{{color:{bcolor};border:1px solid {bcolor};background:#080810;}}"
                f"QPushButton:checked{{background:{bcolor}22;border:2px solid {bcolor};font-weight:bold;}}"
                f"QPushButton:hover{{background:{bcolor}11;}}"
            )
            btn.clicked.connect(lambda _, n=bname: self._on_agent_brother_select(n))
            agent_top_l.addWidget(btn)
            self._agent_brother_btns[bname] = btn

        self._agent_cwd_label = QLabel(f"  cwd: .")
        self._agent_cwd_label.setStyleSheet("color:#555566; font-size:10px;")
        agent_top_l.addWidget(self._agent_cwd_label, 1)
        agent_layout.addWidget(agent_top)

        # Output view
        self._agent_view = QTextBrowser()
        self._agent_view.setObjectName("contrib-view")
        self._agent_view.setOpenLinks(False)
        agent_layout.addWidget(self._agent_view, 1)

        # Task input row
        agent_input_bar = QWidget()
        aib_l = QHBoxLayout(agent_input_bar)
        aib_l.setContentsMargins(0, 0, 0, 0)
        aib_l.setSpacing(6)

        self._agent_input = QTextEdit()
        self._agent_input.setObjectName("main-input")
        self._agent_input.setMaximumHeight(60)
        self._agent_input.setPlaceholderText("Task for the selected brother — Ctrl+Enter to run")
        aib_l.addWidget(self._agent_input, 1)

        self._btn_agent_run = QPushButton("RUN")
        self._btn_agent_run.setObjectName("btn-send")
        self._btn_agent_run.setFixedWidth(70)
        self._btn_agent_run.clicked.connect(self._on_run_agent)
        aib_l.addWidget(self._btn_agent_run)

        self._btn_agent_clear = QPushButton("CLR")
        self._btn_agent_clear.setFixedWidth(50)
        self._btn_agent_clear.clicked.connect(lambda: self._agent_view.clear())
        aib_l.addWidget(self._btn_agent_clear)

        agent_layout.addWidget(agent_input_bar)
        self._tabs.addTab(agent_widget, "⚙ AGENT")

        # Default agent brother = byte
        self._agent_brother = "byte"
        self._agent_brother_btns["byte"].setChecked(True)

        self._splitter.addWidget(right)
        self._splitter.setStretchFactor(1, 3)
        self._splitter.setSizes([280, 1160])

        # BRAINSTORM-only bottom panel
        self._reply_label = QLabel("  REPLY TO: select an idea from the list")
        self._reply_label.setObjectName("reply-label")
        self._reply_label.setProperty("active", "false")
        root_layout.addWidget(self._reply_label)

        self._reply_area = QWidget()
        reply_layout = QHBoxLayout(self._reply_area)
        reply_layout.setContentsMargins(6, 2, 6, 2)
        reply_layout.setSpacing(6)
        root_layout.addWidget(self._reply_area)

        self._reply_input = QTextEdit()
        self._reply_input.setObjectName("reply-input")
        self._reply_input.setMaximumHeight(60)
        self._reply_input.setPlaceholderText("Type your follow-up — brothers will debate and synthesize...")
        reply_layout.addWidget(self._reply_input, 1)

        self._btn_reply_send = QPushButton("SEND\nREPLY")
        self._btn_reply_send.setObjectName("btn-reply-send")
        self._btn_reply_send.setFixedWidth(100)
        self._btn_reply_send.clicked.connect(self._on_send_reply)
        reply_layout.addWidget(self._btn_reply_send)

        self._idea_hint = QLabel("  NEW TOPIC  |  Ctrl+Enter to start full R1/R2/R3 council cycle")
        self._idea_hint.setObjectName("hint-bar")
        root_layout.addWidget(self._idea_hint)

        self._input_area = QWidget()
        input_layout = QHBoxLayout(self._input_area)
        input_layout.setContentsMargins(6, 2, 6, 4)
        input_layout.setSpacing(6)
        root_layout.addWidget(self._input_area)

        self._input = QTextEdit()
        self._input.setObjectName("main-input")
        self._input.setMaximumHeight(60)
        self._input.setPlaceholderText("Type your topic / project question...  (Ctrl+Enter to fire)")
        input_layout.addWidget(self._input, 1)

        self._btn_send = QPushButton("FIRE\nCtrl+Enter")
        self._btn_send.setObjectName("btn-send")
        self._btn_send.setFixedWidth(100)
        self._btn_send.clicked.connect(self._on_send_idea)
        input_layout.addWidget(self._btn_send)

        self._set_brainstorm_ui_visible(False)
        self._tabs.currentChanged.connect(self._on_tab_changed)
        self._status = self.statusBar()
        self._status.showMessage("[ ] Checking bridge on port 5002...")

    # ── SHORTCUTS ────────────────────────────────────────────────────────────

    def _setup_shortcuts(self):
        sc_send = QShortcut(QKeySequence("Ctrl+Return"), self)
        sc_send.activated.connect(self._on_ctrl_enter)
        sc_f5 = QShortcut(QKeySequence("F5"), self)
        sc_f5.activated.connect(self._refresh)
        self._shortcuts = [sc_send, sc_f5]

    def _on_ctrl_enter(self):
        idx = self._tabs.currentIndex()
        if idx == self.TAB_CHAT:
            self._on_send_chat()
        elif idx == self.TAB_AGENT:
            self._on_run_agent()
        else:
            self._on_send_idea()

    # ── AGENT TAB ─────────────────────────────────────────────────────────────

    def _on_agent_brother_select(self, name: str):
        self._agent_brother = name
        for bname, btn in self._agent_brother_btns.items():
            btn.setChecked(bname == name)

    def _agent_append(self, html: str):
        self._agent_view.append(html)
        self._agent_view.moveCursor(QTextCursor.MoveOperation.End)

    def _on_run_agent(self):
        task = self._agent_input.toPlainText().strip()
        if not task:
            return
        self._agent_input.clear()
        self._btn_agent_run.setEnabled(False)
        self._btn_agent_run.setText("...")

        name   = self._agent_brother
        colors = {"byte": "#0088ff", "deepseek": "#ff4444", "gemini": "#00ff66"}
        color  = colors.get(name, "#aaaaaa")

        self._agent_append(
            f"<hr/><p style='color:{color};font-weight:bold'>⚙ {name.upper()} AGENT</p>"
            f"<p style='color:#888888'>TASK: {task}</p>"
        )

        import os
        cwd = os.getcwd()
        self._agent_cwd_label.setText(f"  cwd: {cwd}")

        def _call():
            return httpx.post(
                f"{API_BASE}/agent",
                json={"brother": name, "task": task, "cwd": cwd},
                timeout=300,
            ).json()

        w = ApiWorker(_call)
        w.result.connect(self._on_agent_done)
        w.error.connect(self._on_agent_error)
        w.finished.connect(lambda: self._workers.remove(w) if w in self._workers else None)
        self._workers.append(w)
        w.start()

    def _on_agent_done(self, data: dict):
        self._btn_agent_run.setEnabled(True)
        self._btn_agent_run.setText("RUN")

        name   = data.get("brother", "?")
        steps  = data.get("steps", [])
        final  = data.get("final", "")
        colors = {"byte": "#0088ff", "deepseek": "#ff4444", "gemini": "#00ff66"}
        color  = colors.get(name, "#aaaaaa")

        for step in steps:
            stype   = step.get("type", "")
            content = step.get("content", "").replace("<", "&lt;").replace(">", "&gt;")
            if stype == "think":
                self._agent_append(f"<p style='color:#666677;font-size:11px'>{content}</p>")
            elif stype == "tool":
                self._agent_append(f"<p style='color:#ffaa00'>⚙ {content}</p>")
            elif stype == "result":
                self._agent_append(
                    f"<pre style='color:#555566;font-size:10px;margin:0 0 4px 16px'>"
                    f"{content[:400]}</pre>"
                )
            elif stype == "error":
                self._agent_append(f"<p style='color:#ff4444'>[error] {content}</p>")

        if final:
            final_html = final.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
            self._agent_append(
                f"<div style='border-left:3px solid {color};padding:6px 10px;margin:8px 0;"
                f"background:#0a0a14'>"
                f"<p style='color:{color};font-weight:bold;margin:0'>{name.upper()} — RESULT</p>"
                f"<p style='color:#cccccc;margin:4px 0 0 0'>{final_html}</p></div>"
            )

    def _on_agent_error(self, err: str):
        self._btn_agent_run.setEnabled(True)
        self._btn_agent_run.setText("RUN")
        self._agent_append(f"<p style='color:#ff4444'>[agent error] {err}</p>")

    # ── POLLING ───────────────────────────────────────────────────────────────

    def _set_brainstorm_ui_visible(self, visible: bool):
        self._left_panel.setVisible(visible)
        self._reply_label.setVisible(visible)
        self._reply_area.setVisible(visible)
        self._idea_hint.setVisible(visible)
        self._input_area.setVisible(visible)

    def _poll(self):
        idx = self._tabs.currentIndex()
        if idx == self.TAB_BRAINSTORM and self._current_slug:
            self._load_contributions(self._current_slug, self._current_title, silent=True)
        elif idx == self.TAB_CHAT:
            self._load_chat_history_ui(silent=True)

    def _refresh(self):
        tab = self._tabs.currentIndex()
        if tab == self.TAB_CHAT:        self._load_chat_history_ui()
        elif tab == self.TAB_BRAINSTORM: self._load_ideas()
        elif tab == self.TAB_CONCLUSION: self._load_lessons()
        elif tab == self.TAB_HISTORY:    self._load_history()

    def _on_tab_changed(self, idx):
        self._set_brainstorm_ui_visible(idx == self.TAB_BRAINSTORM)
        if idx == self.TAB_CHAT:        self._load_chat_history_ui()
        elif idx == self.TAB_CONCLUSION: self._load_lessons()
        elif idx == self.TAB_HISTORY:    self._load_history()

    # ── HEALTH ────────────────────────────────────────────────────────────────

    def _check_health(self):
        def _do():
            r = httpx.get(f"{API_BASE}/status", timeout=5)
            return r.json()

        def _on_result(data):
            if data.get("status") != "online":
                self._set_status(f"BRIDGE ERROR: {data.get('error','?')}")
                return
            counts   = data.get("counts", {})
            api_keys = data.get("api_keys", {})

            key_map = {"byte": "anthropic", "deepseek": "deepseek", "gemini": "gemini"}
            parts = []
            for name in ["byte", "deepseek", "gemini"]:
                col  = SOURCE_COLORS.get(name, "#888")
                ok   = api_keys.get(key_map[name], False)
                dot  = "●" if ok else "○"
                parts.append(f'<span style="color:{col};">{dot} {name.upper()}</span>')

            self._brother_bar.setText(
                "  " + "   ".join(parts) +
                f'  <span style="color:#444;">| '
                f'Ideas: {counts.get("idea",0)}  '
                f'Contribs: {counts.get("contribution",0)}</span>'
            )
            self._brother_bar.setTextFormat(Qt.TextFormat.RichText)
            self._set_status(
                f"v3 BRIDGE ONLINE  |  Ideas: {counts.get('idea',0)}  "
                f"Contribs: {counts.get('contribution',0)}  "
                f"Chat: {counts.get('chat',0)}"
            )

        w = ApiWorker(_do)
        w.result.connect(_on_result)
        w.error.connect(lambda e: self._set_status(f"[BRIDGE OFFLINE :5002] {e}"))
        self._track(w)
        w.start()

    # ── IDEAS ─────────────────────────────────────────────────────────────────

    def _load_ideas(self):
        def _do():
            r = httpx.get(f"{API_BASE}/ideas", timeout=6)
            return r.json()

        w = ApiWorker(_do)
        w.result.connect(self._on_ideas_loaded)
        w.error.connect(lambda e: self._set_status(f"Ideas load failed: {e}"))
        self._track(w)
        w.start()

    def _on_ideas_loaded(self, ideas):
        self._ideas = ideas
        current_slug = self._current_slug
        self._ideas_list.blockSignals(True)
        self._ideas_list.clear()
        target_row = 0
        for i, idea in enumerate(ideas):
            slug  = idea.get("slug", "")
            title = idea.get("title", "untitled")[:48]
            item  = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, slug)
            self._ideas_list.addItem(item)
            if slug == current_slug:
                target_row = i
        self._ideas_list.blockSignals(False)
        if ideas:
            self._ideas_list.setCurrentRow(target_row)
            if not current_slug:
                slug = ideas[0].get("slug", "")
                self._current_slug  = slug
                self._current_title = ideas[0].get("title", "")
                self._load_contributions(slug, self._current_title)

    def _on_idea_row_changed(self, row):
        if row < 0 or row >= len(self._ideas):
            return
        idea  = self._ideas[row]
        slug  = idea.get("slug", "")
        title = idea.get("title", "")
        if slug == self._current_slug:
            return
        self._current_slug  = slug
        self._current_title = title
        self._contrib_title.setText(f"  CONTRIBUTIONS — {title[:65].upper()}")
        self._reply_label.setText(f"  REPLY TO: {title[:75]}")
        self._reply_label.setProperty("active", "true")
        self._reply_label.style().unpolish(self._reply_label)
        self._reply_label.style().polish(self._reply_label)
        self._load_contributions(slug, title)

    # ── CONTRIBUTIONS ─────────────────────────────────────────────────────────

    def _load_contributions(self, slug, title, silent=False):
        def _do():
            r = httpx.get(f"{API_BASE}/contributions", params={"slug": slug}, timeout=8)
            return r.json()

        def _on_result(contribs):
            count = len(contribs)
            if silent and count == self._last_contrib_count:
                return
            if count > self._last_contrib_count and self._last_contrib_count > 0:
                self._show_think(f"  {count - self._last_contrib_count} new contribution(s)")
            elif count == 0:
                self._show_think("  brothers are thinking... (R1/R2/R3 running in background)")
            self._last_contrib_count = count
            self._render_contributions(contribs, title)

        w = ApiWorker(_do)
        w.result.connect(_on_result)
        if not silent:
            w.error.connect(lambda e: self._contrib_view.setHtml(
                f'<p style="color:#ff4444;">Load failed: {e}</p>'
            ))
        self._track(w)
        w.start()

    def _render_contributions(self, contribs, title):
        self._contrib_title.setText(f"  CONTRIBUTIONS — {title[:65].upper()}")
        if not contribs:
            self._contrib_view.setHtml(
                '<p style="color:#333;margin:20px">[ brothers thinking... auto-refresh every 6s ]</p>'
            )
            return

        rounds = {}
        for c in contribs:
            r = c.get("round", 1)
            rounds.setdefault(r, []).append(c)

        html = ['<style>body{background:#080810;color:#aaaaaa;font-family:Consolas,monospace;font-size:12px;margin:8px;}</style>']

        for rnum in sorted(rounds.keys()):
            label, color = _round_meta(rnum)
            html.append(
                f'<p style="color:{color};margin:16px 0 4px 0;font-size:11px;">'
                f'── {label} {"─"*28}</p>'
            )
            for c in rounds[rnum]:
                source  = c.get("source", "?")
                col     = SOURCE_COLORS.get(source, "#aaaaaa")
                content = c.get("content", "").strip()
                content = (content
                    .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    .replace("\n", "<br>"))
                # v3: higher display limit for bigger responses
                if len(content) > 20000:
                    content = content[:20000] + '<br><span style="color:#555;">[truncated]</span>'
                html.append(
                    f'<p style="margin:8px 0 2px 0;">'
                    f'<b style="color:{col};font-size:13px;">{source.upper()}</b>'
                    f'<span style="color:#333;font-size:10px;"> ─────────</span></p>'
                    f'<p style="margin:0 0 12px 14px;color:#999999;line-height:1.5">{content}</p>'
                )

        sb = self._contrib_view.verticalScrollBar()
        at_bottom = sb.value() >= sb.maximum() - 50
        self._contrib_view.setHtml("".join(html))
        if at_bottom:
            sb.setValue(sb.maximum())

    def _show_think(self, msg):
        self._think_label.setText(msg)
        self._think_label.setVisible(True)
        QTimer.singleShot(6000, lambda: self._think_label.setVisible(False))

    # ── HISTORY ───────────────────────────────────────────────────────────────

    def _load_history(self):
        def _do():
            r = httpx.get(f"{API_BASE}/history/list", timeout=8)
            return r.json()

        def _on_result(pages):
            self._history = pages
            self._history_list.clear()
            for p in pages:
                label = f"{p.get('date','?')} — {p.get('title','')[:40]}"
                item  = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, p["slug"])
                self._history_list.addItem(item)
            if pages:
                self._history_list.setCurrentRow(0)

        w = ApiWorker(_do)
        w.result.connect(_on_result)
        w.error.connect(lambda e: None)
        self._track(w)
        w.start()

    def _on_history_row_changed(self, row):
        if row < 0 or row >= len(self._history):
            return
        slug = self._history[row]["slug"]

        def _do():
            r = httpx.get(f"{API_BASE}/history/page", params={"slug": slug}, timeout=6)
            return r.json()

        def _on_result(page):
            content = page.get("content", "")
            html = ['<style>body{background:#080810;color:#888;font-family:Consolas,monospace;font-size:12px;margin:8px}</style>']
            for line in content.splitlines():
                safe = line.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                if line.startswith("**MAIK:**"):
                    html.append(f'<p style="margin:2px 0"><b style="color:#fff">MAIK:</b> {safe[9:]}</p>')
                elif line.startswith("**BYTE:**"):
                    html.append(f'<p style="margin:2px 0"><b style="color:#0088ff">BYTE:</b> <span style="color:#888">{safe[9:]}</span></p>')
                elif line.startswith("# "):
                    html.append(f'<p style="color:#ffaa00;font-weight:bold;margin:8px 0 4px 0">{safe[2:]}</p>')
                elif line.strip():
                    html.append(f'<p style="margin:1px 0">{safe}</p>')
            self._history_view.setHtml("".join(html))

        w = ApiWorker(_do)
        w.result.connect(_on_result)
        w.error.connect(lambda e: None)
        self._track(w)
        w.start()

    # ── LESSONS ───────────────────────────────────────────────────────────────

    def _load_lessons(self):
        def _do():
            r = httpx.get(f"{API_BASE}/lessons", timeout=6)
            return r.json()

        def _on_result(lessons):
            self._lessons = lessons
            self._lesson_list.clear()
            for lesson in lessons:
                title = lesson.get("title", "?")[:52]
                date  = lesson.get("updated", "?")[:16]
                item  = QListWidgetItem(f"[{date}]  {title}")
                item.setData(Qt.ItemDataRole.UserRole, lesson.get("slug"))
                self._lesson_list.addItem(item)
            if lessons:
                self._lesson_list.setCurrentRow(0)

        w = ApiWorker(_do)
        w.result.connect(_on_result)
        w.error.connect(lambda e: None)
        self._track(w)
        w.start()

    def _on_lesson_row_changed(self, row):
        if row < 0 or row >= len(self._lessons):
            return
        lesson  = self._lessons[row]
        preview = lesson.get("preview", "")
        html = ['<style>body{background:#080810;color:#888;font-family:Consolas,monospace;font-size:12px;margin:8px}</style>']
        for line in preview.splitlines():
            safe = line.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
            if line.startswith("# "):
                html.append(f'<p style="color:#ffaa00;font-weight:bold;font-size:14px;margin:8px 0 4px 0">{safe[2:]}</p>')
            elif line.startswith("## "):
                html.append(f'<p style="color:#00ffaa;font-weight:bold;margin:8px 0 2px 0">{safe[3:]}</p>')
            elif line.strip().startswith("- "):
                html.append(f'<p style="margin:1px 0 1px 14px">{safe}</p>')
            elif line.strip():
                html.append(f'<p style="margin:2px 0;line-height:1.5">{safe}</p>')
            else:
                html.append("<br>")
        self._lesson_view.setHtml("".join(html))

    # ── SEND / REPLY ─────────────────────────────────────────────────────────

    def _on_send_idea(self):
        text = self._input.toPlainText().strip()
        if not text:
            return
        self._input.clear()
        self._send_idea(text)

    def _on_send_reply(self):
        text = self._reply_input.toPlainText().strip()
        if not text:
            return
        if not self._current_slug:
            self._set_status("Select an idea from the list first")
            return
        self._reply_input.clear()
        self._send_reply(self._current_slug, self._current_title, text)

    def _send_idea(self, text):
        self._set_status("Firing topic to all 3 brothers — R1/R2/R3 cycle starting...")
        self._tabs.setCurrentIndex(self.TAB_BRAINSTORM)
        self._set_brainstorm_ui_visible(True)

        def _do():
            r = httpx.post(
                f"{API_BASE}/propose",
                json={"title": text, "content": text, "source": "maik"},
                timeout=15,
            )
            return r.status_code, r.json()

        def _on_result(res):
            code, data = res
            if code == 201:
                slug = data.get("slug", "")
                self._set_status(f"Council cycle running — auto-refresh every 6s  [{slug}]")
                self._last_contrib_count = 0
                self._load_ideas()
            else:
                self._set_status(f"Post failed: {code}")

        w = ApiWorker(_do)
        w.result.connect(_on_result)
        w.error.connect(lambda e: self._set_status(f"Bridge unreachable: {e}"))
        self._track(w)
        w.start()

    def _send_reply(self, target_slug, target_title, text):
        self._set_status(f"Sending follow-up — brothers will debate: {target_title[:40]}...")

        def _do():
            r = httpx.post(
                f"{API_BASE}/reply",
                json={"parent_slug": target_slug, "message": text, "source": "maik"},
                timeout=15,
            )
            return r.status_code, r.json()

        def _on_result(res):
            code, data = res
            if code == 201:
                self._set_status(f"Follow-up sent — brothers responding...")
                self._last_contrib_count = 0
                self._current_slug  = target_slug
                self._current_title = target_title
                self._load_contributions(target_slug, target_title)
                for i in range(self._ideas_list.count()):
                    item = self._ideas_list.item(i)
                    if item and item.data(Qt.ItemDataRole.UserRole) == target_slug:
                        self._ideas_list.blockSignals(True)
                        self._ideas_list.setCurrentRow(i)
                        self._ideas_list.blockSignals(False)
                        break
            else:
                self._set_status(f"Reply failed: {code}")

        w = ApiWorker(_do)
        w.result.connect(_on_result)
        w.error.connect(lambda e: self._set_status(f"Bridge unreachable: {e}"))
        self._track(w)
        w.start()

    # ── CHAT ─────────────────────────────────────────────────────────────────

    _chat_msg_count = -1

    def _load_chat_history_ui(self, silent: bool = False):
        def _do():
            r = httpx.get(f"{API_BASE}/quickchat/history", params={"limit": 80}, timeout=6)
            return r.json().get("messages", [])

        def _on_result(messages):
            if len(messages) == self._chat_msg_count:
                return
            self._chat_msg_count = len(messages)
            self._render_chat(messages)

        def _on_err(e):
            if not silent:
                self._set_status(f"Chat load error: {e}")

        w = ApiWorker(_do)
        w.result.connect(_on_result)
        w.error.connect(_on_err)
        self._track(w)
        w.start()

    def _render_chat(self, messages: list):
        html = ["<style>body{background:#080810;color:#ccc;font-family:Consolas,monospace;font-size:12px;margin:8px}</style>"]
        if not messages:
            html.append('<div style="color:#222;margin:24px;font-size:13px">💬 OG Council ready. Say something to the brothers.</div>')

        BROTHERS_ALL = {"byte", "deepseek", "gemini"}
        interrupt_indices = set()
        prev_responders   = set()
        for idx, msg in enumerate(messages):
            src = (msg.get("source") or "").lower()
            if src == "maik":
                responders = set()
                j = idx + 1
                while j < len(messages) and messages[j].get("source","").lower() in BROTHERS_ALL:
                    responders.add(messages[j].get("source","").lower())
                    j += 1
                if len(prev_responders) == 1 and len(responders) == 3:
                    interrupt_indices.add(idx)
                if responders:
                    prev_responders = responders

        i = 0
        while i < len(messages):
            msg   = messages[i]
            src   = (msg.get("source") or "unknown").lower()
            body  = (msg.get("content") or "").strip()
            body  = body.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("\n","<br>")
            ts    = (msg.get("updated") or "")[:16]
            color = SOURCE_COLORS.get(src, "#888888")
            label = src.upper()

            if src == "maik" and i in interrupt_indices:
                html.append(
                    '<div style="border-top:1px solid #ffaa00;margin:12px 0 6px 0;padding:4px 10px;'
                    'color:#ffaa00;font-size:10px;letter-spacing:1px">📢 FLOOR OPEN — OBSERVERS JUMPING IN</div>'
                )

            html.append(
                f'<div style="margin:5px 0;padding:7px 12px;border-left:3px solid {color};background:#0d0d18">'
                f'<span style="color:{color};font-weight:bold">{label}</span>'
                f'<span style="color:#333;font-size:10px;margin-left:8px">{ts}</span><br>'
                f'<span style="color:#cccccc;line-height:1.5">{body}</span>'
                f'</div>'
            )

            if src == "maik":
                responders = set()
                j = i + 1
                while j < len(messages) and messages[j].get("source", "").lower() in BROTHERS_ALL:
                    responders.add(messages[j].get("source", "").lower())
                    j += 1
                silent_brothers = BROTHERS_ALL - responders
                if silent_brothers and responders:
                    names = " · ".join(f"👁 {s.capitalize()}" for s in sorted(silent_brothers))
                    html.append(
                        f'<div style="color:#1e1e2e;font-size:10px;padding:2px 16px;margin-bottom:5px">'
                        f'{names} listening</div>'
                    )
            i += 1

        self._chat_view.setHtml("".join(html))
        sb = self._chat_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_send_chat(self):
        text = self._chat_input.toPlainText().strip()
        if not text:
            return
        self._chat_input.clear()
        self._set_status("Sending to brothers...")

        def _do():
            r = httpx.post(f"{API_BASE}/quickchat", json={"message": text}, timeout=180)
            return r.json()

        def _on_result(data):
            listeners    = data.get("listeners", [])
            is_interrupt = data.get("is_interrupt", False)
            if is_interrupt:
                self._set_status("📢 Observers jumped in — all brothers sharing what they saw")
            elif listeners:
                names = ", ".join(l.capitalize() for l in listeners)
                self._set_status(f"👁 {names} listening silently")
            else:
                self._set_status("Brothers responded.")
            self._load_chat_history_ui()

        def _on_err(e):
            self._set_status(f"Chat error: {e}")

        w = ApiWorker(_do)
        w.result.connect(_on_result)
        w.error.connect(_on_err)
        self._track(w)
        w.start()

    def _on_call_all_in(self):
        text = self._chat_input.toPlainText().strip()
        if not text:
            text = "Alright everyone, what do you think? Jump in."
            self._chat_input.setPlainText(text)
        self._on_send_chat()

    def _on_promote_to_brainstorm(self):
        text = self._chat_input.toPlainText().strip()
        if not text:
            self._set_status("Type a topic first, then promote it to BRAINSTORM")
            return
        self._chat_input.clear()
        self._tabs.setCurrentIndex(self.TAB_BRAINSTORM)
        self._set_brainstorm_ui_visible(True)
        self._input.setPlainText(text)
        self._set_status(f"Topic loaded into BRAINSTORM — press Ctrl+Enter to fire: {text[:60]}")

    # ── HELPERS ───────────────────────────────────────────────────────────────

    def _set_status(self, msg):
        self._status.showMessage(msg)

    def _track(self, worker):
        self._workers = [w for w in self._workers if w.isRunning()]
        self._workers.append(worker)


# ── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Council OS v3")
    win = CouncilWindow()
    win.show()
    sys.exit(app.exec())
