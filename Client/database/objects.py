"""
Objects for statistics to utilize
"""

from .queries import get_player, get_player_games

class PlayerObj():
    """ A object that builds and contains player info """
    def __init__(self, player_name):
        
        player_info = get_player(player_name)[0]

        self.player_id = player_info[0]
        self.name = player_info[1]
        self.member = player_info[2]
        self.points = round(player_info[3], 2)
        self.num_games_played = player_info[4]
        self.wins = player_info[5]
        self.elo = player_info[6]
        
        self.games_played_info = get_player_games(player_name)
        
        self.winrate = round((self.wins / self.num_games_played) * 100, 1)
        
        if self.member:
            self.member_displayable = "Yes"
        else:
            self.member_displayable = "No"