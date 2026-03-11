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

def find_opponent(arr, player):
    for first, second in arr:
        if first == player:
            return second
        if second == player:
            return first
    return None