from ..queries import add_game, add_player, add_semester, add_session, get_player_id_from_name
from ..schema import create_tables

create_tables(dest="extradata.db")

with open("Client/database/prev_data/25-26sm1.txt", "r") as file:
    sm1 = file.read()

with open("Client/database/prev_data/25-26sm2.txt", "r") as file:
    sm2 = file.read()

#with open("client/test.txt", "r") as file:
#    sm1 = file.read()

# clean data
sm1 = sm1.split("\n")
sm1 = list(filter(lambda x: x != "", sm1))

sm2 = sm2.split("\n")
sm2 = list(filter(lambda x: x != "", sm2))

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

    return sessions

def add_sessions_db(sessions, sm):

    sem_id = add_semester(sm, dest="extradata.db")

    for session in sessions:
        ses_id = add_session(sem_id, session[0], dest="extradata.db")

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

            add_player(player, dest="extradata.db")

        for game in games:

            if game[2] == "1":
                winner = game[0]
                loser = game[1]
            if game[3] == "1":
                winner = game[1]
                loser = game[0]

            winner_id = get_player_id_from_name(winner, dest="extradata.db")
            loser_id = get_player_id_from_name(loser, dest="extradata.db")

            add_game(ses_id, winner_id, loser_id, winner_id, dest="extradata.db")

sm1_sessions = clean_to_sessions(sm1)
sm2_sessions = clean_to_sessions(sm2)

add_sessions_db(sm1_sessions, "2025-2026.1")
add_sessions_db(sm2_sessions, "2025-2026.2")