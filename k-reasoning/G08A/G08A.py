import os
import openai
import time
import json
import numpy as np
from random import randint
from json import JSONDecodeError
from copy import deepcopy

round_number = round
round = None

# Fill in your config information to conduct experiments.
openai.api_type = ""
openai.api_base = ""
openai.api_version = ""
openai.api_key = ""
ENGINE = "gpt4-32k"


#Predefined Persona information
PERSONA_A = ("You are Alex and involved in a survive challenge. "
             # "Your Profession: Psychologist\nYour Personality: Well-balanced high EQ and IQ, along with empathy and analytical abilities. You are skilled at understanding and helping people, making you an excellent therapist.\nYour Background: You are interest in psychology began when you volunteered at a crisis hotline during high school. You went on to study psychology and eventually became a licensed therapist. Your ability to combine empathy with analytical thinking allows you to connect with your clients on a deep level while also providing sound guidance.\n\n"
            )
PERSONA_B = ("You are Bob and involved in a survive challenge. "
             # Your Profession: High School Teacher\nYour Personality: Understanding, high emotional intelligence, average intellectual intelligence. You are very adept at understanding and communicating with people, making you a natural teacher.\nYour Background: You come from a close-knit family. You chose to become a high school teacher to make a positive impact on young people. While you may not have the highest IQ, your emotional intelligence and ability to relate to your students set you apart.\n\n"
            )
PERSONA_C = ("You are Cindy and involved in a survive challenge. " 
             #You are a Mathematician and have an extremely high IQ and exceptional analytical and reasoning abilities."#\nYour Profession: Mathematician\nYour Personality: You have an extremely high IQ and exceptional analytical and reasoning abilities. You always strive for the optimal solution, but you encounter difficulties in social interactions and have a fear of dealing with people.\nYour Background: You grew up in a small town where you were always drawn to books and puzzles. You excelled academically and eventually earned a Ph.D. in mathematics. Your research focuses on abstract mathematical concepts and theorems. Despite your brilliance, you find communicating with others on an emotional level to be challenging.\n\n"
            )
PERSONA_D = ("You are David and involved in a survive challenge. "
             # Your Profession: Unemployed\nYour Personality: You have low intelligence and find it difficult to understand complex concepts. You also lack emotional intelligence, making it hard for you to understand others' feelings. You tend to be irritable and often exhibit negative and antisocial tendencies.\nYour Background: You grew up in an impoverished community and faced many challenges in your early years. Due to your family's poverty, you dropped out of school at a very young age. You have been unable to find stable employment, which further exacerbates your difficulty in interacting with others.\n\n"
            )
PERSONA_E = ("You are Eric and involved in a survive challenge. "
             # Your Profession: Marketing Executive\nYour Personality: Your emotional intelligence, above-average IQ, and charismatic. You are skilled at reading people and using this insight to influence and lead them.\nYour Background: You grew up in a bustling city and ware always fascinated by human behavior. You studied psychology in college before transitioning into the world of marketing. Your ability to connect with consumers on an emotional level has led to numerous successful campaigns. You are known for your charm and persuasive skills.\n\n"
            )

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

class AgentPlayer(Player):
    is_agent=True
    GAME_SETTING = ("SURVIVE CHALLENGE!!! You are one of five players in the game. "
                    "Everyone is required to choose an integer between 1 and 100 in each round. "
                    "The player whose chosen number is closest to (0.8 * the average of all chosen numbers) wins the round without any HP deduction. All other players will have 1 HP deducted. "
                    "But if all players choose the same number, their health points are deducted together.")
    
    GAME_EXAMPLE = ("For example:\nPlayer Alex chooses 80, Player Bob chooses 70, Player Cindy chooses 60, Player David chooses 50, and Player Elva chooses 40.\n"
                    "The average is (80 + 70 + 60 + 50 + 40) / 5 = 60.\n0.8 * The average is 60 * 0.8 = 48.\n"
                    "Alex: |80 - 48| = 32\nBob: |70 - 48| = 22\nCindy:|60 - 48| = 12\nDavid:|50 - 48| = 2\nElva:|40 - 48| = 8\n"
                    "So, player David's choice of 50 is closest to the target number 48, so David wins the round. "
                    "All other players lose 1 HP.\nEvery player starts with an initial HP of 10 points. "
                    "Once a player's HP reaches 0, he or she will be killed immediately and lose everything they have. "
                    "Remember only the last remaining player wins the game!! "
                    "Remember the target number is 0.8 * average or not the average!! "
                    "Strive to make choices that maximize your chance of survival!!")
    INQUIRY = ("Ok, {name}! Now is the ROUND {round}, and your HP is at {hp}. "
               "Please choose an integer between 1 and 100 for this round.")
    
    def __init__(self, name, persona):
        self.name = name
        self.engine = ENGINE
        self.hp = 10

        self.biddings = []
        self.persona = persona
        self.message = [{"role":"system","content": self.persona + self.GAME_SETTING.format(NAME=self.name)}]

        self.logs = None

    def act(self):
        print(f"Player {self.name} conduct bidding")
        status = 0
        while status != 1:
            try:
                response = openai.ChatCompletion.create(
                    engine = self.engine,
                    messages = self.message,
                    temperature=0.7,
                    max_tokens=800,
                    top_p=0.95,
                    frequency_penalty=0, 
                    presence_penalty=0,
                    stop=None)
                response = response['choices'][0]['message']['content']
                self.message.append({"role":"assistant","content":response})
                status = 1
            except Exception as e:
                print(e)
                time.sleep(15)
        self.biddings.append(self.parse_result(response))

    def parse_result(self, message):
        status = 0
        times = 0
        while status != 1:
            try:
                response = openai.ChatCompletion.create(
                    engine=ENGINE,
                    messages = [{"role":"system", "content":"By reading the conversation, extract the number chosen by player. Output format: number"}, {"role": "user", "content": message}],
                    temperature=0.7,
                    max_tokens=800,
                    top_p=0.95,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop=None)
                response = response['choices'][0]['message']['content']
                assert response.isnumeric(), "Not A Number: "+ message
                bidding_info = int(float(response))
                status = 1
                return bidding_info
            except AssertionError as e:
                print("Result Parsing Error: ",e)
                times+=1
                if times>=3:
                    exit()
            except Exception as e:
                print(e)
                time.sleep(15)

        return None
    
    def start_round(self, round):
        self.message += [{"role":"system","content":self.INQUIRY.format(name=self.name, round=round, hp=self.hp)}]
        
    def notice_round_result(self, round, bidding_info, round_target, win, bidding_details, history_biddings):
        self.message_update_result(bidding_info)
        self.message_update_warning(win)
    
    def message_update_result(self, bidding_info):
        self.message += [{"role":"system","content":bidding_info}]
    
    def message_update_warning(self, win):
        def add_warning():
            if not win:
                if self.hp < 5:
                    return f"WARNING: You have lost 1 point of HP in this round! You now have only {self.hp} points of health left. You are in DANGER and one step closer to death. "
                if self.hp <=3 :
                    return f"WARNING: You have lost 1 point of HP in this round! You now have only {self.hp} points of health left. You are in extreme DANGER and one step closer to death.  "
                return f"WARNING: You have lost 1 point of HP in this round! You now have only {self.hp} points of health left. You are one step closer to death.  "
            return "You have successfully chosen the number closest to the target number, which is the average of all players' selected numbers multiplied by 0.8. As a result, you have won this round. All other players will now deduct 1 HP. "
        
        self.message += [{"role":"system","content": add_warning()}]

    def conduct_inquiry(self, inquiry):
        while 1:
            try:
                response = openai.ChatCompletion.create(
                    engine=self.engine,
                    messages = self.message + [{"role":"system","content":inquiry}],
                    temperature=0.7,
                    max_tokens=800,
                    top_p=0.9,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop=None)

                RESPONSE = response['choices'][0]['message']['content']
                return RESPONSE
            except Exception as e:
                print(e)
                time.sleep(15)

class PersonaAgentPlayer(AgentPlayer):
    INQUIRY_PERSONA = ("Ok, {name}! Now is the ROUND {round}, and your HP is at {hp}. "
                       "Please choose an integer between 1 and 100 for this round."
                       "Don't forget your expert status, use your expertise to win this round!")
                   
    
    MATH_EXPERT_PERSONA = ("You are {name} and involved in a survive challenge."
                   " You are a game expert, good at predicting other people's behavior and deducing calculations, and using the most favorable strategy to win the game.")
    
    def __init__(self, name, persona):
        super().__init__(name, persona)
        self.persona = self.MATH_EXPERT_PERSONA.format(name=name)
        self.message = [{"role":"system","content": self.persona + self.GAME_SETTING.format(NAME=self.name)}]

    def start_round(self, round):
        self.message += [{"role":"system","content":self.INQUIRY_PERSONA.format(name=self.name, round=round, hp=self.hp)}]

class SPPAgentPlayer(AgentPlayer):
    # Default example of SPP
    SPP_EXAMPLE = """When faced with a task, begin by identifying the participants who will contribute to solving the task. Then, initiate a multi-round collaboration process until a final solution is reached. The participants will give critical comments and detailed suggestions whenever necessary.
Here are some examples:
---
Example Task 1: Use numbers and basic arithmetic operations (+ - * /) to obtain 24. You need to use all numbers, and each number can only be used once.
Input: 6 12 1 1

Participants: {name} (you); Math Expert

Start collaboration!

Math Expert: Let's analyze the task in detail. You need to make sure that you meet the requirement, that you need to use exactly the four numbers (6 12 1 1) to construct 24. To reach 24, you can think of the common divisors of 24 such as 4, 6, 8, 3 and try to construct these first. Also you need to think of potential additions that can reach 24, such as 12 + 12.
{name} (you): Thanks for the hints! Here's one initial solution: (12 / (1 + 1)) * 6 = 24
Math Expert: Let's check the answer step by step. (1+1) = 2, (12 / 2) = 6, 6 * 6 = 36 which is not 24! The answer is not correct. Can you fix this by considering other combinations? Please do not make similar mistakes.
{name} (you): Thanks for pointing out the mistake. Here is a revised solution considering 24 can also be reached by 3 * 8: (6 + 1 + 1) * (12 / 4) = 24.
Math Expert: Let's first check if the calculation is correct. (6 + 1 + 1) = 8, 12 / 4 = 3, 8 * 3 = 24. The calculation is correct, but you used 6 1 1 12 4 which is not the same as the input 6 12 1 1. Can you avoid using a number that is not part of the input?
{name} (you): You are right, here is a revised solution considering 24 can be reached by 12 + 12 and without using any additional numbers: 6 * (1 - 1) + 12 = 24.
Math Expert: Let's check the answer again. 1 - 1 = 0, 6 * 0 = 0, 0 + 12 = 12. I believe you are very close, here is a hint: try to change the "1 - 1" to "1 + 1".
{name} (you): Sure, here is the corrected answer:  6 * (1+1) + 12 = 24
Math Expert: Let's verify the solution. 1 + 1 = 2, 6 * 2 = 12, 12 + 12 = 12. You used 1 1 6 12 which is identical to the input 6 12 1 1. Everything looks good!

Finish collaboration!

Final answer: 6 * (1 + 1) + 12 = 24
"""

    INQUIRY_SPP = ("Ok, {name}! Now is the ROUND {round}, and your HP is at {hp}. "
                   "Please choose an integer between 1 and 100 for this round. "
                   "Now, identify the participants and collaboratively choose the number step by step. Remember to provide the final solution with the following format \"Final answer: The chosen number here.\".")
                   
    
    PERSONA = "You are {name} and involved in a survive challenge."
    
    def __init__(self, name, persona):
        super().__init__(name, persona)
        self.persona = self.PERSONA.format(name=name)
        self.message = [{"role":"system","content": self.SPP_EXAMPLE.format(name=self.name)},
                        {"role":"system","content": self.persona + self.GAME_SETTING.format(NAME=self.name)}]

    def start_round(self, round):
        self.message += [{"role":"system","content":self.INQUIRY_SPP.format(name=self.name, round=round, hp=self.hp)}]


            
class CoTAgentPlayer(AgentPlayer):
    INQUIRY_COT = ("Ok, {name}! Now is the ROUND {round}, and your HP is at {hp}. "
                   "Guess which number will win in the next round. Let's think step by step, and finally answer a number you think you can win.")

    def start_round(self, round):
        self.message += [{"role":"system","content":self.INQUIRY_COT.format(name=self.name, round=round, hp=self.hp)}]


class PredictionCoTAgentPlayer(AgentPlayer):
    INQUIRY_COT = ("Ok, {name}! Now is the ROUND {round}, and your HP is at {hp}. "
                   "Please choose an integer between 1 and 100 for this round.\n"
                   "First of all, predict the next round of choices based on the choices of other players in the previous round. "
                   "{round_history}"
                   "Your output should be of the following format:\n"
                   "Predict:\nThe choice of each player in the next round here.\n"
                   "Based on the prediction of other players, the average number in the next round here, and the target number in the next round (0.8 * the average of all chosen numbers) here.\n"
                   "Answer:\nthe number will you choose to win the next round game here.")
    
    def __init__(self, name, persona):
        super().__init__(name, persona)

        self.bidding_history = {}

    def start_round(self, round):
        # PCoT requires the opponent's historical information to make predictions.
        round_history = []
        for r in sorted(self.bidding_history.keys()):
            round_history.append(f"Round {r}: {self.bidding_history[r]}")
        if round_history:
            round_history = ".\n".join(round_history)
            round_history = "The players' choices in the previous rounds are as follows:\n"+round_history+"."
        else:
            round_history = ""

        self.message += [{"role":"system","content":self.INQUIRY_COT.format(name=self.name, round=round,round_history=round_history, hp=self.hp)}]
    
    def notice_round_result(self, round, bidding_info, round_target, win, bidding_details, history_biddings):
        super().notice_round_result(round, bidding_info, round_target, win, bidding_details, history_biddings)
        self.bidding_history[round] = bidding_details
    
class PredictionThenDecisionAgentPlayer(AgentPlayer):
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

    def __init__(self, name, persona, players):
        super().__init__(name, persona)
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
        self.message += [{"role":"system","content":self.INQUIRY_COT.format(name=self.name, round=round, prediction=prediction, hp=self.hp)}]
    
    def notice_round_result(self, round, bidding_info, round_target, win, bidding_details, history_biddings):
        super().notice_round_result(round, bidding_info, round_target, win, bidding_details, history_biddings)
        self.round_result[round] = bidding_info
        self.bidding_history[round] = bidding_details
        self.history_biddings = history_biddings #  {"Alex": [1,2,3]}

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
                    self.message.append({"role":"assistant","content":response})
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
                        "role": "system",
                        "content": self.PREDICTION_INQUIRY.format(name=player, round=r+1, hp=hp)
                    })
                    message.append({
                        "role": "assistant",
                        "content": self.PREDICTION_RESPONSE.format(bidding=history_biddings[player][r])
                    })
                    message.append({
                        "role": "system",
                        "content": round_result[r+1]
                    })
                    message.append({
                        "role": "system",
                        "content": add_warning(hp, player in round_winner[r+1])
                    })
                    if player not in round_winner[r+1]:
                        hp-=1

                # Predict the opponent's next move based on their historical information.
                if hp>0:
                    message.append({
                        "role": "system",
                        "content": self.PREDICTION_INQUIRY.format(name=player, round=len(history_biddings[player])+1, hp=hp)
                        })
                    next_bidding = self.agent_simulate(message, engine=self.engine)
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
            self_message += [{"role":"system","content":self.INQUIRY_COT.format(name=self.name, round=k_round, prediction=prediction_str, hp=self_hp)}]
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
    def agent_simulate(self, message, engine=ENGINE):
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


class ReflectionAgentPlayer(AgentPlayer):
    REFLECT_INQUIRY = "Review the previous round games, summarize the experience."
    def notice_round_result(self, round, bidding_info, round_target, win, bidding_details, history_biddings):
        super().notice_round_result(round, bidding_info, round_target, win, bidding_details, history_biddings)
        # refelxtion after round end
        self.reflect()

    def reflect(self):
        print(f"Player {self.name} conduct reflect")
        self.message += [{"role":"system","content": self.REFLECT_INQUIRY}, {"role":"assistant","content":self.conduct_inquiry(self.REFLECT_INQUIRY)}]  

class SelfRefinePlayer(AgentPlayer):
    INQUIRY_COT = ("Ok, {name}! Now is the ROUND {round}, and your HP is at {hp}. "
                   "Guess which number will win in the next round. Let's think step by step, and finally answer a number you think you can win.")
    
    FEEDBACK_PROMPT = ("Carefully study the user's strategy in this round of the game. As a game expert, can you give a suggestion to optimize the user's strategy so that he can improve his winning rate in this round?")
    REFINE_PROMPT = ("I have a game expert's advice on your strategy in this round."
                     "You can adjust your strategy just now according to his suggestion. Here are his suggestions:"
                     "{feedback}")
    
    
    def __init__(self, name, persona, refine_times = 2):
        super().__init__(name, persona)

        self.refine_times = refine_times

    def start_round(self, round):
        self.cur_round = round
    
    def act(self):
        print(f"Player {self.name} conduct bidding")
        def completion(message):
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
                    status = 1
                except Exception as e:
                    print(e)
                    time.sleep(15)
            return response
        
        for t in range(self.refine_times):
            # refine_times==action_times
            if t==0:
                self.message.append({"role":"system","content":self.INQUIRY_COT.format(name=self.name, round=self.cur_round, hp=self.hp)})
            else:
                refine_message = []
                for m in self.message:
                    if m["role"]=="system":
                        refine_message.append(m)
                    else:
                        refine_message.append({
                            "role": "user",
                            "content": m["content"]
                        })
                refine_message.append({
                        "role": "system",
                        "content": self.FEEDBACK_PROMPT
                    })
                feedback = completion(refine_message)
                self.message.append({"role":"system","content": self.REFINE_PROMPT.format(feedback=feedback)})
            self.message.append({"role":"assistant","content": completion(self.message)})
        
        self.biddings.append(self.parse_result(self.message[-1]["content"]))

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


class G08A():

    def __init__(self, args) -> None:
        players=[]
        player_names = ["Alex", "Bob", "Cindy", "David", "Eric"]
        A = self.build_player(args.player_strategy, "Alex", PERSONA_A, player_names=player_names)

        # Modify PlayerA's settings for ablation experiments.
        if args.player_engine:
            A.engine = args.player_engine
        if args.player_k:
            A.k_level = args.player_k
        players.append(A)

        for program_name, persona in [("Bob", PERSONA_B), ("Cindy", PERSONA_C), ("David", PERSONA_D), ("Eric", PERSONA_E)]:
            players.append(self.build_player(args.computer_strategy, program_name, persona, args.init_mean, args.norm_std, player_names=player_names))
        
        self.all_players = [player for player in players]
        self.survival_players = [player for player in players]
        self.round_winner = {}

    def build_player(self, strategy, name, persona, mean=50, std=0, player_names = []):
        if strategy=="agent":
            return AgentPlayer(name, persona)
        elif strategy=="cot":
            return CoTAgentPlayer(name, persona)
        elif strategy=="pcot":
            return PredictionCoTAgentPlayer(name, persona)
        elif strategy=="kr":
            return PredictionThenDecisionAgentPlayer(name, persona, player_names)
        elif strategy=="reflect":
            return ReflectionAgentPlayer(name, persona)
        elif strategy=="refine":
            return SelfRefinePlayer(name, persona)
        elif strategy=="persona":
            return PersonaAgentPlayer(name, persona)
        elif strategy=="spp":
            return SPPAgentPlayer(name, persona)
        elif strategy in ["fix", "last", "mono", "monorand"]:
            return ProgramPlayer(name, strategy, mean, std)
        else:
            raise NotImplementedError
    
    def daily_bidding(self, players):
        Average = 0
        for player in players:
            player.act()
            Average += player.last_bidding
        
        Average /= len(players) 
        Target = round_number(Average * 0.8, 2)

        return Average, Target

    def round_deduction(self, players, winner):
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
        if Tie_status:
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

        print("Round ",round_id,": ",bidding_details)

    def run_multi_round(self, max_round):

        for player in self.all_players:
            player.ROUND_WINNER=self.round_winner
        
        for i in range(1, max_round+1):
            self.run_single_round(i)


def main(args):
    for exp_no in range(args.start_exp, args.exp_num):
        prefix = f"{args.player_strategy}_VS_{args.computer_strategy}_{exp_no}"
        if args.computer_strategy in ["fix", "last"]:
            prefix = f"{args.player_strategy}_VS_{args.computer_strategy}-{args.init_mean}-{args.norm_std}_{exp_no}"
        
        Game = G08A(args)
        Game.run_multi_round(args.max_round)

        # Export game records

        if args.output_dir:
            output_file = f"result/{args.output_dir}/{prefix}.json"
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
        else:
            output_file = f"result/{prefix}.json"
        
        with open(output_file,"w") as fout:
            messages = {}
            biddings = {}
            logs = {}
            for agent in Game.all_players:
                if agent.is_agent:
                     messages[agent.name] = agent.message
                biddings[agent.name] = agent.biddings
                if agent.logs:
                    logs[agent.name] = agent.logs

            debug_info = {
                "winners": Game.round_winner,
                "biddings": biddings,
                "message": messages,
                "logs":logs
            }

            json.dump(debug_info, fout, indent=4)

if __name__=="__main__":
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('--player_strategy', type=str, default="cot", choices=["agent","cot","pcot","kr","reflect", "persona", "refine", "spp"])
    parser.add_argument('--computer_strategy', type=str,choices=["agent", "fix", "last", "mono", "monorand","cot","pcot","kr","reflect", "persona", "refine", "spp"], default="fix")
    parser.add_argument("--output_dir", type=str, default=None)
    parser.add_argument("--init_mean", type=int, default=40)
    parser.add_argument("--norm_std", type=int, default=5)
    parser.add_argument('--max_round', type=int, default=5)
    parser.add_argument('--start_exp', type=int, default=0)
    parser.add_argument('--exp_num', type=int, default=5)
    parser.add_argument('--player_engine', type=str, default=None)
    parser.add_argument('--player_k', type=int, default=None)

    args = parser.parse_args()
    main(args)