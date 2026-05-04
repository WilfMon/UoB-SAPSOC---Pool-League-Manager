""" 
Rebuild class:
UpdateDatabase
- Allow updating who is a member

- Allow removing and adding players
- Allow removing and adding sessions
- Allow removing and adding semesters
- Allow removing and adding games
    - Have a confimation step
    - Dont delete permanently, create a backup database that is deleted after 30 days before changes were made

UploadDatabse
- Allow logging in and uploading to the website the current database
- Allow retriving the current database without logging in
"""


import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s -- %(levelname)-8s -- %(name)s -- %(message)s",
)
logger = logging.getLogger(__name__)

from PySide6.QtWidgets import QMainWindow, QLineEdit, QGridLayout, QWidget, QLabel, QPushButton, QListWidget, QMenu, QListWidgetItem
from PySide6.QtCore import Qt, QPoint, QSize
from PySide6.QtGui import QFont

from utils.utils import clean_name
from database.queries import get_members, up_make_member, up_remove_member, get_all_players_name, re_remove_player, add_player, get_player_id_from_name

from .confimation_window import ConfirmationWindow

class MembershipWindow(QMainWindow):
    def __init__(self, dest="league.db", scale=1.0):
        super().__init__()
        
        self.dest = dest
        
        self.scale = scale
        self.default_font = QFont("Segoe UI", round(self.scale * 18))
        
        self.setWindowTitle("Memberships")
        self.setMinimumSize(int(400 * scale), int(300 * scale))
        
        central = QWidget()
        layout = QGridLayout()
        central.setLayout(layout)
        self.setCentralWidget(central)
        
        self.label1_text_box = QLabel("Current Members:")
        self.label1_text_box.setFixedSize(self.label1_text_box.sizeHint())
        layout.addWidget(self.label1_text_box, 0, 0)
        
        self.player_list = QListWidget()
        self.player_list.setFixedSize(QSize(250 * scale, 450 * scale))
        self.player_list.setFont(self.default_font)
        self.player_list.itemClicked.connect(self.submit_text_selected)
        layout.addWidget(self.player_list, 1, 0, alignment=Qt.AlignTop)
        
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
        self.display_players()
        
    def submit_text_selected(self, player):
        
        text = clean_name(player.text())
        
        item = self.list_widget.findItems(text, Qt.MatchExactly)
        
        # check if text is aleady submitted
        if not item:

            qitem = QListWidgetItem(text)
            self.list_widget.addItem(qitem)
        
        else: 
            logger.warning(f"Player: {text} already submitted")
        
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
            
    def display_players(self):
        self.player_list.clear()
        self.list_widget.clear()
        
        members = get_members(dest=self.dest)
        
        for m in members:
            self.player_list.addItem(str(m))
            
    def add(self):
        players_to_make_member = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
    
        for name in players_to_make_member:
            up_make_member(name, dest=self.dest)
            
        self.display_players()
    
    def remove(self):
        players_to_make_member = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
    
        for name in players_to_make_member:
            up_remove_member(name, dest=self.dest)
            
        self.display_players()
        

class DataWindow(MembershipWindow):
    def __init__(self, dest="league.db", scale=1):
        super().__init__(dest, scale)
        
        self.setWindowTitle("Update Database")
        
        self.label1_text_box.setText("Current Players:")
        
    def display_players(self):
        self.player_list.clear()
        self.list_widget.clear()
        
        players = get_all_players_name(dest=self.dest)
        
        for p in players:
            self.player_list.addItem(str(p))
            
    def add(self):
        players_to_remove = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
    
        for name in players_to_remove:
            add_player(name, dest=self.dest)
            
        self.display_players()
    
    def remove(self):
        
        def players_confirmed(yesorno):
            if yesorno:
                logger.info("Players confirmed, removing players")
                
                commit()
            else:
                logger.info("Players not confirmed")
        
        def commit():
            for name in players_to_remove:
                
                player_id = get_player_id_from_name(name, dest=self.dest)
                re_remove_player(player_id, dest=self.dest)
                
            self.display_players()
        
        players_to_remove = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
    
        self.confimation_window =  ConfirmationWindow(scale=self.scale, display_items=players_to_remove, message="Are you sure you want to delete these players? (cannot be undone)")
        self.confimation_window.signal_to_send.connect(players_confirmed)
        self.confimation_window.show()