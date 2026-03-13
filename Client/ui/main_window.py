import numpy as np
import datetime

from database.db import get_connection
from database.schema import create_tables
from database.queries import add_player, get_session_id_by_name, get_semester_id_by_name, make_member, get_player, get_all_players, add_semester, add_session, add_game, get_player_id_by_name

from PySide6.QtWidgets import QMainWindow, QComboBox, QListWidgetItem, QSizePolicy, QLabel, QGridLayout,  QFrame, QPushButton, QWidget, QListWidget, QMenu, QApplication, QLineEdit, QScrollArea, QHBoxLayout
from PySide6.QtGui import QAction, QCursor, QFont
from PySide6.QtCore import Qt, QSize, QPoint

from ui.session_setup_window import SetupWindow
from ui.text_box_window import TextBoxWindow
from ui.confimation_window import ConfirmationWindow
from ui.update_memberships_window import MembershipWindow

from utils.utils import check_for_new_players, save_scale
from utils.utils_classes import LeagueRoundBuilder, StatisticsBuilder, Leaderboard

class MainWindow(QMainWindow):
    def __init__(self, scale=1.0):
        super().__init__()
        self.scale = scale
        self.default_font = QFont("Segoe UI", round(self.scale * 18))

        self.setWindowTitle("My Dark Themed PySide6 App")
        self.setMinimumSize(int(1920 * scale), int(1080 * scale))
        
        central = QWidget()
        self.main_layout = QGridLayout(central)
        self.setCentralWidget(central)
        
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
            sem_name = self.year + ".1"
            
            add_semester(sem_name)
            self.semester_id = get_semester_id_by_name(sem_name)

        if 1 <= self.month <= 8:
            sem_name = self.year + ".2"
            
            add_semester(sem_name)
            self.semester_id = get_semester_id_by_name(sem_name)

    def create_menu_bar(self):
        self.menu_bar = self.menuBar()  # Built-in QMainWindow menu bar

        # File menu
        self.file_menu = self.menu_bar.addMenu("File")

        # File menu actions
        self.new_session_action = QAction("New Session", self)
        self.new_session_action.triggered.connect(self.on_new_session)
        self.file_menu.addAction(self.new_session_action)

        self.new_statistics_action = QAction("New Statisctics", self)
        self.new_statistics_action.triggered.connect(self.on_new_statistics)
        self.file_menu.addAction(self.new_statistics_action)
        
        self.view_leaderboard = QAction("View Leaderboard", self)
        self.view_leaderboard.triggered.connect(self.on_view_leaderboard)
        self.file_menu.addAction(self.view_leaderboard)

        self.edit_memberships = QAction("Edit Members", self)
        self.edit_memberships.triggered.connect(self.on_edit_memberships)
        self.file_menu.addAction(self.edit_memberships)

        self.file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)  # Built-in close method
        self.file_menu.addAction(exit_action)

        # View menu
        view_menu = self.menu_bar.addMenu("View")
        
        self.change_scale = QAction("Change Scale", self)
        self.change_scale.triggered.connect(self.on_change_scale)
        view_menu.addAction(self.change_scale)

    # Action callbacks
    def on_new_session(self):
        # logic for new session window
        self.session_setup_window = SetupWindow(scale=self.scale)
        self.session_setup_window.submitted_players.connect(self.players_recived)
        
        self.session_setup_window.show()
        
        self.clear_layout(self.main_layout)
        
        # Session menu
        self.file_menu = self.menu_bar.addMenu("Session")
        
        self.new_session_action.setDisabled(True)
        
        self.confirm_players_action = QAction("Confirm", self)
        self.confirm_players_action.triggered.connect(self.on_confirm_players)
        self.file_menu.addAction(self.confirm_players_action)
        
        self.new_round_action = QAction("New Round", self)
        self.new_round_action.triggered.connect(self.on_new_round)
        self.file_menu.addAction(self.new_round_action)
        self.new_round_action.setDisabled(True)
        
        self.remove_round_action = QAction("Remove Last Round", self)
        self.remove_round_action.triggered.connect(self.on_remove_round)
        self.file_menu.addAction(self.remove_round_action)
        self.remove_round_action.setDisabled(True)
        
        self.save_session_action = QAction("Save", self)
        self.save_session_action.triggered.connect(self.on_save_session)
        self.file_menu.addAction(self.save_session_action)
        self.save_session_action.setDisabled(True)
        
        self.file_menu.addSeparator()
        
        self.cancel_action = QAction("Cancel", self)
        self.cancel_action.triggered.connect(self.on_cancel_session)
        self.file_menu.addAction(self.cancel_action)
        
        # logic for main window on new session
        self.players_list_title = QLabel("List of Players:")
        self.main_layout.addWidget(self.players_list_title, 0, 0, alignment=Qt.AlignLeft)
        
        self.players_list = QListWidget()
        self.players_list.setFixedWidth(250 * self.scale)
        self.players_list.setFont(self.default_font)
        self.main_layout.addWidget(self.players_list, 1, 0, alignment=Qt.AlignLeft)
        
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
        # check if the player is already in the session
        found = False
        
        for i in range(self.players_list.count()):
            item = self.players_list.item(i)
            
            if item.text() == player:
                found = True
                break
        
        # update list accordingly
        if not found:
            self.players_list.addItem(player)
        
            print(f"Added to list: {[player]}")
        else:
            print(f"Player: {[player]} is already in the list")
        
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
            self.main_layout.addWidget(self.round_title, 0, 1, alignment=Qt.AlignLeft)
            
            self.round_area = QScrollArea()
            self.round_area.setWidgetResizable(True)
            self.round_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.round_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.round_area.setStyleSheet("background-color: #0b0b0b;")

            self.round_container = QWidget()
            self.round_container_layout = QHBoxLayout(self.round_container)
            self.round_container_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

            self.round_area.setWidget(self.round_container)
            self.main_layout.addWidget(self.round_area, 1, 1)
            
            # disable and enable menu options
            self.confirm_players_action.setDisabled(True)
            self.new_round_action.setDisabled(False)
            self.remove_round_action.setDisabled(False)
            self.save_session_action.setDisabled(False)
            
            # logic for round pairings            
            self.round_number = 0
            
            self.finished_games = [] # martix
            
            self.last_round_players = set(players)
                
            self.builder = LeagueRoundBuilder(players)
            
            self.on_new_round() # creates first round
                
        else:
            print("Not proceeding to rounds")

    def on_new_round(self):
        # check for new players
        players = set(self.get_players_from_list())
        difference_in_players = players ^ self.last_round_players
        if difference_in_players != set(): # if there is a difference in players from last round
            
            more_players = players - self.last_round_players
            less_players = self.last_round_players - players
        
            # update the LeagueRoundBuilder with this infomaion
            if more_players != set():
                self.builder.add_players(list(more_players))
                
            if less_players != set():
                self.builder.add_players(list(less_players))
            
        # Create new round and the bye (None for no bye)
        round_, bye = self.builder.create_round()
        self.finished_games.append([])
        
        self.last_round_players = players
                    
        # creating display of round pairings
        round_container = QFrame()
        round_container.setStyleSheet("background-color: #1f1f1f;")
        round_container_layout = QGridLayout(round_container)
        
        round_container_layout.addWidget(QLabel(f"Round: {self.round_number + 1}"), 0, self.round_number)
        
        # shuffle order of round and games so display is random
        rng = np.random.default_rng()
    
        round_ = [list(t) for t in list(round_)]
        rng.shuffle(round_)
        
        for game in round_:
            rng.shuffle(game)
        
        # create buttons to display players and track wins
        for n, pair in enumerate(round_):
            left = QPushButton(pair[0])
            right = QPushButton(pair[1])
            
            left.clicked.connect(self.toggle_match_state)
            right.clicked.connect(self.toggle_match_state)
            
            # to track what round each button is created in
            left.setProperty("round_num", self.round_number)
            right.setProperty("round_num", self.round_number)
            
            # keep track of the order of buttons and therefore games
            left.setProperty("index", n)
            right.setProperty("index", n)
            
            # keep track of opponent
            left.setProperty("opp", pair[1])
            right.setProperty("opp", pair[0])
            
            # adding buttons to the gui
            round_container_layout.addWidget(left, n + 1, self.round_number)
            round_container_layout.addWidget(QLabel("v"), n + 1, self.round_number + 1)
            round_container_layout.addWidget(right, n + 1, self.round_number + 2)
        
        if bye != None:
            bye_text = QLabel(f"Bye: {bye}")
        else:
            bye_text = QLabel(f"Bye: None")
            
        round_container_layout.addWidget(bye_text, n + 2, self.round_number)
        
        self.round_container_layout.addWidget(round_container)
        
        self.remove_round_action.setDisabled(False)
        if not self.builder.rounds_left: # no rounds left to play
            self.new_round_action.setDisabled(True)

        self.round_number += 1
        
    def on_remove_round(self):
        self.builder.remove_round()
        self.finished_games.pop(-1)
        
        # delete display of last round
        item = self.round_container_layout.takeAt(self.round_number - 1)
        widget = item.widget()
        if widget:
            widget.setParent(None)
            widget.deleteLater()

        self.new_round_action.setDisabled(False)
        
        self.round_number -= 1
        
        if self.round_number == 0: # no rounds displayed
            self.remove_round_action.setDisabled(True)
        
    def toggle_match_state(self):
        button = self.sender()
        
        current_color = button.property("color_state")
        round_num = button.property("round_num")
        index = button.property("index")
        opp = button.property("opp")
        
        name = button.text()
        
        # toggle button to green for a win and update the finsihed games tracker to reflect the result
        if current_color is None:
            button.setStyleSheet("background-color: green")
            button.setProperty("color_state", "green")
            
            # check if this is an adjustment
            if [opp, name] in self.finished_games[round_num]:
                self.finished_games[round_num].remove([opp, name])
            
            if [name, opp] in self.finished_games[round_num]:
                self.finished_games[round_num].remove([name, opp])
            
            self.finished_games[round_num].append([name, opp])
            
        elif current_color == "green":
            button.setStyleSheet("background-color: #1f1f1f")
            button.setProperty("color_state", None)
            
            # check if this is an adjustment
            if [name, opp] in self.finished_games[round_num]:
                self.finished_games[round_num].remove([name, opp])
            
        print(self.finished_games)
        #print(self.finished_games[round_num].append([name, opp]))

    def on_save_session(self):
        
        self.session_id = add_session(semester_id=self.semester_id, session_date=self.date)
        
        # write to database
        players = set(self.get_players_from_list())
        for name in players:
            add_player(name)
        
        for round_ in self.finished_games:
            for game in round_:
                
                player1_id = get_player_id_by_name(game[0])
                player2_id = get_player_id_by_name(game[1])
                
                add_game(self.session_id, player1_id, player2_id, winner_id=player1_id)
            
        print("Saved Session")
        
        self.on_cancel_session()
            
    def on_cancel_session(self):
        
        # enable new session creation again
        self.new_session_action.setDisabled(False)
        
        # clear the session layout
        self.clear_layout(self.main_layout)
        
        # delete session menu bar
        for action in self.menu_bar.actions():
            if action.text() == "Session":
                
                self.menu_bar.removeAction(action)

                action.menu().deleteLater()
                break
            
        # clear finished games
        self.finished_games = []

    def on_new_statistics(self):
        # set up the visulalise menu
        self.file_menu = self.menu_bar.addMenu("Statistics")

        self.enter_player = QAction("Enter Player", self)
        self.enter_player.triggered.connect(self.on_enter_player)
        self.file_menu.addAction(self.enter_player)

        self.select_player = QAction("Select Player", self)
        self.file_menu.addAction(self.select_player)

        self.select_session = QAction("Select Session", self)
        self.file_menu.addAction(self.select_session)

        self.select_sememster = QAction("Select Semester", self)
        self.file_menu.addAction(self.select_sememster)

        self.select_alltime = QAction("Select Alltime", self)
        self.file_menu.addAction(self.select_alltime)

        self.file_menu.addSeparator()

        self.advanced = QAction("Advanced", self)
        self.file_menu.addAction(self.advanced)
        self.advanced.setDisabled(True)

    def on_enter_player(self):

        def player_recived(player):
            player_obj = self.stats_builder.display_player_stats(player)
            
            # display crucial stats
            player_name = QLabel(f"{player_obj.name}:")
            self.main_layout.addWidget(player_name, 0, 0, alignment=Qt.AlignLeft | Qt.AlignTop)
            
            player_points = QLabel(f"Points: {player_obj.points}")
            player_points.setStyleSheet("font-weight: normal;")
            self.main_layout.addWidget(player_points, 0, 1, alignment=Qt.AlignLeft | Qt.AlignTop)
            
            player_games_played = QLabel(f"Games Played: {int(player_obj.num_games_played)}")
            player_games_played.setStyleSheet("font-weight: normal;")
            self.main_layout.addWidget(player_games_played, 0, 2, alignment=Qt.AlignLeft | Qt.AlignTop)
            
            player_winrate = QLabel(f"Winrate: {player_obj.winrate}%")
            player_winrate.setStyleSheet("font-weight: normal;")
            self.main_layout.addWidget(player_winrate, 0, 3, alignment=Qt.AlignLeft | Qt.AlignTop)
            
            player_member = QLabel(f"Member: {player_obj.member_displayable}")
            player_member.setStyleSheet("font-weight: normal;")
            self.main_layout.addWidget(player_member, 0, 4, alignment=Qt.AlignLeft | Qt.AlignTop)

        self.clear_layout(self.main_layout)

        # init stats class
        self.stats_builder = StatisticsBuilder()

        self.text_box = TextBoxWindow(scale=self.scale)
        self.text_box.open_at_cursor()
        
        self.text_box.submitted_player.connect(player_recived)
        
        self.text_box.show()

    def on_view_leaderboard(self):
        
        self.clear_layout(self.main_layout)
        
        def on_semester_selected(semester="first"):
            
            self.leaderboard_container_layout.removeWidget(leaderboard_container_sm)
            
            # decide which semester to display
            if semester == "first": # perform on first call to show most recent semester
                index = len(semester_leaderboard) - 1
                sem = semester_leaderboard[index]
            
            else:
                semester = self.L_select_semester.currentData()
                
                # clean data
                data = semester.split()
                data.pop(1)
                data.reverse()
                
                for i, sem in enumerate(semester_leaderboard):
                    if int(sem[-1][0]) == int(data[0]): # check if semester_id matches
                        break
            
            for n, player in enumerate(sem, start=1):
                n *= 2
                
                # prevent the semester data from being displayed
                if sem[-1] == player:
                    break
                
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                line.setFrameShadow(QFrame.Sunken)
                line.setStyleSheet("background-color: #3d3d3d")
                
                leaderboard_container_layout_sm.addWidget(line, n, 0, 1, 2)
                
                points = QLabel(f"{player[2]}")
                points.setStyleSheet("font-weight: normal;")
                
                name = QLabel(f"{player[1]}")
                name.setStyleSheet("font-weight: normal;")

                leaderboard_container_layout_sm.addWidget(points, n + 1, 0)
                leaderboard_container_layout_sm.addWidget(name, n + 1, 1)
                                
            self.L_semester_label = QLabel("Semester Leaderboard:", self)
            leaderboard_container_layout_sm.addWidget(self.L_semester_label, 0, 0, alignment=Qt.AlignLeft | Qt.AlignTop)

            self.L_select_semester_score = QLabel("Points:", self)
            self.L_select_semester_score.setStyleSheet("font-weight: normal;")
            leaderboard_container_layout_sm.addWidget(self.L_select_semester_score, 1, 0, alignment=Qt.AlignLeft | Qt.AlignTop)
            
            self.L_select_semester_name = QLabel("Name:", self)
            self.L_select_semester_name.setStyleSheet("font-weight: normal;")
            leaderboard_container_layout_sm.addWidget(self.L_select_semester_name, 1, 1, alignment=Qt.AlignLeft | Qt.AlignTop)

            # combo box
            self.L_select_semester = QComboBox()
            
            for semester_ in semester_leaderboard:
                # pass all data but only display the semester year and number
                year_num = str(semester_[-1][1]).split(".")
                
                self.L_select_semester.addItem(f"{year_num[0]} Semester: {year_num[1]}", str(semester_[-1][1]) + " - " + str(semester_[-1][0]))
            
            if semester == "first": # perform on first call to show most recent session
                self.L_select_semester.setCurrentIndex(len(semester_leaderboard) - 1)
            else:     
                self.L_select_semester.setCurrentIndex(i) # set index found earlier
                
            self.L_select_semester.currentIndexChanged.connect(on_semester_selected)
            leaderboard_container_layout_sm.addWidget(self.L_select_semester, 0, 1, alignment=Qt.AlignLeft | Qt.AlignTop)

            self.leaderboard_container_layout.addWidget(leaderboard_container_sm, 0, 0)
            
        def on_session_selected(session="first"):
            
            self.leaderboard_container_layout.removeWidget(leaderboard_container_se)

            # decide which session to display
            if session == "first": # perform on first call to show most recent session
                index = len(session_leaderboard) - 1
                ses = session_leaderboard[index]
            
            else:
                session = self.L_select_session.currentData()
                
                # clean data
                data = session.split()
                data.pop(1)
                data.pop(2)
                
                for i, ses in enumerate(session_leaderboard):
                    if int(ses[-1][0]) == int(data[0]) and int(ses[-1][3]) == int(data[2]): # check if session_id and semester_id matches
                        break
                
            for n, player in enumerate(ses, start=1):
                n *= 2
                
                # prevent the semester data from being displayed
                if ses[-1] == player:
                    break
                
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                line.setFrameShadow(QFrame.Sunken)
                line.setStyleSheet("background-color: #3d3d3d")
                
                leaderboard_container_layout_se.addWidget(line, n, 0, 1, 2)
                
                points = QLabel(f"{player[2]}")
                points.setStyleSheet("font-weight: normal;")
                
                name = QLabel(f"{player[1]}")
                name.setStyleSheet("font-weight: normal;")

                leaderboard_container_layout_se.addWidget(points, n + 1, 0)
                leaderboard_container_layout_se.addWidget(name, n + 1, 1)
                
            self.L_session_label = QLabel("Session Leaderboard:", self)
            leaderboard_container_layout_se.addWidget(self.L_session_label, 0, 0, alignment=Qt.AlignLeft | Qt.AlignTop)

            self.L_select_session_score = QLabel("Points:", self)
            self.L_select_session_score.setStyleSheet("font-weight: normal;")
            leaderboard_container_layout_se.addWidget(self.L_select_session_score, 1, 0, alignment=Qt.AlignLeft | Qt.AlignTop)
            
            self.L_select_session_name = QLabel("Name:", self)
            self.L_select_session_name.setStyleSheet("font-weight: normal;")
            leaderboard_container_layout_se.addWidget(self.L_select_session_name, 1, 1, alignment=Qt.AlignLeft | Qt.AlignTop)

            # combo box
            self.L_select_session = QComboBox()
            
            for session_ in session_leaderboard:
                # pass all data but only display the date of the session
                self.L_select_session.addItem(str(session_[-1][1]), str(session_[-1][0]) + " - " + str(session_[-1][1]) + " - " + str(session_[-1][3]))
            
            if session == "first": # perform on first call to show most recent session
                self.L_select_session.setCurrentIndex(len(session_leaderboard) - 1)
            else:     
                self.L_select_session.setCurrentIndex(i) # set index found earlier
                
            self.L_select_session.currentIndexChanged.connect(on_session_selected)
            leaderboard_container_layout_se.addWidget(self.L_select_session, 0, 1, alignment=Qt.AlignLeft | Qt.AlignTop)

            self.leaderboard_container_layout.addWidget(leaderboard_container_se, 0, 1)
        
        # get leaderboards
        L = Leaderboard()
        semester_leaderboard, session_leaderboard, alltime_leaderboard = L.collect_leaderboards()
        
        # ui setup
        self.leaderboard_area = QScrollArea()
        self.leaderboard_area.setWidgetResizable(True)
        self.leaderboard_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.leaderboard_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.leaderboard_area.setStyleSheet("background-color: #0b0b0b;")
        
        self.leaderboard_container = QWidget()
        self.leaderboard_container_layout = QGridLayout(self.leaderboard_container)
        self.leaderboard_container_layout.setSpacing(35)

        self.leaderboard_area.setWidget(self.leaderboard_container)
        self.main_layout.addWidget(self.leaderboard_area, 1, 1)
        
        leaderboard_container_sm = QFrame()
        leaderboard_container_sm.setStyleSheet("background-color: #1f1f1f;")
        leaderboard_container_layout_sm = QGridLayout(leaderboard_container_sm)
        
        leaderboard_container_se = QFrame()
        leaderboard_container_se.setStyleSheet("background-color: #1f1f1f;")
        leaderboard_container_layout_se = QGridLayout(leaderboard_container_se)
        
        leaderboard_container_at = QFrame()
        leaderboard_container_at.setStyleSheet("background-color: #1f1f1f;")
        leaderboard_container_layout_at = QGridLayout(leaderboard_container_at)
                        
        # alltime leaderboard
        self.L_alltime_label = QLabel("All-Time Leaderboard:", self)
        leaderboard_container_layout_at.addWidget(self.L_alltime_label, 0, 0, alignment=Qt.AlignLeft | Qt.AlignTop)
        
        self.L_alltime_label_score = QLabel("Points:", self)
        self.L_alltime_label_score.setStyleSheet("font-weight: normal;")
        leaderboard_container_layout_at.addWidget(self.L_alltime_label_score, 1, 0, alignment=Qt.AlignLeft | Qt.AlignTop)
        
        self.L_alltime_label_name = QLabel("Name:", self)
        self.L_alltime_label_name.setStyleSheet("font-weight: normal;")
        leaderboard_container_layout_at.addWidget(self.L_alltime_label_name, 1, 1, alignment=Qt.AlignLeft | Qt.AlignTop)

        # displaying leaderboards
        for n, player in enumerate(alltime_leaderboard, start=1):
            n *= 2
            
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            line.setStyleSheet("background-color: #3d3d3d")
            
            leaderboard_container_layout_at.addWidget(line, n, 0, 1, 2)
            
            points = QLabel(f"{player[2]}")
            points.setStyleSheet("font-weight: normal;")
            
            name = QLabel(f"{player[1]}")
            name.setStyleSheet("font-weight: normal;")

            leaderboard_container_layout_at.addWidget(points, n + 1, 0)
            leaderboard_container_layout_at.addWidget(name, n + 1, 1)
        
        on_semester_selected()
        on_session_selected()
        
        self.leaderboard_container_layout.addWidget(leaderboard_container_sm, 0, 0)
        self.leaderboard_container_layout.addWidget(leaderboard_container_se, 0, 1)
        self.leaderboard_container_layout.addWidget(leaderboard_container_at, 0, 2)

    def on_edit_memberships(self):
        self.update_membership_window = MembershipWindow(scale=self.scale)
        
        self.update_membership_window.show()

    def on_change_scale(self):
        self.scale_window = TextBoxWindow(scale=self.scale)
        self.scale_window.open_at_cursor()
        
        self.scale_window.submitted_player.connect(self.on_change_scale2)
        
        self.scale_window.show()
        
    def on_change_scale2(self, scale):
        s = int(scale)
        s = s / 100
    
        save_scale(s)
        
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