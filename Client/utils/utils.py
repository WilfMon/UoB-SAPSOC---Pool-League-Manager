import numpy as np

from PySide6.QtWidgets import QListWidgetItem
from PySide6.QtCore import Qt

from .utils_classes import Settings
from database.db import elo_prob, get_player_current_elo_high_low, get_connection, list_active_players
    
def clean_name(name):
    """ Make a input clean as required by the program """
    
    name = name.lower()
    name = name.title()
    name = name.strip()
    
    return name

def clean_first_last_name(name):
    """ Make a input clean as required by the program """
    
    name = name.lower()
    name = name.title()
    name = name.strip()
    
    names = name.split(" ")
    
    return (names[0], names[1])

def remove_menu(menu_bar, menu_to_remove):

    for action in menu_bar.actions():
        if action.text() == menu_to_remove:
            
            menu_bar.removeAction(action)

            action.menu().deleteLater()
            break

    return menu_bar

def get_items_from_qlist(q_list):
    players = []
    
    for i in range(q_list.count()):
        item = q_list.item(i)
        players.append(item.text())
        
    return players if players != [] else None

def remove_item_from_qlist(list_widget, text):
    matches = list_widget.findItems(text, Qt.MatchFlag.MatchExactly)
    
    for item in matches:
        row = list_widget.row(item)
        removed_item = list_widget.takeItem(row)
        
        del removed_item
        
def remove_all_from_qlist(list_widget):
    
    items = get_items_from_qlist(list_widget)
    
    for item in items:
        remove_item_from_qlist(list_widget, item)

def clear_layout(layout):
    if layout is not None:
        while layout.count():
            
            item = layout.takeAt(0)
            widget = item.widget()
            
            if widget is not None:
                widget.setParent(None)

def clear_grid_after_row(layout, start_row: int):
    """
    Removes and deletes all widgets and items in layout at or after `start_row`.
    """
    # Iterate backwards to avoid index shifting issues
    for i in reversed(range(layout.count())):
        item = layout.itemAt(i)
        if item is None:
            continue

        # Get the row position of the item
        row, column, row_span, col_span = layout.getItemPosition(i)

        # Check if the item starts at or after the target row
        if row >= start_row:
            # Remove item from layout
            item_to_remove = layout.takeAt(i)

            # Safely delete the widget if it exists
            widget = item_to_remove.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()


def calc_match_quality(p1, p2, normalize=True):
    """
    Returns a normalized float that rates how good quality a game should be.\n
    Uses the diff in elo between players and the total elo of the players.
    """
    s = Settings()
    config = s.load_settings()
    
    q_factors = config["match_quality_factors"]
    
    _min = q_factors["min_quality"]
    _max = q_factors["max_quality"]
    e = q_factors["peak_factor"]
    
    raw_prob, _ = elo_prob(p1, p2)
    
    diff = np.sqrt((0.5 - raw_prob)**2 + e**2)
    total = p1["current_elo"] + p2["current_elo"]
    
    quality = (1 / diff) * q_factors["diff_factor"] + total / q_factors["total_elo_factor"]
    
    if not normalize:
        return quality
    
    q_norm = (quality - _min)/(_max - _min)
    
    return int(round(10*q_norm, 0))

def optimise_quality_vars():
    """
    Optimises the match quality variables to give a more accurate match quality rating.\n
    Uses the best and worst case possible
    """
    
    conn = get_connection()
    
    s = Settings()
    config = s.load_settings()
    
    high, low = get_player_current_elo_high_low()
    
    q_high = calc_match_quality(high, high, normalize=False)
        
    lows = [calc_match_quality(low, player, normalize=False) for player in list_active_players(conn)]
    q_low = min(lows)
    
    config["match_quality_factors"]["max_quality"] = q_high
    config["match_quality_factors"]["min_quality"] = q_low
    
    s.save_settings(config)
    
    return q_high, q_low