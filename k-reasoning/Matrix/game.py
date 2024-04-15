import json

class MatrixGame():
    # Matrix
    """
    +---+---+
    | C | B |
    +---+---+
    | 0 | 1 |
    +---+---+

    +---+-------+-------+
    |   |   C   |   B   |
    +---+-------+-------+
    | C | (0,0) | (0,1) |
    +---+-------+-------+
    | B | (1,0) | (1,1) |
    +---+-------+-------+
    """

    ACTION_MAP = {
        0: "cooperate",
        1: "betray"
    }

    # Prompt
    ROUND_NOTICE = "Thank you all for participating in Round {}. In this round, {}.\nAccording to the rules, receiving a lighter punishment or no punishment at all is considered a victory. Therefore, {} won this round. After this round, all player' information is as follows: \n {}"

    def __init__(self, players) -> None:
        self.players = players[::]
        self.survival_players = players[::]
        self.round_winners = {}
        self.round_status = {}

    def _check_result(self):
        """
        get the result of the current round
        """
        return tuple([player.last_action for player in self.survival_players])
    
    def _check_winner(self):
        """
        get the winners of the current round
        """
        choices = list(set([player.last_action for player in self.survival_players]))
        if len(choices)==1 and choices[0]==1:
            return []
        
        if len(choices)==1 and choices[0]==0:
            return [player.name for player in self.survival_players]

        winners = []
        for player in self.survival_players:
            if player.last_action==1:
                winners.append(player.name)
        return winners
    
    def _check_equilibrium(self, result):
        """
        Determine if the current result is balanced.
        """
        return result==(1,1)
    
    def _round_settlement(self, winners):
        for player in self.survival_players:
            if player.name in winners:
                player.success_bid()
            else:
                player.unsuccess_bid()
    
    def run_single_round(self, round_id):
        """
        Execute a single round of game

        Args:
            round_id (int): number of the current round, beginning from 1.
        """
        print(f"Round {round_id} begins.")

        # 1. bid
        history_actions = {player.name: player.actions[::] for player in self.survival_players}
        player_status = {player.name: player.get_status() for player in self.survival_players}

        for player in self.survival_players:
            player.update_public_info(round_id, history_actions, player_status)
            player.start_round(round_id)
        
        for player in self.survival_players:
            player.act()
        
        # 2. check winners
        winners = self._check_winner()
        print("Winner(s): ", winners)

        # 3. get action results (str)
        action_details = []
        for player in self.survival_players:
            action_details += [f"{player.name} choose to {self.ACTION_MAP[player.last_action]}"]
        action_details = ", ".join(action_details)
        print("Choice(s): ", action_details)

        if len(winners):
            winners_str = []
            for winner in winners:
                winners_str += [winner]
            winners_str = ", ".join(winners_str)
        else:
            winners_str = "no one"

        # 4. settlement
        self._round_settlement(winners)

        player_status_str = []
        players_status = {}
        for player in self.survival_players:
            player_status_str += [player.get_status()]
            players_status[player.name] = player.get_status()
        player_status_str = "\n".join(player_status_str)
        
        round_results = self.ROUND_NOTICE.format(round_id, action_details, winners_str, player_status_str)
        print("Round result:\n" + round_results)
        

        # 5. update round results to every player
        for player in self.survival_players:
            player.notice_round_result(round_id, round_results, player.name in winners, action_details)

        # 6. check the survival situation
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

    def run_multi_round(self, n_round):
        for i in range(1, n_round+1):
            self.run_single_round(i)
            if len(self.survival_players) == 0:
                break