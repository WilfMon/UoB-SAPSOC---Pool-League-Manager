from PySide6.QtWidgets import QMainWindow, QLineEdit, QGridLayout, QWidget, QLabel, QPushButton, QListWidget, QMenu, QListWidgetItem
from PySide6.QtCore import Qt, QPoint, QSize
from PySide6.QtGui import QFont

from utils.utils import clean_name
from database.queries import get_members, make_member, remove_member

class MembershipWindow(QMainWindow):
    def __init__(self, scale=1.0):
        super().__init__()
        self.scale = scale
        self.default_font = QFont("Segoe UI", round(self.scale * 18))
        
        self.setWindowTitle("Memberships")
        self.setMinimumSize(int(400 * scale), int(300 * scale))
        
        central = QWidget()
        layout = QGridLayout()
        central.setLayout(layout)
        self.setCentralWidget(central)
        
        label1_text_box = QLabel("Current Members:")
        label1_text_box.setFixedSize(label1_text_box.sizeHint())
        layout.addWidget(label1_text_box, 0, 0)
        
        self.membership_list = QListWidget()
        self.membership_list.setFixedSize(QSize(250 * scale, 450 * scale))
        self.membership_list.setFont(self.default_font)
        layout.addWidget(self.membership_list, 1, 0, alignment=Qt.AlignTop)
        
        label2_text_box = QLabel("Enter Players:")
        label2_text_box.setFixedSize(label2_text_box.sizeHint())
        layout.addWidget(label2_text_box, 0, 1)
        
        self.input_box = QLineEdit()
        layout.addWidget(self.input_box, 1, 1, alignment=Qt.AlignTop)
        
        self.input_box.returnPressed.connect(self.submit_text)
        
        self.list_widget = QListWidget()
        self.list_widget.setFixedSize(QSize(250 * scale, 450 * scale))
        self.list_widget.setFont(self.default_font)
        layout.addWidget(self.list_widget, 1, 2, alignment=Qt.AlignTop)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        
        button_remove = QPushButton("Remove")
        button_remove.adjustSize()
        button_remove.clicked.connect(self.remove)
        layout.addWidget(button_remove, 2, 2, alignment=Qt.AlignLeft)
        
        button_add = QPushButton("Add")
        button_add.adjustSize()
        button_add.clicked.connect(self.add)
        layout.addWidget(button_add, 2, 2, alignment=Qt.AlignRight)
        
        button_close = QPushButton("Close")
        button_close.adjustSize()
        button_close.clicked.connect(self.close)
        layout.addWidget(button_close, 2, 0, alignment=Qt.AlignLeft)
        
        # show current members
        self.display_members()
        
    def submit_text(self):
        text = self.input_box.text()
        
        text = clean_name(text)
        
        if text == "":
            print("--Err-- no valid name submitted")
            return
        
        print("Submitted:", text)
        
        # set size of items to be smaller
        text = QListWidgetItem(text)
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
            
    def display_members(self):
        self.membership_list.clear()
        self.list_widget.clear()
        
        members = get_members()
        
        for m in members:
            self.membership_list.addItem(str(m))
            
    def add(self):
        players_to_make_member = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
    
        for name in players_to_make_member:
            make_member(name)
            
        self.display_members()
    
    def remove(self):
        players_to_make_member = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
    
        for name in players_to_make_member:
            remove_member(name)
            
        self.display_members()