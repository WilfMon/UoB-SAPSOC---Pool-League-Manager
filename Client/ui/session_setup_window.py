from PySide6.QtWidgets import QMainWindow, QLineEdit, QGridLayout, QWidget, QLabel, QPushButton, QListWidget, QMenu, QListWidgetItem
from PySide6.QtCore import Qt, QPoint, Signal, QSize

from utils.utils import clean_name

class SetupWindow(QMainWindow):
    # Define a signal that sends a list
    submitted_players = Signal(list)
    
    def __init__(self, scale=1.0):
        super().__init__()
        self.scale = scale
        self.setWindowTitle("Setup")
        self.setMinimumSize(int(400 * scale), int(300 * scale))

        central = QWidget()
        layout = QGridLayout()
        central.setLayout(layout)
        self.setCentralWidget(central)

        label_text_box = QLabel("Enter Players:")
        label_text_box.setStyleSheet(f"font-size: {int(14*scale)}px; font-weight: bold;")
        label_text_box.setFixedSize(label_text_box.sizeHint())
        layout.addWidget(label_text_box, 0, 0)

        self.input_box = QLineEdit()
        self.input_box.setStyleSheet(f"font-size: {int(14*scale)}px;")
        layout.addWidget(self.input_box, 1, 0, alignment=Qt.AlignTop)
        
        self.input_box.returnPressed.connect(self.submit_text)
        
        self.list_widget = QListWidget()
        self.list_widget.setFixedSize(QSize(250 * scale, 450 * scale))
        layout.addWidget(self.list_widget, 1, 1, alignment=Qt.AlignTop)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        
        button_cancel = QPushButton("Cancel")
        button_cancel.setStyleSheet(f"font-size: {int(14*scale)}px;")
        button_cancel.adjustSize()
        button_cancel.clicked.connect(self.close)
        layout.addWidget(button_cancel, 2, 0, alignment=Qt.AlignLeft)
        
        button_accept = QPushButton("Accept")
        button_accept.setStyleSheet(f"font-size: {int(14*scale)}px;")
        button_accept.adjustSize()
        button_accept.clicked.connect(self.accept)
        layout.addWidget(button_accept, 2, 1, alignment=Qt.AlignRight)
        
    def submit_text(self):
        text = self.input_box.text()
        
        text = clean_name(text)
        
        if text == "":
            print("--Err-- no valid name submitted")
            return
        
        print("Submitted:", text)
        
        # set size of items to be smaller
        text = QListWidgetItem(text)
        text.setSizeHint(QSize(0, 18))
        self.list_widget.addItem(text)

        self.input_box.clear()
        
    def show_context_menu(self, position: QPoint):
        # Get the item under the cursor
        item = self.list_widget.itemAt(position)
        if item is None:
            return  # clicked empty space

        # Create context menu
        menu = QMenu()
        remove_action = menu.addAction("Remove")
        
        # Show menu and wait for user selection
        action = menu.exec(self.list_widget.mapToGlobal(position))
        
        if action == remove_action:
            i = self.list_widget.row(item)
            self.list_widget.takeItem(i)
            
    def accept(self):
        participants = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
        
        self.submitted_players.emit(participants)
        self.close()