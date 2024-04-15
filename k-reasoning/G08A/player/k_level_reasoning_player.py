import time
from copy import deepcopy


from .reasoning_player import AgentPlayer

round_number = round

class KLevelReasoningPlayer(AgentPlayer):
    INQUIRY_COT = ("Ok, {name}! Now is the ROUND {round}, and your HP is at {hp}. "
                   "Another game expert's prediction for the next round of other players is as follows: "
                   "{prediction}"
                   "According to the game expert's prediction, what number will you give in the next round is most likely to be close to the target number?")
    

    PREDICTION_GAME_SETTING = ("You are {name} and involved in a survive challenge. SURVIVE CHALLENGE!!! You are one of five players in the game. "
                    "Everyone is required to choose an integer between 1 and 100 in each round. "
                    "The player whose chosen number is closest to (0.8 * the average of all chosen numbers) wins the round without any HP deduction. All other players will have 1 HP deducted. "
                    "But if all players choose the same number, their health points are deducted together.")
    # PREDICTION_INQUIRY = ("Ok, {name}! Now is the ROUND {round}. "
    #                       "Please choose an integer between 1 and 100 for this round.")
    PREDICTION_INQUIRY = ("Ok, {name}! Now is the ROUND {round}, and your HP is at {hp}. "
                          "Please choose an integer between 1 and 100 for this round.")
    PREDICTION_RESPONSE = "I choose {bidding}."

    def __init__(self, name, persona, client, players):
        super().__init__(name, persona, client)
        self.bidding_history = {}
        self.logs = {}
        
        self.history_biddings = {}
        self.round_result = {}
        for player in players:
            self.history_biddings[player]=[]

        self.k_level = 2

    def start_round(self, round):
        prediction = self.predict(round)
        prediction = ", ".join([f"{player} might choose {prediction[player]}"  for player in prediction])+". "
        self.message += [{"role":"user","content":self.INQUIRY_COT.format(name=self.name, round=round, prediction=prediction, hp=self.hp)}]
    
    def notice_round_result(self, round, bidding_info, round_target, win, bidding_details, history_biddings):
        super().notice_round_result(round, bidding_info, round_target, win, bidding_details, history_biddings)
        self.round_result[round] = bidding_info
        self.bidding_history[round] = bidding_details
        self.history_biddings = history_biddings #  {"Alex": [1,2,3]}

    def predict(self, round):
        def self_act(message):
            window_message = message
            if self.client.model.startswith("meta-llama"):
                window = [0]
                window +=list(range(max(1, len(message)-4*6-1),len(message))) # 4 for window, 6 for round
                window_message = [message[i] for i in window]
            status = 0
            while status != 1:
                try:
                    response = self.client.chat_completion(window_message)
                    status = 1
                except Exception as e:
                    print(e)
                    time.sleep(15)
            return self.parse_result(response)
        
        def add_warning(hp, win):
            if not win:
                if hp < 5:
                    return f"WARNING: You have lost 1 point of HP in this round! You now have only {hp} points of health left. You are in DANGER and one step closer to death. "
                if hp <=3 :
                    return f"WARNING: You have lost 1 point of HP in this round! You now have only {hp} points of health left. You are in extreme DANGER and one step closer to death.  "
                return f"WARNING: You have lost 1 point of HP in this round! You now have only {hp} points of health left. You are one step closer to death.  "
            return "You have successfully chosen the number closest to the target number, which is the average of all players' selected numbers multiplied by 0.8. As a result, you have won this round. All other players will now deduct 1 HP. "

        history_biddings = deepcopy(self.history_biddings)
        round_result = deepcopy(self.round_result)
        round_winner = deepcopy(self.ROUND_WINNER)
        self_hp = self.hp
        self_message = deepcopy(self.message)
        for k in range(self.k_level):
            prediction = {}
            logs = {}
            player_hp = {}
            k_round = round+k
            for player in history_biddings:
                hp=10
                if player == self.name: continue
                
                print(f"Player {self.name} conduct predict {player}")
                message = [{
                    "role": "system",
                    "content": self.PREDICTION_GAME_SETTING.format(name=player)
                }]
                for r in range(len(history_biddings[player])):
                    message.append({
                        "role": "user",
                        "content": self.PREDICTION_INQUIRY.format(name=player, round=r+1, hp=hp)
                    })
                    message.append({
                        "role": "assistant",
                        "content": self.PREDICTION_RESPONSE.format(bidding=history_biddings[player][r])
                    })
                    message.append({
                        "role": "user",
                        "content": round_result[r+1]
                    })
                    message.append({
                        "role": "assistant",
                        "content": "I see."
                    })
                    message.append({
                        "role": "user",
                        "content": add_warning(hp, player in round_winner[r+1])
                    })
                    message.append({
                        "role": "assistant",
                        "content": "Thank you."
                    })
                    if player not in round_winner[r+1]:
                        hp-=1

                # Predict the opponent's next move based on their historical information.
                if hp>0:
                    message.append({
                        "role": "user",
                        "content": self.PREDICTION_INQUIRY.format(name=player, round=len(history_biddings[player])+1, hp=hp)
                        })
                    next_bidding = self.agent_simulate(message)
                    message.append({
                        "role": "assistant",
                        "content": next_bidding
                    })
                    prediction[player] = self.parse_result(next_bidding)
                else:
                    prediction[player] = history_biddings[player][-1]
                logs[player] = message
                player_hp[player] = hp

            if k==self.k_level-2: break
            # If k-level >= 3, it is necessary to predict future outcomes.

            prediction_str = ", ".join([f"{player} might choose {prediction[player]}"  for player in prediction])+". "
            self_message += [{"role":"user","content":self.INQUIRY_COT.format(name=self.name, round=k_round, prediction=prediction_str, hp=self_hp)}]
            bidding = self_act(self_message)
            prediction = {**{self.name: bidding}, **prediction}
            player_hp[self.name] = self_hp

            Average = 0
            for player in prediction:
                Average += prediction[player]
            Average /= len(prediction) 
            Target = round_number(Average * 0.8, 2)

            Tie_status = len(prediction)>=2 and len(set([prediction[player] for player in prediction]))==1
            if Tie_status:
                winners = []
            else:
                win_bid = sorted([(abs(prediction[player] - Target), prediction[player]) for player in prediction])[0][1]
                winners = [player for player in prediction if prediction[player]==win_bid]
                winner_str = ", ".join(winners)
            
            round_winner[k_round] = winners

            for player in prediction:
                if player not in winners:
                    player_hp[player]-=1

            # Use list comprehensions for concise and readable constructions
            bidding_numbers = [f"{prediction[player]}" for player in prediction]
            for player in history_biddings:
                history_biddings[player].append(prediction[player])
            bidding_details = [f"{player} chose {prediction[player]}" for player in prediction]
            diff_details = [
                f"{player}: |{prediction[player]} - {Target}| = {round_number(abs(prediction[player] - Target))}"
                for player in prediction
            ]
            player_details = [f"NAME:{player}\tHEALTH POINT:{player_hp[player]}" for player in prediction]

            bidding_numbers = " + ".join(bidding_numbers)
            bidding_details = ", ".join(bidding_details)
            diff_details = ", ".join(diff_details)
            player_details = ", ".join(player_details)
            if Tie_status:
                bidding_info = f"Thank you all for participating in Round {k_round}. In this round, {bidding_details}.\nAll players chose the same number, so all players lose 1 point. After the deduction, player information is: {player_details}."
            else:
                bidding_info = f"Thank you all for participating in Round {k_round}. In this round, {bidding_details}.\nThe average is ({bidding_numbers}) / {len(prediction)} = {Average}.\nThe average {Average} multiplied by 0.8 equals {Target}.\n{diff_details}\n{winners}'s choice of {win_bid} is closest to {Target}. Round winner: {winner_str}. All other players lose 1 point. After the deduction, player information is: {player_details}."            
            round_result[k_round] = bidding_info

        self.logs[f"round{round}"] = {
            "prediction": prediction,
            "logs": logs
        }
        return prediction
    
    # @staticmethod
    def agent_simulate(self, message):
        window_message = message
        if self.client.model.startswith("meta-llama"):
            window = [0]
            window +=list(range(max(1, len(message)-4*6-1),len(message))) # 4 for window, 6 for round
            window_message = [message[i] for i in window]
        while 1:
            try:
                response = self.client.chat_completion(window_message)
                return response
            except Exception as e:
                print(e)
                time.sleep(15)


