import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s -- %(levelname)-8s -- %(name)s -- %(message)s",
)
logger = logging.getLogger(__name__)

import string
import itertools

from PySide6.QtWidgets import QMainWindow, QPlainTextEdit, QSpacerItem, QInputDialog, QListWidgetItem, QSizePolicy, QLabel, QGridLayout,  QFrame, QPushButton, QVBoxLayout, QWidget, QListWidget, QMenu, QApplication, QLineEdit, QScrollArea, QHBoxLayout
from PySide6.QtGui import QAction, QCursor, QFont
from PySide6.QtCore import Qt, QSize, QPoint, Signal, QTimer

from ui.confimation_window import ConfirmationWindow
from ui.setup_windows import TournamentSetupWindow
from ui.custom_widgets import CustomButton, CustomHeaderBar, ConsoleWidget

from utils.utils import check_for_new_players, clear_layout
from utils.utils_classes import IdGen, TournamentBuilder

from resources.colours import DARK, HEAD, PANEL_COL, LINE

class MainTournamentWindow(QMainWindow):
    info = Signal(dict)
    
    def __init__(self, dest, scale=1.0):
        super().__init__()
        
        self.scale = scale
        self.dest = dest

        self.setWindowTitle(f"Tournament")
        self.setMinimumSize(int(1280 * self.scale), int(720 * self.scale))
        self.default_font = QFont("Segoe UI", round(self.scale * 18))
        self.small_font = QFont("Segoe UI", round(self.scale * 12))
        
        central = QWidget()
        self.layout_ = QGridLayout()
        central.setLayout(self.layout_)
        self.setCentralWidget(central)
        
        # top menu
        self.flie_menu = self.menuBar().addMenu("File")
        
        # actions
        self.setup_action = QAction("Setup Tournament")
        self.setup_action.triggered.connect(self.on_setup)
        self.flie_menu.addAction(self.setup_action)
        
        self.confirm_action = QAction("Confirm")
        self.confirm_action.triggered.connect(self.on_confirm_setup)
        self.flie_menu.addAction(self.confirm_action)
        
        self.test_action = QAction("Test")
        self.test_action.triggered.connect(self.on_test)
        self.flie_menu.addAction(self.test_action)
        
        # Create header bar
        def console_panel() -> QWidget:
            self.console = ConsoleWidget()
            self.console.setFont(self.default_font)
            self.console.setMinimumWidth(int(300 * self.scale))
            
            self.console.commandEntered.connect(self.handle_command)

            return self.console
        
        def settings_panel() -> QWidget:
            settings_panel_widget = QWidget()
            self.settings_panel_layout = QVBoxLayout(settings_panel_widget)
            self.settings_panel_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            self.settings_panel_layout.setContentsMargins(10, 10, 10, 10)
            
            return settings_panel_widget
        
        def player_seed_planel() -> QWidget:
            self.players_list_tournament = QListWidget()
            self.players_list_tournament.setFont(self.default_font)
            self.players_list_tournament.setMinimumWidth(int(300 * self.scale))

            return self.players_list_tournament
        
        def game_manager_panel() -> QWidget:
            self.main_game_manager_layout = QVBoxLayout()
            game_manager_panel_widget = QWidget()
            game_manager_panel_widget.setLayout(self.main_game_manager_layout)
            game_manager_panel_widget.setMinimumWidth(int(300 * self.scale))
            
            # init id generator for game manager buttons
            self.gm_id_gen = IdGen()

            return game_manager_panel_widget
        
        def groups_panel() -> QWidget:
            self.main_groups_layout = QGridLayout()
            groups_panel_widget = QWidget()
            groups_panel_widget.setLayout(self.main_groups_layout)
            groups_panel_widget.setMinimumWidth(int(300 * self.scale))
            
            return groups_panel_widget
        
        def tree_panel() -> QWidget:
            self.main_tree_layout = QVBoxLayout()
            tree_panel_widget = QWidget()
            tree_panel_widget.setLayout(self.main_tree_layout)
            tree_panel_widget.setMinimumWidth(int(300 * self.scale))
            
            return tree_panel_widget
        
        PANELS = [
            ("console", "Console", True, console_panel),
            ("settings", "Settings", False, settings_panel),
            ("players", "Player Seeding", True, player_seed_planel),
            ("game_manager", "Game Manager", False, game_manager_panel),
            ("groups", "Groups", False, groups_panel),
            ("tree", "Tournament Tree", False, tree_panel),
        ]

        # Build all panel widgets up-front
        self.panel_widgets: dict[str, QWidget] = {}
        for pid, _, visible, build_fn in PANELS:
            
            w = build_fn()
            w.setStyleSheet(w.styleSheet() + f"""
                QWidget#panel_{pid} {{ background:{PANEL_COL}; }}
            """)
            w.setObjectName(f"panel_{pid}")
            
            # Wrap in a frame so border is easy to style
            frame = QFrame()
            frame.setFrameShape(QFrame.StyledPanel)
            frame.setStyleSheet(f"""
                QFrame {{
                    background:{PANEL_COL};
                    border-right: 1px solid {LINE};
                }}
            """)
            
            fl = QHBoxLayout(frame)
            fl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            fl.setContentsMargins(0, 0, 0, 0)
            fl.addWidget(w)
            
            self.panel_widgets[pid] = frame
            if not visible:
                frame.hide()

        # Header references panel_widgets to toggle visibility
        self.header = CustomHeaderBar(PANELS, self.panel_widgets)
        self.layout_.addWidget(self.header, 0, 0, alignment=Qt.AlignTop | Qt.AlignLeft)

        # Panels sit side-by-side in a horizontal scroll area
        panels_row = QWidget()
        panels_row.setStyleSheet(f"background:{DARK};")
        panels_layout = QHBoxLayout(panels_row)
        panels_layout.setContentsMargins(0, 0, 0, 0)
        panels_layout.setSpacing(0)

        for pid, _, _, _ in PANELS:
            panels_layout.addWidget(self.panel_widgets[pid])

        scroll = QScrollArea()
        scroll.setWidget(panels_row)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border:none; background:{DARK}; }}
            QScrollBar:vertical {{
                background:{HEAD}; width:10px; border-radius:5px;
            }}
            QScrollBar::handle:vertical {{
                background:#555; border-radius:5px; min-height:20px;
            }}
            QScrollBar:horizontal {{
                background:{HEAD}; height:10px;
            }}
            QScrollBar::handle:horizontal {{
                background:#555; border-radius:5px; min-width:20px;
            }}
        """)
        self.layout_.addWidget(scroll, 1, 0)
        

    def handle_command(self, command: str):
        parts = command.split()

        if not parts:
            return

        cmd = parts[0].lower()

        if cmd == "refresh":
            self.update_game_manager()

        elif cmd == "clear":
            self.console.clear()

        elif cmd == "echo":
            text = " ".join(parts[1:])
            self.console.append(text)

        else:
            self.console.append(f"Unknown command: {cmd}")

    """ Called when the configure menu is pressed """
    def on_setup(self):
        # logic for new tournament window
        self.tournament_setup_window = TournamentSetupWindow(dest=self.dest, scale=self.scale)
        self.tournament_setup_window.signal.connect(self.setup_complete)
        
        self.tournament_setup_window.show()
        
        self.setup_action.setDisabled(True)

    """ Called when the tournament setup window sends the players and settings """
    def setup_complete(self,players, settings):

        self.tournament_builder = TournamentBuilder(players, settings)
        self.tournament_builder.define_weight() # calculates seed order
        
        self.settings = settings
        self.players = players
        
        self.setWindowTitle(f"Tournament: {self.settings['title']}")
            
        # add players to the list
        for i, player in enumerate(self.tournament_builder.seed_order):
            self.players_list_tournament.addItem(f"{i + 1} - {player["name"]}")
            
        """ add settings to the settings panel """
        # name
        label = QLabel("Tournament Name:")
        label.setFont(self.small_font)
        self.settings_panel_layout.addWidget(label)
        
        self.tournament_name_input = QLineEdit()
        self.tournament_name_input.setPlaceholderText(self.settings["title"])
        self.tournament_name_input.setFont(self.default_font)
        self.tournament_name_input.setMinimumWidth(int(300 * self.scale))
        def set_title():
            self.setWindowTitle(f"Tournament: {self.tournament_name_input.text()}")
            self.settings["title"] = self.tournament_name_input.text()
        self.tournament_name_input.returnPressed.connect(set_title)
        
        self.settings_panel_layout.addWidget(self.tournament_name_input)

    """ Called when the confirm menu is pressed """
    def on_confirm_setup(self):
        new_players = check_for_new_players(self.players, dest=self.dest)
        if new_players != []:
            
            self.confimation_window = ConfirmationWindow(scale=self.scale, new_players=new_players)
            
            self.confimation_window.signal_to_send.connect(self.players_confirmed)
            
            self.confimation_window.show()
            
        else:
            self.players_confirmed(True)
            
    """ Called when players are confirmed in the confirm window """
    def players_confirmed(self, yesorno):
        if yesorno:
            logger.info("Players confirmed, proceeding")
            
            self.confirm_action.setDisabled(True)
            
            # logic to init tournament or groups depending on settings
            self.game_man_labels = []
            
            self.init_game_manager()
            
            if self.settings["groups"] == None:
                self.init_tournament(self.tournament_builder.player_names)
            else:
                self.init_groups()
            
        else:
            logger.info("Players not confirmed")

    """ Called when a tournament is begun """
    def init_tournament(self, players):
        # set the tree visable
        self.panel_widgets["tree"].setVisible(True)
        self.header.set_panel_visible("tree", True)
        
        initial_round = self.tournament_builder.start_tournament(players)

        #print(initial_round)
        
        crushed_round = self.crush_round(initial_round)
        
        # set up frame
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        self.tree_body = QFrame()
        self.tree_body_layout = QGridLayout(self.tree_body)
        
        self.tree_body_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(self.tree_body)

        letters = string.ascii_lowercase
        possible_player_labels = [''.join(pair) for pair in itertools.product(letters, repeat=2)]
                
        self.player_labels = {}
        for i in range(0, self.tournament_builder.num_rounds):
            self.player_labels[possible_player_labels[i]] = []
            
        #print(f"PLAYER LABELS: {self.player_labels}")
        
        # display tournament      
        for i in range(1, self.tournament_builder.num_rounds + 1):
            
            # labels for above rounds
            if i == self.tournament_builder.num_rounds:
                label = QLabel(f"Final:")
                label.setMinimumWidth(220 * self.scale)
                self.tree_body_layout.addWidget(label, 0, i - 1)
            elif i == self.tournament_builder.num_rounds - 1:
                label = QLabel(f"Semi-final:")
                label.setMinimumWidth(220 * self.scale)
                self.tree_body_layout.addWidget(label, 0, i - 1)
            elif i == self.tournament_builder.num_rounds - 2:
                label = QLabel(f"Quarter-final:")
                label.setMinimumWidth(220 * self.scale)
                self.tree_body_layout.addWidget(label, 0, i - 1)
            else:
                label = QLabel(f"Round {i}:")
                label.setMinimumWidth(220 * self.scale)
                self.tree_body_layout.addWidget(label, 0, i - 1)
            
            # vars to handle spaces
            tick = False
            j_acc = 1
            j_acc2 = 0
            
            size_round = 2 ** (abs(i - self.tournament_builder.num_rounds) + 1)
            
            for j in range(0, size_round):
                
                nj = j + j_acc
                
                if i == 1:
                    player_label = QPushButton(crushed_round[j])
                else:
                    player_label = QPushButton("TBA")
                    
                def rename_button(button):
                    text, ok = QInputDialog.getText(
                    self,
                    "Rename Button",
                    "Enter new button text:"
                    )

                    if ok and text.strip():
                        button.setText(text)
                    
                player_label.clicked.connect(
                    lambda _, b=player_label: rename_button(b)
                )
                    
                self.player_labels[possible_player_labels[i - 1]].append(player_label)
                
                self.tree_body_layout.addWidget(player_label, nj, i - 1)
                
                # logic to add spaces between each game for first round
                if tick and i == 1:
                    space = QFrame()
                    space.setFixedHeight(30 * self.scale)
                    
                    self.tree_body_layout.addWidget(space, nj + 1, i - 1)
                    self.tree_body_layout.addWidget(space, nj + 2, i - 1)
                    j_acc += 2
                    tick = False
                else:
                    tick = True
                    
                # logic for other rounds
                if i != 1:        
                    if not j % 2: # even
                        j_acc2 = 2**i - 2 + (2**i - 1) * j # maths to correctly layout games
                    
                    self.tree_body_layout.addWidget(player_label, (j + j_acc2 + 1), i - 1)
                
        self.tournament_builder.player_labels = self.player_labels        
        
        self.main_tree_layout.addWidget(scroll)
        self.update_game_manager(round_type="normal", match_format=self.settings["match_format"]["normal"])
            
    """ Used to format the round list """
    def crush_round(self, round) -> list[str]:
        """ takes in a round in the format [[player1, player2], [player3, player4]] and crushes it to [player1, player2, player3, player4] """
        n_round = []
        
        for match in round:
            n_round.append(match[0])
            n_round.append(match[1])
            
        return n_round

    """ Called when a group stage is begun """
    def init_groups(self):
        self.panel_widgets["groups"].setVisible(True)
        self.header.set_panel_visible("groups", True)
        
        self.tournament_builder.start_groups()
        
        self.update_groups()
        
    """ Called to update the group stage display with current groups and players """
    def update_groups(self):
        
        def add_win(button):
            c = button.text()
            button.setText(str(int(c) + 1))
            
        def remove_win(button):
            c = button.text()
            button.setText(str(int(c) - 1))
        
        try:
            self.main_groups_layout.removeWidget(self.group_body)
            self.group_body.deleteLater()
        except AttributeError:
            pass
        
        # set up frame
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        self.group_body = QFrame()
        self.group_body_layout = QGridLayout(self.group_body, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(self.group_body)
        
        MAX_COLS = 4
        for i, group in enumerate(self.tournament_builder.groups):
            frame = QFrame()
            frame.setFrameShape(QFrame.StyledPanel)
            frame.setStyleSheet(f"""
                QFrame {{
                    background:{PANEL_COL};
                    border:1px solid {LINE};
                    border-radius:5px;
                }}
            """)
            
            fl = QGridLayout(frame)
            fl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            fl.setContentsMargins(10, 10, 10, 10)
            fl.setSpacing(5)
            
            label = QLabel(f"{group}")
            label.setFont(self.default_font)
            fl.addWidget(label, 0, 0, 1, 2)
            
            for player in self.tournament_builder.groups[group]:
                name = QLabel(player[0]["name"])
                name.setFont(self.default_font)
                score_button = CustomButton(str(player[1]))
                
                score_button.normalClick.connect(lambda button=score_button: add_win(button))
                score_button.shiftClick.connect(lambda button=score_button: remove_win(button))
                
                score_button.setFont(self.default_font)
                
                fl.addWidget(name, list(self.tournament_builder.groups[group]).index(player) + 1, 0)
                fl.addWidget(score_button, list(self.tournament_builder.groups[group]).index(player) + 1, 1)
                
            row = i // MAX_COLS
            col = i % MAX_COLS

            self.group_body_layout.addWidget(frame, row, col)
            
        self.main_groups_layout.addWidget(scroll, 0, 0)
        self.update_game_manager(round_type="group", match_format=self.settings["groups"]["format"])
        
    def on_test(self):
        logger.info("Test button pressed")
        print(self.tournament_builder.groups)
        
    def init_game_manager(self):
        self.panel_widgets["game_manager"].setVisible(True)
        self.header.set_panel_visible("game_manager", True)
        
        self.gamem_scroll = QScrollArea()
        self.gamem_scroll.setWidgetResizable(True)
        
        self.game_manager_body = QFrame()
        self.game_manager_layout = QVBoxLayout(self.game_manager_body)
        self.game_manager_body.setStyleSheet(f"""
            QFrame {{
                background:{PANEL_COL};
            }}
        """)
        
        self.gamem_scroll.setWidget(self.game_manager_body)
            
        self.main_game_manager_layout.addWidget(self.gamem_scroll)
        self.gamem_scroll.verticalScrollBar().setValue(self.gamem_scroll.verticalScrollBar().minimum())
        
    def update_game_manager(self, round_type, match_format=1):
        clear_layout(self.game_manager_layout)
        
        print(f"ROUND TYPE: {round_type}")
        
        for match in self.tournament_builder.rounds:
            
            frame = QFrame()
            frame.setFrameShape(QFrame.StyledPanel)
            frame.setStyleSheet(f"""
                QFrame {{
                    background:{PANEL_COL};
                    border:1px solid {LINE};
                    border-radius:5px;
                }}
            """)
            
            fl = QGridLayout(frame)
            fl.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
            fl.setContentsMargins(10, 10, 10, 10)
            fl.setSpacing(5)
            
            label = QLabel(f"{match[0]} vs {match[1]}")
            label.setFont(self.default_font)
            fl.addWidget(label, 0, 0, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)
            
            label = QLabel(f"First to {match_format}")
            label.setFont(self.small_font)
            fl.addWidget(label, 1, 0, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)
            
            s1 = QLabel("0")
            s2 = QLabel("0")
            
            self.game_man_labels.append((s1, s2))
            
            fl.addWidget(s1, 2, 0, alignment=Qt.AlignmentFlag.AlignLeft)
            fl.addWidget(s2, 2, 1, alignment=Qt.AlignmentFlag.AlignRight)
            
            us1 = CustomButton("Player 1 +")
            us2 = CustomButton("Player 2 +")
            id1 = self.gm_id_gen.generate()
            id2 = self.gm_id_gen.generate()
            
            us1.normalClick.connect(lambda loc=(id1, (match[0], match[1]), round_type, match_format): self.add_win_gamem(loc))
            us2.normalClick.connect(lambda loc=(id2, (match[1], match[0]), round_type, match_format): self.add_win_gamem(loc))
            us1.shiftClick.connect(lambda loc=(id1,): self.rem_win_gamem(loc))
            us2.shiftClick.connect(lambda loc=(id2,): self.rem_win_gamem(loc))
            
            fl.addWidget(us1, 3, 0, alignment=Qt.AlignmentFlag.AlignLeft)
            fl.addWidget(us2, 3, 1, alignment=Qt.AlignmentFlag.AlignRight)
            
            self.game_manager_layout.addWidget(frame)
            
        self.gamem_scroll.verticalScrollBar().setValue(self.gamem_scroll.verticalScrollBar().minimum())
        
    def add_win_gamem(self, loc: tuple):
        
        player_label0 = self.game_man_labels[loc[0] // 2][0]
        player_label1 = self.game_man_labels[loc[0] // 2][1]
        
        if loc[0] % 2 == 0:
            i = int(player_label0.text())
            player_label0.setText(str(i + 1))
        else:
            i = int(player_label1.text())
            player_label1.setText(str(i + 1))
            
        player_score0 = int(self.game_man_labels[loc[0] // 2][0].text())
        player_score1 = int(self.game_man_labels[loc[0] // 2][1].text())
    
        if player_score0 == loc[3]:
            print(f"player: {loc[1][0]} won best of {loc[3]} with  {player_score0} games won")
            
            # removes finished match from the list
            match_to_remove = (loc[1][0], loc[1][1])  
            for i, p in enumerate(self.tournament_builder.rounds):
                if set(p) == set(match_to_remove):
                    del self.tournament_builder.rounds[i]
                    break
            
            self.console.append(f"{loc[1][0]} - {loc[1][1]}: {player_score0} - {player_score1}")
            self.update_game_manager(round_type=loc[2], match_format=loc[3])
            
        if player_score1 == loc[3]:
            print(f"player: {loc[1][0]} won best of {loc[3]} with  {player_score1} games won")

            # removes finished match from the list
            match_to_remove = (loc[1][0], loc[1][1])  
            for i, p in enumerate(self.tournament_builder.rounds):
                if set(p) == set(match_to_remove):
                    del self.tournament_builder.rounds[i]
                    break            

            self.console.append(f"{loc[1][0]} - {loc[1][1]}: {player_score1} - {player_score0}")
            self.update_game_manager(round_type=loc[2], match_format=loc[3])
            
    def rem_win_gamem(self, loc: tuple):
        
        if loc[0] % 2 == 0:
            i = int(self.game_man_labels[loc[0] // 2][0].text())
            self.game_man_labels[loc[0] // 2][0].setText(str(i - 1))
        else:
            i = int(self.game_man_labels[loc[0] // 2][1].text())
            self.game_man_labels[loc[0] // 2][1].setText(str(i - 1))