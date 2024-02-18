import time
from copy import deepcopy

import openai

from .reasoning_player import AgentPlayer


PERSONA = "You are {name} and a resident living in W-Town. W Town is experiencing a rare drought. Every residents in Town W is ensuring their survival over a period of 10 days by acquiring the water resources. "

class KLevelReasoningPlayer(AgentPlayer):
    INQUIRY_COT = ("Hello, {name}! Today is the Day {round} of the Water Allocation Challenge, with a quantity of {supply} units."
                " Your status:\n{status}\nPlease carefully analyze your situation to decide on this round of bidding."
                " Remember, the most important thing is to SURVIVE!! Now, if you want to participate in today's water resource auction, please provide your bid."
                   " Another game expert's prediction for the next round of other players is as follows: "
                   "{prediction}"
                   " Based on the prediction of other players, think carefully about your next round of bidding strategy to be most likely to survive.")
    
    PREDICTION_GAME_SETTING = PERSONA + AgentPlayer.GAME_SETTING
    PREDICTION_INQUIRY = ("Hello, {name}! Today is the Day {round} of the Water Allocation Challenge, with a quantity of {supply} units."
               " Your status:\n{status}\nPlease carefully analyze your situation to decide on this round of bidding."
               " Remember, the most important thing is to SURVIVE!! Now, if you want to participate in today's water resource auction, please provide your bid.")
    PREDICTION_RESPONSE = "I will bid ${bidding} for today's water resource auction."
    REBID_RESPONSE = "In this round, {biddings}. Due to the detection of leakage issues in today's bids, the bids in this round are invalidated and today's auction will be restarted."


    def __init__(self, name, engine, water_requirement, daily_salary, persona):
        super().__init__(name, engine, water_requirement, daily_salary, persona)
        self.bidding_history = {}
        self.logs = {}
        
        self.history_biddings = {}
        self.opponent_status = {}
        self.round_supply = {}
        self.round_result = {}

        self.k_level = 2
        
        # self.engine = "gpt35prod"

    def start_round(self, round, supply):
        self.round_supply[round]=supply
        prediction = self.predict(round)
        prediction = ", ".join([f"{player} might bid {prediction[player]}"  for player in prediction])+". "
        self.message += [{"role":"system","content":self.INQUIRY_COT.format(name=self.name, round=round, supply=supply, prediction=prediction, status=self.get_status())}]
    
    def notice_round_result(self, round, bidding_info, win, bidding_details):
        super().notice_round_result(round, bidding_info, win, bidding_details)
        self.round_result[round] = bidding_info
        self.bidding_history[round] = bidding_details
    
    def update_public_info(self, round, history_biddings, player_stauts):
        self.history_biddings = history_biddings #  {"Alex": [1,2,3]}
        self.opponent_status[round] = player_stauts

    def predict(self, round):
        def self_act(message):
            status = 0
            while status != 1:
                try:
                    response = openai.ChatCompletion.create(
                        engine = self.engine,
                        messages = message,
                        temperature=0.7,
                        max_tokens=800,
                        top_p=0.95,
                        frequency_penalty=0, 
                        presence_penalty=0,
                        stop=None)
                    response = response['choices'][0]['message']['content']
                    message.append({"role":"assistant","content":response})
                    status = 1
                except Exception as e:
                    print(e)
                    time.sleep(15)
            return self.parse_result(response)

        self_message = deepcopy(self.message)
        prediction = {}
        logs = {}

        for k in range(self.k_level):
            for player in self.history_biddings:
                if player == self.name: continue
                print(f"Player {self.name} conduct predict {player}")
                message = [{
                    "role": "system",
                    "content": self.PREDICTION_GAME_SETTING.format(name=player)
                }]
                for r in range(len(self.history_biddings[player])):
                    message.append({
                        "role": "system",
                        "content": self.PREDICTION_INQUIRY.format(name=player, round=r+1, supply = self.round_supply[r+1], status=self.opponent_status[r+1][player])
                    })
                    message.append({
                        "role": "assistant",
                        "content": self.PREDICTION_RESPONSE.format(bidding=self.history_biddings[player][r])
                    })
                    message.append({
                        "role": "system",
                        "content": self.round_result[r+1]
                    })
                round_id = len(self.history_biddings[player])+1
                if k==0:
                    # Predict the opponent's next move based on their historical information.
                    message.append({
                        "role": "system",
                        "content": self.PREDICTION_INQUIRY.format(name=player, round=round_id, supply = self.round_supply[round_id], status=self.opponent_status[round_id][player])
                    })
                    next_bidding = self.agent_simulate(message, engine=self.engine)
                    message.append({
                        "role": "assistant",
                        "content": next_bidding
                    })
                else:
                    # If k >= 0, make the decision for k based on the prediction result of k-1.

                    prediction_str = ", ".join([f"{oppo} might bid {prediction[oppo]}"  for oppo in prediction if oppo!=player])+". "
                    message.append({
                        "role": "system",
                        "content": self.INQUIRY_COT.format(name=player, round=round_id, supply = self.round_supply[round_id], prediction=prediction_str, status=self.opponent_status[round_id][player])
                    })
                    next_bidding = self.agent_simulate(message, engine=self.engine)
                    message.append({
                        "role": "assistant",
                        "content": next_bidding
                    })

                prediction[player] = self.parse_result(next_bidding)
                logs[player] = message

            if k==self.k_level-2: break
            prediction_str = ", ".join([f"{player} might choose {prediction[player]}"  for player in prediction])+". "
            self_message += [{"role":"system","content":self.INQUIRY_COT.format(name=self.name, round=round, supply=self.round_supply[round], prediction=prediction_str, status=self.get_status())}]

            bidding = self_act(self_message)
            prediction = {**{self.name: bidding}, **prediction}
        
        if self.name in prediction:
            del prediction[self.name]

        self.logs[f"round{round}"] = {
            "prediction": prediction,
            "logs": logs
        }
        return prediction
    
    # @staticmethod
    def agent_simulate(self, message, engine):
        while 1:
            try:
                response = openai.ChatCompletion.create(
                    engine=engine,
                    messages = message,
                    temperature=0.7,
                    max_tokens=80,
                    top_p=0.9,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop=None)
                RESPONSE = response['choices'][0]['message']['content']
                return RESPONSE
            except Exception as e:
                print(e)
                time.sleep(15)