import numpy as np

from PySide6.QtCore import Qt

from .utils_classes import Settings
    
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
        
    return players

def remove_item_from_qlist(list_widget, text):
    matches = list_widget.findItems(text, Qt.MatchFlag.MatchExactly)
    
    for item in matches:
        row = list_widget.row(item)
        removed_item = list_widget.takeItem(row)
        
        del removed_item

def clear_layout(layout):
    if layout is not None:
        while layout.count():
            
            item = layout.takeAt(0)
            widget = item.widget()
            
            if widget is not None:
                widget.setParent(None)
                
def calc_elo_change(a, b) -> tuple[float, float]: # where A is the winner

    s = Settings()
    config = s.load_settings()["elo_vars"]

    # define the constants
    BASE = config["base"]
    SCALE_FACTOR = config["scale_factor"] # controls the trend value (thousends)
    
    # controls how much a win or loss effects the elo change
    k_factor_a = 72
    k_factor_b = 72

    # calc probablity for each player to win given the ratings
    Ea = 1 / (1 + (BASE ** ((b - a) / SCALE_FACTOR)))
    Eb = 1 - Ea
    
    # calc the change in ratings due to the outcome
    Ra = k_factor_a * (1 - Ea) # a won
    Rb = k_factor_b * (0 - Eb) # b lost

    return (Ra, Rb)