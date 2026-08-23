import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s -- %(levelname)-8s -- %(name)s -- %(message)s",
)
logger = logging.getLogger(__name__)

import numpy as np
import datetime

from PySide6.QtWidgets import QMainWindow, QPlainTextEdit, QSpacerItem, QInputDialog, QListWidgetItem, QSizePolicy, QLabel, QGridLayout,  QFrame, QPushButton, QVBoxLayout, QWidget, QListWidget, QMenu, QApplication, QLineEdit, QScrollArea, QHBoxLayout, QSplitter, QComboBox, QSpinBox, QSlider, QRadioButton, QButtonGroup
from PySide6.QtGui import QAction, QCursor, QFont
from PySide6.QtCore import Qt, QSize, QPoint, Signal, QTimer

from .confimation_window import ConfirmationWindow

from ui.custom_widgets import CustomButton, CustomHeaderBar, ConsoleWidget, ToggleSwitch
from ui.text_box_window import TextBoxWindow

from utils.utils import clean_name, clear_layout, get_items_from_qlist, remove_item_from_qlist, calc_elo_change
from utils.utils_classes import SessionBuilder

from DB.db import get_connection, list_active_players, get_pid_from_name, get_player, create_round, create_semester, create_session, list_all_players, add_player, record_match, delete_match, get_match_id

from resources.colours import DARK, HEAD, PANEL_COL, LINE, TEXT, ACCENT, GREEN, RED
from resources.stylesheets import _scrollbar_stylesheet, _settings_controls_stylesheet, _title_text_stylesheet

class MainSessionWindow(QMainWindow):
    info = Signal(dict)
    
    def __init__(self, dest, scale=1.0):
        super().__init__()
        
        self.scale = scale
        self.dest = dest

        self.setWindowTitle(f"Session")
        self.setMinimumSize(int(1280 * self.scale), int(720 * self.scale))
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
        
        conn = get_connection()
        
        # automatically determine semester and year
        if 9 <= self.month <= 12:
            sem_name = f"{int(self.year) - 1}.{self.year}.1"
            
            self.semester_id = create_semester(conn, sem_name, self.date)

        if 1 <= self.month <= 8:
            sem_name = f"{int(self.year) - 1}.{self.year}.2"
            
            
            self.semester_id = create_semester(conn, sem_name, self.date)

        logger.info(f"Semester set to: {sem_name}")
        
        # Create header bar
        def console_panel() -> QWidget:
            self.console = ConsoleWidget()
            self.console.setFont(self.small_font)
            
            self.console.setMinimumWidth(int(100 * self.scale))
            
            self.console.commandEntered.connect(self.handle_command)

            return self.console
        
        def settings_panel() -> QWidget:
            content = QWidget()
            content.setStyleSheet(f"background:{PANEL_COL};")
            
            self.settings_panel_layout = QVBoxLayout(content)
            self.settings_panel_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.settings_panel_layout.setContentsMargins(20, 20, 20, 20)
            self.settings_panel_layout.setSpacing(16)
            
            def _settings_section_header(text: str) -> QLabel:
                lbl = QLabel(text.upper())
                lbl.setFont(self.small_font)
                lbl.setStyleSheet(_title_text_stylesheet())
                return lbl

            def _settings_card(rows: list[QWidget]) -> QFrame:
                card = QFrame()
                card.setStyleSheet(f"""
                    QFrame {{
                        background: {HEAD};
                        border-radius: 5px;
                    }}
                """)
                card_layout = QVBoxLayout(card)
                card_layout.setContentsMargins(16, 4, 16, 4)
                card_layout.setSpacing(0)

                for i, row in enumerate(rows):
                    card_layout.addWidget(row)
                    if i < len(rows) - 1:
                        divider = QFrame()
                        divider.setFixedHeight(1)
                        divider.setStyleSheet(f"background:{LINE}; border:none;")
                        card_layout.addWidget(divider)

                return card

            def _settings_row(label_text: str, control: QWidget, hint: str = None) -> QWidget:
                row = QWidget()
                row.setStyleSheet("background: transparent;")
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(0, 10, 0, 10)
                row_layout.setSpacing(12)

                text_col = QVBoxLayout()
                text_col.setSpacing(2)

                title = QLabel(label_text)
                title.setFont(self.small_font)
                title.setStyleSheet(f"color:{TEXT}; background:transparent;")
                text_col.addWidget(title)

                if hint:
                    hint_lbl = QLabel(hint)
                    hint_lbl.setStyleSheet("color:#888; background:transparent; font-size:11px;")
                    text_col.addWidget(hint_lbl)

                row_layout.addLayout(text_col)
                row_layout.addStretch()
                row_layout.addWidget(control, alignment=Qt.AlignVCenter)

                return row
            
            def _make_toggle(checked: bool = False) -> ToggleSwitch:
                toggle = ToggleSwitch()
                toggle.setChecked(checked)
                return toggle

            def _make_combobox(items: list[str]) -> QComboBox:
                box = QComboBox()
                box.addItems(items)
                box.setFont(self.small_font)
                box.setStyleSheet(f"background:{DARK};")
                return box

            def _make_lineedit(value: str) -> QLineEdit:
                edit = QLineEdit()
                edit.setText(value)
                edit.setFont(self.small_font)
                edit.setFixedWidth(int(160 * self.scale))
                return edit

            def _make_spinbox(minimum: int, maximum: int, value: int) -> QSpinBox:
                spin = QSpinBox()
                spin.setRange(minimum, maximum)
                spin.setValue(value)
                spin.setFont(self.small_font)
                return spin

            def _make_slider(minimum: int, maximum: int, value: int, suffix: str = ""):
                container = QWidget()
                container.setStyleSheet("background: transparent;")
                h = QHBoxLayout(container)
                h.setContentsMargins(0, 0, 0, 0)
                h.setSpacing(10)

                slider = QSlider(Qt.Horizontal)
                slider.setRange(minimum, maximum)
                slider.setValue(value)
                slider.setFixedWidth(int(140 * self.scale))

                value_lbl = QLabel(f"{value}{suffix}")
                value_lbl.setFont(self.small_font)
                value_lbl.setStyleSheet(f"color:{TEXT}; background:transparent;")
                value_lbl.setFixedWidth(int(40 * self.scale))
                value_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

                slider.valueChanged.connect(lambda v: value_lbl.setText(f"{v}{suffix}"))

                h.addWidget(slider)
                h.addWidget(value_lbl)

                return container, slider

            def _make_radio_group(options: list[str], checked_index: int = 0):
                container = QWidget()
                container.setStyleSheet("background: transparent;")
                h = QHBoxLayout(container)
                h.setContentsMargins(0, 0, 0, 0)
                h.setSpacing(14)

                group = QButtonGroup(container)
                for i, option in enumerate(options):
                    rb = QRadioButton(option)
                    rb.setFont(self.small_font)
                    if i == checked_index:
                        rb.setChecked(True)
                    group.addButton(rb, i)
                    h.addWidget(rb)

                return container, group
            
            def _populate_settings_panel(layout: QVBoxLayout):
                """Fill the settings panel with example controls, grouped into cards."""
        
                layout.addWidget(_settings_section_header("General"))
                layout.addWidget(_settings_card([
                    _settings_row("Player Display Name", _make_lineedit("Player1")),
                    _settings_row("Language", _make_combobox(
                        ["English", "French", "German", "Spanish", "Japanese"])),
                    _settings_row(
                        "Sound Effects", _make_toggle(True),
                        hint="Play audio cues during the session"),
                    _settings_row(
                        "Desktop Notifications", _make_toggle(False),
                        hint="Notify me when it's my turn"),
                ]))
        
                layout.addWidget(_settings_section_header("Gameplay"))
                difficulty_row, self.difficulty_group = _make_radio_group(
                    ["Easy", "Normal", "Hard"], checked_index=1)
                turn_timer_row, self.turn_timer_slider = _make_slider(10, 120, 60, suffix="s")
                layout.addWidget(_settings_card([
                    _settings_row("Difficulty", difficulty_row),
                    _settings_row("Max Players", _make_spinbox(2, 12, 6)),
                    _settings_row("Turn Timer", turn_timer_row),
                    _settings_row("Game Mode", _make_combobox(
                        ["Classic", "Tournament", "Sandbox"])),
                ]))
        
                layout.addWidget(_settings_section_header("Advanced"))
                layout.addWidget(_settings_card([
                    _settings_row("Auto-Save Session", _make_toggle(True)),
                    _settings_row("Verbose Console Logging", _make_toggle(False)),
                    _settings_row(
                        "Network Port", _make_lineedit("7777"),
                        hint="Requires a restart to take effect"),
                ]))
        
                layout.addStretch()
 
            _populate_settings_panel(self.settings_panel_layout)
 
            settings_scroll = QScrollArea()
            settings_scroll.setWidget(content)
            settings_scroll.setWidgetResizable(True)
            settings_scroll.setFrameShape(QFrame.NoFrame)
            settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            settings_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            settings_scroll.setStyleSheet(
                f"QScrollArea {{ border:none; background:{PANEL_COL}; }}"
                + _settings_controls_stylesheet()
                + _scrollbar_stylesheet(PANEL_COL)
            )
 
            return settings_scroll
        
        def player_seed_panel() -> QWidget:
            self.players_list_seed = QListWidget()
            self.players_list_seed.setFont(self.small_font)
            
            self.players_list_seed.setMinimumWidth(int(100 * self.scale))
            
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
        
        def leaderboard_panel() -> QWidget:
            self.leaderboard_list = QWidget()
            self.leaderboard_list.setFont(self.default_font)
            
            self.leaderboard_list.setMinimumWidth(int(100 * self.scale))

            return self.leaderboard_list
        
        def statistics_panel() -> QWidget:
            self.stats_panel_widget = QWidget()
            self.stats_panel_widget.setFont(self.default_font)
            
            self.stats_panel_widget.setMinimumWidth(int(100 * self.scale))

            return self.stats_panel_widget            
        
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
                        
                        conn = get_connection()
                        
                        for p in players:
                            fn, ln = p.split(" ")
                            
                            add_player(conn, fn, ln)
                            
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
                
                conn = get_connection()
                players = list_all_players(conn)
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


            conn = get_connection()
            active_players = list_active_players(conn)
            
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
                
                main_elo.setText(new_m)
                other_elo.setText(new_o)
                
                round_id = main.round_id
                
                # find player ids
                p1_id = main_elo.property("elo_change")[0]["player_id"]
                p2_id = other_elo.property("elo_change")[0]["player_id"]
                
                # database updates
                conn = get_connection()
                record_match(conn, round_id, p1_id, p2_id, p1_id)
                
                refresh_session_items()
                main.clicked = True
                other.clicked = True
                
            def on_shift_click(btns):
                """Revert button states to how they were before they were clicked; also revert match to unplayed in the database"""
                
                main, other = btns
                # check if the button has already been shift clicked and return if so
                if not main.clicked:
                    print("already not clicked")
                    return
                
                main.setStyleSheet(f"border-radius: 3px; background-color: {LINE}; {_pad(4)}")
                other.setStyleSheet(f"border-radius: 3px; background-color: {LINE}; {_pad(4)}")
                
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
                conn = get_connection()
                match_id = get_match_id(conn, p1_id, p2_id, round_id)
                if match_id == None:
                    match_id = get_match_id(conn, p2_id, p1_id, round_id)
                
                print(p1_id, p2_id, round_id)
                print(match_id)
                delete_match(conn, match_id)
                
                main.clicked = False
                other.clicked = False
                refresh_session_items()
            
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
                        background: {HEAD};
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
                left_btn.setStyleSheet(f"border-radius: 3px; background-color: {LINE}; {_pad(4)}")
                
                right_btn = CustomButton()
                right_btn.setText(right)
                right_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                right_btn.normalClick.connect(on_normal_click)
                right_btn.shiftClick.connect(on_shift_click)
                right_btn.setStyleSheet(f"border-radius: 3px; background-color: {LINE}; {_pad(4)}")

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
                spacer.setStyleSheet("background-color: #333333; max-height: 3px; border: none;")
                
                layout.addWidget(spacer, vert_offset, 0, 1, 3)
            
            def round_bye_row(layout, vert_offset, bye: str) -> QWidget:
                """Adds the last row to the round container for the bye"""
                bye_lbl = QLabel(f"Bye: {bye}")
                bye_lbl.setStyleSheet(f"color:{TEXT}; background:transparent; font-size:12px; font-weight:600;")
                
                layout.addWidget(bye_lbl, vert_offset, 0)
            
            # ---------------------------------------------------------------
            # Functions
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

                conn = get_connection()
                round_id = create_round(conn, self.session_id, self.round_number)

                vert_offset = 0
                for idx, match in enumerate(round_):
                    vert_offset = idx * 3

                    fn1, ln1 = match[0].split(" ")
                    p1 = get_player(conn, get_pid_from_name(conn, fn1.strip(), ln1.strip()))

                    fn2, ln2 = match[1].split(" ")
                    p2 = get_player(conn, get_pid_from_name(conn, fn2.strip(), ln2.strip()))

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
                self.console.append(f"{edges}, {nodes}")
                return card_layout
            
            def refresh_session_items():
                """Updates the session elo labels with potentially new database updates"""
                
                conn = get_connection()
                
                for _round in self.session_items:
                    for row in _round:
                        # retrive old elo
                        p1_old = row["p1_elo_label"].property("elo_change")[0]
                        p2_old = row["p2_elo_label"].property("elo_change")[0]
                        
                        # find new elo and elo change
                        p1_new = get_player(conn, p1_old["player_id"])
                        p2_new = get_player(conn, p2_old["player_id"])
                        
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
                
            
            self.action_menu = self.menuBar().addMenu("Action")
            self.action_menu.addAction(QAction("Add Round", self, triggered=lambda: add_new_round(self.main_game_manager_layout)))
                
            self.main_game_manager_layout = QGridLayout()
            self.main_game_manager_layout.setSpacing(12)  # Controls horizontal distance between round columns
            self.main_game_manager_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            
            game_manager_panel_widget = QWidget()
            game_manager_panel_widget.setLayout(self.main_game_manager_layout)

            game_manager_panel_scoll_area = QScrollArea()
            game_manager_panel_scoll_area.setWidget(game_manager_panel_widget)
            game_manager_panel_scoll_area.setWidgetResizable(True)
            game_manager_panel_scoll_area.setMinimumWidth(int(200 * self.scale))
            
            self.round_number = 0
            
            self.finished_games = [] # martix
            self.session_items = [] # matrix
                
            self.builder = SessionBuilder()
            
            conn = get_connection()
            self.session_id = create_session(conn, self.semester_id, self.date, [])

            return game_manager_panel_scoll_area
        
        PANELS = [
            ("console", "Console", False, console_panel),
            ("settings", "Settings", False, settings_panel),
            ("players", "Player Seed", True, player_seed_panel),
            ("leaderboard", "Leaderboard", False, leaderboard_panel),
            ("statistics", "Statistics", False, statistics_panel),
            ("player_manager", "Player Manager", True, player_manager_panel),
            ("game_manager", "Game Manager", True, game_manager_panel),
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
        self.header = CustomHeaderBar(PANELS, self.panel_widgets)

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

        for pid, _, _, _ in PANELS:
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
            self.console.append("Available commands:")
            self.console.append("  help - Show this help message")
            self.console.append("  clear - Clear the console")
            self.console.append("  echo <text> - Echo the text back to the console")

        elif cmd == "cls" or cmd == "clear":
            self.console.clear()

        elif cmd == "echo":
            text = " ".join(parts[1:])
            self.console.append(text)

        elif cmd == "show-elo":
            text = " ".join(parts[1:])
            
            if text == "true":
                print("true")
                
            if text == "false":
                print("flase")

        else:
            self.console.append(f"Unknown command: {cmd}")
            
 
    # -- scoped stylesheets --------------------------------------------------
    # Set directly on a widget (not the QApplication), so these only cascade
    # to that widget's own descendants and won't affect other panels.