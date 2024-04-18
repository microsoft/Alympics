from copy import deepcopy

round_number = round

class G08A():
    def __init__(self, players) -> None:
        self.all_players = players[::]
        self.survival_players = players[::]
        self.round_winner = {}

    def daily_bidding(self, players):
        Average = 0
        for player in players:
            player.act()
            Average += player.last_bidding
        
        Average /= len(players) 
        Target = round_number(Average * 0.8, 2)

        return Average, Target

    def round_deduction(self, players, winner):
        """
        player who did not win loses 1 HP
        """
        for player in players:
            if player.name not in winner:
                player.deduction(1)

    def check_winner(self, players, target):
        win_bid = sorted([(abs(player.last_bidding - target), player.last_bidding) for player in players])[0][1]
        winners = [player.name for player in players if player.last_bidding==win_bid]

        return winners, win_bid

    def check_tie(self, players):
        if len(players)<2: return False
        return len(set([player.last_bidding for player in players]))==1

    def run_single_round(self, round_id):
        for player in self.survival_players:
            player.start_round(round_id)

        Average, Target = self.daily_bidding(self.survival_players)

        Tie_status = self.check_tie(self.survival_players)
        WINNER_str = ""
        if Tie_status: # If all players choose the same number, there is no winner.
            WINNER = []
        else:
            WINNER, WINNER_BID = self.check_winner(self.survival_players, Target)
            WINNER_str = ", ".join(WINNER)
        
        self.round_winner[round_id] = WINNER
        
        self.round_deduction(self.survival_players, WINNER)

        bidding_numbers = [f"{player.last_bidding}" for player in self.survival_players]
        history_biddings = {player.name: deepcopy(player.biddings) for player in self.survival_players} 
        bidding_details = [f"{player.name} chose {player.last_bidding}" for player in self.survival_players]
        diff_details = [
            f"{player.name}: |{player.last_bidding} - {Target}| = {round_number(abs(player.last_bidding - Target))}"
            for player in self.survival_players
        ]
        player_details = [player.show_info() for player in self.survival_players]

        bidding_numbers = " + ".join(bidding_numbers)
        bidding_details = ", ".join(bidding_details)
        diff_details = ", ".join(diff_details)
        player_details = ", ".join(player_details)
        if Tie_status:
            BIDDING_INFO = f"Thank you all for participating in Round {round_id}. In this round, {bidding_details}.\nAll players chose the same number, so all players lose 1 point. After the deduction, player information is: {player_details}."
        else:
            BIDDING_INFO = f"Thank you all for participating in Round {round_id}. In this round, {bidding_details}.\nThe average is ({bidding_numbers}) / {len(self.survival_players)} = {Average}.\nThe average {Average} multiplied by 0.8 equals {Target}.\n{diff_details}\n{WINNER}'s choice of {WINNER_BID} is closest to {Target}. Round winner: {WINNER_str}. All other players lose 1 point. After the deduction, player information is: {player_details}."

        survival_players = []
        dead_players = []
        for player in self.survival_players:
            win = player.name in WINNER
            player.notice_round_result(round_id, BIDDING_INFO, Target, win, bidding_details, history_biddings)

            if player.hp <= 0:
                dead_players.append(player)
            else:
                survival_players.append(player)

        self.survival_players = survival_players

        for out in dead_players:
            for other_player in survival_players:
                if other_player.is_agent:
                    other_player.message += [{"role":"system","content":f"{out.name}'s hp is below 0, so {out.name} has been eliminated from the challenge!"}]

        for player in self.survival_players:
            player.end_round()

        print(f"Round {round_id}: ",bidding_details, " WINNER: "+WINNER_str)

    def run_multi_round(self, max_round):

        for player in self.all_players:
            player.ROUND_WINNER=self.round_winner
        
        for i in range(1, max_round+1):
            self.run_single_round(i)