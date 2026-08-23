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
#from ui.update_database_windows import DataWindow, MembershipWindow

from utils.utils import remove_menu, get_items_from_qlist, clear_layout
from utils.utils_classes import Settings, SessionBuilder

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