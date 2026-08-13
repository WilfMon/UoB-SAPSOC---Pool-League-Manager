import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s -- %(levelname)-8s -- %(name)s -- %(message)s",
)
logger = logging.getLogger(__name__)

import numpy as np

from PySide6.QtWidgets import QMainWindow, QPlainTextEdit, QSpacerItem, QInputDialog, QListWidgetItem, QSizePolicy, QLabel, QGridLayout,  QFrame, QPushButton, QVBoxLayout, QWidget, QListWidget, QMenu, QApplication, QLineEdit, QScrollArea, QHBoxLayout, QSplitter, QComboBox, QSpinBox, QSlider, QRadioButton, QButtonGroup
from PySide6.QtGui import QAction, QCursor, QFont
from PySide6.QtCore import Qt, QSize, QPoint, Signal, QTimer

from ui.custom_widgets import CustomButton, CustomHeaderBar, ConsoleWidget, ToggleSwitch
from ui.text_box_window import TextBoxWindow

from utils.utils import check_for_new_players, clean_name, clear_layout, get_items_from_qlist, remove_item_from_qlist
from utils.utils_classes import SessionBuilder

from database.queries import get_all_players_name, get_player_id_from_name

from resources.colours import DARK, HEAD, PANEL_COL, LINE, TEXT, ACCENT
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
        
        # actions 
        """
        self.setup_action = QAction("Setup Session")
        self.setup_action.triggered.connect(self.on_setup)
        self.file_menu.addAction(self.setup_action)
        
        self.confirm_action = QAction("Confirm")
        self.confirm_action.triggered.connect(self.on_confirm_setup)
        self.file_menu.addAction(self.confirm_action)
        
        self.test_action = QAction("Test")
        self.test_action.triggered.connect(self.on_test)
        self.file_menu.addAction(self.test_action)
        """
        
        # Create header bar
        def console_panel() -> QWidget:
            self.console = ConsoleWidget()
            self.console.setFont(self.default_font)
            
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
            self.players_list_seed.setFont(self.default_font)
            
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
                participants = get_items_from_qlist(self.selected_players_list)
                
                for player in participants:
                    matches = self.players_list_seed.findItems(player, Qt.MatchFlag.MatchExactly)
                    
                    if not matches:
                        self.players_list_seed.addItem(player)
                    
            def remove():
                participants = get_items_from_qlist(self.selected_players_list)
                
                for player in participants:
                    remove_item_from_qlist(self.players_list_seed, player)
            
            self.player_manager_layout = QGridLayout()
            player_manager_panel_widget = QWidget()
            player_manager_panel_widget.setLayout(self.player_manager_layout)
            
            player_manager_panel_widget.setMinimumWidth(int(450 * self.scale))

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

            for player in get_all_players_name(dest=self.dest):
                self.selection_list.addItem(player)

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
            
            self.main_game_manager_layout = QGridLayout()
            game_manager_panel_widget = QWidget()
            game_manager_panel_widget.setLayout(self.main_game_manager_layout)
            
            game_manager_panel_widget.setMinimumWidth(int(100 * self.scale))
            
            def _round_header(text: str) -> QLabel:
                lbl = QLabel(text.upper())
                lbl.setFont(self.small_font)
                lbl.setStyleSheet(_title_text_stylesheet())
                return lbl
            
            def _round_card(rows: list[QWidget]) -> QFrame:
                card = QFrame()
                card.setStyleSheet(f"""
                    QFrame {{
                        background: {HEAD};
                        border-radius: 5px;
                    }}
                """)
                card_layout = QVBoxLayout(card)
                card_layout.setContentsMargins(4, 4, 4, 4)
                card_layout.setSpacing(0)
                
                for i, row in enumerate(rows):
                    card_layout.addWidget(row)
                    if i < len(rows) - 1:
                        divider = QFrame()
                        divider.setFixedHeight(1)
                        divider.setStyleSheet(f"background:{LINE}; border:none;")
                        card_layout.addWidget(divider)
                
                return card
            
            def _round_row(left: str, right: str) -> QWidget:
                row = QWidget()
                row.setStyleSheet("background: transparent;")
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(10, 10, 10, 10)
                row_layout.setSpacing(12)

                left_btn = CustomButton(left)
                left_btn.setStyleSheet(f"border-radius: 5px; border-color: {ACCENT}; background-color: {LINE};")
                right_btn = CustomButton(right)
                right_btn.setStyleSheet(f"border-radius: 5px; border-color: {ACCENT}; background-color: {LINE};")

                row_layout.addWidget(left_btn)
                row_layout.addWidget(QLabel("v"))
                row_layout.addWidget(right_btn)

                return row
            
            def add_new_round(layout: QGridLayout):
                
                layout.addWidget(_round_header(f"Round: {1}"), 0, 0)
                layout.addWidget(_round_card([
                    _round_row("Player1", "Player2"),
                    _round_row("Player3", "Player4"),
                    _round_row("Player5", "Player6"),
                ]), 1, 0)
                
            
            def players_confirmed(yesorno):
                if yesorno:
                    logger.info("Players confirmed, proceeding to rounds")
                    players = get_items_from_qlist(self.players_list_seed)
                    
                    # Ui stuff
                    self.round_title = QLabel("Rounds:")
                    self.main_game_manager_layout.addWidget(self.round_title, 0, 1, alignment=Qt.AlignLeft)
                    
                    self.round_area = QScrollArea()
                    self.round_area.setWidgetResizable(True)
                    self.round_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                    self.round_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                    self.round_area.setStyleSheet("background-color: #0b0b0b;")

                    self.round_container = QWidget()
                    self.round_container_layout = QHBoxLayout(self.round_container)
                    self.round_container_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

                    self.round_area.setWidget(self.round_container)
                    self.main_game_manager_layout.addWidget(self.round_area, 1, 1)
                    
                    # disable and enable menu options
                    #self.confirm_players_action.setDisabled(True)
                    #self.new_round_action.setDisabled(False)
                    #self.remove_round_action.setDisabled(False)
                    #self.save_session_action.setDisabled(False)
                    
                    # write to database players
                    players_ = set(get_items_from_qlist(self.players_list_seed))
                    for name in players_:
                        #add_player(name, dest=self.dest)
                        pass

                    # logic for round pairings            
                    self.round_number = 0
                    
                    self.finished_games = [] # martix
                    
                    self.session_items = [] # matrix
                    
                    self.last_round_players = set(players)
                        
                    self.builder = SessionBuilder(players)
                    
                    on_new_round() # creates first round

                    # update tracker
                    self.players_confimed = True
                        
                else:
                    logger.info("Players not confirmed")            
            
            def on_new_round():
                
                def toggle_match_state(loc):
                    
                    round_num, index, side = loc
                    
                    left, right = self.session_items[round_num][index]
                    
                    if side == "left":
                        pressed = left
                        opp = right
                        
                    if side == "right":
                        pressed = right
                        opp = left
                        
                    pressed.setStyleSheet("background-color: green")
                    opp.setStyleSheet("background-color: #5e0202")
                    
                    # adjustment therefore remove the previous game stored
                    if (opp.text(), pressed.text()) in self.finished_games[round_num]:
                        self.finished_games[round_num].remove((opp.text(), pressed.text()))
                    
                    self.finished_games[round_num].add((pressed.text(), opp.text()))
                    
                def remove_match_state(loc):
                    round_num, index = loc
                    
                    left, right = self.session_items[round_num][index]
                    
                    left.setStyleSheet("background-color: #1f1f1f") # default colour
                    right.setStyleSheet("background-color: #1f1f1f")
                    
                    self.finished_games[round_num].discard((left.text(), right.text()))
                    self.finished_games[round_num].discard((right.text(), left.text()))
                
                # check for new players
                players = set(get_items_from_qlist(self.players_list_seed))
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
                self.finished_games.append(set())
                self.session_items.append([])
                
                self.last_round_players = players
                            
                # creating display of round pairings
                round_container = QFrame()
                round_container.setStyleSheet("background-color: #1f1f1f;")
                round_container_layout = QGridLayout(round_container, alignment=Qt.AlignTop)
                
                round_container_layout.addWidget(QLabel(f"Round: {self.round_number + 1}"), 0, self.round_number)
                
                # shuffle order of round and games so display is random
                rng = np.random.default_rng()
            
                round_ = [list(t) for t in list(round_)]
                rng.shuffle(round_)
                
                for game in round_:
                    rng.shuffle(game)
                
                # create buttons to display players and track wins
                for n, pair in enumerate(round_):
                    
                    left = CustomButton(pair[0])
                    right = CustomButton(pair[1])
                    
                    left.normalClick.connect(lambda loc=(self.round_number, n, "left"): toggle_match_state(loc))
                    right.normalClick.connect(lambda loc=(self.round_number, n, "right"): toggle_match_state(loc))
                    
                    left.shiftClick.connect(lambda loc=(self.round_number, n): remove_match_state(loc))
                    right.shiftClick.connect(lambda loc=(self.round_number, n): remove_match_state(loc))
                    
                    # adding buttons to the gui
                    round_container_layout.addWidget(left, n + 1, self.round_number)
                    round_container_layout.addWidget(QLabel("v"), n + 1, self.round_number + 1)
                    round_container_layout.addWidget(right, n + 1, self.round_number + 2)
                    
                    # adding buttons to the tracker
                    self.session_items[self.round_number].append((left, right))
                    
                if bye != None:
                    bye_text = QLabel(f"Bye: {bye}")
                else:
                    bye_text = QLabel(f"Bye: None")
                    
                round_container_layout.addWidget(bye_text, n + 3, self.round_number)
                
                self.round_container_layout.addWidget(round_container)
                
                #self.remove_round_action.setDisabled(False)
                if not self.builder.rounds_left: # no rounds left to play
                    #self.new_round_action.setDisabled(True)
                    pass

                self.round_number += 1
                    
                """ Called when the remove round menu item is pressed """
                def on_remove_round():
                    self.builder.remove_round()
                    self.finished_games.pop(-1)
                    self.session_items.pop(-1)
                    
                    # delete display of last round
                    item = self.round_container_layout.takeAt(self.round_number - 1)
                    widget = item.widget()
                    if widget:
                        widget.setParent(None)
                        widget.deleteLater()

                    #self.new_round_action.setDisabled(False)
                    
                    self.round_number -= 1
                    
                    if self.round_number == 0: # no rounds displayed
                        #self.remove_round_action.setDisabled(True)
                        pass

                """ Called when the save session menu item is pressed """
                def on_save_session():

                    # self.session_id = add_session(semester_id=self.semester_id, session_date=self.date, dest=self.dest)
                    
                    for round_ in self.finished_games:
                        for game in list(round_):
                            
                            player1_id = get_player_id_from_name(game[0], dest=self.dest)
                            player2_id = get_player_id_from_name(game[1], dest=self.dest)
                            
                            # add_game(self.session_id, player1_id, player2_id, winner_id=player1_id, dest=self.dest)
                        
                    logger.info("Saved Session")
                    
                    on_cancel_session()
                    
                """ Called when the cancel session menu item is pressed """
                def on_cancel_session():
                
                    # enable new session creation again
                    self.new_session_action.setDisabled(False)
                    
                    # clear the session layout
                    clear_layout(self.main_game_manager_layout)
                    
                    # delete session menu bar
                    # self.menu_bar = remove_menu(self.menu_bar, "Session")
                        
                    # clear finished games
                    self.finished_games = []

                """ Called when the listWidget is right clicked """
                def show_context_menu(position: QPoint): # menu for adding and removing players from left list
                    # Get the item under the cursor
                    item = self.players_list_seed.itemAt(position)
                    
                    if item is None:
                        menu = QMenu()
                        new_action = menu.addAction("New")
                        
                        # Show menu and wait for user selection
                        action = menu.exec(self.players_list_seed.mapToGlobal(position))
                        
                        if action == new_action:
                            self.text_box = TextBoxWindow(scale=self.scale)
                            self.text_box.open_at_cursor()
                            
                            #self.text_box.submitted_player.connect(player_recived)
                            
                            self.text_box.show()

                    else:
                        # Create context menu
                        menu = QMenu()
                        remove_action = menu.addAction("Remove")
                        
                        # Show menu and wait for user selection
                        action = menu.exec(self.players_list_seed.mapToGlobal(position))
                        
                        if action == remove_action:
                            i = self.players_list_seed.row(item)
                            self.players_list_seed.takeItem(i)

                """ Called when the view menu item is pressed """
                def on_tab_in():            
                    self.central.setCurrentWidget(game_manager_panel_widget)

                # logic for new session window
                #self.session_setup_window = SetupWindow(dest=self.dest, scale=self.scale)
                #self.session_setup_window.submitted_players.connect(players_recived)

                # create tracker that tracks when players have been confirmed
                
                self.players_confimed = False
                
                # Session menu
                self.file_menu = self.menuBar().addMenu("Session")
                
                #self.new_session_action.setDisabled(True)
                
                self.tab_in_action = QAction("View", self)
                self.tab_in_action.triggered.connect(on_tab_in)
                self.file_menu.addAction(self.tab_in_action)
                
                self.file_menu.addSeparator()
                
                """
                self.confirm_players_action = QAction("Confirm", self)
                self.confirm_players_action.triggered.connect(on_confirm_players)
                self.file_menu.addAction(self.confirm_players_action)
                
                self.new_round_action = QAction("New Round", self)
                self.new_round_action.triggered.connect(on_new_round)
                self.file_menu.addAction(self.new_round_action)
                self.new_round_action.setDisabled(True)
                """
                
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
                self.main_game_manager_layout.addWidget(self.players_list_title, 0, 0, alignment=Qt.AlignLeft)
                
                self.players_list_seed = QListWidget()
                self.players_list_seed.setFixedWidth(250 * self.scale)
                self.players_list_seed.setFont(self.default_font)
                self.main_game_manager_layout.addWidget(self.players_list_seed, 1, 0, alignment=Qt.AlignLeft)
                
                self.players_list_seed.setContextMenuPolicy(Qt.CustomContextMenu)
                self.players_list_seed.customContextMenuRequested.connect(show_context_menu)

            # temporary logic for testing
            self.file_menu.addAction(QAction("Confirm Players", self, triggered=lambda: players_confirmed(True)))
            self.file_menu.addAction(QAction("Add Round", self, triggered=lambda: add_new_round(self.main_game_manager_layout)))

            return game_manager_panel_widget
        
        PANELS = [
            ("console", "Console", True, console_panel),
            ("settings", "Settings", False, settings_panel),
            ("players", "Player Seed", False, player_seed_panel),
            ("leaderboard", "Leaderboard", False, leaderboard_panel),
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

        else:
            self.console.append(f"Unknown command: {cmd}")
            
 
    # -- scoped stylesheets --------------------------------------------------
    # Set directly on a widget (not the QApplication), so these only cascade
    # to that widget's own descendants and won't affect other panels.