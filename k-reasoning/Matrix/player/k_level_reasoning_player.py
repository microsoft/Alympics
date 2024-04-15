import time
from copy import deepcopy

import openai

from .reasoning_player import AgentPlayer


PERSONA = "You are {name}, currently playing a strategy game."

class KLevelReasoningPlayer(AgentPlayer):
    INQUIRY_COT = ("Now, {name}, please tell me your decision: Will you cooperate or betray?" # TODO: round number is necessary for multi-round
                   " Another game expert's prediction of other player is as follows: " # TODO: HP information is necessary for multi-round
                   "{prediction}"
                   " Based on your prediction of the other player's action, carefully consider what choice you should make to receive the least amount of punishment.")
    
    PREDICTION_GAME_SETTING = PERSONA + AgentPlayer.GAME_SETTING
    PREDICTION_INQUIRY = ("Now, {name}, please tell me your decision: Will you cooperate or betray?")
    PREDICTION_RESPONSE = "I would choose to {action}."

    def __init__(self, name, engine, persona, k_level=2):
        super().__init__(name, engine, persona)
        self.action_history = {}
        self.logs = {}
        
        self.history_actions = {}
        self.opponent_status = {}
        self.round_result = {}

        self.k_level = k_level
        
        # self.engine = "gpt35prod"

    def start_round(self, round):
        prediction = self.predict(round)
        prediction = ", ".join([f"{player} might choose to {self.to_action(prediction[player])}"  for player in prediction])+". "
        self.message += [{"role":"system","content":self.INQUIRY_COT.format(name=self.name, prediction=prediction)}]
    
    def notice_round_result(self, round, action_info, win, action_details):
        super().notice_round_result(round, action_info, win, action_details)
        self.round_result[round] = action_info
        self.action_history[round] = action_details
    
    def update_public_info(self, round, history_actions, player_stauts):
        self.history_actions = history_actions #  {"Alex": [1,2,3]}
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
            for player in self.history_actions:
                if player == self.name: continue
                print(f"Player {self.name} conduct predict {player}")
                message = [{
                    "role": "system",
                    "content": self.PREDICTION_GAME_SETTING.format(name=player)
                }]
                for r in range(len(self.history_actions[player])):
                    message.append({
                        "role": "system",
                        "content": self.PREDICTION_INQUIRY.format(name=player)
                    })
                    message.append({
                        "role": "assistant",
                        "content": self.PREDICTION_RESPONSE.format(action=self.to_action(self.history_actions[player][r]))
                    })
                    message.append({
                        "role": "system",
                        "content": self.round_result[r+1]
                    })
                round_id = len(self.history_actions[player])+1
                if k==0:
                    # Predict the opponent's next move based on their historical information.
                    message.append({
                        "role": "system",
                        "content": self.PREDICTION_INQUIRY.format(name=player)
                    })
                    next_action = self.agent_simulate(message, engine=self.engine)
                    message.append({
                        "role": "assistant",
                        "content": next_action
                    })
                else:
                    # If k >= 0, make the decision for k based on the prediction result of k-1.
                    prediction_str = ", ".join([f"{oppo} might choose to {self.to_action(prediction[oppo])}"  for oppo in prediction if oppo!=player])+". "
                    message.append({
                        "role": "system",
                        "content": self.INQUIRY_COT.format(name=player, prediction=prediction_str)
                    })
                    next_action = self.agent_simulate(message, engine=self.engine)
                    message.append({
                        "role": "assistant",
                        "content": next_action
                    })

                prediction[player] = self.parse_result(next_action)
                logs[player] = message

            if k==self.k_level-2: break
            prediction_str = ", ".join([f"{player} might choose {self.to_action(prediction[player])}"  for player in prediction])+". "
            self_message += [{"role":"system","content":self.INQUIRY_COT.format(name=self.name, prediction=prediction_str)}]

            action = self_act(self_message)
            prediction = {**{self.name: action}, **prediction}
        
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