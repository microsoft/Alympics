from random import randint
import numpy as np

class Player():
    def __init__(self, name):
        self.name = name
        self.hp = 10
        self.biddings=[]
        self.cur_round = -1

        self.logs = None

    def start_round(self, round: int):
        self.cur_round = round

    def act(self):
        raise NotImplementedError
    
    def notice_round_result(self, round, bidding_info, round_target, win, bidding_details, history_biddings):
        raise NotImplementedError

    def end_round(self):
        pass

    def deduction(self, deducted_hp):
        self.hp -= deducted_hp
    
    @property
    def last_bidding(self):
        return self.biddings[-1]
    
    def show_info(self, print_ = False):
        if print_:
            print(f"NAME:{self.name}\tHEALTH POINT:{self.hp}\n")
        return f"NAME:{self.name}\tHEALTH POINT:{self.hp}"


class ProgramPlayer(Player):
    is_agent=False
    def __init__(self, name, strategy, mean, std):
        self.name = name
        self.hp = 10

        self.biddings = []

        self.strategy=strategy
        self.mean = mean
        self.std = std

        self.logs = None

        if self.strategy=="monorand":
            self.std = randint(0, std)
            self.strategy="mono"
    
    def start_round(self, round):
        return
    
    def end_round(self):
        if self.strategy=="mono":
            # 
            self.mean -= self.std
    
    def notice_round_result(self, round, bidding_info, round_target, win, bidding_details, history_biddings):
        if self.strategy=="last":
            self.mean=round_target
        
    def set_normal(self, mean, std):
        self.normal = True
        self.mean = mean
        self.std = std
    
    def act(self):
        if self.strategy=="mono":
            bidding = self.mean
        else:
            bidding = np.random.normal(self.mean, self.std)
        bidding = min(max(int(bidding), 1),100)
        self.biddings.append(bidding) 