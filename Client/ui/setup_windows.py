import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s -- %(levelname)-8s -- %(name)s -- %(message)s",
)
logger = logging.getLogger(__name__)

from PySide6.QtWidgets import QMainWindow, QFrame, QLineEdit, QScrollArea, QSlider, QComboBox, QSizePolicy , QGridLayout, QVBoxLayout, QWidget, QLabel, QPushButton, QListWidget, QMenu, QListWidgetItem
from PySide6.QtCore import Qt, QPoint, Signal
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
        self.setMinimumSize(int(800 * scale), int(800 * scale))

        central = QWidget()
        self.layout_ = QGridLayout()
        central.setLayout(self.layout_)
        self.setCentralWidget(central)

        label_text_box = QLabel("Enter Players:")
        label_text_box.setFixedSize(label_text_box.sizeHint())
        self.layout_.addWidget(label_text_box, 0, 0)

        self.input_box = QLineEdit()
        self.layout_.addWidget(self.input_box, 1, 0, alignment=Qt.AlignTop)
        self.input_box.returnPressed.connect(self.submit_text_typed)

        label_text_box = QLabel("Select Players:")
        label_text_box.setFixedSize(label_text_box.sizeHint())
        self.layout_.addWidget(label_text_box, 2, 0)
        
        self.selection_list = QListWidget()
        self.selection_list.setFont(self.default_font)
        self.selection_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.selection_list.itemClicked.connect(self.submit_text_selected)
        self.layout_.addWidget(self.selection_list, 3, 0)

        for player in get_all_players_name():
            self.selection_list.addItem(player)

        label_text_box = QLabel("Players Selected:")
        label_text_box.setFixedSize(label_text_box.sizeHint())
        self.layout_.addWidget(label_text_box, 0, 1)

        self.selected_players_list = QListWidget()
        self.selected_players_list.setFont(self.default_font)
        self.selected_players_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.layout_.addWidget(self.selected_players_list, 1, 1, 3, 1)
        self.selected_players_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.selected_players_list.customContextMenuRequested.connect(self.show_context_menu)
        
        self.populate_list = QShortcut(QKeySequence("Ctrl+P"), self)
        self.populate_list.activated.connect(self.on_populate_list)
        
        button_cancel = QPushButton("Cancel")
        button_cancel.adjustSize()
        button_cancel.clicked.connect(self.close)
        self.layout_.addWidget(button_cancel, 4, 0, alignment=Qt.AlignLeft)
        
        self.button_accept = QPushButton("Accept")
        self.button_accept.adjustSize()
        self.button_accept.clicked.connect(self.accept)
        self.layout_.addWidget(self.button_accept, 4, 1, alignment=Qt.AlignRight)

    def on_populate_list(self): # for debugging
        players = ["Wilf Moncrieff", "Robert Fry", "Jak Dables", "Wilf Howard", "Dylan Nolan", "Will Vickers", "Paaras Padhiar", "Elijah Brook", "Malachi Bielby", "George Worsley", "Evan Morris", "Osian Drake"]
        
        for player in players:
            self.selected_players_list.addItem(QListWidgetItem(player))
        
    def submit_text_selected(self, player):
        
        text = clean_name(player.text())

        item = self.selected_players_list.findItems(text, Qt.MatchExactly)
        
        # check if text is aleady submitted
        if not item:

            text = QListWidgetItem(text)
            self.selected_players_list.addItem(text)
        
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
        self.selected_players_list.addItem(text)

        self.input_box.clear()
        
    def show_context_menu(self, position: QPoint):
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
            
    def accept(self):
        participants = [self.selected_players_list.item(i).text() for i in range(self.selected_players_list.count())]
        
        self.submitted_players.emit(participants)
        self.close()

class TournamentSetupWindow(SetupWindow):
    # Define a signal that sends a list
    signal = Signal(list, dict)

    def __init__(self, scale=1.0):
        super().__init__()

        self.setMinimumSize(int(1000 * scale), int(800 * scale))

        self.layout_.addWidget(self.button_accept, 4, 2, alignment=Qt.AlignRight)

        label_text_box = QLabel("Select Settings:")
        label_text_box.setFixedSize(label_text_box.sizeHint())
        self.layout_.addWidget(label_text_box, 0, 2)

        # frame
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        frame = QFrame()
        f_layout = QVBoxLayout(frame)

        # set scroll area
        scroll.setWidget(frame)

        f_layout.setContentsMargins(0, 0, 0, 0)
        f_layout.setAlignment(Qt.AlignTop)

        self.layout_.addWidget(scroll, 1, 2, 3, 1)

        # title
        title_frame = QFrame()
        title_frame.setStyleSheet("background-color: #2b2b2b;")
        title_frame_layout = QVBoxLayout(title_frame)

        title_label = QLabel("Title:")
        title_label.setStyleSheet("font-size: 15px;font-weight: 500;")
        self.title_text_box = QLineEdit()
        self.title_text_box.setStyleSheet("""
            background-color: #1f1f1f;
            color: #ffffff;
            border: 1px solid #333333;
            padding: 3px;
            border-radius: 3px;
        """)

        title_frame_layout.addWidget(title_label)
        title_frame_layout.addWidget(self.title_text_box)
        f_layout.addWidget(title_frame)

        # seed selector
        seed_frame = QFrame()
        seed_frame.setStyleSheet("background-color: #2b2b2b;")
        seed_frame_layout = QVBoxLayout(seed_frame)

        seed_label = QLabel("Seed Method:")
        seed_label.setStyleSheet("font-size: 15px;font-weight: 500;")
        self.seeding_setting_box = QComboBox()
        self.seeding_setting_box.addItem("Elo")
        self.seeding_setting_box.addItem("Semester Leaderboard")
        self.seeding_setting_box.setCurrentIndex(0)

        ran_label = QLabel("Randomness (0% to 100%):")
        ran_label.setStyleSheet("font-size: 15px;font-weight: 500;")
        self.randomness_slider = QSlider(Qt.Horizontal)
        self.randomness_slider.setMinimum(0)
        self.randomness_slider.setMaximum(100)
        self.randomness_slider.setValue(20)

        elo_count_label = QLabel("Games count towards player elo:")
        elo_count_label.setStyleSheet("font-size: 15px;font-weight: 500;")
        self.elo_count_button = QPushButton("No")
        self.elo_count_button.setStyleSheet("background-color: red")

        def toggle():
            if self.elo_count_button.text() == "No":
                self.elo_count_button.setText("Yes")
                self.elo_count_button.setStyleSheet("background-color: green")
            else:
                self.elo_count_button.setText("No")
                self.elo_count_button.setStyleSheet("background-color: red")

        self.elo_count_button.clicked.connect(toggle)

        seed_frame_layout.addWidget(seed_label)
        seed_frame_layout.addWidget(self.seeding_setting_box)

        seed_frame_layout.addWidget(ran_label)
        seed_frame_layout.addWidget(self.randomness_slider)

        seed_frame_layout.addWidget(elo_count_label)
        seed_frame_layout.addWidget(self.elo_count_button)
        f_layout.addWidget(seed_frame)

        # match format selector
        match_frame = QFrame()
        match_frame.setStyleSheet("background-color: #2b2b2b;")
        self.match_frame_layout = QVBoxLayout(match_frame)

        match_format_label = QLabel("Match Format:")
        match_format_label.setStyleSheet("font-size: 15px;font-weight: 500;")

        match_format_label_n = QLabel("Normal Games:")
        match_format_label_n.setStyleSheet("font-size: 13px;font-weight: 500;")
        self.match_format_box_n = QComboBox()
        self.match_format_box_n.addItem("Best of one", 1)
        self.match_format_box_n.addItem("Race to 3", 3)
        self.match_format_box_n.addItem("Race to 4", 4)
        self.match_format_box_n.addItem("Race to 5", 5)
        self.match_format_box_n.addItem("Race to 7", 7)

        match_format_label_q = QLabel("Quater-final Games:")
        match_format_label_q.setStyleSheet("font-size: 13px;font-weight: 500;")
        self.match_format_box_q = QComboBox()
        self.match_format_box_q.addItem("Best of one", 1)
        self.match_format_box_q.addItem("Race to 3", 3)
        self.match_format_box_q.addItem("Race to 4", 4)
        self.match_format_box_q.addItem("Race to 5", 5)
        self.match_format_box_q.addItem("Race to 7", 7)

        match_format_label_s = QLabel("Semi-final Games:")
        match_format_label_s.setStyleSheet("font-size: 13px;font-weight: 500;")
        self.match_format_box_s = QComboBox()
        self.match_format_box_s.addItem("Best of one", 1)
        self.match_format_box_s.addItem("Race to 3", 3)
        self.match_format_box_s.addItem("Race to 4", 4)
        self.match_format_box_s.addItem("Race to 5", 5)
        self.match_format_box_s.addItem("Race to 7", 7)

        match_format_label_f = QLabel("Final Games:")
        match_format_label_f.setStyleSheet("font-size: 13px;font-weight: 500;")
        self.match_format_box_f = QComboBox()
        self.match_format_box_f.addItem("Best of one", 1)
        self.match_format_box_f.addItem("Race to 3", 3)
        self.match_format_box_f.addItem("Race to 4", 4)
        self.match_format_box_f.addItem("Race to 5", 5)
        self.match_format_box_f.addItem("Race to 7", 7)

        self.match_frame_layout.addWidget(match_format_label)
        self.match_frame_layout.addWidget(match_format_label_n)
        self.match_frame_layout.addWidget(self.match_format_box_n)
        self.match_frame_layout.addWidget(match_format_label_q)
        self.match_frame_layout.addWidget(self.match_format_box_q)
        self.match_frame_layout.addWidget(match_format_label_s)
        self.match_frame_layout.addWidget(self.match_format_box_s)
        self.match_frame_layout.addWidget(match_format_label_f)
        self.match_frame_layout.addWidget(self.match_format_box_f)
        f_layout.addWidget(match_frame)

        # Group stage selector
        group_frame = QFrame()
        group_frame.setStyleSheet("background-color: #2b2b2b;")
        self.group_frame_layout = QGridLayout(group_frame)

        groups_yesorno_label = QLabel("Include Groups:")
        groups_yesorno_label.setStyleSheet("font-size: 15px;font-weight: 500;")
        self.groups_button = QPushButton("No")
        self.groups_button.setStyleSheet("background-color: red")
        self.groups_button.clicked.connect(self.on_groups_toggled)

        # group number selector defined
        self.group_num_label = QLabel("Num Groups:")
        self.group_num_label.setStyleSheet("font-size: 15px;font-weight: 500;")
        self.group_num_setting_box = QComboBox()

        # group format
        self.group_form_label = QLabel("Group Format:")
        self.group_form_label.setStyleSheet("font-size: 15px;font-weight: 500;")
        self.group_form_setting_box = QComboBox()
        self.group_form_setting_box.addItem("Half and Half", 0) # top half go to champs, bottom half go to shield, rounds down when odd
        self.group_form_setting_box.addItem("Top Half", 1) # top half go to champs, rounds down when odd
        self.group_form_setting_box.addItem("Top Three", 2) # top three go to champs

        self.group_frame_layout.addWidget(groups_yesorno_label, 0, 0)
        self.group_frame_layout.addWidget(self.groups_button, 0, 1)
        f_layout.addWidget(group_frame)

    def on_groups_toggled(self):
        if self.groups_button.text() == "No":
            self.groups_button.setText("Yes")
            self.groups_button.setStyleSheet("background-color: green")

            self.refresh_group_num_setting_box()

            self.group_frame_layout.addWidget(self.group_num_label, 1, 0)
            self.group_frame_layout.addWidget(self.group_num_setting_box, 2, 0)

            self.group_frame_layout.addWidget(self.group_form_label, 3, 0)
            self.group_frame_layout.addWidget(self.group_form_setting_box, 4, 0)
        else:
            self.groups_button.setText("No")
            self.groups_button.setStyleSheet("background-color: red")

            self.group_frame_layout.removeWidget(self.group_num_label)
            self.group_frame_layout.removeWidget(self.group_num_setting_box)

            self.group_frame_layout.removeWidget(self.group_form_label)
            self.group_frame_layout.removeWidget(self.group_form_setting_box)

    def refresh_group_num_setting_box(self, carry=0):
            num_players = self.selected_players_list.count() + carry

            self.group_num_setting_box.clear()

            for i in range(4, 9):
                option = num_players // i
                
                if option != 0 and not num_players % i:
                    self.group_num_setting_box.addItem(f"{str(option)} Groups of {str(i)}", option)

    def submit_text_selected(self, player):

        self.refresh_group_num_setting_box(1)

        super().submit_text_selected(player)
        
    def on_populate_list(self): # for debugging
        players = ["Wilf Moncrieff", "Robert Fry", "Jak Dables", "Wilf Howard", "Dylan Nolan", "Will Vickers", "Paaras Padhiar", "Elijah Brook", "Malachi Bielby", "George Worsley", "Evan Morris", "Osian Drake", "Henry Myatt", "Theo Mason", "Otto Ashton", "Andrew Collins"]
        
        for player in players:
            self.selected_players_list.addItem(QListWidgetItem(player))

    def accept(self): # called when accept button is called
        # checks
        if self.title_text_box.text() == "":
            return

        settings = dict()

        settings["title"] = self.title_text_box.text()
        settings["seed"] = self.seeding_setting_box.currentText()
        settings["ran"] = self.randomness_slider.value()
        settings["elo_count"] = self.elo_count_button.text()

        settings["match_format"] = dict()
        settings["match_format"]["normal"] = self.match_format_box_n.currentData()
        settings["match_format"]["qfinal"] = self.match_format_box_q.currentData()
        settings["match_format"]["sfinal"] = self.match_format_box_s.currentData()
        settings["match_format"]["final"] = self.match_format_box_f.currentData()

        settings["num_players"] = self.selected_players_list.count()

        if self.groups_button.text() == "Yes":
            settings["groups"] = dict()
            settings["groups"]["num"] = self.group_num_setting_box.currentData()
            settings["groups"]["form"] = self.group_form_setting_box.currentData()
        else:
            settings["groups"] = None

        participants = [self.selected_players_list.item(i).text() for i in range(self.selected_players_list.count())]

        self.signal.emit(participants, settings)
        self.close()