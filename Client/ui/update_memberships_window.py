from PySide6.QtWidgets import QMainWindow, QLineEdit, QGridLayout, QWidget, QLabel, QPushButton, QListWidget, QMenu, QListWidgetItem
from PySide6.QtCore import Qt, QPoint, Signal, QSize

from utils.utils import clean_name
from database.queries import get_members

class MembershipWindow(QMainWindow):
    def __init__(self, scale=1.0):
        super().__init__()
        self.scale = scale
        self.setWindowTitle("Memberships")
        self.setMinimumSize(int(400 * scale), int(300 * scale))
        
        central = QWidget()
        layout = QGridLayout()
        central.setLayout(layout)
        self.setCentralWidget(central)
        
        label1_text_box = QLabel("Current Members:")
        label1_text_box.setStyleSheet(f"font-size: {int(14*scale)}px; font-weight: bold;")
        label1_text_box.setFixedSize(label1_text_box.sizeHint())
        layout.addWidget(label1_text_box, 0, 0)
        
        self.membership_list = QListWidget()
        self.membership_list.setFixedSize(QSize(250 * scale, 450 * scale))
        layout.addWidget(self.membership_list, 1, 0, alignment=Qt.AlignTop)
        
        # show current members
        members = get_members()
        for m in members:
            self.membership_list.addItem(str(m))
        
        label2_text_box = QLabel("Enter Players:")
        label2_text_box.setStyleSheet(f"font-size: {int(14*scale)}px; font-weight: bold;")
        label2_text_box.setFixedSize(label2_text_box.sizeHint())
        layout.addWidget(label2_text_box, 0, 1)
        
        self.input_box = QLineEdit()
        self.input_box.setStyleSheet(f"font-size: {int(14*scale)}px;")
        layout.addWidget(self.input_box, 1, 1, alignment=Qt.AlignTop)
        
        self.input_box.returnPressed.connect(self.submit_text)
        
        self.list_widget = QListWidget()
        self.list_widget.setFixedSize(QSize(250 * scale, 450 * scale))
        layout.addWidget(self.list_widget, 1, 2, alignment=Qt.AlignTop)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        
        button_cancel = QPushButton("Remove")
        button_cancel.setStyleSheet(f"font-size: {int(14*scale)}px;")
        button_cancel.adjustSize()
        button_cancel.clicked.connect(self.remove)
        layout.addWidget(button_cancel, 2, 2, alignment=Qt.AlignLeft)
        
        button_accept = QPushButton("Add")
        button_accept.setStyleSheet(f"font-size: {int(14*scale)}px;")
        button_accept.adjustSize()
        button_accept.clicked.connect(self.add)
        layout.addWidget(button_accept, 2, 2, alignment=Qt.AlignRight)
        
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
            
    def add(self):
        pass
    
    def remove(self):
        pass