import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s -- %(levelname)-8s -- %(name)s -- %(message)s",
)
logger = logging.getLogger(__name__)

from PySide6.QtWidgets import QMainWindow, QLineEdit, QSizePolicy , QGridLayout, QWidget, QLabel, QPushButton, QListWidget, QMenu, QListWidgetItem
from PySide6.QtCore import Qt, QPoint, Signal, QSize
from PySide6.QtGui import QKeySequence, QShortcut, QFont

from utils.utils import clean_name

from database.queries import get_all_players_name

class SetupWindow(QMainWindow):
    # Define a signal that sends a list
    submitted_players = Signal(list)
    
    def __init__(self, scale=1.0):
        super().__init__()
        self.scale = scale
        self.default_font = QFont("Segoe UI", round(self.scale * 18))
        
        self.setWindowTitle("Setup")
        self.setMinimumSize(int(800 * scale), int(600 * scale))

        central = QWidget()
        layout = QGridLayout()
        central.setLayout(layout)
        self.setCentralWidget(central)

        label_text_box = QLabel("Enter Players:")
        label_text_box.setFixedSize(label_text_box.sizeHint())
        layout.addWidget(label_text_box, 0, 0)

        self.input_box = QLineEdit()
        layout.addWidget(self.input_box, 1, 0, alignment=Qt.AlignTop)
        self.input_box.returnPressed.connect(self.submit_text_typed)

        label_text_box = QLabel("Select Players:")
        label_text_box.setFixedSize(label_text_box.sizeHint())
        layout.addWidget(label_text_box, 2, 0)
        
        self.selection_list = QListWidget()
        self.selection_list.setFont(self.default_font)
        self.selection_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.selection_list.itemClicked.connect(self.submit_text_selected)
        layout.addWidget(self.selection_list, 3, 0)

        for player in get_all_players_name():
            self.selection_list.addItem(player)

        self.list_widget = QListWidget()
        self.list_widget.setFont(self.default_font)
        self.list_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        layout.addWidget(self.list_widget, 1, 1, 3, 1)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        
        self.populate_list = QShortcut(QKeySequence("Ctrl+P"), self)
        self.populate_list.activated.connect(self.on_populate_list)
        
        button_cancel = QPushButton("Cancel")
        button_cancel.adjustSize()
        button_cancel.clicked.connect(self.close)
        layout.addWidget(button_cancel, 4, 0, alignment=Qt.AlignLeft)
        
        button_accept = QPushButton("Accept")
        button_accept.adjustSize()
        button_accept.clicked.connect(self.accept)
        layout.addWidget(button_accept, 4, 1, alignment=Qt.AlignRight)

    def on_populate_list(self): # for debugging
        players = ["Wilf Moncrieff", "Robert Fry", "Jak Dables", "Wilf Howard", "Dylan Nolan", "Will Vickers", "Paaras Padhair", "Elijah Brook", "Malachi Bielby", "George Worsley", "Evan Morris", "Osain Drake"]
        
        for player in players:
            self.list_widget.addItem(QListWidgetItem(player))
        
    def submit_text_selected(self, player):
        
        text = clean_name(player.text())

        item = self.list_widget.findItems(text, Qt.MatchExactly)
        
        # check if text is aleady submitted
        if not item:

            text = QListWidgetItem(text)
            self.list_widget.addItem(text)
        
        else: 
            logger.warning(f"Player: {text} already submitted")

    def submit_text_typed(self):
        text = self.input_box.text()
        
        text = clean_name(text)
        
        if text == "":
            logger.warning("No valid name submitted")
            return
        
        text = QListWidgetItem(text)
        #text.setSizeHint(QSize(0, 18))
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