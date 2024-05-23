import json
import os
import time
import openai

class PlayGround:
    def __init__(self) -> None:
        self.players = []
        self.game_setting = ""
        self.history = [] # Historical Records
        self.game_setting = []# Game Setting

    def add_player(self, new_player):
        self.players.append(new_player)

class Player:
    def __init__(self, name, if_persona, persona):
        self.name = name
        self.if_persona = if_persona # Persona Setting
        self.persona = persona
        self.llm = None
        self.player_status = {} # Player Status
        self.history = [] # Memory Cache
        self.reasoning = None # Reasoning Plugin
        self.other_components = None # Other Components

    def append_message(self, role, content):
        self.history.append({"role": role, "content": content})

class LLM:
    def __init__(self, engine=None, temperature=0.7, sleep_time=10) -> None:
        openai.api_type = os.getenv("OPENAI_API_TYPE")   
        openai.api_base = os.getenv("OPENAI_API_BASE")
        openai.api_version = os.getenv("OPENAI_API_VERSION")
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
        self.engine = os.getenv("OPENAI_API_ENGINE") if not engine else engine
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
                time.sleep(5)
                pass
        return RESPONSE