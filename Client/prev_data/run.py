import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))  # adds Client/ to path

from database.queries import add_game, add_player, add_semester, add_session, get_player_id_from_name
from database.schema import create_tables

file_name = "league.db"

create_tables(dest=file_name)

with open("prev_data/raw_data.txt", "r") as file:
    raw_data = file.read()

clean_data = raw_data.split("######################################################################")

#print(clean_data)

raw_semesters = []

for sem in clean_data:
    s = sem.split("\n")
    #print(s)
    s = list(filter(lambda x: x != "", s))
    #print(s)

    raw_semesters.append(s)

def split_to_sessions(semester_data):
    result = []
    current = []

    for item in semester_data:
        if item == ".":
            result.append(current)
            current = []
        else:
            current.append(item)

    result.append(current)

    result.append(result[0])
    
    result.pop(0)
    return result

def clean_to_sessions(sessions_data):
    sessions_data_copy = sessions_data.copy()
    sessions = []

    for k, i in enumerate(sessions_data):
        if i == ".":

            for j in range(k + 1, k + 999):
                try:
                    if sessions_data[j] == ".":
                        f = j - k
                        break
                except:
                    f = j - k
                    break

            sessions.append(sessions_data_copy[:f])

            for i in range(0, f):
                sessions_data_copy.pop(0)
                
    for session in sessions:
        session.pop(0)


    sessions.append(sessions_data[0])
    return sessions

def add_sessions_db(sessions):

    sm = sessions[-1][0]
    sessions.pop(-1)

    sem_id = add_semester(sm, dest=file_name)

    for session in sessions:
        ses_id = add_session(sem_id, session[0], dest=file_name)

        session.pop(0)

        player_names = set()
        games = []

        for game in session:

            game = game.replace(",", "")
            game = game.split(" ")

            p1 = f"{game[0]} {game[1]}"
            p2 = f"{game[2]} {game[3]}"

            game = [p1, p2, game[4], game[5]]

            player_names.add(game[0])
            player_names.add(game[1])

            games.append(game)

        for player in player_names:

            add_player(player, dest=file_name)

        for game in games:

            if game[2] == "1":
                winner = game[0]
                loser = game[1]
            if game[3] == "1":
                winner = game[1]
                loser = game[0]

            winner_id = get_player_id_from_name(winner, dest=file_name)
            loser_id = get_player_id_from_name(loser, dest=file_name)

            add_game(ses_id, winner_id, loser_id, winner_id, dest=file_name)

semesters = []

for sem in raw_semesters:
    semesters.append(split_to_sessions(sem))

for sem in semesters:
    add_sessions_db(sem)