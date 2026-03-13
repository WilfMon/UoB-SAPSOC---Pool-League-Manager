import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from pathlib import Path

from ui.main_window import MainWindow

from utils.utils import load_scale

def main():
    
    scale_factor = load_scale()
    
    # Enable high-DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    
    app.setFont(QFont("Segoe UI", round(scale_factor * 18)))
    
    # Load dark theme
    qss_file = Path(__file__).parent / "resources" / "styles" / "dark.qss"
    if qss_file.exists():
        with open(qss_file, "r") as f:
            app.setStyleSheet(f.read())
    
    window = MainWindow(scale=scale_factor)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()