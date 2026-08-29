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
from ui.session_window import MainSessionWindow
from ui.custom_widgets import ConsoleWidget

from utils.utils import remove_menu, get_items_from_qlist, clear_layout
from utils.utils_classes import Settings

from resources.stylesheets import _scrollbar_stylesheet, _settings_controls_stylesheet, _title_text_stylesheet, _normal_text_stylesheet

class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        
        self.config = config

        self.scale = config["scale"]

        self.default_font = QFont("Segoe UI", round(self.scale * 18))
        self.small_font = QFont("Segoe UI", round(self.scale * 12))

        self.setWindowTitle("UoB SaPSoc Pool League Manager")
        self.setMinimumSize(int(1280 * self.scale), int(720 * self.scale))
        
        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.main_layout = QGridLayout(self.central)
        
        self.console = ConsoleWidget()
        self.console.setFont(self.small_font)
        
        self.console.setMinimumWidth(int(100 * self.scale))
        self.console.setStyleSheet(_normal_text_stylesheet(self.scale))
        
        self.console.commandEntered.connect(self.handle_command)
        self.main_layout.addWidget(self.console, 0, 0)

        # Create the menu bar
        self.create_menu_bar()

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
        
        parts = command.split()

        if not parts:
            return

        cmd = parts[0].lower()

        if cmd == "help":
            self.console.append("Available commands:")
            self.console.append("  help - Show this help message")
            self.console.append("  clear/cls - Clear the console")
            self.console.append("  echo <text> - Echo the text back to the console")

        elif cmd == "cls" or cmd == "clear":
            self.console.clear()

        elif cmd == "echo":
            text = " ".join(parts[1:])
            self.console.append(text)

        elif cmd == "run":
            text = " ".join(parts[1:])
            
            if text == "session":
                self.on_new_session()

        else:
            self.console.append(f"Unknown command: {cmd}")

    def on_new_session(self):
        
        self.session_window = MainSessionWindow(self.config)
        
        self.session_window.show()
        
    def on_edit_memberships(self):
        return
        self.update_membership_window = MembershipWindow(scale=self.scale, dest=self.dest)
        
        self.update_membership_window.show()

    def on_edit_data(self):
        return
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