import csv

from database.queries import get_all_players

def check_for_new_players(players):
    
    db_players = get_all_players()
    
    if (set(players) - set(db_players)):

        new_players = list(set(players) - set(db_players))
        print("New players:", new_players)
        
        return new_players
        
    else:
        return []
    
def clean_name(name):
    
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