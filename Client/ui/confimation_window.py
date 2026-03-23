from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton, QHBoxLayout
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont

class ConfirmationWindow(QDialog):
    signal_to_send = Signal(bool, list)
    
    def __init__(self, scale, new_players):
        super().__init__()
        self.scale = scale
        self.default_font = QFont("Segoe UI", round(self.scale * 18))

        self.setWindowTitle("Confirmation")

        self.new_players = new_players
        
        layout = QVBoxLayout()
        
        label1 = QLabel("New players (haven't ever played before)")
        layout.addWidget(label1)
        
        list_wid = QListWidget()
        list_wid.setFont(self.default_font)
        for player in new_players:
            list_wid.addItem(player)
        
        layout.addWidget(list_wid)
        
        label2 = QLabel("Is this correct?")
        layout.addWidget(label2)
        
        button_layout = QHBoxLayout()
        
        yes_btn = QPushButton("Yes")
        no_btn = QPushButton("No")
        
        yes_btn.clicked.connect(self.accept)
        no_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(yes_btn)
        button_layout.addWidget(no_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def accept(self):
        self.signal_to_send.emit(True, self.new_players)
        super().accept()
    
    def reject(self):
        self.signal_to_send.emit(False, self.new_players)
        super().reject()