from resources.colours import DARK, TEXT, LINE, ACCENT, MUTED


def _scrollbar_stylesheet(bg: str) -> str:
    return f"""
        QScrollBar:vertical {{
            background:{bg}; width:10px; margin:0px; border:none;
        }}
        QScrollBar::handle:vertical {{
            background:{LINE}; border-radius:5px; min-height:20px;
        }}
        QScrollBar::handle:vertical:hover {{ background:{MUTED}; }}
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
            background:{LINE}; border-radius:5px; min-width:20px;
        }}
        QScrollBar::handle:horizontal:hover {{ background:{MUTED}; }}
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