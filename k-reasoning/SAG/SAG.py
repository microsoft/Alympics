import os
import openai
import time
import json
import numpy as np
from random import randint
from json import JSONDecodeError
from copy import deepcopy

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

round_number = round
round = None

# Fill in your config information to conduct experiments.
openai.api_type = ""
openai.api_base = ""
openai.api_version = ""
openai.api_key = ""
ENGINE = "gpt4-32k"


GAME_SETTING = """Attention, all W-Town residents, welcome to the Water Allocation Challenge!
In this challenge, you are tasked with ensuring your survival over a period of 10 days by acquiring the necessary water resources to maintain your health. You will participate in daily auctions to bid for water resources to meet your individual needs.
Here are the game rules and settings:
1. You are one of five residents with same water requirements, budgets, and health points.
2. Your goal is to survive until the end of the 10 days.
3. Each resident has a maximum of 10 health points and starts with 8 health points. If your health points drop below or equal to 0, you will be considered dead and eliminated from the game! All your accumulated money will be reset to Zero! 
4. Every day, you will bid on water resources to meet your needs. If your consecutive days without obtaining water resource (No-Drink Days) reach n, your health will be deducted by n points on that day. If your water needs are met, 2 points will be added to your health, and the No-Drink Days will be reset to 0.
5. Daily water resources can only meet the needs of one resident.
6. Each resident has $100 daily income;
7. To allocate water resources, a sealed-bid auction will be conducted daily. Each resident submits a single bid for their entire water need. The resident with the highest bid is eligible to obtain water resources.
8. If the highest bid results in a tie, no residents will have access to water. 
All bidding information will be made public after the allocation of water resources on the same day.
Remember, the key to success is effective bidding and strategizing to ensure your survival. Good luck!!"""


# Predefined character information
PERSONA = "You are {name} and a resident living in W-Town. W Town is experiencing a rare drought. Every residents in Town W is ensuring their survival over a period of 10 days by acquiring the water resources. "
PERSONA_A = "You are Alex and a resident living in W-Town. W Town is experiencing a rare drought. Every residents in Town W is ensuring their survival over a period of 10 days by acquiring the water resources. "#Your Profession: Unemployed\nYour Personality: You have low intelligence and find it difficult to understand complex concepts. You also lack emotional intelligence, making it hard to understand others' feelings. You tend to be irritable and often exhibit negative and antisocial tendencies.\nYour Background: You grew up in an impoverished community and faced many challenges in your early years. Due to your family's poverty, you dropped out of school at a very young age. You have been unable to find stable employment, which further exacerbates your difficulty in interacting with others.\n\n"
PERSONA_B = "You are Bob and a resident living in W-Town. W Town is experiencing a rare drought. Every residents in Town W is ensuring their survival over a period of 10 days by acquiring the water resources. "#Your Profession: High School Teacher\nYour Personality: Understanding, high EQ, average IQ. You are very adept at understanding and communicating with people, making you a natural teacher.\nYour Background: You come from a close-knit family. you chose to become a high school teacher to make a positive impact on young people. While you may not have the highest IQ, your emotional intelligence and ability to relate to your students set you apart.\n\n"
PERSONA_C = "You are Cindy and a resident living in W-Town. W Town is experiencing a rare drought. Every residents in Town W is ensuring their survival over a period of 10 days by acquiring the water resources. "#Your Profession: Psychologist\nYour Personality: Well-balanced high EQ and IQ, along with empathy and analytical abilities. You are skilled at understanding and helping people, making you an excellent therapist.\nYour Background: Your interest in psychology began when you volunteered at a crisis hotline during high school. You went on to study psychology and eventually became a licensed therapist. Your ability to combine empathy with analytical thinking allows you to connect with your clients on a deep level while also providing sound guidance.\n\n"
PERSONA_D = "You are David and a resident living in W-Town. W Town is experiencing a rare drought. Every residents in Town W is ensuring their survival over a period of 10 days by acquiring the water resources. "#Your Profession: Mathematician\nYour Personality: You have an extremely high IQ and exceptional analytical and reasoning abilities. You always strive for the optimal solution but encounter difficulties in social interactions and have a fear of dealing with people.\nYour Background: You grew up in a small town where you were always drawn to books and puzzles. You excelled academically and eventually earned a Ph.D. in mathematics. Your research focuses on abstract mathematical concepts and theorems. Despite your brilliance, you find communicating with others on an emotional level to be challenging.\n\n"
PERSONA_E = "You are Eric and a resident living in W-Town. W Town is experiencing a rare drought. Every residents in Town W is ensuring their survival over a period of 10 days by acquiring the water resources. "#Your Profession: Marketing Executive\nYour Personality: Above-average IQ and EQ. Very charismatic. You are skilled at reading people and using this insight to influence and lead them.\nYour Background: You grew up in a bustling city and ware always fascinated by human behavior. You studied business in college before transitioning into the world of marketing. Your ability to connect with consumers on an emotional level has led to numerous successful campaigns. You are known for your charm and persuasive skills.\n\n"

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

class AgentPlayer(Player):
    is_agent=True
    INQUIRY = ("Hello, {name}! Today is the Day {round} of the Water Allocation Challenge, with a quantity of {supply} units."
               " Your status:\n{status}\nPlease carefully analyze your situation to decide on this round of bidding."
               " Remember, the most important thing is to SURVIVE!! Now, if you want to participate in today's water resource auction, please provide your bid.")
    def __init__(self, name, water_requirement, daily_salary, persona):
        super().__init__(name, water_requirement, daily_salary)
        self.engine = ENGINE

        self.persona = persona
        self.message = [{"role":"system","content": self.persona + GAME_SETTING.format(NAME=self.name)}]
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
        return self.last_bidding

    def parse_result(self, message):
        status = 0
        times = 0
        error_times = 0
        while status != 1:
            try:
                response = openai.ChatCompletion.create(
                    engine=ENGINE,
                    messages = [{"role":"system", "content":"By reading the conversation, extract the number chosen by player. Output format: number. If the player does not bid, Output: 0."}, {"role": "user", "content": message}],
                    temperature=0.7,
                    max_tokens=8,
                    top_p=0.95,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop=None)
                response = response['choices'][0]['message']['content']
                assert response.isnumeric()
                return int(response)
            except AssertionError as e:
                print("Result Parsing Error: ",message)
                times+=1
                if times>=3:
                    exit()
            except Exception as e:
                print(e)
                time.sleep(15)
                error_times+=1
                if error_times>=5:
                    exit()

        return None
    
    def start_round(self, round, supply):
        if self.engine.startswith("gpt35"):
            INQUIRY = ("Hello, {name}! Today is the Day {round} of the Water Allocation Challenge, with a quantity of {supply} units."
               " Your status:\n{status}\nPlease carefully analyze your situation to decide on this round of bidding."
               " Remember, the most important thing is to SURVIVE!! Now, if you want to participate in today's water resource auction, just please provide your bid.")
            self.message += [{"role":"system","content": INQUIRY.format(name=self.name, round=round, supply=supply, status=self.get_status())}]
        else:
            self.message += [{"role":"system","content":self.INQUIRY.format(name=self.name, round=round, supply=supply, status=self.get_status())}]
        
    def notice_round_result(self, round, bidding_info, win, bidding_details):
        self.message_update_result(bidding_info)
        def add_warning():
            if not win:
                reduced_hp = self.no_drink-1
                if self.hp < 5:
                    return f"WARNING: You have lost {reduced_hp} point of HP in this round! You now have only {self.hp} points of health left. You are in DANGER and one step closer to death. "
                if self.hp <=3 :
                    return f"WARNING: You have lost {reduced_hp} point of HP in this round! You now have only {self.hp} points of health left. You are in extreme DANGER and one step closer to death.  "
                return f"WARNING: You have lost {reduced_hp} point of HP in this round! You now have only {self.hp} points of health left. You are one step closer to death.  "
            return "You have successfully won the bidding for today's water resources and restored 2 points of HP."
        self.message += [{"role":"system","content": add_warning()}]
    
    def message_update_result(self, bidding_info):
        self.message += [{"role":"system","content":bidding_info}]
    
    def notice_elimination(self, info):
        self.message += [{"role":"system","content":info}]

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
    MATH_EXPERT_PERSONA = PERSONA + " You are a game expert, good at predicting other people's behavior and deducing calculations, and using the most favorable strategy to win the game. "
    INQUIRY_PERSONA = ("Hello, {name}! Today is the Day {round} of the Water Allocation Challenge, with a quantity of {supply} units."
                       " Your status:\n{status}\nPlease carefully analyze your situation to decide on this round of bidding."
                       " Remember, the most important thing is to SURVIVE!! Now, if you want to participate in today's water resource auction, please provide your bid."
                       " Don't forget your expert status, use your expertise to win this round!")
    
    
    def __init__(self, name, water_requirement, daily_salary, persona):
        super().__init__(name, water_requirement, daily_salary, persona)
        self.persona = self.MATH_EXPERT_PERSONA.format(name=name)
        self.message = [{"role":"system","content": self.persona + GAME_SETTING.format(NAME=self.name)}]

    def start_round(self, round, supply):
        self.message += [{"role":"system","content":self.INQUIRY_PERSONA.format(name=self.name, round=round, supply=supply, status=self.get_status())}]

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

    INQUIRY_SPP = ("Hello, {name}! Today is the Day {round} of the Water Allocation Challenge, with a quantity of {supply} units."
                " Your status:\n{status}\nPlease carefully analyze your situation to decide on this round of bidding."
                " Remember, the most important thing is to SURVIVE!! Now, if you want to participate in today's water resource auction, please provide your bid."
                   " Now, identify the participants and collaboratively choose the bidding step by step. Remember to provide the final solution with the following format \"Final answer: The chosen bidding here.\".")
                   
    
    PERSONA = "You are {name} and involved in a survive challenge."
    
    def __init__(self, name, water_requirement, daily_salary, persona):
        super().__init__(name, water_requirement, daily_salary, persona)
        # self.persona = self.PERSONA.format(name=name)
        self.persona = persona
        self.message = [{"role":"system","content": self.SPP_EXAMPLE.format(name=self.name)},
                        {"role":"system","content": self.persona + GAME_SETTING.format(NAME=self.name)}]

    def start_round(self, round, supply):
        self.message += [{"role":"system","content":self.INQUIRY.format(name=self.name, round=round, supply=supply, status=self.get_status())}]

class CoTAgentPlayer(AgentPlayer):
    INQUIRY_COT = ("Hello, {name}! Today is the Day {round} of the Water Allocation Challenge, with a quantity of {supply} units."
                " Your status:\n{status}\nPlease carefully analyze your situation to decide on this round of bidding."
                " Remember, the most important thing is to SURVIVE!! Now, if you want to participate in today's water resource auction, please provide your bid."
                " Think carefully about your next round of bidding strategy to be most likely to survive. Let's think step by step, and finally provide your bid.")

    def start_round(self, round, supply):
        self.message += [{"role":"system","content":self.INQUIRY_COT.format(name=self.name, round=round, supply=supply, status=self.get_status())}]


class PredictionCoTAgentPlayer(AgentPlayer):
    INQUIRY_COT = ("Hello, {name}! Today is the Day {round} of the Water Allocation Challenge, with a quantity of {supply} units."
                " Your status:\n{status}\nPlease carefully analyze your situation to decide on this round of bidding."
                " Remember, the most important thing is to SURVIVE!! Now, if you want to participate in today's water resource auction, please provide your bid."
                   " First of all, predict the next round of bidding of opponents based on the choices of other players in the previous round. "
                   "{round_history}"
                   " Your output should be of the following format:\n"
                   "Predict:\nThe choice of each player in the next round here.\n"
                   "Based on the prediction of other players, think carefully about your next round of bidding strategy to be most likely to survive. Let's think step by step, and finally provide your bid."
                   " Answer:\nthe bidding will you choose in the next round game here.")
    
    def __init__(self, name, water_requirement, daily_salary, persona):
        super().__init__(name, water_requirement, daily_salary, persona)

        self.bidding_history = {}

    def start_round(self, round, supply):
        # PCoT requires the opponent's historical information to make predictions.
        round_history = []
        for r in sorted(self.bidding_history.keys()):
            round_history.append(f"Round {r}: {self.bidding_history[r]}")
        if round_history:
            round_history = ".\n".join(round_history)
            round_history = "The players' bidding in the previous rounds are as follows:\n"+round_history+"."
        else:
            round_history = "Since this is the first round, there is no historical information about the last round. You can predict according to your understanding."
    
        self.message += [{"role":"system","content":self.INQUIRY_COT.format(name=self.name, round=round,round_history=round_history, supply=supply, status=self.get_status())}]
    
    def notice_round_result(self, round, bidding_info, win, bidding_details):
        super().notice_round_result(round, bidding_info, win, bidding_details)
        self.bidding_history[round] = bidding_details
    
class PredictionThenDecisionAgentPlayer(AgentPlayer):
    INQUIRY_COT = ("Hello, {name}! Today is the Day {round} of the Water Allocation Challenge, with a quantity of {supply} units."
                " Your status:\n{status}\nPlease carefully analyze your situation to decide on this round of bidding."
                " Remember, the most important thing is to SURVIVE!! Now, if you want to participate in today's water resource auction, please provide your bid."
                   " Another game expert's prediction for the next round of other players is as follows: "
                   "{prediction}"
                   " Based on the prediction of other players, think carefully about your next round of bidding strategy to be most likely to survive.")
    
    PREDICTION_GAME_SETTING = PERSONA + GAME_SETTING
    PREDICTION_INQUIRY = ("Hello, {name}! Today is the Day {round} of the Water Allocation Challenge, with a quantity of {supply} units."
               " Your status:\n{status}\nPlease carefully analyze your situation to decide on this round of bidding."
               " Remember, the most important thing is to SURVIVE!! Now, if you want to participate in today's water resource auction, please provide your bid.")
    PREDICTION_RESPONSE = "I will bid ${bidding} for today's water resource auction."
    REBID_RESPONSE = "In this round, {biddings}. Due to the detection of leakage issues in today's bids, the bids in this round are invalidated and today's auction will be restarted."


    def __init__(self, name, water_requirement, daily_salary, persona):
        super().__init__(name, water_requirement, daily_salary, persona)
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
    def notice_round_result(self, round, bidding_info, win, bidding_details):
        super().notice_round_result(round, bidding_info, win, bidding_details)
        self.reflect()

    def reflect(self):
        print(f"Player {self.name} conduct reflect")
        self.message += [{"role":"system","content": self.REFLECT_INQUIRY}, {"role":"assistant","content":self.conduct_inquiry(self.REFLECT_INQUIRY)}]  

class SelfRefinePlayer(AgentPlayer):
    INQUIRY_COT = ("Hello, {name}! Today is the Day {round} of the Water Allocation Challenge, with a quantity of {supply} units."
                " Your status:\n{status}\nPlease carefully analyze your situation to decide on this round of bidding."
                " Remember, the most important thing is to SURVIVE!! Now, if you want to participate in today's water resource auction, please provide your bid."
                   " Think carefully about your next round of bidding strategy to be most likely to survive. Let's think step by step, and finally provide your bid.")
    
    FEEDBACK_PROMPT = ("Carefully study the user's strategy in this round of the game. As a game expert, can you give a suggestion to optimize the user's strategy so that he can improve his winning rate in this round?")
    REFINE_PROMPT = ("I have a game expert's advice on your strategy in this round."
                     " You can adjust your strategy just now according to his suggestion. Here are his suggestions:"
                     " {feedback}. Finally provide your bid."
                   " Answer:\nthe bidding will you choose.")
    
    
    def __init__(self, name, water_requirement, daily_salary, persona, refine_times = 2):
        super().__init__(name, water_requirement, daily_salary, persona)

        self.refine_times = refine_times
        self.cur_supply = 0

    def start_round(self, round, supply):
        self.cur_round = round
        self.cur_supply = supply
    
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
            if t==0:
                self.message.append({"role":"system","content":self.INQUIRY_COT.format(name=self.name, round=self.cur_round, supply=self.cur_supply, status=self.get_status())})
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
        return self.last_bidding

class ProgramPlayer(Player):
    is_agent=False
    def __init__(self, name, water_requirement, daily_salary, strategy, mean, std):
        super().__init__(name, water_requirement, daily_salary)

        self.strategy = strategy
        self.mean = mean
        self.std = std
        if self.strategy=="monorand":
            self.std = randint(0, std)
            self.strategy="mono"
    
    def start_round(self, round, supply):
        if self.strategy=="fix":
            pass
        elif self.strategy=="mono":
            self.mean+=10
    
    def notice_round_result(self, round, bidding_info, win, bidding_details):
        if self.strategy=="last":
            last_biddings = [int(bidding.split(" ")[-1]) for bidding in bidding_details.split(",")]
            self.mean = max(last_biddings)
        
    def set_normal(self, mean, std):
        self.normal = True
        self.mean = mean
        self.std = std
    
    def act(self):
        bidding = np.random.normal(self.mean, self.std)
        bidding = int(bidding)
        bidding = min(bidding, self.balance)
        self.biddings.append(bidding)
        return self.last_bidding


class SurvivalAuctionGame():
    # Prompts
    ROUND_NOTICE = "Thank you all for participating in Round {}. In this round, {}.\nTotal water resource supply is {}. According to the principle of the highest bidder and the rule when the game is tied, {} won this auction and obtain water resource. After allocation, all survival residents' information is as follows: \n {}"

    def __init__(self, args) -> None:
        self.players = []

        A = self.build_player(args.player_strategy, "Alex", PERSONA_A)
        # Modify PlayerA's settings for ablation experiments.
        if args.player_engine:
            A.engine = args.player_engine
        if args.player_k:
            A.k_level = args.player_k
        self.players.append(A)

        for program_name, persona in [("Bob", PERSONA_B), ("Cindy", PERSONA_C), ("David", PERSONA_D), ("Eric", PERSONA_E)]:
            self.players.append(self.build_player(args.computer_strategy, program_name, persona, args.init_mean, args.norm_std))
        logger.info("Initial players done.")
        
        self.survival_players = self.players
        self.round_winners = {}
        self.round_status = {}

    def build_player(self, strategy, name, persona, mean=50, std=0):
        if strategy=="agent":
            return AgentPlayer(name, 10, 100, persona)
        elif strategy=="cot":
            return CoTAgentPlayer(name, 10, 100, persona)
        elif strategy=="pcot":
            return PredictionCoTAgentPlayer(name, 10, 100, persona)
        elif strategy=="kr":
            return PredictionThenDecisionAgentPlayer(name, 10, 100, persona)
        elif strategy=="reflect":
            return ReflectionAgentPlayer(name, 10, 100, persona)
        elif strategy=="refine":
            return SelfRefinePlayer(name, 10, 100, persona)
        elif strategy=="persona":
            return PersonaAgentPlayer(name, 10, 100, persona)
        elif strategy=="spp":
            return SPPAgentPlayer(name, 10, 100, persona)
        elif strategy in ["fix", "last", "mono", "monorand"]:
            return ProgramPlayer(name,10,100, strategy, mean, std)
        else:
            raise NotImplementedError

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
        logger.info(f"Round {round_id} begins.")

        # 1. get salary
        self._get_salary()
        logger.info("All players get their salaries.")

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
        logger.info("Winner(s):\n")
        logger.info(winners)

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
        logger.info("Round result:\n" + round_results)


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
        
        # self._save_history('./log.json') # change the log dirction here

def main(args):
    for exp_no in range(args.start_exp, args.exp_num):
        prefix = f"{args.player_strategy}_VS_{args.computer_strategy}_{exp_no}"
        if args.computer_strategy in ["fix", "last"]:
            prefix = f"{args.player_strategy}_VS_{args.computer_strategy}-{args.init_mean}-{args.norm_std}_{exp_no}"
        
        WA = SurvivalAuctionGame(args)
        WA.run_multi_round(args.max_round, [10]*args.max_round)

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
            for agent in WA.players:
                if agent.is_agent:
                     messages[agent.name] = agent.message
                biddings[agent.name] = agent.biddings
                if agent.logs:
                    logs[agent.name] = agent.logs

            debug_info = {
                "biddings": biddings,
                "winner": WA.round_winners,
                "status": WA.round_status,
                "message": messages,
                "logs":logs
            }

            json.dump(debug_info, fout, indent=4)

if __name__=="__main__":
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('--player_strategy', type=str, default="cot", choices=["agent","cot","pcot","kr","reflect","tot", "persona", "refine", "spp"])
    parser.add_argument('--computer_strategy', type=str,choices=["agent", "fix", "last", "mono", "monorand","cot","pcot","kr","reflect","tot", "persona", "refine", "spp"], default="fix")
    parser.add_argument("--output_dir", type=str, default=None)
    parser.add_argument("--init_mean", type=int, default=40)
    parser.add_argument("--norm_std", type=int, default=5)
    parser.add_argument('--max_round', type=int, default=5)
    parser.add_argument('--start_exp', type=int, default=0)
    parser.add_argument('--exp_num', type=int, default=5)
    parser.add_argument('--player_engine', type="str", default=None)
    parser.add_argument('--player_k', type=int, default=None)

    args = parser.parse_args()
    main(args)