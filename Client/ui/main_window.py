import numpy as np
import datetime

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s -- %(levelname)-8s -- %(name)s -- %(message)s",
)
logger = logging.getLogger(__name__)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from database.db import get_connection
from database.schema import create_tables
from database.queries import add_player, get_elo_change, get_session_id_by_name, get_semester_id_by_name, make_member, get_player, get_all_players_name, add_semester, add_session, add_game, get_player_id_by_name

from PySide6.QtWidgets import QMainWindow, QStackedWidget, QSpacerItem, QComboBox, QListWidgetItem, QSizePolicy, QLabel, QGridLayout,  QFrame, QPushButton, QWidget, QListWidget, QMenu, QApplication, QLineEdit, QScrollArea, QHBoxLayout
from PySide6.QtGui import QAction, QCursor, QFont
from PySide6.QtCore import Qt, QSize, QPoint

from ui.session_setup_window import SetupWindow
from ui.text_box_window import TextBoxWindow
from ui.confimation_window import ConfirmationWindow
from ui.update_memberships_window import MembershipWindow

from utils.utils import check_for_new_players, save_scale, remove_menu, get_players_from_qlist, clear_layout
from utils.utils_classes import LeagueRoundBuilder, StatisticsBuilder, Leaderboard

class MainWindow(QMainWindow):
    def __init__(self, scale=1.0):
        super().__init__()
        self.scale = scale
        self.default_font = QFont("Segoe UI", round(self.scale * 18))

        self.setWindowTitle("My Dark Themed PySide6 App")
        self.setMinimumSize(int(1920 * scale), int(1080 * scale))
        
        self.central = QStackedWidget()
        self.setCentralWidget(self.central)
        
        main = QWidget()
        session = QWidget()
        
        self.central.addWidget(main)
        self.central.addWidget(session)
        
        self.main_layout = QGridLayout(main)
        self.main_session_layout = QGridLayout(session)
        
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

        logger.info(f"Semester set to: {sem_name}")

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
        
    def on_new_session(self):

        """ Called when a new session is created to show setup window and ask what players to add """
        def players_recived(players):
            for name in players:
                self.players_list_session.addItem(name)
                
            logger.info(f"listWidget updated")

        """ Called when the confirm menu is pressed """
        def on_confirm_players():
            players = get_players_from_qlist(self.players_list_session)
                    
            new_players = check_for_new_players(players)
            if new_players != []:
                
                self.confimation_window = ConfirmationWindow(scale=self.scale, new_players=new_players)
                
                self.confimation_window.signal_to_send.connect(players_confirmed)
                
                self.confimation_window.show()
                
            else:
                players_confirmed(True)
        
        """ Called when players are confirmed in the confirm window """
        def players_confirmed(yesorno):
            if yesorno:
                logger.info("Players confirmed, proceeding to rounds")
                players = get_players_from_qlist(self.players_list_session)
                
                # Ui stuff
                self.round_title = QLabel("Rounds:")
                self.main_session_layout.addWidget(self.round_title, 0, 1, alignment=Qt.AlignLeft)
                
                self.round_area = QScrollArea()
                self.round_area.setWidgetResizable(True)
                self.round_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                self.round_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.round_area.setStyleSheet("background-color: #0b0b0b;")

                self.round_container = QWidget()
                self.round_container_layout = QHBoxLayout(self.round_container)
                self.round_container_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

                self.round_area.setWidget(self.round_container)
                self.main_session_layout.addWidget(self.round_area, 1, 1)
                
                # disable and enable menu options
                self.confirm_players_action.setDisabled(True)
                self.new_round_action.setDisabled(False)
                self.remove_round_action.setDisabled(False)
                self.save_session_action.setDisabled(False)
                
                # write to database players
                players_ = set(get_players_from_qlist(self.players_list_session))
                for name in players_:
                    add_player(name)

                # logic for round pairings            
                self.round_number = 0
                
                self.finished_games = [] # martix
                
                self.last_round_players = set(players)
                    
                self.builder = LeagueRoundBuilder(players)
                
                on_new_round() # creates first round

                # update tracker
                self.players_confimed = True
                    
            else:
                logger.info("Players no confirmed")
        
        """ Called when a player is added through right clicking the listWidget """
        def player_recived(player):
            # check if the player is already in the session
            found = False
            
            for i in range(self.players_list_session.count()):
                item = self.players_list_session.item(i)
                
                if item.text() == player:
                    found = True
                    break
            
            # update list accordingly
            if not found:
                self.players_list_session.addItem(player)

                if self.players_confimed: # ask to confirm if the rounds have began
                    self.confimation_window = ConfirmationWindow(scale=self.scale, new_players=[player])
                    
                    self.confimation_window.signal_to_send.connect(one_player_confirmed)
                    
                    self.confimation_window.show()
            
                logger.info(f"Added to listWifget: {[player]}")
            else:
                logger.warning(f"Player: {[player]} is already in the list")

        """ Called when the session has started and a player is added through right clicking the listWidget """
        def one_player_confirmed(yesorno, players):
            if yesorno:
                add_player(players[0])

                logger.info(f"Player confirmed: {players[0]}")

            else: # remove the player from the listwidget
                item = self.players_list_session.findItems(players[0], Qt.MatchExactly)

                i = self.players_list_session.row(item[0])
                self.players_list_session.takeItem(i)

                logger.info(f"Player not confirmed: {players[0]}")
                
        """ Called when the new round menu item is pressed """
        def on_new_round():

            def update_advanced():
                pass
            
            def toggle_match_state(button):
                
                current_color = button.property("color_state")
                round_num = button.property("round_num")
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
            
            # check for new players
            players = set(get_players_from_qlist(self.players_list_session))
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

                # for advanced view
                if False:
                    n *= 2
                
                    left_id = get_player_id_by_name(pair[0])
                    right_id = get_player_id_by_name(pair[1])
                    
                    left_change, _ = get_elo_change(left_id, right_id)
                    right_change, _ = get_elo_change(right_id, left_id)

                    left_change = round(left_change)
                    right_change = round(right_change)
                    
                    elo_left = QLabel(f"+ {left_change}")
                    elo_right = QLabel(f"+ {right_change}")
                    
                    elo_left.setProperty("elo_gain", left_change)
                    elo_right.setProperty("elo_gain", right_change)

                    #elo_left.setStyleSheet()
                    
                    round_container_layout.addWidget(elo_left, n + 2, self.round_number, alignment=Qt.AlignLeft)
                    round_container_layout.addWidget(elo_right, n + 2, self.round_number + 2, alignment=Qt.AlignRight)
                
                left.clicked.connect(lambda _, b=left: toggle_match_state(b))
                right.clicked.connect(lambda _, b=right: toggle_match_state(b))
                
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
                
            round_container_layout.addWidget(bye_text, n + 3, self.round_number)
            
            self.round_container_layout.addWidget(round_container)
            
            self.remove_round_action.setDisabled(False)
            if not self.builder.rounds_left: # no rounds left to play
                self.new_round_action.setDisabled(True)

            self.round_number += 1
        
        """ Called when the remove round menu item is pressed """
        def on_remove_round():
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

        """ Called when the save session menu item is pressed """
        def on_save_session():

            self.session_id = add_session(semester_id=self.semester_id, session_date=self.date)
            
            for round_ in self.finished_games:
                for game in round_:
                    
                    player1_id = get_player_id_by_name(game[0])
                    player2_id = get_player_id_by_name(game[1])
                    
                    add_game(self.session_id, player1_id, player2_id, winner_id=player1_id)
                
            logger.info("Saved Session")
            
            on_cancel_session()
            
        """ Called when the cancel session menu item is pressed """
        def on_cancel_session():
        
            # enable new session creation again
            self.new_session_action.setDisabled(False)
            
            # clear the session layout
            clear_layout(self.main_session_layout)
            
            # delete session menu bar
            self.menu_bar = remove_menu(self.menu_bar, "Session")
                
            # clear finished games
            self.finished_games = []

        """ Called when the listWidget is right clicked """
        def show_context_menu(position: QPoint): # menu for adding and removing players from left list
            # Get the item under the cursor
            item = self.players_list_session.itemAt(position)
            
            if item is None:
                menu = QMenu()
                new_action = menu.addAction("New")
                
                # Show menu and wait for user selection
                action = menu.exec(self.players_list_session.mapToGlobal(position))
                
                if action == new_action:
                    self.text_box = TextBoxWindow(scale=self.scale)
                    self.text_box.open_at_cursor()
                    
                    self.text_box.submitted_player.connect(player_recived)
                    
                    self.text_box.show()

            else:
                # Create context menu
                menu = QMenu()
                remove_action = menu.addAction("Remove")
                
                # Show menu and wait for user selection
                action = menu.exec(self.players_list_session.mapToGlobal(position))
                
                if action == remove_action:
                    i = self.players_list_session.row(item)
                    self.players_list_session.takeItem(i)

        """ Called when the view menu item is pressed """
        def on_tab_in():
            # remove menus
            remove_menu(self.menu_bar, "Statistics")
            
            self.central.setCurrentIndex(1)

        # logic for new session window
        self.session_setup_window = SetupWindow(scale=self.scale)
        self.session_setup_window.submitted_players.connect(players_recived)
        
        self.session_setup_window.show()
        
        on_tab_in()

        # create tracker that tracks when players have been confirmed
        self.players_confimed = False
        
        # remove menus
        remove_menu(self.menu_bar, "Statistics")
        
        # Session menu
        self.file_menu = self.menu_bar.addMenu("Session")
        
        self.new_session_action.setDisabled(True)
        
        self.tab_in_action = QAction("View", self)
        self.tab_in_action.triggered.connect(on_tab_in)
        self.file_menu.addAction(self.tab_in_action)
        
        self.file_menu.addSeparator()
        
        self.confirm_players_action = QAction("Confirm", self)
        self.confirm_players_action.triggered.connect(on_confirm_players)
        self.file_menu.addAction(self.confirm_players_action)
        
        self.new_round_action = QAction("New Round", self)
        self.new_round_action.triggered.connect(on_new_round)
        self.file_menu.addAction(self.new_round_action)
        self.new_round_action.setDisabled(True)
        
        self.remove_round_action = QAction("Remove Last Round", self)
        self.remove_round_action.triggered.connect(on_remove_round)
        self.file_menu.addAction(self.remove_round_action)
        self.remove_round_action.setDisabled(True)
        
        self.save_session_action = QAction("Save", self)
        self.save_session_action.triggered.connect(on_save_session)
        self.file_menu.addAction(self.save_session_action)
        self.save_session_action.setDisabled(True)
        
        self.file_menu.addSeparator()
        
        self.cancel_action = QAction("Cancel", self)
        self.cancel_action.triggered.connect(on_cancel_session)
        self.file_menu.addAction(self.cancel_action)
        
        # logic for main window on new session
        self.players_list_title = QLabel("List of Players:")
        self.main_session_layout.addWidget(self.players_list_title, 0, 0, alignment=Qt.AlignLeft)
        
        self.players_list_session = QListWidget()
        self.players_list_session.setFixedWidth(250 * self.scale)
        self.players_list_session.setFont(self.default_font)
        self.main_session_layout.addWidget(self.players_list_session, 1, 0, alignment=Qt.AlignLeft)
        
        self.players_list_session.setContextMenuPolicy(Qt.CustomContextMenu)
        self.players_list_session.customContextMenuRequested.connect(show_context_menu)

    def on_new_statistics(self):

        def player_recived(player):
            # init stats class
            stats_builder = StatisticsBuilder(player)
            player_obj = stats_builder.player

            clear_layout(self.stats_container_layout)
            
            # display stats
            player_name = QLabel(f"{player_obj.name}:")
            self.stats_container_layout.addWidget(player_name, 0, 0, alignment=Qt.AlignLeft | Qt.AlignTop)
            
            player_points = QLabel(f"Points: {player_obj.points}")
            player_points.setStyleSheet("font-weight: normal;")
            self.stats_container_layout.addWidget(player_points, 0, 1, alignment=Qt.AlignLeft | Qt.AlignTop)
            
            player_games_played = QLabel(f"Games Played: {int(player_obj.num_games_played)}")
            player_games_played.setStyleSheet("font-weight: normal;")
            self.stats_container_layout.addWidget(player_games_played, 0, 2, alignment=Qt.AlignLeft | Qt.AlignTop)
            
            player_winrate = QLabel(f"Winrate: {player_obj.winrate}%")
            player_winrate.setStyleSheet("font-weight: normal;")
            self.stats_container_layout.addWidget(player_winrate, 0, 3, alignment=Qt.AlignLeft | Qt.AlignTop)
            
            player_member = QLabel(f"Member: {player_obj.member_displayable}")
            player_member.setStyleSheet("font-weight: normal;")
            self.stats_container_layout.addWidget(player_member, 0, 4, alignment=Qt.AlignLeft | Qt.AlignTop)
            
            # display graphs
            graphs_container = QFrame()
            graphs_container_layout = QGridLayout(graphs_container)
            
            graphs = stats_builder.display_player_stats()
            for i, fig in enumerate(graphs):
                canvas = FigureCanvas(fig)
                graphs_container_layout.addWidget(canvas, 0, i, alignment=Qt.AlignLeft)

            self.stats_container_layout.addWidget(graphs_container, 1, 0, 1, 5)

        def on_enter_player():
            # text box for entering player name
            self.text_box = TextBoxWindow(scale=self.scale)
            self.text_box.open_at_cursor()
            
            self.text_box.submitted_player.connect(player_recived)
            
            self.text_box.show()

        def on_selected_player(player):
            player_recived(player.text())
        
        # set up the visulalise menu
        clear_layout(self.main_layout)
        self.central.setCurrentIndex(0)

        self.file_menu = self.menu_bar.addMenu("Statistics")

        self.enter_player = QAction("Enter Player", self)
        self.enter_player.triggered.connect(on_enter_player)
        self.file_menu.addAction(self.enter_player)

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
        
        # left side list of players
        self.players_list_statistics = QListWidget()
        self.players_list_statistics.setFixedWidth(250 * self.scale)
        self.players_list_statistics.setFont(self.default_font)
        self.players_list_statistics.itemClicked.connect(on_selected_player)
        self.main_layout.addWidget(self.players_list_statistics, 0, 0, alignment=Qt.AlignLeft)
    
        players = get_all_players_name()
        for player in players:
            self.players_list_statistics.addItem(player)

        # container for statisitcs
        self.stats_contanier = QWidget()
        self.stats_container_layout = QGridLayout(self.stats_contanier)

        self.main_layout.addWidget(self.stats_contanier, 0, 1)

    def on_view_leaderboard(self):
        
        def construct(name, leaderboard, layout):
            
            # to allow for spacing
            num_players = len(alltime_leaderboard_points_sorted)
            
            title_label = QLabel(f"{name}:", self)
            layout.addWidget(title_label, 0, 0, alignment=Qt.AlignLeft | Qt.AlignTop)

            points_label = QLabel("Points:", self)
            points_label.setStyleSheet("font-weight: normal;")
            layout.addWidget(points_label, 1, 0, alignment=Qt.AlignLeft | Qt.AlignTop)
            
            name_label = QLabel("Name:", self)
            name_label.setStyleSheet("font-weight: normal;")
            layout.addWidget(name_label, 1, 1, alignment=Qt.AlignLeft | Qt.AlignTop)
            
            # create the players in the leaderboard
            for n, player in enumerate(leaderboard, start=1):
                n *= 2
                
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                line.setFrameShadow(QFrame.Sunken)
                line.setStyleSheet("background-color: #3d3d3d")
                
                layout.addWidget(line, n, 0, 1, 2)
                
                points = QLabel(f"{round(player[1], 2)}")
                points.setStyleSheet("font-weight: normal;")
                
                name_ = QLabel(f"{player[0]}")
                name_.setStyleSheet("font-weight: normal;")

                layout.addWidget(points, n + 1, 0)
                layout.addWidget(name_, n + 1, 1)

            # add spaces to make each leaderboard aligned     
            if False:       
                for i in range(num_players):
                    if i > len(leaderboard):
                        
                        layout.addItem(QSpacerItem(0, 41), n + i, 0)
                        layout.addItem(QSpacerItem(0, 41), n + i + 1, 0)
            
            return layout
            
        def construct_alltime():
            
            name = "All Time"
            layout = leaderboard_container_layout_at

            leaderboard = self.box_to_select_alltime.currentData()

            # add elo parts
            title_label = QLabel(f"{name}:", self)
            layout.addWidget(title_label, 0, 0, alignment=Qt.AlignLeft | Qt.AlignTop)

            points_label = QLabel("Points:", self)
            points_label.setStyleSheet("font-weight: normal;")
            layout.addWidget(points_label, 1, 0, alignment=Qt.AlignLeft | Qt.AlignTop)

            elo_label = QLabel("Elo:", self)
            elo_label.setStyleSheet("font-weight: normal;")
            layout.addWidget(elo_label, 1, 1, alignment=Qt.AlignLeft | Qt.AlignTop)
            
            name_label = QLabel("Name:", self)
            name_label.setStyleSheet("font-weight: normal;")
            layout.addWidget(name_label, 1, 2, alignment=Qt.AlignLeft | Qt.AlignTop)
            
            # create the players in the leaderboard
            for n, player in enumerate(leaderboard, start=1):
                n *= 2
                
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                line.setFrameShadow(QFrame.Sunken)
                line.setStyleSheet("background-color: #3d3d3d")
                
                layout.addWidget(line, n, 0, 1, 3) # 3 wide to allow for elo to be covered
                
                name_ = QLabel(f"{player[0]}")
                name_.setStyleSheet("font-weight: normal;")

                points = QLabel(f"{round(player[1], 2)}")
                points.setStyleSheet("font-weight: normal;")

                elo = QLabel(f"{round(player[2])}")
                elo.setStyleSheet("font-weight: normal;")

                layout.addWidget(name_, n + 1, 2)
                layout.addWidget(points, n + 1, 0)
                layout.addWidget(elo, n + 1, 1)

            return layout

        def refresh_leaderboards(semester_l, session_l):
            
            # create editable copies
            semester_l_copy = semester_l.copy()
            session_l_copy = session_l.copy()
            
            # remove tracking data
            semester_l_copy.pop(-1)
            session_l_copy.pop(-1)
            
            construct("Semester", semester_l_copy, leaderboard_container_layout_sm)
            construct("Session", session_l_copy, leaderboard_container_layout_se)
            
        def update_semester():
            sem_id = self.box_to_select_semester.currentData()
            
            # find the semester selected
            for sem in semester_leaderboard:
                if sem[-1][0][0] == sem_id:
                    break
                
            # find the latest session in the chosen semester
            possible_sessions = []
            for ses in session_leaderboard:
                if ses[-1][0][0] == sem_id:
                    possible_sessions.append(ses)
                    
            refresh_leaderboards(sem, possible_sessions[-1])
            
            sem_title = str(sem[-1][0][1]).split(".")
            ses_title = str(possible_sessions[-1][-1][0][2])
            
            self.box_to_select_semester.blockSignals(True)
            self.box_to_select_semester.setCurrentText(f"{sem_title[0]} Semester: {sem_title[1]}")
            self.box_to_select_semester.blockSignals(False)
                
            self.box_to_select_session.blockSignals(True)
            self.box_to_select_session.setCurrentText(f"Session: {ses_title}")
            self.box_to_select_session.blockSignals(False)
                
        def update_session():
            ses_id = self.box_to_select_session.currentData()
            
            # find the session selected
            for ses in session_leaderboard:
                if ses[-1][0][1] == ses_id:
                    break
                
            # find the semester the session is in
            for sem in semester_leaderboard:
                if sem[-1][0][0] == ses[-1][0][0]:
                    break
                
            refresh_leaderboards(sem, ses)
            
            ses_title = str(ses[-1][0][2])
            sem_title = str(sem[-1][0][1]).split(".")
            
            self.box_to_select_session.blockSignals(True)
            self.box_to_select_session.setCurrentText(f"Session: {ses_title}")
            self.box_to_select_session.blockSignals(False)
            
            self.box_to_select_semester.blockSignals(True)
            self.box_to_select_semester.setCurrentText(f"{sem_title[0]} Semester: {sem_title[1]}")
            self.box_to_select_semester.blockSignals(False)
       
        clear_layout(self.main_layout)
        self.central.setCurrentIndex(0)

        self.menu_bar = remove_menu(self.menu_bar, "Statistics")

        # get leaderboards
        L = Leaderboard()
        semester_leaderboard, session_leaderboard, alltime_leaderboard_points_sorted, alltime_leaderboard_elo_sorted = L.collect_leaderboards()
        
        # ui setup
        """ Whole window widget to allow vertical scrolling """
        leaderboard_area = QScrollArea()
        leaderboard_area.setWidgetResizable(True)
        leaderboard_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        leaderboard_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        leaderboard_area.setStyleSheet("background-color: #0b0b0b;")
        
        """ Widget for whole window to give to the scroller """
        leaderboard_container = QWidget()
        leaderboard_container_layout = QGridLayout(leaderboard_container)
        leaderboard_container_layout.setSpacing(35)

        leaderboard_area.setWidget(leaderboard_container)
        self.main_layout.addWidget(leaderboard_area, 0, 0)
        
        """ Widgets for each leaderboard """
        leaderboard_container_sm = QFrame()
        leaderboard_container_sm.setStyleSheet("background-color: #1f1f1f;")
        leaderboard_container_layout_sm = QGridLayout(leaderboard_container_sm)
        
        leaderboard_container_se = QFrame()
        leaderboard_container_se.setStyleSheet("background-color: #1f1f1f;")
        leaderboard_container_layout_se = QGridLayout(leaderboard_container_se)
        
        leaderboard_container_at = QFrame()
        leaderboard_container_at.setStyleSheet("background-color: #1f1f1f;")
        leaderboard_container_layout_at = QGridLayout(leaderboard_container_at)
        
        # first call to init the leaderboards
        refresh_leaderboards(semester_leaderboard[-1], session_leaderboard[-1])
        
        # combo boxes
        self.box_to_select_semester = QComboBox()
        for sem in semester_leaderboard:
            title = str(sem[-1][0][1]).split(".")
            
            self.box_to_select_semester.addItem(f"{title[0]} Semester: {title[1]}", sem[-1][0][0])
            
        self.box_to_select_semester.setCurrentIndex(len(semester_leaderboard) - 1) # latest semster
            
        leaderboard_container_layout_sm.addWidget(self.box_to_select_semester, 0, 1, alignment=Qt.AlignLeft | Qt.AlignTop)

        self.box_to_select_semester.currentIndexChanged.connect(update_semester)
        
        self.box_to_select_session = QComboBox()
        for ses in session_leaderboard:
            title = str(ses[-1][0][2])
            
            self.box_to_select_session.addItem(f"Session: {title}", ses[-1][0][1])
            
        self.box_to_select_session.setCurrentIndex(len(semester_leaderboard) - 1) # latest session
            
        leaderboard_container_layout_se.addWidget(self.box_to_select_session, 0, 1, alignment=Qt.AlignLeft | Qt.AlignTop)

        self.box_to_select_session.currentIndexChanged.connect(update_session)

        self.box_to_select_alltime = QComboBox()

        self.box_to_select_alltime.addItem(f"Sort by Points", alltime_leaderboard_points_sorted)
        self.box_to_select_alltime.addItem(f"Sort by Elo", alltime_leaderboard_elo_sorted)
            
        leaderboard_container_layout_at.addWidget(self.box_to_select_alltime, 0, 1, alignment=Qt.AlignLeft | Qt.AlignTop)

        self.box_to_select_alltime.currentIndexChanged.connect(construct_alltime)
        
        # call updated functions once to make sure the combo boxes are set correctly
        update_semester()
        update_session()

        # making the alltime leaderboard
        construct_alltime()

        # finish layout
        leaderboard_container_layout.addWidget(leaderboard_container_sm, 0, 0)
        leaderboard_container_layout.addWidget(leaderboard_container_se, 0, 1)
        leaderboard_container_layout.addWidget(leaderboard_container_at, 0, 2)

    def on_edit_memberships(self):
        self.update_membership_window = MembershipWindow(scale=self.scale)
        
        self.update_membership_window.show()

    def on_change_scale(self):

        def change_scale(scale):
            s = int(scale)
            s = s / 100
        
            save_scale(s)

        self.scale_window = TextBoxWindow(scale=self.scale)
        self.scale_window.open_at_cursor()
        
        self.scale_window.submitted_player.connect(change_scale)
        
        self.scale_window.show()