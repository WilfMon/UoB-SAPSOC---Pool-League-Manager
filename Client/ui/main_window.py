from PySide6.QtWidgets import QMainWindow, QLabel, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

from ui.setup_window import TextWindow

class MainWindow(QMainWindow):
    def __init__(self, scale=1.0):
        super().__init__()
        self.setWindowTitle("My PySide6 App")
        self.scale = scale

        self.setWindowTitle("My Dark Themed PySide6 App")
        self.setMinimumSize(int(1920 * scale), int(1080 * scale))

        label = QLabel("Hello, PySide6!", alignment=Qt.AlignCenter)
        self.setCentralWidget(label)
        
        # Create the menu bar
        self._create_menu_bar()

    def _create_menu_bar(self):
        menu_bar = self.menuBar()  # Built-in QMainWindow menu bar

        # File menu
        file_menu = menu_bar.addMenu("File")

        # File menu actions
        news_action = QAction("New Session", self)
        news_action.triggered.connect(self.on_news)
        file_menu.addAction(news_action)

        open_action = QAction("Open", self)
        open_action.triggered.connect(self.on_open)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)  # Built-in close method
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = menu_bar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.on_about)
        help_menu.addAction(about_action)

    # Action callbacks
    def on_news(self):
        self.text_window = TextWindow(scale=self.scale)
        self.text_window.submitted_participants.connect(self.participants_recived)
        
        self.text_window.show()
        
    def participants_recived(self, participants):
        print(participants)

    def on_open(self):
        print("Open file triggered!")

    def on_about(self):
        print("This is a PySide6 demo app.")