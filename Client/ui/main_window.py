import numpy as np
import datetime

from database.db import get_connection
from database.schema import create_tables
from database.queries import add_player, get_session_id_by_name, get_semester_id_by_name, make_member, get_player, get_all_players, add_semester, add_session, add_game, get_player_id_by_name

from PySide6.QtWidgets import QMainWindow, QSizePolicy, QLabel, QGridLayout,  QFrame, QPushButton, QWidget, QListWidget, QMenu, QApplication, QLineEdit, QScrollArea, QHBoxLayout
from PySide6.QtGui import QAction, QCursor
from PySide6.QtCore import Qt, QSize, QPoint

from ui.setup_window import SetupWindow
from ui.text_box_window import TextBoxWindow
from ui.confimation_window import ConfirmationWindow
from ui.utils import LeagueRoundBuilder, check_for_new_players, find_opponent, round_robin_schedule

class MainWindow(QMainWindow):
    def __init__(self, scale=1.0):
        super().__init__()
        self.scale = scale

        self.setWindowTitle("My Dark Themed PySide6 App")
        self.setMinimumSize(int(1920 * scale), int(1080 * scale))
        
        # Create the menu bar
        self.create_menu_bar()
        
        # Database things
        date_time = datetime.datetime.now()
        self.date = date_time.strftime("%d") + "." + date_time.strftime("%m") + "." + date_time.strftime("%Y") # 01.01.2000 first jan 2000
        self.year = date_time.strftime("%Y")
        self.month = int(date_time.strftime("%m"))
        
        create_tables()
        
        # automatically determine semester and year
        if 9 <= self.month <= 12:
            sem_name = self.year + " semester 1"
            
            add_semester(sem_name)
            self.semester_id = get_semester_id_by_name(sem_name)

        if 1 <= self.month <= 8:
            sem_name = self.year + " semester 2"
            
            add_semester(sem_name)
            self.semester_id = get_semester_id_by_name(sem_name)

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
        self.session_setup_window = SetupWindow(scale=self.scale)
        self.session_setup_window.submitted_players.connect(self.players_recived)
        
        self.session_setup_window.show()
        
        # logic for main window on new session
        central = QWidget()
        self.layout1 = QGridLayout(central)
        self.setCentralWidget(central)
        
        # Session menu
        self.file_menu = self.menu_bar.addMenu("Session")
        
        confirm_players_action = QAction("Confirm", self)
        confirm_players_action.triggered.connect(self.on_confirm_players)
        self.file_menu.addAction(confirm_players_action)
        
        new_round_action = QAction("New Round", self)
        new_round_action.triggered.connect(self.on_new_round)
        self.file_menu.addAction(new_round_action)
        
        save_session_action = QAction("Save", self)
        save_session_action.triggered.connect(self.on_save_session)
        self.file_menu.addAction(save_session_action)
        
        self.file_menu.addSeparator()
        
        cancel_action = QAction("Cancel", self)
        cancel_action.triggered.connect(self.on_cancel_session)
        self.file_menu.addAction(cancel_action)
        
        self.players_list_title = QLabel("List of Players:")
        self.layout1.addWidget(self.players_list_title, 0, 0, alignment=Qt.AlignLeft)
        
        self.players_list = QListWidget()
        self.players_list.setFixedWidth(250 * self.scale)
        self.layout1.addWidget(self.players_list, 1, 0, alignment=Qt.AlignLeft)
        
        self.players_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.players_list.customContextMenuRequested.connect(self.show_context_menu)
        
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
            
        print(f"Added to list: {players}")
        
    def player_recived(self, player):
        self.players_list.addItem(player)
        
        print(f"Added to list: {[player]}")
        
    def on_confirm_players(self):
        players = self.get_players_from_list()
                
        new_players = check_for_new_players(players)
        if new_players != []:
            
            self.confimation_window = ConfirmationWindow(scale=self.scale, new_players=new_players)
            
            self.confimation_window.yesorno.connect(self.players_confirmed)
            
            self.confimation_window.show()
            
        else:
            self.players_confirmed(True)
        
    def players_confirmed(self, yesorno):
        if yesorno:
            print("Proceeding to rounds")
            players = self.get_players_from_list()
            
            # Ui stuff
            self.round_title = QLabel("Rounds:")
            self.layout1.addWidget(self.round_title, 0, 1, alignment=Qt.AlignLeft)
            
            self.round_area = QScrollArea()
            self.round_area.setWidgetResizable(True)
            self.round_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.round_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.round_area.setStyleSheet("background-color: #0b0b0b;")

            self.container = QWidget()
            self.container_layout = QHBoxLayout(self.container)
            self.container_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

            self.round_area.setWidget(self.container)
            self.layout1.addWidget(self.round_area, 1, 1)
            
            self.round_number = -1
            
            self.finished_games = [] # [[winner, loser], [winner, loser]]
            
            # logic for round pairings
            self.first_round_players = players
                
            self.builder = LeagueRoundBuilder(players)
            self.builder.round_robin_schedule()
            self.rounds_to_play = self.builder.rounds
            self.byes = self.builder.byes
            
            print(f"Number of rounds to play: {len(self.rounds_to_play)}")
            
            self.on_new_round() # creates first round
                
        else:
            print("Not proceeding to rounds")

    def on_new_round(self):
        # Logic for round pairings
        self.round_number += 1
        self.builder.round_complete(self.round_number)
        
        # check for new players
        players = set(self.get_players_from_list())
        new_players = players - set(self.first_round_players)
        if False:
            self.builder.add_players(new_players) # add new players to the builder class
            
            self.rounds_to_play, self.byes = self.builder.round_robin_schedule()
            print(f"Rounds to play: {self.rounds_to_play}")
            print(f"Byes: {self.byes}")
                    
        # creating display of round pairings
        round_container = QFrame()
        round_container.setStyleSheet("background-color: #1f1f1f;")
        round_container_layout = QGridLayout(round_container)
        
        round_container_layout.addWidget(QLabel(f"Round: {self.round_number + 1}"), 0, self.round_number)
        
        # create buttons to display players and track wins
        for n, pair in enumerate(self.rounds_to_play[self.round_number]):
            left = QPushButton(pair[0])
            right = QPushButton(pair[1])
            
            left.clicked.connect(self.toggle_match_state)
            right.clicked.connect(self.toggle_match_state)
            
            # to track what round each button is created in
            left.setProperty("round_num", self.round_number)
            right.setProperty("round_num", self.round_number)
            
            # adding buttons to the gui
            round_container_layout.addWidget(left, n + 1, self.round_number)
            round_container_layout.addWidget(QLabel("v"), n + 1, self.round_number + 1)
            round_container_layout.addWidget(right, n + 1, self.round_number + 2)
        
        if self.byes != None:
            bye_text = QLabel(f"Bye: {self.byes[self.round_number]}")
        else:
            bye_text = QLabel(f"Bye: None")
        bye_text.setStyleSheet(f"font-size: {int(12*self.scale)}px;")
        round_container_layout.addWidget(bye_text, n + 2, self.round_number)
        
        self.container_layout.addWidget(round_container)
        
    def toggle_match_state(self):
        button = self.sender()
        current_color = button.property("color_state")
        round_num = button.property("round_num")
        name = button.text()
        
        # toggle button to green for a win and update the finsihed games tracker to reflect the result
        if current_color is None:
            button.setStyleSheet("background-color: green")
            button.setProperty("color_state", "green")
            
            # make sure the rounc searched is the same as the round played
            opp = find_opponent(self.rounds_to_play[round_num], name)
            
            # check if this is an adjustment
            if [opp, name] in self.finished_games:
                self.finished_games.remove([opp, name])
            if [name, opp] in self.finished_games:
                self.finished_games.remove([name, opp])
            
            self.finished_games.append([name, opp])
            
        elif current_color == "green":
            button.setStyleSheet("background-color: #1f1f1f")
            button.setProperty("color_state", None)

    def on_save_session(self):
        
        self.session_id = add_session(semester_id=self.semester_id, session_date=self.date)
        
        # write to database
        players = set(self.get_players_from_list())
        for name in players:
            add_player(name)
        
        for game in self.finished_games:
            
            player1_id = get_player_id_by_name(game[0])
            player2_id = get_player_id_by_name(game[1])
            
            add_game(self.session_id, player1_id, player2_id, winner_id=player1_id)
            
        print("Saved Session")
        
        self.on_cancel_session()
            
    def on_cancel_session(self):
        
        # clear the session layout
        self.clear_layout(self.layout1)
        
        # delete session menu bar
        for action in self.menu_bar.actions():
            if action.text() == "Session":
                
                self.menu_bar.removeAction(action)

                action.menu().deleteLater()
                break
            
        # clear finished games
        self.finished_games = []
    

    def on_open(self):
        print("Open file triggered!")

    def on_about(self):
        print("This is a PySide6 demo app.")
        
    def get_players_from_list(self):
        players = []
        
        for i in range(self.players_list.count()):
            item = self.players_list.item(i)
            players.append(item.text())
            
        return players
    
    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                
                item = layout.takeAt(0)
                widget = item.widget()
                
                if widget is not None:
                    widget.setParent(None)