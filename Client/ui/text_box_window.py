from PySide6.QtWidgets import QDialog, QGridLayout, QWidget, QLineEdit
from PySide6.QtGui import QCursor, QFont
from PySide6.QtCore import Qt, Signal

from utils.utils import clean_name
from resources.colours import HEAD, LINE, TEXT, ACCENT

class TextBoxWindow(QDialog):
    submitted_player = Signal(str)
    
    def __init__(self, scale=1.0):
        super().__init__()
        self.scale = scale
        self.setWindowTitle("Text Box")
        self.setModal(True)
        
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        # 🔹 Remove ALL extra spacing
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.box = QLineEdit()
        self.box.setFont(QFont("Segoe UI", round(self.scale * 12)))
        self.box.setStyleSheet(f"""
            QLineEdit {{
                padding: 6px 10px;
                margin: 0px;
                background-color: {HEAD};
                color: {TEXT};
                border: 1px solid {LINE};
                border-radius: 4px;
                selection-background-color: {ACCENT};
            }}
            QLineEdit:focus {{
                border: 1px solid {ACCENT};
            }}
        """)
        layout.addWidget(self.box)

        self.box.returnPressed.connect(self.submit_text)
        
    def submit_text(self):
        text = self.box.text()#
        
        text = clean_name(text)
        
        if text == "":
            print("--Err-- no valid name submitted")
            self.close()
            return
        
        self.submitted_player.emit(text)
        self.close()
        
    def open_at_cursor(self):
        cursor_pos = QCursor.pos()
        self.move(cursor_pos.x(), cursor_pos.y())