import networkx as nx
import itertools

from networkx import max_weight_matching

class LeagueRoundBuilder():
    def __init__(self, players):

        self.players = list(players)
        self.num_players = len(self.players)
        self.odd = False
        
        self.rounds_played = []
        self.rounds_left = True
        
        self.G = nx.Graph()
        
        # Handle odd number of players
        if self.num_players % 2 == 1:
            self.num_players += 1
            self.players.append("Dummy")
            
            self.odd = True
        
        self.G.add_nodes_from(self.players) # add players to the graph
        for a, b in itertools.combinations(self.players, 2): # add connections between players
            self.G.add_edge(a, b)

    def add_players(self, players_to_add):
        
        self.players_to_add = list(players_to_add)
        
        if len(self.players_to_add) % 2 == 1 and self.odd:  # if creating even number of players
            self.players.remove("Dummy")
            
            self.G.remove_node("Dummy")
            
            self.odd = False
            
        elif len(self.players_to_add) % 2 == 1:  # if creating odd number of players
            self.players_to_add.append("Dummy")
            
            self.odd = True
            
        
        self.players.extend(self.players_to_add)
        self.num_players = len(self.players)
        
        self.G.add_nodes_from(self.players_to_add) # add players to the graph
        
        for a, b in itertools.combinations(self.players, 2): # add connections between players
            self.G.add_edge(a, b)
            
        # make sure all previous matches played are removed from the graph again
        for r in self.rounds_played:
            self.remove_played_matches(r)
            
    def remove_players(self, players_to_remove):
        
        self.players_to_remove = list(players_to_remove)
        
        if len(self.players_to_remove) % 2 == 1 and self.odd: # if creating even number of players
            self.players.remove("Dummy")
            
            self.G.remove_node("Dummy")
            
            self.odd = False
            
        elif len(self.players_to_remove) % 2 == 1: # if creating odd number of players
            self.players.append("Dummy")
            
            self.odd = True
            
        
        self.players = list(set(self.players) - set(self.players_to_remove))
        self.num_players = len(self.players)
        
        self.G.remove_nodes_from(self.players_to_remove) # remove players to the graph
        for a, b in itertools.combinations(self.players, 2): # add connections between players
            self.G.add_edge(a, b)
            
        # make sure all previous matches played are removed from the graph again
        for r in self.rounds_played:
            self.remove_played_matches(r)

    def create_round(self):
        
        round_ = []

        round_ = max_weight_matching(self.G, maxcardinality=True)
        
        self.remove_played_matches(round_)
        self.rounds_played.append(round_)
        
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
                
        return round_, bye
    
    def remove_round(self):
        
        round_ = self.rounds_played[-1] # gets the last round
        
        for u, v in round_:
            
            self.G.add_edge(u, v)
        
        self.rounds_played.pop() # deletes the last round
        self.rounds_left = True
    
    def remove_played_matches(self, round_):
        
        # Remove used matches so they can't repeat
        for u, v in round_:
            
            if self.G.has_edge(u, v): # check if the edge exists and if it doesn't don't attempt to remove
                self.G.remove_edge(u, v)

if __name__ == "__main__" and False:
    players = ["Wilf", "Fred", "Jon", "Fin"]
        
    build = LeagueRoundBuilder(players)
    round1 = build.create_round()
    print(round1)
    
    build.add_players(["Evan"])
    
    round1 = build.create_round()
    print(round1)
    
    round1 = build.create_round()
    print(round1)
    round1 = build.create_round()
    print(round1)
    round1 = build.create_round()
    print(round1)
    round1 = build.create_round()
    print(round1)
    round1 = build.create_round()
    print(round1)
    round1 = build.create_round()
    print(round1)
    round1 = build.create_round()
    print(round1)

if __name__ == "__main__" and False:    
    players = ["name1", "name2", "name3", "name4"]
        
    build = LeagueRoundBuilder(players)
    round1 = build.create_round()
    print(round1)

    build.add_players(["new1"])

    round2 = build.create_round()
    print(round2)

    build.add_players(["new2"])

    round3 = build.create_round()
    print(round3)

    build.add_players(["verynew1", "verynew2"])

    round4 = build.create_round()
    print(round4)
    round5 = build.create_round()
    print(round5)
    round6 = build.create_round()
    print(round6)
    round7 = build.create_round()
    print(round7)

    build.remove_players(["name1"])

    round8 = build.create_round()
    print(round8)
    round9 = build.create_round()
    print(round9)
    round10 = build.create_round()
    print(round10)
    round11 = build.create_round()
    print(round11)
    round12 = build.create_round()
    print(round12)