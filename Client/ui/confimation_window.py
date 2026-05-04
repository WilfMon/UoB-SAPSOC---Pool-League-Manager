from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton, QHBoxLayout
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont

class ConfirmationWindow(QDialog):
    signal_to_send = Signal(bool, list)
    
    def __init__(self, scale: float, display_items: list, message: str, display_type: str = "list"):
        super().__init__()
        self.scale = scale
        self.default_font = QFont("Segoe UI", round(self.scale * 18))

        self.setWindowTitle("Confirmation")
        
        self.new_players = display_items

        self.main_layout = QVBoxLayout()
        
        label1 = QLabel(message)
        self.main_layout.addWidget(label1)
        
        # Decide the display
        if display_type == "list":
            list_wid = QListWidget()
            list_wid.setFont(self.default_font)
            for player in display_items:
                list_wid.addItem(player)
            
            self.main_layout.addWidget(list_wid)

        if display_type == "single":
            self.display_session()
        
        label2 = QLabel("Is this correct?")
        self.main_layout.addWidget(label2)
        
        button_layout = QHBoxLayout()
        
        yes_btn = QPushButton("Yes")
        no_btn = QPushButton("No")
        
        yes_btn.clicked.connect(self.accept)
        no_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(yes_btn)
        button_layout.addWidget(no_btn)
        
        self.main_layout.addLayout(button_layout)
        self.setLayout(self.main_layout)
        
    def display_session(self):
        pass

    def display_semester(self):
        pass

    def display_game(self):
        pass
    
    def accept(self):
        self.signal_to_send.emit(True, self.new_players)
        super().accept()
    
    def reject(self):
        self.signal_to_send.emit(False, self.new_players)
        super().reject()