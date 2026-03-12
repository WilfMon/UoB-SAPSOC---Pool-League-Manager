class PlayerObj():
    def __init__(self, info_array, games_array):
        
        info = info_array[0]

        self.player_id = info[0]
        self.name = info[1]
        self.member = info[2]    
        self.points = round(info[3], 2)
        self.num_games_played = info[4]
        self.wins = info[5]
        
        self.games_played_info = games_array
        
        self.winrate = round((self.wins / self.num_games_played) * 100, 1)
        
        if self.member:
            self.member_displayable = "Yes"
        else:
            self.member_displayable = "No"