import json

class SurvivalAuctionGame():
    # Prompts
    ROUND_NOTICE = "Thank you all for participating in Round {}. In this round, {}.\nTotal water resource supply is {}. According to the principle of the highest bidder and the rule when the game is tied, {} won this auction and obtain water resource. After allocation, all survival residents' information is as follows: \n {}"

    def __init__(self, players) -> None:
        self.players = players[::]
        self.survival_players = players[::]
        self.round_winners = {}
        self.round_status = {}

    def _get_salary(self):
        for player in self.survival_players:
            player.get_salary()

    def _round_settlement(self, winners):
        for player in self.survival_players:
            if player.name in winners:
                player.success_bid()
            else:
                player.unsuccess_bid()

    def _check_winner(self, supply):
        """
        get the winners of the current round
        """
        winners = []
        largest_bidding = max([player.last_bidding for player in self.survival_players])
        winners = [player.name for player in self.survival_players 
                   if (player.last_bidding == largest_bidding)  and (player.last_bidding <= player.balance)]
        if len(winners)>1:
            winners = []
        return winners

    
    def run_single_round(self, round_id, supply):
        """
        Execute a single round of game

        Args:
            round_id (int): number of the current round, beginning from 1.
            supply (int): supply of the current round
        """
        print(f"Round {round_id} begins.")

        # 1. get salary
        self._get_salary()
        print("All players get their salaries.")

        # 2. bid
        history_biddings = {player.name: player.biddings[::] for player in self.survival_players}
        player_status = {player.name: player.get_status() for player in self.survival_players}

        for player in self.survival_players:
            player.update_public_info(round_id, history_biddings, player_status)
            player.start_round(round_id, supply)
        
        for player in self.survival_players:
            player.act()
        
        # 3. check winners
        winners = self._check_winner(supply)
        self.round_winners[round_id] = winners
        print("Winner(s):\n")
        print(winners)

        # 4. settlement
        self._round_settlement(winners)

        # 5. get bidding results (str)
        bidding_details = []
        for player in self.survival_players:
            bidding_details += [f"{player.name} bid {player.last_bidding}"]
        bidding_details = ", ".join(bidding_details)

        if len(winners):
            winners_str = []
            for winner in winners:
                winners_str += [winner]
            winners_str = ", ".join(winners_str)
        else:
            winners_str = "no one"

        player_status_str = []
        players_status = {}
        for player in self.survival_players:
            player_status_str += [player.get_status()]
            players_status[player.name] = player.get_status()
        player_status_str = "\n".join(player_status_str)
        
        round_results = self.ROUND_NOTICE.format(round_id, bidding_details, supply, winners_str, player_status_str)
        print("Round result:\n" + round_results)


        # 6. update round results to every player
        for player in self.survival_players:
            player.notice_round_result(round_id, round_results, player.name in winners, bidding_details)

        # 7. check the survival situation
        survival_players = []
        self.round_status[round_id]  = {}
        for player in self.survival_players:
            self.round_status[round_id][player.name] = player.get_status()
            if player.hp <= 0:
                for other_player in self.survival_players:
                    other_player.notice_elimination( f"{player.name}'s hp is below 0, so {player.name} has been eliminated from the challenge!")
            else:
                survival_players.append(player)
        self.survival_players = survival_players

    def _save_history(self, path):
        history = []
        for player in self.players:
            history.append({player.name: player.message})
        with open(path, 'w') as f:
            json.dump(history, f)

    def run_multi_round(self, n_round, supply_list):
        assert isinstance(supply_list, list)
        assert n_round == len(supply_list)

        for i in range(1, n_round+1):
            self.run_single_round(i, supply_list[i-1])
            if len(self.survival_players) == 0:
                break