import networkx as nx
import itertools
import numpy as np
import random

from networkx import max_weight_matching

class SessionBuilder():
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

from database.queries import get_player

class TournamentBuilder():
    def __init__(self, players, settings):

        self.player_names = players
        self.settings = settings
        
        self.random_amount = 2 # higher = more random
        
        self.rounds = []

        # create graph of players with no connections
        self.G = nx.Graph()
        self.G.add_nodes_from(self.player_names)

        self.get_players_info(self.player_names)
        
        print(settings)
        
    def get_players_info(self, player_names):
        """ From the list of player names, create a list of dicts of name and elo """
        self.players = []

        for player in player_names:
            info = get_player(player)
            
            self.players.append({"name": player, "elo": info[0][6]})
        
    def define_weight(self):
        # define weight function as elo based
        if self.settings["seed"] == "Elo":
            def weight(p1, p2):
                diff = abs(p1["elo"] - p2["elo"])

                rng = np.random.default_rng()
                ran_factor = (rng.random() - 0.5) * (self.settings["ran"] * self.random_amount)

                return 1 / (1 + (diff + ran_factor))
            
            # order a list of seed
            self.seed_order = sorted(self.players, key=lambda x: x["elo"], reverse=True)

        # define weight function as semester leaderboard based
        if self.settings["seed"] == "Semester Leaderboard":
            pass

        # define weight function as random
        if self.settings["seed"] == "Random":
            def weight(p1, p2):
                rng = np.random.default_rng()
                return rng.random() * 100
            
            self.seed_order = self.players
            random.shuffle(self.seed_order)

        self.weight_func = weight

    def start_tournament(self, player_names: list[str]) -> list[tuple[str, str]]:
        """ Returns a set of the pairings of players """
        
        # calculate amount of rounds
        for n in range(1, self.settings["num_players"] + 1):
            if self.settings["num_players"] // (2 ** n) == 1:
                break
            
        self.num_rounds = n
        
        # round calculation
        self.get_players_info(player_names)

        for a, b in itertools.combinations(self.players, 2): # add connections between players
            
            w = self.weight_func(a, b)
            self.G.add_edge(a["name"], b["name"], weight=w)

        round_ =  list(max_weight_matching(self.G, maxcardinality=True))
        
        self.rounds.append(round_)

        return round_


import matplotlib.pyplot as plt

from database.queries import get_player, get_player_games
from database.objects import PlayerObj

class StatisticsBuilder():
    def __init__(self, player_name):
        # player object
        player_info = get_player(player_name)
        player_games = get_player_games(player_name)

        # make an object that holds all the info on the player
        print(player_info)
        self.player = PlayerObj(player_info, player_games)

    def display_player_stats(self):
        
        # cleanup figures
        plt.close("all")

        # visual data
        points = [0]
        wins = [0]
        elo = [1000.0]
        games_played = [0]
        winrate = []
        
        for i, game in enumerate(self.player.games_played_info):
            # update games played
            games_played.append(games_played[i] + 1)
            
            # check if won
            if game[4] == self.player.player_id:
                wins.append(wins[i] + 1)
                points.append(points[i] + game[5])
                elo.append(elo[i] + game[6])
            
            # if not won
            else:
                wins.append(wins[i])
                points.append(points[i])
                elo.append(elo[i] + game[7])
            
            # track winrate
            if games_played[i] == 0:
                pass

            else:
                winrate.append(100 * (wins[i] / games_played[i]))

            
        fig1, ax1 = plt.subplots()
        
        ax1.plot(games_played, wins, label="Wins")

        ax1.set_title("Wins Plot")
        ax1.set_xlabel("Games Played")
        ax1.set_ylabel("Wins")
        
        ax1.legend()
        
        fig2, ax2 = plt.subplots()
        
        copy = games_played.copy()
        copy.pop(0)
        copy.pop(0)
        
        ax2.plot(copy, winrate, label="Winrate")
        
        ax2.set_title("Winrate Plot")
        ax2.set_xlabel("Games Played")
        ax2.set_ylabel("Winrate")

        ax2.set_ybound(0, 100)
        
        ax2.legend()
        
        fig3, ax3 = plt.subplots()
        
        ax3.plot(games_played, elo, label="Elo")
        
        ax3.set_title("Elo Plot")
        ax3.set_xlabel("Games Played")
        ax3.set_ylabel("Elo")
        
        ax3.legend()
        
        return (fig1, fig2, fig3)
    
from database.db import get_connection
from database.queries import get_player_num_games_played, get_player_id_by_name
    
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
    
    def semester(self):
        conn = get_connection()
        cursor = conn.cursor()

        # list of all semester ids
        cursor.execute("""
            SELECT semester_id FROM semester               
        """)
        
        semester_id_list = cursor.fetchall()
        
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

        # list of all session ids
        cursor.execute("""
            SELECT session_id FROM sessions
        """)
        
        session_id_list = cursor.fetchall()
        
        conn.close()
        
        games_per_session = []
        players_per_session = []
        
        # sort games into sessions
        for i in range(len(session_id_list)): # loop though sessions
            games_per_session.append([])
            for game in self.games: # loop though games and make lists of the same session
                if session_id_list[i][0] == game[1]:
                    games_per_session[i].append(game)
                
        # sort players in each session into a new list
        for session in games_per_session:
            names = set()
            for game in session:
                
                names.add((game[6], 0.0))  # name at index 6
                names.add((game[8], 0.0))  # name at index 8
            
            names.add(((game[0], game[1], game[4]), -1)) # add data about session to the set
                    
            players_per_session.append(list(names))
            
        # add up points to each of the players from the list of all games this session
        for n, session in enumerate(games_per_session):
            
            for game in session:
                
                for i, (name, score) in enumerate(players_per_session[n]):
                    if name == game[10]:
                        players_per_session[n][i] = (name, score + game[11])
          
        in_order = []
                  
        for player in players_per_session:
            in_order.append(sorted(player, key=lambda x: x[1], reverse=True))
        
        return in_order    
    
    def alltime_points(self):
        
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name, points, elo FROM players
        """)
    
        players = cursor.fetchall()
        players_copy = players.copy()
        
        # to remove players that havent played much from the alltime leaderboard
        for player in players:
            num_games = get_player_num_games_played(get_player_id_by_name(player[0]))
            
            if num_games < 10:
                players_copy.remove(player)
        
        # order the leaderboard
        in_order = sorted(players_copy, key=lambda x: x[1], reverse=True)

        return in_order
    
    def alltime_elo(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name, points, elo FROM players
        """)
    
        players = cursor.fetchall()
        
        # to remove players that havent played much from the alltime leaderboard
        for player in players:
            num_games = get_player_num_games_played(get_player_id_by_name(player[0]))
            
            if num_games < 10:
                players.remove(player)

        in_order = sorted(players, key=lambda x: x[2], reverse=True)

        return in_order

    def collect_leaderboards(self):
        
        sessions = self.session()
        semesters = self.semester()
        alltime_points = self.alltime_points()
        alltime_elo = self.alltime_elo()
        
        return semesters, sessions, alltime_points, alltime_elo