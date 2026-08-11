from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QMenu, QPushButton, QSizePolicy, QApplication, QPlainTextEdit, QLineEdit, QVBoxLayout
from PySide6.QtGui import QAction

from resources.colours import HEAD, LINE, TEXT, ACCENT

class CustomButton(QPushButton):
    normalClick = Signal()
    shiftClick = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clicked.connect(self._handle_click)

    def _handle_click(self):
        if QApplication.keyboardModifiers() & Qt.ShiftModifier:
            self.shiftClick.emit()
        else:
            self.normalClick.emit()
        
class CustomHeaderBar(QWidget):
    def __init__(self, panels, panel_widgets: dict, parent=None):
        
        super().__init__(parent)
        self.panels = panels
        self.panel_widgets = panel_widgets  # id → QWidget
        self.setFixedHeight(32)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)
        self.setStyleSheet(f"background:{HEAD};")

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._labels: dict[str, QLabel] = {}
        for pid, label, visible, _ in panels:
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            lbl.setFixedHeight(32)
            lbl.setMinimumWidth(120)
            lbl.setStyleSheet(f"""
                QLabel {{
                    color: #c8c8c8; font-size: 12px; font-weight: 600;
                    padding-left: 10px;
                    border-right: 1px solid {LINE};
                    border-bottom: 2px solid #555;
                    background: {HEAD};
                }}
                QLabel:hover {{ background: #353535; }}
            """)
            self._layout.addWidget(lbl)
            self._labels[pid] = lbl
            if not visible:
                lbl.hide()

        self._layout.addStretch()

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
                return toggle

            action.toggled.connect(make_toggle(pid))
            menu.addAction(action)

        menu.exec(self.mapToGlobal(pos))
        
    def set_panel_visible(self, panel_id, visible):
        self._labels[panel_id].setVisible(visible)
        self.panel_widgets[panel_id].setVisible(visible)

class ConsoleWidget(QWidget):
    commandEntered = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setLineWrapMode(QPlainTextEdit.NoWrap)

        self.input = QLineEdit()
        self.input.setPlaceholderText("...")

        layout = QVBoxLayout(self)
        layout.addWidget(self.output)
        layout.addWidget(self.input)

        self.input.returnPressed.connect(self._on_return_pressed)

    def _on_return_pressed(self):
        text = self.input.text().strip()
        if not text:
            return

        # echo command
        self.append(f"> {text}")

        self.commandEntered.emit(text)

        self.input.clear()

    def append(self, text: str):
        """Append text to console output."""
        self.output.appendPlainText(text)

    def clear(self):
        self.output.clear()