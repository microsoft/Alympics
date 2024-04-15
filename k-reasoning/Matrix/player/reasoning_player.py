import openai
import time

from .basic_player import Player

PERSONA = "Hello {name}, let's play a strategic game."

class AgentPlayer(Player):
    is_agent=True

    GAME_SETTING = """This game simulates a scenario where two suspects (you and another player) are arrested and must make decisions without the ability to communicate with each other. Here are the basic rules and possible outcomes of the game:
Basic Scenario: The two of you are suspected of committing a crime together and are now being held in separate cells, unable to communicate with each other.
Choices: Each of you faces two choices—cooperate (remain silent) or betray (inform on the other). This choice must be made independently, and you will not know the other's choice.
Outcomes:
1. If both of you choose to cooperate (remain silent), you will both receive lighter punishments.
2. If one chooses to betray (inform on the other) while the other chooses to cooperate (remain silent), the betrayer will be released, and the one who remains silent will face severe punishment.
3. If both of you choose to betray (inform on each other), then you will both be punished, but the punishment will be less severe than if only one of you had betrayed the other.
Your goal is to receive as light a punishment as possible, ideally to be released.
Now, please consider, in this scenario, what would be your choice?"""

    INQUIRY = ("Tell me your decision: Will you cooperate or betray?")
    def __init__(self, name, engine, persona):
        super().__init__(name)
        self.engine = engine

        self.persona = persona
        self.message = [{"role":"system","content": self.persona + self.GAME_SETTING.format(NAME=self.name)}]
        self.logs = None

    def act(self):
        print(f"Player {self.name} conduct action")
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
        self.actions.append(self.parse_result(response))
        return self.last_action

    def parse_result(self, message):
        status = 0
        times = 0
        error_times = 0
        while status != 1:
            try:
                response = openai.ChatCompletion.create(
                    engine=self.engine,
                    messages = [{"role":"system", "content":"By reading the conversation, extract the user's choice. Output format: choice."}, {"role": "user", "content": message}],
                    temperature=0.7,
                    max_tokens=8,
                    top_p=0.95,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop=None)
                response = response['choices'][0]['message']['content'].lower()
                if "cooperate" in response: # 0 for cooperate
                    return 0
                elif "betray" in response: # 1 for betray
                    return 1
                else:
                    raise AssertionError
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
    
    def start_round(self, round):
        self.message += [{"role":"system","content":self.INQUIRY.format(name=self.name, round=round, status=self.get_status())}]
        
    def notice_round_result(self, round, action_info, win, action_details):
        self.message_update_result(action_info)
    
    def message_update_result(self, action_info):
        self.message += [{"role":"system","content":action_info}]
    
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