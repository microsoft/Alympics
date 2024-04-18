import openai
import time

from .basic_player import Player


from openai import OpenAI, AzureOpenAI


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
    
    def __init__(self, name, persona, client):
        self.name = name
        self.client = client
        self.hp = 10

        self.biddings = []
        self.persona = persona
        self.message = [{"role":"system","content": self.persona + self.GAME_SETTING.format(NAME=self.name)}]

        self.logs = None


        self.parse_client = AzureOpenAI(
            api_key="",
            api_version="",
            azure_endpoint=""
        )
        self.parse_engine = ""
    
    @property
    def window_message(self):
        if self.client.model.startswith("meta-llama"):
            window = [0]
            window +=list(range(max(1, len(self.message)-4*6-1),len(self.message))) # 4 for window, 6 for round
            message = [self.message[i] for i in window]
            return message
        else:
            return self.message
        

    def act(self):
        print(f"Player {self.name} conduct bidding")
        status = 0
        while status != 1:
            try:
                response = self.client.chat_completion(messages = self.window_message)
                # response = response.choices[0].message.content
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
                response = self.parse_client.chat.completions.create(
                    # engine=self.engine,
                    model = parse_engine,
                    messages = [{"role":"system", "content":"By reading the conversation, extract the number chosen by player. Output format: number"}, {"role": "user", "content": text}],
                    temperature=0.7,
                    max_tokens=80,
                    top_p=0.95,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop=None)
                response = response.choices[0].message.content
                # response = response
                assert response.isnumeric(), "Not A Number: "+ text
                bidding_info = int(float(response))
                status = 1
                return str(bidding_info)
            except AssertionError as e:
                print("Result Parsing Error: ",e)
                times+=1
                if times>=3:
                    exit()
            except Exception as e:
                print(e)
                time.sleep(15)
        # 返回结果
        return None
    
    def start_round(self, round):
        self.message += [{"role":"user","content":self.INQUIRY.format(name=self.name, round=round, hp=self.hp)}]
        self.cur_round = round
        
    def notice_round_result(self, round, bidding_info, round_target, win, bidding_details, history_biddings):
        self.message_update_result(bidding_info)
        self.message_update_warning(win)
    
    def message_update_result(self, bidding_info):
        self.message += [{"role":"user","content":bidding_info}]
        self.message += [{"role":"assistant","content":"I see."}]
    
    def message_update_warning(self, win):
        def add_warning():
            if not win:
                if self.hp < 5:
                    return f"WARNING: You have lost 1 point of HP in this round! You now have only {self.hp} points of health left. You are in DANGER and one step closer to death. "
                if self.hp <=3 :
                    return f"WARNING: You have lost 1 point of HP in this round! You now have only {self.hp} points of health left. You are in extreme DANGER and one step closer to death.  "
                return f"WARNING: You have lost 1 point of HP in this round! You now have only {self.hp} points of health left. You are one step closer to death.  "
            return "You have successfully chosen the number closest to the target number, which is the average of all players' selected numbers multiplied by 0.8. As a result, you have won this round. All other players will now deduct 1 HP. "
        
        self.message += [{"role":"user","content": add_warning()}]
        self.message += [{"role":"assistant","content":"Thank you."}]

    def conduct_inquiry(self, inquiry):
        while 1:
            try:
                response = openai.ChatCompletion.create(
                    engine=self.engine,
                    messages = self.message + [{"role":"user","content":inquiry}],
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


class CoTAgentPlayer(AgentPlayer):
    INQUIRY_COT = ("Ok, {name}! Now is the ROUND {round}, and your HP is at {hp}. "
                   "Guess which number will win in the next round. Let's think step by step, and finally answer a number you think you can win.")

    def start_round(self, round):
        self.message += [{"role":"user","content":self.INQUIRY_COT.format(name=self.name, round=round, hp=self.hp)}]


class PersonaAgentPlayer(AgentPlayer):
    INQUIRY_PERSONA = ("Ok, {name}! Now is the ROUND {round}, and your HP is at {hp}. "
                       "Please choose an integer between 1 and 100 for this round."
                       "Don't forget your expert status, use your expertise to win this round!")
                   
    
    MATH_EXPERT_PERSONA = ("You are {name} and involved in a survive challenge."
                   " You are a game expert, good at predicting other people's behavior and deducing calculations, and using the most favorable strategy to win the game.")
    
    def __init__(self, name, persona, engine):
        super().__init__(name, persona, engine)
        self.persona = self.MATH_EXPERT_PERSONA.format(name=name)
        self.message = [{"role":"user","content": self.persona + self.GAME_SETTING.format(NAME=self.name)}]

    def start_round(self, round):
        self.message += [{"role":"user","content":self.INQUIRY_PERSONA.format(name=self.name, round=round, hp=self.hp)}]


class ReflectionAgentPlayer(AgentPlayer):
    REFLECT_INQUIRY = "Review the previous round games, summarize the experience."
    def notice_round_result(self, round, bidding_info, round_target, win, bidding_details, history_biddings):
        super().notice_round_result(round, bidding_info, round_target, win, bidding_details, history_biddings)
        # refelxtion after round end
        self.reflect()

    def reflect(self):
        print(f"Player {self.name} conduct reflect")
        self.message += [{"role":"user","content": self.REFLECT_INQUIRY}, {"role":"assistant","content":self.conduct_inquiry(self.REFLECT_INQUIRY)}]  


class SelfRefinePlayer(AgentPlayer):
    INQUIRY_COT = ("Ok, {name}! Now is the ROUND {round}, and your HP is at {hp}. "
                   "Guess which number will win in the next round. Let's think step by step, and finally answer a number you think you can win.")
    
    FEEDBACK_PROMPT = ("Carefully study the user's strategy in this round of the game. As a game expert, can you give a suggestion to optimize the user's strategy so that he can improve his winning rate in this round?")
    REFINE_PROMPT = ("I have a game expert's advice on your strategy in this round."
                     "You can adjust your strategy just now according to his suggestion. Here are his suggestions:"
                     "{feedback}")
    
    
    def __init__(self, name, persona, engine,  refine_times = 2):
        super().__init__(name, persona, engine)

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
                self.message.append({"role":"user","content":self.INQUIRY_COT.format(name=self.name, round=self.cur_round, hp=self.hp)})
            else:
                refine_message = []
                for m in self.message:
                    if m["role"]=="user":
                        refine_message.append(m)
                    else:
                        refine_message.append({
                            "role": "user",
                            "content": m["content"]
                        })
                refine_message.append({
                        "role": "user",
                        "content": self.FEEDBACK_PROMPT
                    })
                feedback = completion(refine_message)
                self.message.append({"role":"user","content": self.REFINE_PROMPT.format(feedback=feedback)})
            self.message.append({"role":"assistant","content": completion(self.message)})
        
        self.biddings.append(self.parse_result(self.message[-1]["content"]))


class PredictionCoTAgentPlayer(AgentPlayer):
    INQUIRY_COT = ("Ok, {name}! Now is the ROUND {round}, and your HP is at {hp}. "
                   "Please choose an integer between 1 and 100 for this round.\n"
                   "First of all, predict the next round of choices based on the choices of other players in the previous round. "
                   "{round_history}"
                   "Your output should be of the following format:\n"
                   "Predict:\nThe choice of each player in the next round here.\n"
                   "Based on the prediction of other players, the average number in the next round here, and the target number in the next round (0.8 * the average of all chosen numbers) here.\n"
                   "Answer:\nthe number will you choose to win the next round game here.")
    
    def __init__(self, name, persona, engine):
        super().__init__(name, persona, engine)

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

        self.message += [{"role":"user","content":self.INQUIRY_COT.format(name=self.name, round=round,round_history=round_history, hp=self.hp)}]
    
    def notice_round_result(self, round, bidding_info, round_target, win, bidding_details, history_biddings):
        super().notice_round_result(round, bidding_info, round_target, win, bidding_details, history_biddings)
        self.bidding_history[round] = bidding_details


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
    
    def __init__(self, name, persona, engine):
        super().__init__(name, persona, engine)
        self.persona = self.PERSONA.format(name=name)
        self.message = [{"role":"user","content": self.SPP_EXAMPLE.format(name=self.name)},
                        {"role":"user","content": self.persona + self.GAME_SETTING.format(NAME=self.name)}]

    def start_round(self, round):
        self.message += [{"role":"user","content":self.INQUIRY_SPP.format(name=self.name, round=round, hp=self.hp)}]