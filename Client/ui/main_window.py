import re

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
from ui.session_window import MainSessionWindow
from ui.custom_widgets import ConsoleWidget

from utils.utils import clean_name
from utils.utils_classes import Settings

from DB.db import (
                    get_connection, list_active_players, get_pid_from_name, get_player, create_round, get_match, get_name_from_pid, delete_round, get_round_id, get_session, list_all_semesters,
                   create_semester, create_session, list_all_players, add_player, record_match, delete_match, get_match_id, listen, get_rounds_in_session, delete_session, up_session_status, update_player_active,
                   get_semester_standings, get_alltime_standings, update_player_membership, list_all_matches, get_session_id_from_round, get_semester_id_from_round, list_all_sessions, complete_semester,
                   ACTIONS
                   )

from resources.colours import DARK, HEAD, PANEL_COL, LINE, TEXT, ACCENT, GREEN, RED
from resources.stylesheets import _scrollbar_stylesheet, _normal_text_stylesheet

class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        
        self.config = config

        self.scale = config["scale"]
        
        self.conn = get_connection()

        self.default_font = QFont("Segoe UI", round(self.scale * 18))
        self.small_font = QFont("Segoe UI", round(self.scale * 12))

        self.setWindowTitle("UoB SaPSoc Pool League Manager")
        self.setMinimumSize(int(1280 * self.scale), int(720 * self.scale))
        
        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.main_layout = QGridLayout(self.central)
        
        self.central.setAttribute(Qt.WA_StyledBackground, True)
        self.central.setStyleSheet(f"background: {DARK};")

        # optional: bring the native File/View menu bar onto the same palette
        self.menuBar().setStyleSheet(f"""
            QMenuBar {{
                background: {HEAD};
                color: {TEXT};
                border-bottom: 1px solid {LINE};
            }}
            QMenuBar::item {{
                background: transparent;
                padding: 4px 10px;
            }}
            QMenuBar::item:selected {{
                background: {LINE};
            }}
            QMenu {{
                background: {HEAD};
                color: {TEXT};
                border: 1px solid {LINE};
            }}
            QMenu::item:selected {{
                background: {LINE};
            }}
        """)
        
        self.console = ConsoleWidget()
        self.console.setFont(self.small_font)
        
        self.console.setMinimumWidth(int(100 * self.scale))
        self.console.setStyleSheet(_normal_text_stylesheet(self.scale))
        self.console.commandEntered.connect(self.handle_command)
        
        scroll = QScrollArea()
        scroll.setWidget(self.console)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet(_scrollbar_stylesheet(bg=PANEL_COL))
        self.main_layout.addWidget(scroll, 0, 0)

        # Create the menu bar
        self.create_menu_bar()
        
        def on_database_change(action_code, db_name, table_name, rowid):
            """ Logger Function for the console """
            action = ACTIONS.get(action_code, "UNKNOWN")
            
            if table_name == "players" and action == "UPDATE":
                player_info = get_player(self.conn, rowid)
                
                self.console.append(f"{player_info["first_name"]} {player_info["last_name"]} -- IS MEMBER: {player_info["is_member"]} -- IS ACTIVE {player_info["is_active"]}")
            
            else:
                self.console.append(f"{table_name} # {action}")
            
        listen(self.conn, on_database_change)

    def create_menu_bar(self):
        self.menu_bar = self.menuBar()  # Built-in QMainWindow menu bar

        # File menu
        self.file_menu = self.menu_bar.addMenu("File")

        # File menu actions
        test_action = QAction("New Session", self)
        test_action.triggered.connect(self.on_new_session)
        self.file_menu.addAction(test_action)
        
        self.file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)  # Built-in close method
        self.file_menu.addAction(exit_action)

        # View menu
        view_menu = self.menu_bar.addMenu("View")
        
        self.change_scale = QAction("Change Scale", self)
        self.change_scale.triggered.connect(self.on_change_scale)
        view_menu.addAction(self.change_scale)

    def handle_command(self, command: str):
        """ Handle commands entered in the console """
        
        def write_matches(path):
            # wipe file
            with open(path, "w") as file:
                pass
            
            matches = list_all_matches(self.conn)
            sessions = list_all_sessions(self.conn)
            semesters, _ = list_all_semesters(self.conn)
            
            round_tracker = None
            session_tracker = None
            semester_tracker = None

            for match in matches:
                session_id = get_session_id_from_round(self.conn, match["round_id"])
                semester_id = get_semester_id_from_round(self.conn, match["round_id"])
                
                if semester_id != semester_tracker:
                    semester_tracker = semester_id
                    
                    for target_sem in semesters:
                        if target_sem["semester_id"] == semester_id:
                            break
                    
                    with open(path, "a") as file:
                        file.write("######################################################################\n")
                        file.write(f"{target_sem["name"]}\n")
                                                
                if session_id != session_tracker:
                    session_tracker = session_id
                    
                    for target_session in sessions:
                        if target_session["session_id"] == session_id:
                            break
                        
                    with open(path, "a") as file:
                        file.write(".\n")
                        file.write(f"{target_session["session_date"]}\n")
                
                if match["round_id"] != round_tracker:
                    round_tracker = match["round_id"]
                    with open(path, "a") as file:
                        file.write(" \n")
                        
                if match["player1_id"] == match["winner_id"]:
                    winner = get_player(self.conn, match["player1_id"])
                    loser = get_player(self.conn, match["player2_id"])
                else:
                    winner = get_player(self.conn, match["player2_id"])
                    loser = get_player(self.conn, match["player1_id"])
                
                with open(path, "a") as file:
                    file.write(f"{winner["first_name"]}, {winner["last_name"]}, {loser["first_name"]}, {loser["last_name"]}, 1, 0\n")
        
        parts = command.split()

        if not parts:
            return

        cmd = parts[0].lower()

        if cmd == "help":
            self.console.append("Available commands:")
            self.console.append("  help - Show this help message")
            self.console.append("  clear/cls - Clear the console")
            self.console.append("  echo <text> - Echo the text back to the console")
            self.console.append("  run <window> - run the window specified 'session'")
            self.console.append("  save matches <path> - write all matches to a .txt file for safekeeping")
            self.console.append("  members <action> <first_name last_name> ... - update the membership status of a player")
            self.console.append("  semester end - completes the current semester")

        elif cmd == "cls" or cmd == "clear":
            self.console.clear()

        elif cmd == "echo":
            text = " ".join(parts[1:])
            self.console.append(text)

        elif cmd == "run":
            text = " ".join(parts[1:])
            
            if text == "session":
                self.on_new_session()
                
        elif cmd == "save":
            
            if parts[1] == "matches" and parts[2]:
                path = f"{parts[2]}.txt"
                write_matches(path)
                
            else:
                self.console.warn("Command not recognised - Expected format: save matches <path>")
                
        elif cmd == "members":
            
            # add members
            if parts[1] == "add":
                action = 1
            elif parts[1] == "remove":
                action = 0
            elif parts[1] == "removeall":
                for player in list_all_players(self.conn):
                    update_player_membership(self.conn, player["player_id"], 0)
                           
                return
            
            else:
                self.console.warn(f"Unknown Command: {parts[1]}")
                
            match = re.findall(r"<(.*?)>", command)
            
            if not match:
                self.console.warn("No Name Provided - Expected format: member <action> <fist_name last_name> ...")
                return
            
            for text in match:
                fn, ln = text.split(" ")
                fn = clean_name(fn)
                ln = clean_name(ln)
                
                pid = get_pid_from_name(self.conn, fn, ln)
                if pid:
                    update_player_membership(self.conn, pid, action)
                
                else:
                    self.console.warn("Player Doesn't exist")
                    return
                    
        elif cmd == "semester":
            
            def format_date(date):
                day, month, year = date.split(".")
                
                return f"{year}-{month}-{day} 00:00:00"
            
            if parts[1] == "end":
                sems, _ = list_all_semesters(self.conn)
                sessions = list_all_sessions(self.conn)
                complete_semester(self.conn, sems[-1]["semester_id"], format_date(sessions[-1]["session_date"]))
                    
        elif cmd == "ping":
            
            if parts[1] == "active":
                if parts[2]:
                    update_player_active(self.conn, int(parts[2]))
                else:
                    update_player_active(self.conn)
        
        else:
            self.console.append(f"Unknown Command: {cmd}")

    def on_new_session(self):
        
        self.session_window = MainSessionWindow(self.config)
        
        self.session_window.show()

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