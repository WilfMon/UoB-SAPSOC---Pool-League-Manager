from resources.colours import DARK, TEXT, LINE, ACCENT


def _settings_controls_stylesheet() -> str:
    return f"""
        QComboBox {{
            background: {DARK};
            color: {TEXT};
            border: 1px solid {LINE};
            border-radius: 6px;
            padding: 5px 10px;
            min-width: 150px;
        }}
        QComboBox:hover {{ border-color: {ACCENT}; }}
        QComboBox::drop-down {{ border: none; width: 22px; }}
        QComboBox QAbstractItemView {{
            background: {DARK};
            color: {TEXT};
            border: 1px solid {LINE};
            selection-background-color: {ACCENT};
            outline: none;
        }}
        QLineEdit {{
            background: {DARK};
            color: {TEXT};
            border: 1px solid {LINE};
            border-radius: 6px;
            padding: 5px 10px;
        }}
        QLineEdit:focus {{ border-color: {ACCENT}; }}
        QSpinBox {{
            background: {DARK};
            color: {TEXT};
            border: 1px solid {LINE};
            border-radius: 6px;
            padding: 4px 8px;
            min-width: 70px;
        }}
        QSpinBox:hover {{ border-color: {ACCENT}; }}
        QSlider::groove:horizontal {{
            height: 4px;
            background: {LINE};
            border-radius: 2px;
        }}
        QSlider::sub-page:horizontal {{
            height: 4px;
            background: {ACCENT};
            border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            width: 14px; height: 14px;
            margin: -5px 0;
            background: #ffffff;
            border-radius: 7px;
        }}
        QSlider::handle:horizontal:hover {{ background: {ACCENT}; }}
        QRadioButton {{
            color: {TEXT};
            spacing: 8px;
            background: transparent;
        }}
        QRadioButton::indicator {{
            width: 15px; height: 15px;
            border-radius: 8px;
            border: 1px solid {LINE};
            background: {DARK};
        }}
        QRadioButton::indicator:checked {{
            border: 1px solid {ACCENT};
            background: {ACCENT};
        }}
    """
 
def _scrollbar_stylesheet(bg: str) -> str:
    return f"""
        QScrollBar:vertical {{
            background:{bg}; width:10px; margin:0px; border:none;
        }}
        QScrollBar::handle:vertical {{
            background:#555; border-radius:5px; min-height:20px;
        }}
        QScrollBar::handle:vertical:hover {{ background:#777; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height:0px; width:0px; background:transparent; border:none;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background:{bg}; border:none;
        }}
        QScrollBar:horizontal {{
            background:{bg}; height:10px; margin:0px; border:none;
        }}
        QScrollBar::handle:horizontal {{
            background:#555; border-radius:5px; min-width:20px;
        }}
        QScrollBar::handle:horizontal:hover {{ background:#777; }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            height:0px; width:0px; background:transparent; border:none;
        }}
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background:{bg}; border:none;
        }}
    """

def _title_text_stylesheet() -> str:
    return f"""
            color: {ACCENT};
            font-weight: 700;
            letter-spacing: 1px;
            background: transparent;
            padding-left: 2px;
        """
        
def _normal_text_stylesheet(scale) -> str:
    return f"""
            color: {TEXT};
            font-weight: 500;
            font-size: {16 * scale}px;
            letter-spacing: 1px;
            background: transparent;
            padding-left: 2px;
        """