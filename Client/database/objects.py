class PlayerObj():
    def __init__(self, info_array):
        
        info = info_array[0]

        self.player_id = info[0]
        self.name = info[1]
        self.member = info[2]
        self.points = info[3]
        self.games_played = info[4]