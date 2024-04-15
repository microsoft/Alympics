class Player():
    ACTION_MAP = {
        0: "cooperate",
        1: "betray"
    }

    def __init__(self, name):
        self.name = name
        self.actions=[]
        self.cur_round = -1

        self.hp = 10
        self.logs = None
    
    def success_bid(self):
        """
        Update self status when succeeds the bids
        """
        pass
    
    def unsuccess_bid(self):
        """
        Update self status when fails the bids
        """
        self.hp -= 1

    def start_round(self, round: int):
        self.cur_round = round

    def act(self):
        raise NotImplementedError
    
    def notice_round_result(self, round, action_info, win, action_details):
        raise NotImplementedError
    
    def notice_elimination(self, info):
        pass
    
    def update_public_info(self,round, history_actions, player_stauts):
        pass

    def end_round(self):
        pass

    def to_action(self, choice):
        return self.ACTION_MAP[choice]

    @property
    def last_action(self):
        return self.actions[-1]
    
    def get_status(self, print_ = False):
        if print_:
            print(f"NAME:{self.name}\tHEALTH POINT:{self.hp}\n\n")
        return f"NAME:{self.name}\tHEALTH POINT:{self.hp}"