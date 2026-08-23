import itertools, random, os, json
import networkx as nx
import numpy as np


class IdGen:
    def __init__(self, start=0):
        self._next_id = start

    def generate(self):
        id_ = self._next_id
        self._next_id += 1
        return id_

class Settings():
    def __init__(self):
        self.DEFAULT_SETTINGS = {
        "scale": 0.75,
        }

        self.SETTINGS_FILE = "settings.json"

    def load_settings(self):
        if os.path.exists(self.SETTINGS_FILE):
            
            with open(self.SETTINGS_FILE, "r") as f:
                return json.load(f)
            
        self.save_settings(self.DEFAULT_SETTINGS)
        return self.DEFAULT_SETTINGS.copy()

    def save_settings(self, settings):
        
        with open(self.SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)

from networkx import max_weight_matching

class SessionBuilder():
    def __init__(self):

        self.players = []
        self.num_players = len(self.players)
        
        self.rounds_played = []
        self.byes = []
        self.rounds_left = True
        
        self.G = nx.Graph()
        
        self.rng = np.random.default_rng()

    def update_players(self, players_to_update):
        """ Updates the list of players in the builder to match the list of players in the seed """
        
        # remove players that are no longer in the seed
        players_to_remove = list(set(self.players) - set(players_to_update))
        self.remove_players(players_to_remove)
        
        # add new players that are in the seed but not in the builder
        players_to_add = list(set(players_to_update) - set(self.players))
        self.add_players(players_to_add)
        
        # add a dummy player if the number of players is odd
        if len(self.players) % 2 == 1:
            
            if "Dummy" not in self.players:
                self.add_players(["Dummy"])
                
        # remove the dummy player if the number of players is even
        else:
            if "Dummy" in self.players:
                self.remove_players(["Dummy"])

    def add_players(self, players_to_add):
        
        self.players_to_add = list(set(players_to_add) - set(self.players)) # remove duplicates and players already in the list
            
        self.players = list(set(self.players + self.players_to_add))
        self.num_players = len(self.players)
        
        self.G.add_nodes_from(self.players_to_add) # add players to the graph
        
        for a, b in itertools.combinations(self.players, 2): # add connections between players
            
            ran_float = self.rng.random()
            
            self.G.add_edge(a, b, weight=1000 + ran_float)
            
        # make sure all previous matches played are removed from the graph again
        for r in self.rounds_played:
            self.remove_played_matches(r)
            
    def remove_players(self, players_to_remove):
        
        self.players_to_remove = list(players_to_remove)
        
        self.players = list(set(self.players) - set(self.players_to_remove))
        self.num_players = len(self.players)
        
        self.G.remove_nodes_from(self.players_to_remove) # remove players to the graph
        for a, b in itertools.combinations(self.players, 2): # add connections between players
            
            ran_float = self.rng.random()
            
            self.G.add_edge(a, b, weight=1000 + ran_float)
            
        # make sure all previous matches played are removed from the graph again
        for r in self.rounds_played:
            self.remove_played_matches(r)

    def create_round(self):
        
        round_ = []

        round_ = max_weight_matching(self.G, maxcardinality=True)
        
        self.remove_played_matches(round_)
        
        bye = None
        
        # find the tuple that contains dummy and the pair that will be the bye
        for a, b in round_:
            if a == "Dummy":
                bye = b
                break
            elif b == "Dummy":
                bye = a
                break
            
        # Find the tuple that contains "Dummy"
        to_remove = None
        for t in round_:
            if "Dummy" in t:
                to_remove = t
                break

        # Remove it from the set
        if to_remove:
            round_.remove(to_remove)
            
        # Check if any rounds are left to play
        if self.G.number_of_edges() == 0:
            self.rounds_left = False
                
        self.rounds_played.append(round_)
        self.byes.append(bye)
        return round_, bye
    
    def remove_round(self):
        
        round_ = self.rounds_played[-1] # gets the last round
        
        for u, v in round_:
            ran_float = self.rng.random()
            
            self.G.add_edge(u, v, weight=1000 + ran_float)
        
        self.rounds_played.pop() # deletes the last round
        self.rounds_left = True
    
    def remove_played_matches(self, round_):
        
        # Remove used matches so they can't repeat
        for u, v in round_:
            
            if self.G.has_edge(u, v): # check if the edge exists and if it doesn't don't attempt to remove
                self.G.remove_edge(u, v)

    def estimate_rounds_left(self) -> int:
        
        edges = self.G.number_of_edges()
        nodes = self.G.number_of_nodes()
        
        return edges, nodes