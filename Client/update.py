from database.queries import add_game, add_player, add_semester, add_session, get_player_id_by_name
from database.schema import create_tables

create_tables()

semester_id = add_semester("2026.2")
session_id = add_session(semester_id, "27.01.2026")

with open("client/prev_match_data.txt", "r") as file:
    game_data = file.read()

game_data = game_data.split("\n")

# add all players that played a game
player_names = set()

games = []

for game in game_data:
    game = game.replace(",", "")
    game = game.split(" ")

    games.append(game)

    player_names.add(game[0])
    player_names.add(game[1])

for player in player_names:

    add_player(player)

for game in games:

    if game[2] == "1":
        winner = game[0]
        loser = game[1]
    if game[3] == "1":
        winner = game[1]
        loser = game[0]

    winner_id = get_player_id_by_name(winner)
    loser_id = get_player_id_by_name(loser)

    add_game(session_id, winner_id, loser_id, winner_id)