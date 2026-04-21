import csv
import numpy as np

from database.queries import get_all_players_name

def check_for_new_players(players):
    
    db_players = get_all_players_name()
    
    if (set(players) - set(db_players)):

        new_players = list(set(players) - set(db_players))
        print("New players:", new_players)
        
        return new_players
        
    else:
        return []
    
def clean_name(name):
    """ Make a input clean as required by the program """
    
    name = name.lower()
    name = name.title()
    name = name.strip()
    
    return name

def load_scale():
    with open("Client/config.csv", mode="r") as file:
        
        reader = csv.DictReader(file)  # read CSV as dictionary
        
        for row in reader:
            scale = float(row["scale"])
            return scale
        
def save_scale(scale: float):
    with open("Client/config.csv", mode="w", newline="") as file:
        
        writer = csv.writer(file)
        
        writer.writerow(["scale"])  # header row
        writer.writerow([scale])     # data row

def remove_menu(menu_bar, menu_to_remove):

    for action in menu_bar.actions():
        if action.text() == menu_to_remove:
            
            menu_bar.removeAction(action)

            action.menu().deleteLater()
            break

    return menu_bar

def get_players_from_qlist(q_list):
    players = []
    
    for i in range(q_list.count()):
        item = q_list.item(i)
        players.append(item.text())
        
    return players

def clear_layout(layout):
    if layout is not None:
        while layout.count():
            
            item = layout.takeAt(0)
            widget = item.widget()
            
            if widget is not None:
                widget.setParent(None)
                
def calc_elo_change(a, b, games_a, games_b): # where A is the winner

    # define the constants
    BASE = 10
    SCALE_FACTOR = 600 # controls the trend value (thousends)
    
    def placement_factor(games):
        # returns a factor when games = 0 of 2.71 (e)
        # drops off slowly until at games = 10 the multiple is 1
        
        return 1 + np.e - np.e ** (0.1 * games)
    
    # controls how much a win or loss effects the elo change
    k_factor_a = 72
    k_factor_b = 72
    
    # check for placements
    if games_a < 10:
        k_factor_a = k_factor_a * placement_factor(games_a)

    if games_b < 10:
        k_factor_b = k_factor_b * placement_factor(games_b)

    # calc probablity for each player to win given the ratings
    Ea = 1 / (1 + (BASE ** ((b - a) / SCALE_FACTOR)))
    Eb = 1 - Ea
    
    # calc the change in ratings due to the outcome
    Ra = k_factor_a * (1 - Ea) # a won
    Rb = k_factor_b * (0 - Eb) # b lost

    return (Ra, Rb)