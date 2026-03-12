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

import numpy as np
import matplotlib.pyplot as plt

from database.queries import get_player, get_player_games
from database.objects import PlayerObj

class StatisticsBuilder():
    def __init__(self):
        pass

    def display_player_stats(self, player_name):
        
        # player object
        player_info = get_player(player_name)
        player_games = get_player_games(player_name)

        player = PlayerObj(player_info, player_games)
        
        # visual data
        points = [0]
        wins = [0]
        games_played = [0]
        
        for i, game in enumerate(player.games_played_info):
            games_played.append(games_played[i] + 1)
            
            # check if won
            if game[4] == player.player_id:
                wins.append(wins[i] + 1)
                points.append(points[i] + game[5])
            else:
                wins.append(wins[i])
                points.append(points[i])
            
        plt.plot(games_played, points)
        plt.plot(games_played, wins)
        plt.xlabel("Games Played")
        
        #plt.show()
        
        return player
    
from database.db import get_connection
    
class Leaderboard():
    def __init__(self):
        pass
    
    def session(self):
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
            s.session_id,
            s.session_date,
            p.player_id,
            p.name,
            SUM(g.points_to_winner) AS total_points
            FROM games g
            JOIN sessions s ON g.session_id = s.session_id
            JOIN players p ON g.winner_id = p.player_id
            GROUP BY s.session_id, p.player_id
            ORDER BY s.session_id, total_points DESC;    
        """)
        
        result = cursor.fetchall()
        conn.close()
        
        return result
    
    def semester(self):
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
            sem.semester_id,
            sem.semester_name,
            p.player_id,
            p.name,
            SUM(g.points_to_winner) AS total_points
            FROM games g
            JOIN sessions s ON g.session_id = s.session_id
            JOIN semester sem ON s.semester_id = sem.semester_id
            JOIN players p ON g.winner_id = p.player_id
            GROUP BY sem.semester_id, p.player_id
            ORDER BY sem.semester_id, total_points DESC;   
        """)
        
        result = cursor.fetchall()
        conn.close()
        
        return result
    
    def alltime(self):
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
            p.player_id,
            p.name,
            SUM(g.points_to_winner) AS total_points
            FROM games g
            JOIN players p ON g.winner_id = p.player_id
            GROUP BY p.player_id
            ORDER BY total_points DESC;    
        """)
        
        result = cursor.fetchall()
        conn.close()
        
        return result