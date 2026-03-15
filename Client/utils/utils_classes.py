import networkx as nx
import itertools
import numpy as np

from networkx import max_weight_matching

class LeagueRoundBuilder():
    def __init__(self, players):

        self.players = list(players)
        self.num_players = len(self.players)
        self.odd = False
        
        self.rounds_played = []
        self.rounds_left = True
        
        self.G = nx.Graph()
        
        self.rng = np.random.default_rng()
                
        self.add_players(self.players)

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
            
            ran_float = self.rng.random()
            
            self.G.add_edge(a, b, weight=1000 + ran_float)
            
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
            
            ran_float = self.rng.random()
            
            self.G.add_edge(a, b, weight=1000 + ran_float)
            
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
            ran_float = self.rng.random()
            
            self.G.add_edge(u, v, weight=1000 + ran_float)
        
        self.rounds_played.pop() # deletes the last round
        self.rounds_left = True
    
    def remove_played_matches(self, round_):
        
        # Remove used matches so they can't repeat
        for u, v in round_:
            
            if self.G.has_edge(u, v): # check if the edge exists and if it doesn't don't attempt to remove
                self.G.remove_edge(u, v)

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
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT
                s.semester_id,
                g.session_id,
                g.games_id,
                sem.semester_name,
                s.session_date,
                p1.player_id AS player1_id,
                p1.name AS player1_name,
                p2.player_id AS player2_id,
                p2.name AS player2_name,
                w.player_id  AS winner_id,
                w.name       AS winner_name,
                g.points_to_winner
            FROM games g
            JOIN sessions s 
                ON g.session_id = s.session_id
            JOIN semester sem
                ON s.semester_id = sem.semester_id
            JOIN players p1
                ON g.player1_id = p1.player_id
            JOIN players p2
                ON g.player2_id = p2.player_id
            JOIN players w
                ON g.winner_id = w.player_id
            ORDER BY sem.semester_id, s.session_id, g.games_id;
        """)
        
        self.games = cursor.fetchall()
        conn.close()
        
        print(self.games)
    
    def semester(self):
        conn = get_connection()
        cursor = conn.cursor()

        # list of all semester ids
        cursor.execute("""
            SELECT semester_id FROM semester               
        """)
        
        semester_id_list = cursor.fetchall()
        print(semester_id_list)
        
        conn.close()
        
        games_per_semester = []
        players_per_semester = []
        
        # sort games into semesters
        for i in range(len(semester_id_list)): # loop though semesters
            games_per_semester.append([])
            for game in self.games: # loop though games and make lists of the same semester
                if semester_id_list[i][0] == game[0]:
                    games_per_semester[i].append(game)
                
        # sort players in each semester into a new list
        for semester in games_per_semester:
            names = set()
            for game in semester:
                
                names.add((game[6], 0.0))  # name at index 6
                names.add((game[8], 0.0))  # name at index 8
            
            names.add(((game[0], game[3]), -1)) # add data about semster to the set
                    
            players_per_semester.append(list(names))
            
        # add up points to each of the players from the list of all games this semester
        for n, semester in enumerate(games_per_semester):
            
            for game in semester:
                
                for i, (name, score) in enumerate(players_per_semester[n]):
                    if name == game[10]:
                        players_per_semester[n][i] = (name, score + game[11])
          
        in_order = []
                  
        for player in players_per_semester:
            in_order.append(sorted(player, key=lambda x: x[1], reverse=True))
        
        return in_order    

    def session(self):
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            WITH participants AS (
                SELECT session_id, player1_id AS player_id FROM games
                UNION ALL
                SELECT session_id, player2_id FROM games
            )
            SELECT 
                s.session_id,
                s.session_date,
                s.semester_id,
                p.player_id,
                p.name,
                COALESCE(SUM(CASE WHEN g.winner_id = p.player_id 
                                THEN g.points_to_winner ELSE 0 END), 0) AS total_points
            FROM sessions s
            JOIN participants pt 
                ON pt.session_id = s.session_id
            JOIN players p 
                ON p.player_id = pt.player_id
            LEFT JOIN games g 
                ON g.session_id = s.session_id 
                AND g.winner_id = p.player_id
            GROUP BY s.session_id, p.player_id
            ORDER BY s.session_id, total_points DESC, p.name;
        """)
        
        result = cursor.fetchall()
        
        cursor.execute("""
            SELECT session_id FROM sessions
        """)
        
        session_list = cursor.fetchall()
        conn.close()
        
        # order the leaderboard
        results_per_session = []
        
        for i in range(len(session_list)): # loop though sessions
            results_per_session.append([])
            
            for player in result:
                if player[0] == session_list[i][0]:
                    
                    if results_per_session[i] == []: # last item contains info about session
                        results_per_session[i].append((player[0], player[1], -1, player[2]))
                    
                    tup = (player[3], player[4], player[5])
                    
                    results_per_session[i].append(tup)
          
        in_order = []
                  
        for result in results_per_session:
            in_order.append(sorted(result, key=lambda x: x[2], reverse=True))
        
        return in_order
    
    def alltime(self):
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
            p.player_id,
            p.name,
            COALESCE(SUM(g.points_to_winner), 0) AS total_points
            FROM players p
            LEFT JOIN games g 
            ON g.winner_id = p.player_id
            GROUP BY p.player_id
            ORDER BY total_points DESC, p.name;   
        """)
        
        result = cursor.fetchall()
        conn.close()
        
        # order the leaderboard
        in_order = sorted(result, key=lambda x: x[2], reverse=True)
        
        return in_order
    
    def collect_leaderboards(self):
        
        sessions = self.session()
        semesters = self.semester()
        alltime = self.alltime()
        
        return semesters, sessions, alltime