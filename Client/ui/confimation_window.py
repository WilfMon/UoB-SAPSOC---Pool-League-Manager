from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton, QHBoxLayout
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from resources.colours import DARK, PANEL_COL, HEAD, LINE, TEXT, MUTED, ACCENT, GREEN, RED
from resources.stylesheets import _scrollbar_stylesheet


class ConfirmationWindow(QDialog):
    signal_to_send = Signal(bool, list)
    
    def __init__(self, scale, new_players, message="New players (haven't ever played before)"):
        super().__init__()
        self.scale = scale
        self.default_font = QFont("Segoe UI", round(self.scale * 18))

        self.setWindowTitle("Confirmation")

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            QDialog {{
                background: {PANEL_COL};
            }}
        """)

        self.new_players = new_players
        
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        
        label1 = QLabel(message.upper())
        label1.setWordWrap(True)
        label1.setStyleSheet(f"""
            color: {ACCENT};
            font-weight: 700;
            font-size: {13 * self.scale}px;
            letter-spacing: 1px;
            background: transparent;
        """)
        layout.addWidget(label1)
        
        list_wid = QListWidget()
        list_wid.setFont(self.default_font)
        list_wid.setStyleSheet(f"""
            QListWidget {{
                background: {HEAD};
                color: {TEXT};
                border: 1px solid {LINE};
                border-radius: 5px;
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 4px 6px;
            }}
            QListWidget::item:selected {{
                background: {LINE};
                color: {TEXT};
            }}
        """ + _scrollbar_stylesheet(bg=HEAD))
        for player in new_players:
            list_wid.addItem(player)
        
        layout.addWidget(list_wid)
        
        label2 = QLabel("Is this correct?")
        label2.setStyleSheet(f"""
            color: {MUTED};
            font-size: {13 * self.scale}px;
            background: transparent;
        """)
        layout.addWidget(label2)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        yes_btn = QPushButton("Yes".upper())
        no_btn = QPushButton("No".upper())

        for btn, colour in ((yes_btn, GREEN), (no_btn, RED)):
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {DARK};
                    color: {colour};
                    border: 1px solid {colour};
                    border-radius: 4px;
                    font-weight: 700;
                    letter-spacing: 1px;
                    padding: 6px 18px;
                }}
                QPushButton:hover {{
                    background: {colour};
                    color: {DARK};
                }}
            """)
        
        yes_btn.clicked.connect(self.accept)
        no_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(yes_btn)
        button_layout.addWidget(no_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def info(self, stored_players):
        self.stored_players = stored_players
        
    def accept(self):
        self.signal_to_send.emit(True, self.new_players)
        super().accept()
    
    def reject(self):
        self.signal_to_send.emit(False, self.new_players)
        super().reject()