from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton, QHBoxLayout
from PySide6.QtCore import Signal

class ConfirmationWindow(QDialog):
    yesorno = Signal(bool)
    
    def __init__(self, scale, new_players):
        super().__init__()
        self.scale = scale
        self.setWindowTitle("Confirmation")
        #self.setModal(True)  # Blocks interaction
        
        layout = QVBoxLayout()
        
        label1 = QLabel("New players (haven't ever played before)")
        layout.addWidget(label1)
        
        list_wid = QListWidget()
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
        self.yesorno.emit(True)
        super().accept()
    
    def reject(self):
        self.yesorno.emit(False)
        super().reject()