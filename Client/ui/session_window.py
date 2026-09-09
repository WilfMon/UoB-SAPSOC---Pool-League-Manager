import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s -- %(levelname)-8s -- %(name)s -- %(message)s",
)
logger = logging.getLogger(__name__)

import datetime

from PySide6.QtWidgets import QMainWindow, QPlainTextEdit, QSpacerItem, QInputDialog, QMessageBox, QListWidgetItem, QSizePolicy, QLabel, QGridLayout,  QFrame, QPushButton, QVBoxLayout, QWidget, QListWidget, QMenu, QApplication, QLineEdit, QScrollArea, QHBoxLayout, QSplitter, QComboBox, QSpinBox, QSlider, QRadioButton, QButtonGroup
from PySide6.QtGui import QAction, QCursor, QFont, QCloseEvent
from PySide6.QtCore import Qt, QSize, QPoint, Signal, QTimer

from .confimation_window import ConfirmationWindow

from ui.custom_widgets import CustomButton, CustomHeaderBar, ConsoleWidget

from utils.utils import clean_name, clear_grid_after_row, get_items_from_qlist, remove_item_from_qlist, calc_elo_change
from utils.utils_classes import SessionBuilder

from DB.db import (
                    get_connection, list_active_players, get_pid_from_name, get_player, create_round, get_match, get_name_from_pid, delete_round, get_round_id, get_session, list_all_semesters,
                   create_semester, create_session, list_all_players, add_player, record_match, delete_match, get_match_id, listen, get_rounds_in_session, delete_session, up_session_status, update_player_active,
                   get_semester_standings, get_alltime_standings,
                   ACTIONS
                   )

from resources.colours import DARK, HEAD, PANEL_COL, LINE, TEXT, ACCENT, GREEN, RED, CUE_WHITE
from resources.stylesheets import _scrollbar_stylesheet, _title_text_stylesheet, _normal_text_stylesheet

class MainSessionWindow(QMainWindow):
    info = Signal(dict)
    
    def __init__(self, config):
        super().__init__()
        
        self.exit_code = None
        logger.info(f"Session Window Running...")
        
        self.config = config
        self.scale = config["scale"]

        WIDTH = int(1960 * self.scale)
        HEIGHT = int(1080 * self.scale)

        self.setWindowTitle(f"Session")
        self.setMinimumSize(WIDTH, HEIGHT)
        self.default_font = QFont("Segoe UI", round(self.scale * 18))
        self.small_font = QFont("Segoe UI", round(self.scale * 12))
        
        central = QWidget()
        self.layout_ = QGridLayout()
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.setSpacing(0)
        central.setLayout(self.layout_)
        self.setCentralWidget(central)
        
        # top menu
        self.file_menu = self.menuBar().addMenu("File")
        
        self.file_menu.addAction(QAction("Exit", self, triggered=lambda: self.close()))
        
        # create semester if it already dosent exist
        date_time = datetime.datetime.now()
        self.date = date_time.strftime("%d") + "." + date_time.strftime("%m") + "." + date_time.strftime("%Y") # 01.01.2000 first jan 2000
        self.year = date_time.strftime("%Y")
        self.month = int(date_time.strftime("%m"))
        
        self.conn = get_connection()
        
        self.save = False
        
        # automatically determine semester and year
        if 9 <= self.month <= 12:
            sem_name = f"{int(self.year)}.{int(self.year) + 1}.1"
            
            self.semester_id = create_semester(self.conn, sem_name, self.date)

        if 1 <= self.month <= 8:
            sem_name = f"{int(self.year) - 1}.{self.year}.2"
            
            self.semester_id = create_semester(self.conn, sem_name, self.date)

        logger.info(f"Semester set to: {sem_name}")
        
        # Create header bar
        def console_panel() -> QWidget:
            self.console = ConsoleWidget()
            self.console.setFont(self.small_font)
            
            self.console.setMinimumWidth(int(200 * self.scale))
            self.console.setStyleSheet(_normal_text_stylesheet(self.scale))
            
            self.console.commandEntered.connect(self.handle_command)

            return self.console
        
        def players_panel() -> QWidget:
            self.players_list_seed = QListWidget()
            self.players_list_seed.setFont(self.small_font)
            self.players_list_seed.setStyleSheet(f"color: {TEXT};")
            
            self.players_list_seed.setMinimumWidth(int(180 * self.scale))
            
            def refresh_players_list():
                
                self.players_list_seed.blockSignals(True)
                self.players_list_seed.model().blockSignals(True)
                
                players = get_items_from_qlist(self.players_list_seed)
                
                self.players_list_seed.clear()

                # sort players
                
                for player in players:
                    self.players_list_seed.addItem(player)
                    
                self.players_list_seed.blockSignals(False)
                self.players_list_seed.model().blockSignals(False)
            
            self.players_list_seed.model().rowsInserted.connect(refresh_players_list)
            self.players_list_seed.model().rowsRemoved.connect(refresh_players_list)

            return self.players_list_seed
        
        def leaderboard_panel() -> QScrollArea:
            self.leaderboard_widget = QWidget()
            self.lb_wid_layout = QGridLayout()
            self.leaderboard_widget.setLayout(self.lb_wid_layout)
            
            self.leaderboard_widget.setStyleSheet(f"""
                QFrame {{
                    background: {PANEL_COL};
                    border-radius: 5px;
                }}
            """)
            
            self.lb_wid_layout.setContentsMargins(8, 8, 8, 8)
            self.lb_wid_layout.setSpacing(8)
            
            scroll_area = QScrollArea()
            scroll_area.setWidget(self.leaderboard_widget)
            scroll_area.setWidgetResizable(True)  # Allows the inner widget to resize smoothly
            scroll_area.viewport().setStyleSheet("background: transparent;")
            
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            
            scroll_area.setMinimumWidth(int(450 * self.scale))
            
            # combobox setup
            label = QLabel("Leaderboard".upper())
            label.setFont(self.small_font)
            label.setStyleSheet(_title_text_stylesheet())
            self.lb_wid_layout.addWidget(label, 0, 0, 1, 2)
            
            self.lb_box = QComboBox()
            self.lb_box.setFont(self.small_font)
            self.lb_box.setStyleSheet("""
                                color: {TEXT};
                                font-weight: 500;
                                letter-spacing: 1px;
                                padding-left: 2px;
                            """)
            
            self.lb_box.currentIndexChanged.connect(self.update_leaderboard)
            
            self.lb_box.addItem("Active", (get_alltime_standings, (self.conn, True)))
            self.lb_box.addItem("Alltime", (get_alltime_standings, (self.conn, False)))
            
            semesters, sem_ids = list_all_semesters(self.conn)
            for _id in sem_ids:
                for sem in semesters:
                    if sem["semester_id"] == _id:
                        break
                
                self.lb_box.addItem(f"- {sem["display_name"]}", (get_semester_standings, (self.conn, _id)))
                
            self.lb_wid_layout.addWidget(self.lb_box, 0, 2, 1, 2)

            self.update_leaderboard()

            return scroll_area          
        
        def player_manager_panel() -> QWidget:
            
            def submit_text_selected(player):
                
                text = clean_name(player.text())

                item = self.selected_players_list.findItems(text, Qt.MatchExactly)
                
                # check if text is aleady submitted
                if not item:

                    text = QListWidgetItem(text)
                    self.selected_players_list.addItem(text)
                
                else: 
                    logger.warning(f"Player: {text} already submitted")

            def submit_text_typed():
                text = self.input_box.text()
                
                text = clean_name(text)
                
                if text == "":
                    logger.warning("No valid name submitted")
                    return
                
                text = QListWidgetItem(text)
                #text.setSizeHint(QSize(0, 18))
                self.selected_players_list.addItem(text)

                self.input_box.clear()
                
            def show_context_menu(position: QPoint):
                # Get the item under the cursor
                item = self.selected_players_list.itemAt(position)
                if item is None:
                    return  # clicked empty space

                # Create context menu
                menu = QMenu()
                remove_action = menu.addAction("Remove")
                
                # Show menu and wait for user selection
                action = menu.exec(self.selected_players_list.mapToGlobal(position))
                
                if action == remove_action:
                    i = self.selected_players_list.row(item)
                    self.selected_players_list.takeItem(i)
                    
            def clear_selection():
                
                self.selected_players_list.clear()

            def add():
                
                def add_after_check(yes_no):
                    if yes_no:
                        players = confim_wind.stored_players
                        possible_selections = get_items_from_qlist(self.selection_list)
                        
                        for p in players:
                            fn, ln = p.split(" ")
                            
                            add_player(self.conn, fn, ln)
                            
                            # update the selection list with these new players
                            if p not in possible_selections:
                                self.selection_list.addItem(p)
                        
                        add_players_to_seed(players)
                    
                def add_players_to_seed(players):
                    for player in players:
                        matches = self.players_list_seed.findItems(player, Qt.MatchFlag.MatchExactly)
                        
                        if not matches:
                            self.players_list_seed.addItem(player)
                
                participants = get_items_from_qlist(self.selected_players_list)
                
                players = list_all_players(self.conn)
                players_names = []
                new_players = []
                
                for p in players:
                    players_names.append(f"{p["first_name"]} {p["last_name"]}")
                    
                if (set(participants) - set(players_names)):
                    new_players = list(set(participants) - set(players_names))
                
                if new_players != []:
                    confim_wind = ConfirmationWindow(self.scale, new_players)
                    confim_wind.info(participants)
                    confim_wind.signal_to_send.connect(add_after_check)
                    confim_wind.show()
                
                else:
                    add_players_to_seed(participants)
                    
            def remove():
                participants = get_items_from_qlist(self.selected_players_list)
                
                for player in participants:
                    remove_item_from_qlist(self.players_list_seed, player)
            
            self.player_manager_layout = QGridLayout()
            player_manager_panel_widget = QWidget()
            player_manager_panel_widget.setLayout(self.player_manager_layout)
            
            player_manager_panel_widget.setMinimumWidth(int(420 * self.scale))

            label_text_box = QLabel("Enter Players:".upper())
            label_text_box.setFont(self.small_font)
            label_text_box.setStyleSheet(_title_text_stylesheet())
            label_text_box.setFixedSize(label_text_box.sizeHint())
            self.player_manager_layout.addWidget(label_text_box, 0, 0)

            self.input_box = QLineEdit()
            self.player_manager_layout.addWidget(self.input_box, 1, 0, alignment=Qt.AlignTop)
            self.input_box.returnPressed.connect(submit_text_typed)

            label_text_box = QLabel("Select Players:".upper())
            label_text_box.setFont(self.small_font)
            label_text_box.setStyleSheet(_title_text_stylesheet())
            label_text_box.setFixedSize(label_text_box.sizeHint())
            self.player_manager_layout.addWidget(label_text_box, 2, 0)
            
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: {HEAD};
                    border-radius: 5px;
                }}
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(8, 4, 0, 4)
            card_layout.setSpacing(0)
            
            self.selection_list = QListWidget()
            self.selection_list.setFont(self.small_font)
            self.selection_list.setStyleSheet(_scrollbar_stylesheet(bg=HEAD))
            self.selection_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
            self.selection_list.itemClicked.connect(submit_text_selected)
            card_layout.addWidget(self.selection_list)
            self.player_manager_layout.addWidget(card, 3, 0)


            active_players = list_active_players(self.conn)
            
            for player in active_players:
                
                name = f"{player["first_name"]} {player["last_name"]}"
                self.selection_list.addItem(name)

            label_text_box = QLabel("Players Selected:".upper())
            label_text_box.setFont(self.small_font)
            label_text_box.setStyleSheet(_title_text_stylesheet())
            label_text_box.setFixedSize(label_text_box.sizeHint())
            self.player_manager_layout.addWidget(label_text_box, 0, 1, 1, 2)

            card2 = QFrame()
            card2.setStyleSheet(f"""
                QFrame {{
                    background: {HEAD};
                    border-radius: 5px;
                }}
            """)
            card2_layout = QVBoxLayout(card2)
            card2_layout.setContentsMargins(8, 4, 0, 4)
            card2_layout.setSpacing(0)

            self.selected_players_list = QListWidget()
            self.selected_players_list.setFont(self.small_font)
            self.selected_players_list.setStyleSheet(_scrollbar_stylesheet(bg=HEAD))
            self.selected_players_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
            card2_layout.addWidget(self.selected_players_list)
            self.player_manager_layout.addWidget(card2, 1, 1, 3, 2)
            self.selected_players_list.setContextMenuPolicy(Qt.CustomContextMenu)
            self.selected_players_list.customContextMenuRequested.connect(show_context_menu)
            
            button_clear = QPushButton("Clear".upper())
            button_clear.setFont(self.small_font)
            button_clear.adjustSize()
            button_clear.clicked.connect(clear_selection)
            self.player_manager_layout.addWidget(button_clear, 4, 0, alignment=Qt.AlignLeft)
            
            self.button_remove = QPushButton("Remove".upper())
            self.button_remove.setFont(self.small_font)
            self.button_remove.adjustSize()
            self.button_remove.clicked.connect(remove)
            self.player_manager_layout.addWidget(self.button_remove, 4, 1, alignment=Qt.AlignLeft)
            
            self.button_add = QPushButton("Add".upper())
            self.button_add.setFont(self.small_font)
            self.button_add.adjustSize()
            self.button_add.clicked.connect(add)
            self.player_manager_layout.addWidget(self.button_add, 4, 2, alignment=Qt.AlignRight)
            
            return player_manager_panel_widget
        
        def game_manager_panel() -> QWidget:
            
            # ---------------------------------------------------------------
            # Helper Functions
            # ---------------------------------------------------------------
            
            def _pad(pxl) -> str:
                return f"padding: {pxl}px {pxl*2}px {pxl}px {pxl*2}px;"
            
            def _fetch_elo_label(pos: tuple) -> QLabel:
                return self.session_items[pos[0]][pos[1]][f"p{pos[2] + 1}_elo_label"]
            
            def _calc_new_elo_for_labels(main: QLabel, other: QLabel) -> tuple[str, str]:
                a = main.property("elo_change")
                a_elo = a[0]["current_elo"]
                
                b = other.property("elo_change")
                b_elo = b[0]["current_elo"]
                
                return (f"{a_elo:.0f} --> {a_elo + a[1]:.0f}", f"{b_elo:.0f} --> {b_elo - b[2]:.0f}")
            
            # ---------------------------------------------------------------
            # Functions to control the buttons
            # ---------------------------------------------------------------
            
            def on_normal_click(btns):
                """Update button states to show the game has been resolved; also update the database"""
                
                main, other = btns
                # check if the button has already been normal clicked and return if so
                if main.clicked or other.clicked:
                    print("already clicked")
                    return
                
                main.setStyleSheet(f"border-radius: 3px; background-color: {GREEN}; {_pad(4)}")
                other.setStyleSheet(f"border-radius: 3px; background-color: {RED}; {_pad(4)}")
                
                main_elo = _fetch_elo_label(main.position)
                other_elo = _fetch_elo_label(other.position)
                
                main_elo.setStyleSheet(f"background:transparent; font-size:{14 * self.scale}px; color:{GREEN}")
                other_elo.setStyleSheet(f"background:transparent; font-size:{14 * self.scale}px; color:{RED}")
                
                new_m, new_o = _calc_new_elo_for_labels(main_elo, other_elo)
                
                round_id = main.round_id
                
                # find player ids
                p1_id = main_elo.property("elo_change")[0]["player_id"]
                p2_id = other_elo.property("elo_change")[0]["player_id"]
                
                # database updates
                record_match(self.conn, round_id, p1_id, p2_id, p1_id)
                
                refresh_session_items()
                self.update_leaderboard()
                
                main_elo.setText(new_m)
                other_elo.setText(new_o)
                
                main.clicked = True
                other.clicked = True
                
            def on_shift_click(btns):
                """Revert button states to how they were before they were clicked; also revert match to unplayed in the database"""
                
                main, other = btns
                # check if the button has already been shift clicked and return if so
                if not main.clicked:
                    print("already not clicked")
                    return
                
                main.setStyleSheet(f"border-radius: 3px; background-color: {CUE_WHITE}; {_pad(4)}")
                other.setStyleSheet(f"border-radius: 3px; background-color: {CUE_WHITE}; {_pad(4)}")
                
                main_elo = _fetch_elo_label(main.position)
                other_elo = _fetch_elo_label(other.position)
                
                main_elo.setStyleSheet(f"background:transparent; font-size:{14 * self.scale}px; color:{TEXT}")
                other_elo.setStyleSheet(f"background:transparent; font-size:{14 * self.scale}px; color:{TEXT}")
                
                p1_elo = main_elo.property("elo_change")
                main_elo.setText(f"{p1_elo[0]["current_elo"]:.0f} + {p1_elo[1]:.0f}, - {p1_elo[2]:.0f}")
                
                p2_elo = other_elo.property("elo_change")
                other_elo.setText(f"{p2_elo[0]["current_elo"]:.0f} + {p2_elo[1]:.0f}, - {p2_elo[2]:.0f}")
                
                round_id = main.round_id
                
                # find player ids
                p1_id = main_elo.property("elo_change")[0]["player_id"]
                p2_id = other_elo.property("elo_change")[0]["player_id"]
                
                # database updates
                match_id = get_match_id(self.conn, p1_id, p2_id, round_id)
                if match_id == None:
                    match_id = get_match_id(self.conn, p2_id, p1_id, round_id)
                
                delete_match(self.conn, match_id)
                
                main.clicked = False
                other.clicked = False
                refresh_session_items()
                self.update_leaderboard()
            
            def refresh_session_items():
                """Updates the session elo labels with potentially new database updates"""
                
                for _round in self.session_items:
                    for row in _round:
                        # retrive old elo
                        p1_old = row["p1_elo_label"].property("elo_change")[0]
                        p2_old = row["p2_elo_label"].property("elo_change")[0]
                        
                        # find new elo and elo change
                        p1_new = get_player(self.conn, p1_old["player_id"])
                        p2_new = get_player(self.conn, p2_old["player_id"])
                        
                        p_change1, _ = calc_elo_change(p1_new["current_elo"], p2_new["current_elo"])
                        p_change2, _ = calc_elo_change(p2_new["current_elo"], p1_new["current_elo"])
                        p_change1 = abs(p_change1)
                        p_change2 = abs(p_change2)
                        
                        # update stored info
                        row["p1_elo_label"].setProperty("elo_change", (p1_new, p_change1, p_change2))
                        row["p2_elo_label"].setProperty("elo_change", (p2_new, p_change2, p_change1))
                        
                        if not row["p1_button"].clicked or not row["p1_button"].clicked:
                            
                            # update display text
                            row["p1_elo_label"].setText(f"{p1_new["current_elo"]:.0f} + {p_change1:.0f}, - {p_change2:.0f}")
                            row["p2_elo_label"].setText(f"{p2_new["current_elo"]:.0f} + {p_change2:.0f}, - {p_change1:.0f}")
            
            # ---------------------------------------------------------------
            # Functions to build the UI
            # ---------------------------------------------------------------
            
            def _round_header(text: str) -> QLabel:
                lbl = QLabel(text.upper())
                lbl.setFont(self.small_font)
                lbl.setStyleSheet(_title_text_stylesheet())
                return lbl
            
            def _round_card():
                """Creates the container for round pairings, returns widget and layout"""
                card = QFrame()
                card.setStyleSheet(f"""
                    QFrame {{
                        background: {PANEL_COL};
                        border-radius: 5px;
                    }}
                """)
                card_layout = QGridLayout(card)
                card_layout.setContentsMargins(8, 8, 8, 8)
                card_layout.setSpacing(8)
                
                return card, card_layout
            
            def _round_row(layout, vert_offset, left: str, right: str, p1_elo: str, p2_elo: str, round_id: int) -> QWidget:

                left_btn = CustomButton()
                left_btn.setText(left)
                left_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                left_btn.normalClick.connect(on_normal_click)
                left_btn.shiftClick.connect(on_shift_click)
                left_btn.setStyleSheet(f"border-radius: 3px; background-color: {CUE_WHITE}; {_pad(4)}")
                
                right_btn = CustomButton()
                right_btn.setText(right)
                right_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                right_btn.normalClick.connect(on_normal_click)
                right_btn.shiftClick.connect(on_shift_click)
                right_btn.setStyleSheet(f"border-radius: 3px; background-color: {CUE_WHITE}; {_pad(4)}")

                left_btn.info((left_btn, right_btn), (self.round_number, vert_offset // 3, 0), round_id)
                right_btn.info((right_btn, left_btn), (self.round_number, vert_offset // 3, 1), round_id)

                # Center the VS label
                vs_lbl = QLabel("v")
                vs_lbl.setStyleSheet("background: transparent;")
                
                layout.addWidget(left_btn, vert_offset, 0)
                layout.addWidget(vs_lbl, vert_offset, 1, alignment=Qt.AlignCenter)
                layout.addWidget(right_btn, vert_offset, 2)

                # Rounded float formatting for ELO labels
                p1_elo_lbl = QLabel(f"{p1_elo[0]["current_elo"]:.0f} + {p1_elo[1]:.0f}, - {p1_elo[2]:.0f}")
                p1_elo_lbl.setProperty("elo_change", p1_elo)
                p1_elo_lbl.setStyleSheet(f"background:transparent; font-size:{14 * self.scale}px; color:{TEXT}")
                layout.addWidget(p1_elo_lbl, vert_offset + 1, 0, alignment=Qt.AlignLeft)
                
                p2_elo_lbl = QLabel(f"{p2_elo[0]["current_elo"]:.0f} + {p2_elo[1]:.0f}, - {p2_elo[2]:.0f}")
                p2_elo_lbl.setProperty("elo_change", p2_elo)
                p2_elo_lbl.setStyleSheet(f"background:transparent; font-size:{14 * self.scale}px; color:{TEXT}")
                layout.addWidget(p2_elo_lbl, vert_offset + 1, 2, alignment=Qt.AlignLeft)
                
                self.session_items[self.round_number].append({"p1_button": left_btn, "p2_button": right_btn, "p1_elo_label": p1_elo_lbl, "p2_elo_label": p2_elo_lbl})
                
            def _round_spacer(layout, vert_offset):
                """Adds a spacer to the round container"""
                spacer = QFrame()
                spacer.setFrameShape(QFrame.HLine)
                spacer.setFrameShadow(QFrame.Sunken)
                spacer.setStyleSheet(f"background-color: {LINE}; max-height: 3px; border: none;")
                
                layout.addWidget(spacer, vert_offset, 0, 1, 3)
            
            def round_bye_row(layout, vert_offset, bye: str) -> QWidget:
                """Adds the last row to the round container for the bye"""
                bye_lbl = QLabel(f"Bye: {bye}")
                bye_lbl.setStyleSheet(f"color:{TEXT}; background:transparent; font-size:12px; font-weight:600;")
                
                layout.addWidget(bye_lbl, vert_offset, 0)
            
            # ---------------------------------------------------------------
            # Functions to control rounds
            # ---------------------------------------------------------------
            
            def add_new_round(layout: QGridLayout, round_to_rebuild=None):
                """
                Adds a new round to the game manager panel.
                Accepts round_to_rebuild so that an exact copy of a previous round can be refreshed to update the UI.
                """
                
                if round_to_rebuild is None:
                    # Get players from seed and update the builder
                    players_names = get_items_from_qlist(self.players_list_seed)
                    self.builder.update_players(players_names)
                    
                    # Start a new row for a new round
                    self.session_items.append([])
                    round_, bye = self.builder.create_round()
                else:
                    round_, bye = round_to_rebuild

                col = self.round_number

                header = _round_header(f"ROUND: {self.round_number + 1}")
                layout.addWidget(header, 0, col, alignment=Qt.AlignTop | Qt.AlignLeft)

                card, card_layout = _round_card()
                layout.addWidget(card, 1, col, alignment=Qt.AlignTop | Qt.AlignLeft)

                layout.setColumnStretch(col, 0)
                layout.setColumnStretch(col + 1, 1)

                round_id = create_round(self.conn, self.session_id, self.round_number)

                vert_offset = 0
                for idx, match in enumerate(round_):
                    vert_offset = idx * 3

                    fn1, ln1 = match[0].split(" ")
                    p1 = get_player(self.conn, get_pid_from_name(self.conn, fn1.strip(), ln1.strip()))

                    fn2, ln2 = match[1].split(" ")
                    p2 = get_player(self.conn, get_pid_from_name(self.conn, fn2.strip(), ln2.strip()))

                    p_change1, _ = calc_elo_change(p1["current_elo"], p2["current_elo"])
                    p_change2, _ = calc_elo_change(p2["current_elo"], p1["current_elo"])

                    p_change1 = abs(p_change1)
                    p_change2 = abs(p_change2)

                    _round_row(card_layout, vert_offset, match[0], match[1], (p1, p_change1, p_change2), (p2, p_change2, p_change1), round_id)
                    _round_spacer(card_layout, vert_offset + 2)

                if bye is None:
                    bye = "Na"

                # Fixed: Use vert_offset + 3 (next available row) instead of i * 3
                round_bye_row(card_layout, vert_offset + 3, bye)

                # 3. Standardize layout row height constraints
                card_layout.setRowStretch(vert_offset + 4, 1)  # Pushes internal rows upward cleanly

                self.round_number += 1
                
                edges, nodes = self.builder.estimate_rounds_left()
                self.console.append(f"Edges: {edges}, Nodes: {nodes}")
                return card_layout
                
            def remove_last_round(layout: QGridLayout, col: int):
                
                for row in range(layout.rowCount()):
                    item = layout.itemAtPosition(row, col)
                    
                    if item is not None:
                        widget = item.widget()
                        if widget is not None:
                            # Remove widget visually and queue it for deletion
                            widget.setParent(None)
                            widget.deleteLater()
                        else:
                            # If the item was a nested layout or spacer, remove it from layout
                            layout.removeItem(item)
                
                round_id = get_round_id(self.conn, self.session_id, col)
                delete_round(self.conn, round_id)
                
                self.builder.remove_round()
                
                self.round_number -= 1
                
            self.action_menu = self.menuBar().addMenu("Action")
            self.add_round_action = QAction("Add Round", self, triggered=lambda: add_new_round(self.main_game_manager_layout))
            self.remove_round_action = QAction("Remove Round", self, triggered=lambda: remove_last_round(self.main_game_manager_layout, self.round_number - 1))
            self.action_menu.addAction(self.add_round_action)
            self.action_menu.addAction(self.remove_round_action)
                
            self.main_game_manager_layout = QGridLayout()
            self.main_game_manager_layout.setSpacing(12)  # Controls horizontal distance between round columns
            self.main_game_manager_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            
            game_manager_panel_widget = QWidget()
            game_manager_panel_widget.setLayout(self.main_game_manager_layout)

            game_manager_panel_scoll_area = QScrollArea()
            game_manager_panel_scoll_area.setWidget(game_manager_panel_widget)
            game_manager_panel_scoll_area.setWidgetResizable(True)
            game_manager_panel_scoll_area.setMinimumWidth(int(200 * self.scale))
            game_manager_panel_scoll_area.viewport().setStyleSheet("background: transparent;")
            
            self.round_number = 0
            
            self.finished_games = [] # martix
            self.session_items = [] # matrix
                
            self.builder = SessionBuilder()
            
            self.session_id = create_session(self.conn, self.semester_id, self.date, [])

            return game_manager_panel_scoll_area
        
        self.PANELS = [
            ("console", "Console", True, console_panel),
            ("players", "Players in Session", True, players_panel),
            ("leaderboard", "Leaderboard", True, leaderboard_panel),
            ("player_manager", "Player Manager", True, player_manager_panel),
            ("game_manager", "Game Manager", True, game_manager_panel),
        ]

        # Build all panel widgets up-front
        self.panel_widgets: dict[str, QWidget] = {}
        for pid, _, visible, build_fn in self.PANELS:
            
            w = build_fn()
            w.setStyleSheet(w.styleSheet() + f"""
                QWidget#panel_{pid} {{ background:{DARK}; }}
            """)
            w.setObjectName(f"panel_{pid}")
            
            # Wrap in a frame so border is easy to style
            frame = QFrame()
            frame.setFrameShape(QFrame.StyledPanel)
            frame.setStyleSheet(f"""
                QFrame {{
                    background:{DARK};
                    border: none;
                }}
            """)
            
            fl = QHBoxLayout(frame)
            fl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            fl.setContentsMargins(0, 0, 0, 0)
            fl.addWidget(w)
            
            # Keep the frame from collapsing smaller than its content wants to be,
            # but let the splitter grow/shrink it freely above that.
            frame.setMinimumWidth(w.minimumWidth() if w.minimumWidth() > 0 else int(150 * self.scale))
            
            self.panel_widgets[pid] = frame
            if not visible:
                frame.hide()

        # Header references panel_widgets to toggle visibility
        self.header = CustomHeaderBar(self.PANELS, self.panel_widgets)

        # Let the header stretch across the full width of the window.
        # (AlignLeft previously forced it to shrink to its sizeHint width.)
        self.header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.layout_.addWidget(self.header, 0, 0, alignment=Qt.AlignTop)

        # Panels sit side-by-side in a QSplitter so their shared edges can be
        # dragged to resize them horizontally.
        self.panels_splitter = QSplitter(Qt.Horizontal)
        self.panels_splitter.setContentsMargins(0, 0, 0, 0)
        self.panels_splitter.setHandleWidth(3)
        self.panels_splitter.setChildrenCollapsible(False)
        self.panels_splitter.setStyleSheet(f"""
            QSplitter {{ background:{DARK}; border: none; }}
            QSplitter::handle {{ background:{LINE}; }}
            QSplitter::handle:hover {{ background:#777; }}
        """)

        for pid, _, _, _ in self.PANELS:
            self.panels_splitter.addWidget(self.panel_widgets[pid])

        scroll = QScrollArea()
        scroll.setWidget(self.panels_splitter)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet(_scrollbar_stylesheet(bg=PANEL_COL))
        self.layout_.addWidget(scroll, 1, 0)

        # Make sure the panel row grows to fill remaining vertical space,
        # while the header row keeps its natural height.
        self.layout_.setRowStretch(0, 0)
        self.layout_.setRowStretch(1, 1)
        self.layout_.setColumnStretch(0, 1)

        # Keep the header's tab splitter and the panel splitter in sync in
        # both directions: dragging either one resizes the other to match.
        self.panels_splitter.splitterMoved.connect(self._sync_tabs_to_panels)
        self.header.tabsResized.connect(self._sync_panels_to_tabs)
        self.header.panelVisibilityChanged.connect(
            lambda: QTimer.singleShot(0, self._sync_tabs_to_panels)
        )
        # Run once after the initial layout pass so real pixel widths exist.
        QTimer.singleShot(0, self._sync_tabs_to_panels)
        
        def on_database_change(action_code, db_name, table_name, rowid):
            """ Logger Function for the console """
            action = ACTIONS.get(action_code, "UNKNOWN")
            
            #print(f"{action} # {table_name}")
            
            # Matches
            if action == "INSERT" and table_name == "matches":
                match_info = get_match(self.conn, rowid)
                
                fn, ln = get_name_from_pid(self.conn, match_info["player1_id"])
                p1_name = f"{fn} {ln}"
                fn, ln = get_name_from_pid(self.conn, match_info["player2_id"])
                p2_name = f"{fn} {ln}"
                fn, ln = get_name_from_pid(self.conn, match_info["winner_id"])
                winner_name = f"{fn} {ln}"
                
                self.console.append(f"Match Added | {p1_name} v {p2_name} | {winner_name}")
                
            if action == "DELETE" and table_name == "matches":
                self.console.append(f"==== MATCH DELETED ====")
                
            elif action != "UPDATE" and table_name != "elo_history":
                self.console.append(f"{table_name} # {action}")
            
        listen(self.conn, on_database_change)
        
        
    def update_leaderboard(self):
        
        def _add_row(layout: QGridLayout, player: dict, row_num: int):
            """Adds one row of the leaderboard directly into the shared grid layout"""

            rank = QLabel(f"{row_num}")
            rank.setStyleSheet(_normal_text_stylesheet(self.scale))
            layout.addWidget(rank, row_num, 0)

            name = QLabel(player["player_name"])
            name.setStyleSheet(_normal_text_stylesheet(self.scale))
            layout.addWidget(name, row_num, 1)
            
            _points = QLabel(f"{player['points']:.0f}")
            _points.setStyleSheet(_normal_text_stylesheet(self.scale))
            layout.addWidget(_points, row_num, 2)

            elo = QLabel(f"{player['current_elo']:.0f}")
            elo.setStyleSheet(_normal_text_stylesheet(self.scale))
            layout.addWidget(elo, row_num, 3)
            
            row_num += 1

        clear_grid_after_row(self.lb_wid_layout, 1)

        self.lb_wid_layout.setColumnStretch(0, 0)   # rank: fits content
        self.lb_wid_layout.setColumnStretch(1, 1)   # name: takes extra space
        self.lb_wid_layout.setColumnStretch(2, 0)   # elo: fits content
        self.lb_wid_layout.setHorizontalSpacing(12)

        func, args = self.lb_box.currentData()
        conn, index = args
        
        players = func(conn, index)
            
        for i, player in enumerate(players):
            _add_row(self.lb_wid_layout, player, i + 1)
            
            
    def closeEvent(self, event: QCloseEvent):
        """
        Runs on close of the window\n
        If no is selected when promted to save all matches, rounds and sessions that were created are deleted from the database
        """
        
        if self.exit_code == None:
            reply = QMessageBox.question(
                self, 
                "Confrim Close", 
                "Do you want to save the current session on close?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.save = True
            elif reply == QMessageBox.StandardButton.No:
                self.save = False
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            
        else:
            logger.info(f"Closed with code: {self.exit_code}")
            self.save = self.exit_code
        
        session = get_session(self.conn, self.session_id)
            
        
        # if we are not saving the current session
        if not self.save and session["status"] != "completed":
            delete_session(self.conn, self.session_id)
            
        # if we are saving
        else:
            update_player_active(self.conn, self.config["active_sessions_count"])
            up_session_status(self.conn, self.session_id, "completed")
                
        event.accept()
        

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Window resizes reflow the splitter's proportional sizes without
        # emitting splitterMoved, so resync after the resize is applied.
        QTimer.singleShot(0, self._sync_tabs_to_panels)


    def _sync_tabs_to_panels(self, *args):
        sizes = self.panels_splitter.sizes()
        if sizes:
            self.header.tabs_splitter.setSizes(sizes)


    def _sync_panels_to_tabs(self, sizes):
        if sizes:
            self.panels_splitter.setSizes(sizes)
            # panels_splitter may clamp/redistribute to respect its own
            # widgets' minimum widths, so read back what it actually applied
            # and reflect that onto the tab splitter, rather than trusting
            # the originally-requested sizes.
            self.header.tabs_splitter.setSizes(self.panels_splitter.sizes())


    def handle_command(self, command: str):
        """ Handle commands entered in the console """
        
        parts = command.split()

        if not parts:
            return

        cmd = parts[0].lower()

        if cmd == "help":
            text = " ".join(parts[1:])
            
            if not text:
                self.console.append("Available commands:")
                self.console.append("\n")
                self.console.append("  help - Show this help message")
                self.console.append("  clear - Clear the console")
                self.console.append("  echo <text> - Echo the text back to the console")
                self.console.append("  nround - creates a new round")
                self.console.append("  dround - deletes the last round")
                self.console.append("  lay <action> - quickly changes the layout")
                self.console.append("  close <action> - closes the window and either 'save' or 'discard' session")
                
            elif text == "lay":
                self.console.append("Possible Decorators for comand 'lay'")
                self.console.append("setup")
                self.console.append("mini")
                self.console.append("adv")
                self.console.append("all")
                self.console.append("cmd")

        elif cmd == "cls" or cmd == "clear":
            self.console.clear()

        elif cmd == "echo":
            text = " ".join(parts[1:])
            self.console.append(text)
                
        elif cmd == "nround":
            if get_items_from_qlist(self.players_list_seed) == None:
                self.console.warn("No players selected")
            else:
                self.add_round_action.trigger()
            
        elif cmd == "dround":
            if self.round_number == 0:
                self.console.warn("No rounds to delete")
            else:
                self.remove_round_action.trigger()
            
        elif cmd == "close":
            text = " ".join(parts[1:])
            
            if text == "save":
                self.exit_code = 1
                self.close()
                
            if text == "discard":
                self.exit_code = 0
                self.close()
                
            else:
                self.console.warn(f"Decorator not recognised: {text}")

        elif cmd == "lay":
            text = " ".join(parts[1:])
            
            if text == "setup":
                [self.header.set_panel_visible(panel[0], False) for panel in self.PANELS]
                self.header.set_panel_visible("console", True)
                self.header.set_panel_visible("players", True)
                self.header.set_panel_visible("player_manager", True)
            
            elif text == "mini":
                [self.header.set_panel_visible(panel[0], False) for panel in self.PANELS]
                self.header.set_panel_visible("game_manager", True)
            
            elif text == "adv":
                [self.header.set_panel_visible(panel[0], False) for panel in self.PANELS]
                self.header.set_panel_visible("console", True)
                self.header.set_panel_visible("game_manager", True)
            
            elif text == "all":
                [self.header.set_panel_visible(panel[0], True) for panel in self.PANELS]
            
            elif text == "cmd":
                [self.header.set_panel_visible(panel[0], False) for panel in self.PANELS]
                self.header.set_panel_visible("console", True)
                
            else:
                self.console.warn(f"Decorator not recognised: {text}")

        else:
            self.console.inform(f"Unknown command: {cmd}")