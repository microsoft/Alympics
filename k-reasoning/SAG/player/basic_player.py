class Player():
    def __init__(self, name, water_requirement, daily_salary):
        self.name = name
        self.biddings=[]
        self.cur_round = -1

        self.requirement = water_requirement
        self.daily_salary = daily_salary
        self.balance = 0
        self.hp = 8
        self.no_drink = 1
        self.maximum_health = 10

        self.logs = None
    
    def success_bid(self):
        """
        Update self status when succeeds the bids
        """
        self.hp += 2
        self.hp = min(self.maximum_health, self.hp)
        self.balance -= self.last_bidding
        self.no_drink = 1
    
    def unsuccess_bid(self):
        """
        Update self status when fails the bids
        """
        self.hp -= self.no_drink
        self.no_drink += 1
        if self.hp <= 0:
            print(self.name + "is out of game!")
    
    def get_salary(self):
        self.balance += self.daily_salary

    def start_round(self, round: int, supply: int):
        self.cur_round = round

    def act(self):
        raise NotImplementedError
    
    def notice_round_result(self, round, bidding_info, win, bidding_details):
        raise NotImplementedError
    
    def notice_elimination(self, info):
        pass
    
    def update_public_info(self,round, history_biddings, player_stauts):
        pass

    def end_round(self):
        pass

    @property
    def last_bidding(self):
        return self.biddings[-1]
    
    def get_status(self, print_ = False):
        if print_:
            print(f"NAME:{self.name}\tBALANCE:{self.balance}\tHEALTH POINT:{self.hp}\tNO_DRINK:{self.no_drink}\n\n")
        return f"NAME:{self.name}\tBALANCE:{self.balance}\tHEALTH POINT:{self.hp}\tNO_DRINK:{self.no_drink}"