from PySide6.QtCore import QPoint, Qt, Signal, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QMenu, QPushButton, QSizePolicy, QApplication, QPlainTextEdit, QLineEdit, QVBoxLayout, QSplitter, QCheckBox
from PySide6.QtGui import QAction, QPainter, QColor

from resources.colours import HEAD, LINE, TEXT, ACCENT

class CustomButton(QPushButton):
    normalClick = Signal(tuple)
    shiftClick = Signal(tuple)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clicked.connect(self._handle_click)
        
        self.clicked = False
        
    def info(self, buttons: tuple[QPushButton, QPushButton], position: tuple[int, int], round_id: int): # first one is the subject button
        self.buttons = buttons
        self.position = position
        self.round_id = round_id

    def _handle_click(self):
        if QApplication.keyboardModifiers() & Qt.ShiftModifier:
            self.shiftClick.emit(self.buttons)
        else:
            self.normalClick.emit(self.buttons)


class CustomHeaderBar(QWidget):
    panelVisibilityChanged = Signal()
    tabsResized = Signal(list)  # emitted with new sizes when the user drags a tab handle

    def __init__(self, panels, panel_widgets: dict, parent=None):
        
        super().__init__(parent)
        self.panels = panels
        self.panel_widgets = panel_widgets  # id → QWidget
        self.setFixedHeight(32)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)

        # WA_StyledBackground is needed for a plain QWidget subclass to
        # actually paint stylesheet background/border properties.
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            background: {HEAD};
            border: none;
            border-bottom: 1px solid {LINE};
        """)

        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # A real splitter (same handle width/colour as the panel splitter)
        # gives the tabs an actual draggable divider, and its handles are
        # kept in sync with the panel splitter's from MainSessionWindow.
        self.tabs_splitter = QSplitter(Qt.Horizontal, self)
        self.tabs_splitter.setHandleWidth(3)
        self.tabs_splitter.setChildrenCollapsible(False)
        self.tabs_splitter.setStyleSheet(f"""
            QSplitter {{ background: transparent; border: none; }}
            QSplitter::handle {{ background:{LINE}; }}
            QSplitter::handle:hover {{ background:#777; }}
        """)
        outer_layout.addWidget(self.tabs_splitter)

        self._labels: dict[str, QLabel] = {}
        for pid, label, visible, _ in panels:
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            lbl.setFixedHeight(32)
            lbl.setStyleSheet(f"""
                QLabel {{
                    color: #c8c8c8; font-size: 12px; font-weight: 600;
                    padding-left: 10px;
                    background: transparent;
                }}
                QLabel:hover {{ background: #353535; }}
            """)
            # Match the panel's minimum width so both splitters share the
            # same constraints. Without this, dragging a tab narrower than
            # its panel's minimum causes the panel splitter to silently
            # clamp/redistribute differently than the tab splitter did,
            # and the two permanently drift out of sync.
            panel_widget = panel_widgets.get(pid)
            if panel_widget is not None and panel_widget.minimumWidth() > 0:
                lbl.setMinimumWidth(panel_widget.minimumWidth())
            self.tabs_splitter.addWidget(lbl)
            self._labels[pid] = lbl
            if not visible:
                lbl.hide()

        self.tabs_splitter.splitterMoved.connect(self._on_tabs_resized)

    def _on_tabs_resized(self, *args):
        self.tabsResized.emit(self.tabs_splitter.sizes())

    def _show_menu(self, pos: QPoint):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background:{HEAD}; color:{TEXT};
                border:1px solid #444; padding:4px 0;
            }}
            QMenu::item {{ padding:5px 28px 5px 28px; font-size:13px; }}
            QMenu::item:selected {{ background:#3c3f41; }}
            QMenu::indicator {{ width:14px; height:14px; left:6px; }}
            QMenu::indicator:checked {{
                background:{ACCENT}; border:1px solid #6ab0ff; border-radius:2px;
            }}
            QMenu::indicator:unchecked {{
                background:transparent; border:1px solid #666; border-radius:2px;
            }}
        """)

        visible_count = sum(
        lbl.isVisible()
        for lbl in self._labels.values()
        )

        for pid, label, _, _ in self.panels:
            action = QAction(label, menu)
            action.setCheckable(True)

            is_visible = self._labels[pid].isVisible()
            action.setChecked(is_visible)

            # Disable the last visible panel's action
            if visible_count == 1 and is_visible:
                action.setEnabled(False)

            def make_toggle(panel_id):
                def toggle(checked):
                    self._labels[panel_id].setVisible(checked)
                    self.panel_widgets[panel_id].setVisible(checked)
                    self.panelVisibilityChanged.emit()
                return toggle

            action.toggled.connect(make_toggle(pid))
            menu.addAction(action)

        menu.exec(self.mapToGlobal(pos))
        
    def set_panel_visible(self, panel_id, visible):
        self._labels[panel_id].setVisible(visible)
        self.panel_widgets[panel_id].setVisible(visible)
        self.panelVisibilityChanged.emit()

class ConsoleWidget(QWidget):
    commandEntered = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.output.setFrameShape(QPlainTextEdit.NoFrame)
        self.output.setStyleSheet(f"""
            QPlainTextEdit {{
                background: transparent;
                border: none;
                color: {TEXT};
            }}
        """)

        self.input = QLineEdit()
        self.input.setPlaceholderText("...")
        self.input.setFrame(False)
        self.input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                border-top: 1px solid {LINE};
                padding: 6px 4px;
                color: {TEXT};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.output)
        layout.addWidget(self.input)

        self.input.returnPressed.connect(self._on_return_pressed)

    def _on_return_pressed(self):
        text = self.input.text().strip()
        if not text:
            return

        # echo command
        self.append(f">> {text}")

        self.commandEntered.emit(text)

        self.input.clear()

    def append(self, text: str):
        """Append text to console output."""
        self.output.appendPlainText(text)

    def warn(self, text: str):
        self.output.appendPlainText(f"WARN | {text}")
        
    def inform(self, text: str):
        self.output.appendPlainText(f"INFO | {text}")

    def clear(self):
        self.output.clear()