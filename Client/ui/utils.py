import numpy as np

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

def round_robin_schedule(arr):
    players = list(arr)
    num_players = len(players)
    
    # Handle odd number of players
    odd = False
    if num_players % 2 == 1:
        num_players += 1  # Add a dummy player
        players.append("Dummy")
        odd = True
    
    rounds = []
    byes = []
    
    for rnd in range(num_players - 1):
        pairs = []
        
        for i in range(num_players // 2):
            p1 = players[i]
            p2 = players[num_players - 1 - i]
            
            # Skip dummy player
            if odd and p1 == "Dummy":
                byes.append(p2)
                continue
            
            if odd and p2 == "Dummy":
                byes.append(p1)
                continue
            
            pairs.append((p1, p2))
            
        rounds.append(pairs)
        
        # Rotate players (except first)
        players[1:] = np.roll(players[1:], 1)
    
    return rounds, byes

class LeagueRoundBuilder():
    def __init__(self, players):
        
        # shuffle the list of players randomly
        rng = np.random.default_rng()
        random_players = rng.permutation(players)
        
        self.players = list(random_players)
        self.used_pairs = set()
        
    def round_robin_schedule(self):
        players = self.players
        num_players = len(players)
        
        # Handle odd number of players
        odd = False
        if num_players % 2 == 1:
            num_players += 1  # Add a dummy player
            players.append("Dummy")
            odd = True
        
        rounds = []
        byes = []
        
        if not odd:
            byes = None
        
        for rnd in range(num_players - 1):
            pairs = []
            
            for i in range(num_players // 2):
                p1 = players[i]
                p2 = players[num_players - 1 - i]
                
                # Skip dummy player
                if odd and p1 == "Dummy":
                    byes.append(p2)
                    continue
                
                if odd and p2 == "Dummy":
                    byes.append(p1)
                    continue
                
                pairs.append((p1, p2))
                
            rounds.append(pairs)
            
            # Rotate players (except first)
            players[1:] = np.roll(players[1:], 1)
        
        self.rounds = rounds
        self.byes = byes
    
    def round_complete(self, round_number):
        
        if self.used_pairs == None:
            self.used_pairs = set()
        
        self.used_pairs.update(set(self.rounds[round_number]))
        
    def add_players(self, players_to_add):
        
        self.players.extend(list(players_to_add))