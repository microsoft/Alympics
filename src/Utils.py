import json
import time
import openai

class PlayGround:
    def __init__(self) -> None:
        self.players = []
        self.game_setting = ""

    def add_player(self, new_player):
        self.players.append(new_player)

class Player:
    def __init__(self, name, if_persona, persona):
        self.name = name
        self.if_persona = if_persona
        self.persona = persona
        self.history = []

    def append_message(self, role, content):
        self.history.append({"role": role, "content": content})

class LLM:
    def __init__(self, engine="gpt4-32k", temperature=0.7, sleep_time=60) -> None:
        openai.api_type = "azure"   
        openai.api_base = ""
        openai.api_version = ""
        openai.api_key = ""
        self.engine = engine
        self.temperature = temperature
        self.sleep_time = sleep_time
    
    def call(self, message):
        status = 0
        while status != 1:
            try:
                response = openai.ChatCompletion.create(
                        engine=self.engine,
                        messages=message,
                        temperature=self.temperature,
                        max_tokens=800,
                        top_p=0.95,
                        frequency_penalty=0,
                        presence_penalty=0,
                        stop=None)
                RESPONSE = response['choices'][0]['message']['content']
                status = 1
                time.sleep(self.sleep_time)
            except Exception as e:
                print(e)
                time.sleep(10)
                pass
        return RESPONSE