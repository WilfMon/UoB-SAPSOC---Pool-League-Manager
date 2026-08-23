import numpy as np
import datetime

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s -- %(levelname)-8s -- %(name)s -- %(message)s",
)
logger = logging.getLogger(__name__)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from PySide6.QtWidgets import QMainWindow, QStackedWidget, QSpacerItem, QComboBox, QListWidgetItem, QSizePolicy, QLabel, QGridLayout,  QFrame, QPushButton, QWidget, QListWidget, QMenu, QApplication, QLineEdit, QScrollArea, QHBoxLayout
from PySide6.QtGui import QAction, QCursor, QFont
from PySide6.QtCore import Qt, QSize, QPoint, Signal, QTimer


from ui.text_box_window import TextBoxWindow
from ui.tournament_window import MainTournamentWindow
from ui.session_window import MainSessionWindow
from ui.update_database_windows import DataWindow, MembershipWindow

from utils.utils import check_for_new_players, remove_menu, get_items_from_qlist, clear_layout
from utils.utils_classes import Settings, SessionBuilder, TournamentBuilder, StatisticsBuilder, AdvancedStats, Leaderboard

class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        
        self.config = config
        print(f"settings: {self.config}")

        self.dest = self.config["dest"]
        
        self.scale = config["scale"]
        self.default_font = QFont("Segoe UI", round(self.scale * 18))

        self.setWindowTitle("UoB SaPSoc Pool League Manager")
        self.setMinimumSize(int(1280 * self.scale), int(720 * self.scale))
        
        self.central = QStackedWidget()
        self.setCentralWidget(self.central)
        
        self.main_wid = QWidget()
        self.session_wid = QWidget()
        self.tournament_wid = QWidget()
        self.statistics_wid = QWidget()
        
        self.central.addWidget(self.main_wid)
        self.central.addWidget(self.session_wid)
        self.central.addWidget(self.tournament_wid)
        self.central.addWidget(self.statistics_wid)
        
        self.main_layout = QGridLayout(self.main_wid)
        self.main_session_layout = QGridLayout(self.session_wid)
        self.main_tournament_layout = QGridLayout(self.tournament_wid, alignment=Qt.AlignLeft)
        self.main_statistics_layout = QGridLayout(self.statistics_wid)

        # Create the menu bar
        self.create_menu_bar()

    def create_menu_bar(self):
        self.menu_bar = self.menuBar()  # Built-in QMainWindow menu bar

        # File menu
        self.file_menu = self.menu_bar.addMenu("File")

        # File menu actions
        self.new_session_action = QAction("New Session", self)
        self.new_session_action.triggered.connect(self.on_new_session)
        self.file_menu.addAction(self.new_session_action)

        self.new_tournament_action = QAction("New Tournament", self)
        self.new_tournament_action.triggered.connect(self.on_new_tournament)
        self.file_menu.addAction(self.new_tournament_action)  
        
        self.view_leaderboard = QAction("Leaderboard", self)
        self.view_leaderboard.triggered.connect(self.on_view_leaderboard)
        self.file_menu.addAction(self.view_leaderboard)

        self.open_statistics_action = QAction("Statisctics", self)
        self.open_statistics_action.triggered.connect(self.on_new_statistics)
        self.file_menu.addAction(self.open_statistics_action)

        self.edit_memberships = QAction("Edit Members", self)
        self.edit_memberships.triggered.connect(self.on_edit_memberships)
        self.file_menu.addAction(self.edit_memberships)
        
        self.edit_data = QAction("Edit Data", self)
        self.edit_data.triggered.connect(self.on_edit_data)
        self.file_menu.addAction(self.edit_data)
        
        self.file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)  # Built-in close method
        self.file_menu.addAction(exit_action)
        
        test_action = QAction("Test", self)
        test_action.triggered.connect(self.on_new_session_test)
        self.file_menu.addAction(test_action)

        # View menu
        view_menu = self.menu_bar.addMenu("View")
        
        self.change_scale = QAction("Change Scale", self)
        self.change_scale.triggered.connect(self.on_change_scale)
        view_menu.addAction(self.change_scale)

    def on_new_session_test(self):
        
        self.session_window = MainSessionWindow(dest=self.dest, scale=self.scale)
        
        self.session_window.show()

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

            player_elo = QLabel(f"Elo: {player_obj.elo:.0f}")
            player_elo.setStyleSheet("font-weight: normal;")
            self.stats_container_layout.addWidget(player_elo, 0, 4, alignment=Qt.AlignLeft | Qt.AlignTop)
            
            player_member = QLabel(f"Member: {player_obj.member_displayable}")
            player_member.setStyleSheet("font-weight: normal;")
            self.stats_container_layout.addWidget(player_member, 0, 5, alignment=Qt.AlignLeft | Qt.AlignTop)
            
            # display graphs
            graphs_container = QFrame()
            graphs_container_layout = QGridLayout(graphs_container)
            
            graphs = stats_builder.get_graphs()
            for i, fig in enumerate(graphs):
                canvas = FigureCanvas(fig)
                graphs_container_layout.addWidget(canvas, 0, i, alignment=Qt.AlignLeft)

            self.stats_container_layout.addWidget(graphs_container, 1, 0, 1, 6)

        def on_enter_player():
            setup()

            # text box for entering player name
            self.text_box = TextBoxWindow(scale=self.scale)
            self.text_box.open_at_cursor()
            
            self.text_box.submitted_player.connect(player_recived)
            
            self.text_box.show()

        def on_selected_player(player):
            player_recived(player.text())

        def setup():
            clear_layout(self.main_statistics_layout)

            # left side list of players
            self.players_list_statistics = QListWidget()
            self.players_list_statistics.setFixedWidth(250 * self.scale)
            self.players_list_statistics.setFont(self.default_font)
            self.players_list_statistics.itemClicked.connect(on_selected_player)
            self.main_statistics_layout.addWidget(self.players_list_statistics, 0, 0, alignment=Qt.AlignLeft)
        
            """ ==================================================================================================================================== """
            #players = get_all_players_name(dest=self.dest) 
            #for player in players:
            #    self.players_list_statistics.addItem(player)

            # container for statisitcs
            self.stats_contanier = QWidget()
            self.stats_container_layout = QGridLayout(self.stats_contanier)

            self.main_statistics_layout.addWidget(self.stats_contanier, 0, 1)

        def on_advanced():
            clear_layout(self.main_statistics_layout)

            ad_stats = AdvancedStats()
            
            fig = ad_stats.elo_dist()

            graphs_container = QFrame()
            graphs_container_layout = QGridLayout(graphs_container)
            
            canvas = FigureCanvas(fig)
            
            graphs_container_layout.addWidget(canvas, 0, 0, alignment=Qt.AlignLeft)
            self.main_statistics_layout.addWidget(graphs_container, 0, 0)

        def on_tab_in():
            self.central.setCurrentWidget(self.statistics_wid)
        
        on_tab_in()

        self.open_statistics_action.setDisabled(True)

        self.file_menu = self.menu_bar.addMenu("Statistics")

        self.view = QAction("View", self)
        self.view.triggered.connect(on_tab_in)
        self.file_menu.addAction(self.view)

        self.file_menu.addSeparator()

        self.o_statistics = QAction("Open Statistics", self)
        self.o_statistics.triggered.connect(setup)
        self.file_menu.addAction(self.o_statistics)

        self.enter_player = QAction("Enter Player", self)
        self.enter_player.triggered.connect(on_enter_player)
        self.file_menu.addAction(self.enter_player)

        self.file_menu.addSeparator()

        self.advanced = QAction("Open Advanced Statistics", self)
        self.advanced.triggered.connect(on_advanced)
        self.file_menu.addAction(self.advanced)

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
        L = Leaderboard(self.dest)
        try:
            semester_leaderboard, session_leaderboard, alltime_leaderboard_points_sorted, alltime_leaderboard_elo_sorted = L.collect_leaderboards()
        except Exception as e:
            logger.warning(f"database empty - no leaderboard")
            return

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
        leaderboard_container_layout_sm = QGridLayout(leaderboard_container_sm, alignment=Qt.AlignTop)
        
        leaderboard_container_se = QFrame()
        leaderboard_container_se.setStyleSheet("background-color: #1f1f1f;")
        leaderboard_container_layout_se = QGridLayout(leaderboard_container_se, alignment=Qt.AlignTop)
        
        leaderboard_container_at = QFrame()
        leaderboard_container_at.setStyleSheet("background-color: #1f1f1f;")
        leaderboard_container_layout_at = QGridLayout(leaderboard_container_at, alignment=Qt.AlignTop)
        
        # first call to init the leaderboards
        refresh_leaderboards(semester_leaderboard[-1], session_leaderboard[-1])
        
        # combo boxes
        self.box_to_select_semester = QComboBox()
        for sem in semester_leaderboard:
            title = str(sem[-1][0][1]).split(".")
            print(title)
            
            self.box_to_select_semester.addItem(f"{title[0]}-{title[1]} Semester: {title[2]}", sem[-1][0][0])
            
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
        self.update_membership_window = MembershipWindow(scale=self.scale, dest=self.dest)
        
        self.update_membership_window.show()

    def on_edit_data(self):
        self.update_database_window = DataWindow(sest=self.dest, scale=self.scale)
        
        self.update_database_window.show()

    def on_change_scale(self):

        def change_scale(scale):
            s = int(scale)
            s = s / 100
        
            c = Settings()
            settings = c.load_settings()
            
            settings["scale"] = s
            
            c.save_settings(settings)

        self.scale_window = TextBoxWindow(scale=self.scale)
        self.scale_window.open_at_cursor()
        
        self.scale_window.submitted_player.connect(change_scale)
        
        self.scale_window.show()