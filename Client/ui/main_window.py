import numpy as np
from database.db import get_connection
from database.schema import create_tables
from database.queries import add_player, make_member, get_player, get_all, get_all_players

from PySide6.QtWidgets import QMainWindow, QSizePolicy, QLabel, QGridLayout,  QFrame, QPushButton, QWidget, QListWidget, QMenu, QApplication, QLineEdit, QScrollArea, QHBoxLayout
from PySide6.QtGui import QAction, QCursor
from PySide6.QtCore import Qt, QSize, QPoint

from ui.setup_window import SetupWindow
from ui.text_box_window import TextBoxWindow

class MainWindow(QMainWindow):
    def __init__(self, scale=1.0):
        super().__init__()
        self.scale = scale

        self.setWindowTitle("My Dark Themed PySide6 App")
        self.setMinimumSize(int(1920 * scale), int(1080 * scale))
        
        # Create the menu bar
        self.create_menu_bar()
        
        # Database things
        if False:
            create_tables()
            players = ["Wilf Moncrieff", "Robert Fry", "James Lund", "Rob Hall", "Thomas Henry"]
            for name in players:
                add_player(name)
            
            make_member("Wilf Moncrieff")
            
            print(get_all())

    def create_menu_bar(self):
        self.menu_bar = self.menuBar()  # Built-in QMainWindow menu bar

        # File menu
        self.file_menu = self.menu_bar.addMenu("File")

        # File menu actions
        news_action = QAction("New Session", self)
        news_action.triggered.connect(self.on_new_session)
        self.file_menu.addAction(news_action)

        open_action = QAction("Open Session", self)
        open_action.triggered.connect(self.on_open)
        self.file_menu.addAction(open_action)

        self.file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)  # Built-in close method
        self.file_menu.addAction(exit_action)

        # Help menu
        view_menu = self.menu_bar.addMenu("View")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.on_about)
        view_menu.addAction(about_action)

    # Action callbacks
    def on_new_session(self):
        # logic for new session window
        self.news_window = SetupWindow(scale=self.scale)
        self.news_window.submitted_players.connect(self.players_recived)
        
        self.news_window.show()
        
        # logic for main window on new session
        central = QWidget()
        layout = QGridLayout(central)
        self.setCentralWidget(central)
        
        # Session menu
        self.file_menu = self.menu_bar.addMenu("Session")
        
        newr_action = QAction("New Round", self)
        newr_action.triggered.connect(self.on_new_round)
        self.file_menu.addAction(newr_action)
        
        self.participants_list_title = QLabel("List of Players:")
        layout.addWidget(self.participants_list_title, 0, 0, alignment=Qt.AlignLeft)
        
        self.players_list = QListWidget()
        self.players_list.setFixedWidth(250 * self.scale)
        layout.addWidget(self.players_list, 1, 0, alignment=Qt.AlignLeft)
        
        self.players_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.players_list.customContextMenuRequested.connect(self.show_context_menu)
        
        self.participants_list_title = QLabel("Rounds:")
        layout.addWidget(self.participants_list_title, 0, 1, alignment=Qt.AlignLeft)
        
        self.round_area = QScrollArea()
        self.round_area.setWidgetResizable(True)
        self.round_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.round_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.round_area.setStyleSheet("background-color: #0b0b0b;")

        self.container = QWidget()
        self.container_layout = QHBoxLayout(self.container)
        self.container_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.round_area.setWidget(self.container)
        layout.addWidget(self.round_area, 1, 1)
        
        self.round_count = 0
        
        
    def show_context_menu(self, position: QPoint):
        # Get the item under the cursor
        item = self.players_list.itemAt(position)
        
        if item is None:
            menu = QMenu()
            new_action = menu.addAction("New")
            
            # Show menu and wait for user selection
            action = menu.exec(self.players_list.mapToGlobal(position))
            
            if action == new_action:
                self.text_box = TextBoxWindow(scale=self.scale)
                self.text_box.open_at_cursor()
                
                self.text_box.submitted_player.connect(self.player_recived)
                
                self.text_box.show()

        else:
            # Create context menu
            menu = QMenu()
            remove_action = menu.addAction("Remove")
            
            # Show menu and wait for user selection
            action = menu.exec(self.players_list.mapToGlobal(position))
            
            if action == remove_action:
                i = self.players_list.row(item)
                self.players_list.takeItem(i)
        
    def players_recived(self, players):
        for name in players:
            self.players_list.addItem(name)
            
        db_players = get_all_players()
        
        if (set(players) - set(db_players)):

            new_items = list(set(players) - set(db_players))
            print("New players:", new_items)
            
            # confirm new players
            
        else:
            print("No new players")
            
        print(f"Added: {players}")
        
    def player_recived(self, player):
        self.players_list.addItem(player)
        
        db_players = get_all_players()
        
        if (set([player]) - set(db_players)):

            new_items = list(set([player]) - set(db_players))
            print("New players:", new_items)
            
            # confirm new players
            
        else:
            print("No new players")
        
        print(f"Added: {player}")

    def on_new_round(self):
        # Logic for round pairings
        players = [self.players_list.item(i).text() for i in range(self.players_list.count())]
        
        # shuffle the list of players randomly
        rng = np.random.default_rng()
        random_players = rng.permutation(players)
        
        # check if players are odd
        if len(random_players) % 2:
            bye = random_players[0]
            random_players = np.delete(random_players, 0)
        else:
            bye = None
            
        # create pairings
        player_pairings = []
        
        for _ in range(int(len(random_players) / 2)):
            player_pairings.append([random_players[0], random_players[1]])
            
            random_players = np.delete(random_players, 0)
            random_players = np.delete(random_players, 0)
            
        # creating display of round pairings
        round_container = QFrame()
        round_container.setStyleSheet("background-color: #1f1f1f;")
        round_container_layout = QGridLayout(round_container)
        
        round_container_layout.addWidget(QLabel(f"Round: {self.round_count + 1}"), 0, self.round_count)
        
        for n, pair in enumerate(player_pairings):
            left = QPushButton(pair[0])
            right = QPushButton(pair[1])
            
            left.clicked.connect(self.toggle_match_state)
            right.clicked.connect(self.toggle_match_state)
            
            round_container_layout.addWidget(left, n + 1, self.round_count)
            round_container_layout.addWidget(QLabel("v"), n + 1, self.round_count + 1)
            round_container_layout.addWidget(right, n + 1, self.round_count + 2)
            
            
        bye_text = QLabel(f"Bye: {bye}")
        bye_text.setStyleSheet(f"font-size: {int(12*self.scale)}px;")
        round_container_layout.addWidget(bye_text, n + 2, self.round_count)
        
        self.container_layout.addWidget(round_container)
        
        self.round_count += 1
        
    def toggle_match_state(self):
        button = self.sender()
        current_color = button.property("color_state")
        identity = button.property("id")

        if current_color is None:
            button.setStyleSheet("background-color: green")
            button.setProperty("color_state", "green")
            
        elif current_color == "green":
            button.setStyleSheet("background-color: #1f1f1f")
            button.setProperty("color_state", None)

    def on_open(self):
        print("Open file triggered!")

    def on_about(self):
        print("This is a PySide6 demo app.")