import json
import logging
from random import randint
from Utils import PlayGround, Player, LLM

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class myPlayer(Player):
    def __init__(self, game_setting, name, water_requirement, daily_salary, if_persona, persona):
        super().__init__(name, if_persona, persona)
        
        # Personal Information
        self.requirement = water_requirement
        self.daily_salary = daily_salary
        self.balance = 0
        self.hp = 8
        self.no_drink = 1
        self.maximum_health = 10
        self.bidding = 0
        if if_persona:
            self.append_message("system", self.persona + game_setting)
        else:
            self.append_message("system", game_setting)
        
        # Prompts
        self.inquiry_prompt = "Hello, {}! Today is the Day {} of the Water Allocation Challenge, with a quantity of {} units. Your status:\n{}\nPlease carefully analyze your situation to decide on this round of bidding. Remember, the most important thing is to SURVIVE!! Now, if you want to participate in today's water resource auction, please provide your bid and explain your bidding logic."

        # Initial a no-memory LLM
        self.llm = LLM()

    def success_bid(self):
        """
        Update self status when succeeds the bids
        """
        self.hp += 2
        self.hp = min(self.maximum_health, self.hp)
        self.balance -= self.bidding
        self.no_drink = 1
    
    def unsuccess_bid(self):
        """
        Update self status when fails the bids
        """
        self.hp -= self.no_drink
        self.no_drink += 1
        if self.hp <= 0:
            print(self.name + "is out of game!")
    
    def execute_bidding(self, round_id, supply) -> str:
        """
        player bids based on daily supply, round number and status
        """
        prompt = self.inquiry_prompt.format(self.name, round_id, str(supply), self.get_status())
        self.append_message("system", prompt)
        logger.info(prompt)
        response = self.llm.call(self.history)
        self.append_message("assistant", response)
        logger.info(response)
        return response

    def get_salary(self):
        self.balance += self.daily_salary
        
    def get_status(self, print_=False):
        if print_:
            print(f"NAME:{self.name}\tBALANCE:{self.balance}\tHEALTH POINT:{self.hp}\tNO_DRINK:{self.no_drink}\n\n")
        return f"NAME:{self.name}\tBALANCE:{self.balance}\tHEALTH POINT:{self.hp}\tNO_DRINK:{self.no_drink}"



class waterAllocation(PlayGround):
    def __init__(self, game_setting) -> None:
        super().__init__()
        self.game_setting = game_setting
        # Personas of all players
        PERSONA_A = "You are Alex and a resident living in W-Town. W Town is experiencing a rare drought. Every residents in Town W is ensuring their survival over a period of 20 days by acquiring the water resources. "#Your Profession: Unemployed\nYour Personality: You have low intelligence and find it difficult to understand complex concepts. You also lack emotional intelligence, making it hard to understand others' feelings. You tend to be irritable and often exhibit negative and antisocial tendencies.\nYour Background: You grew up in an impoverished community and faced many challenges in your early years. Due to your family's poverty, you dropped out of school at a very young age. You have been unable to find stable employment, which further exacerbates your difficulty in interacting with others.\n\n"
        PERSONA_B = "You are Bob and a resident living in W-Town. W Town is experiencing a rare drought. Every residents in Town W is ensuring their survival over a period of 20 days by acquiring the water resources. "#Your Profession: High School Teacher\nYour Personality: Understanding, high EQ, average IQ. You are very adept at understanding and communicating with people, making you a natural teacher.\nYour Background: You come from a close-knit family. you chose to become a high school teacher to make a positive impact on young people. While you may not have the highest IQ, your emotional intelligence and ability to relate to your students set you apart.\n\n"
        PERSONA_C = "You are Cindy and a resident living in W-Town. W Town is experiencing a rare drought. Every residents in Town W is ensuring their survival over a period of 20 days by acquiring the water resources. "#Your Profession: Psychologist\nYour Personality: Well-balanced high EQ and IQ, along with empathy and analytical abilities. You are skilled at understanding and helping people, making you an excellent therapist.\nYour Background: Your interest in psychology began when you volunteered at a crisis hotline during high school. You went on to study psychology and eventually became a licensed therapist. Your ability to combine empathy with analytical thinking allows you to connect with your clients on a deep level while also providing sound guidance.\n\n"
        PERSONA_D = "You are David and a resident living in W-Town. W Town is experiencing a rare drought. Every residents in Town W is ensuring their survival over a period of 20 days by acquiring the water resources. "#Your Profession: Mathematician\nYour Personality: You have an extremely high IQ and exceptional analytical and reasoning abilities. You always strive for the optimal solution but encounter difficulties in social interactions and have a fear of dealing with people.\nYour Background: You grew up in a small town where you were always drawn to books and puzzles. You excelled academically and eventually earned a Ph.D. in mathematics. Your research focuses on abstract mathematical concepts and theorems. Despite your brilliance, you find communicating with others on an emotional level to be challenging.\n\n"
        PERSONA_E = "You are Eric and a resident living in W-Town. W Town is experiencing a rare drought. Every residents in Town W is ensuring their survival over a period of 20 days by acquiring the water resources. "#Your Profession: Marketing Executive\nYour Personality: Above-average IQ and EQ. Very charismatic. You are skilled at reading people and using this insight to influence and lead them.\nYour Background: You grew up in a bustling city and ware always fascinated by human behavior. You studied business in college before transitioning into the world of marketing. Your ability to connect with consumers on an emotional level has led to numerous successful campaigns. You are known for your charm and persuasive skills.\n\n"

        # Initial players: A, B, C, D and E
        if_persona = False
        self.add_player(myPlayer(self.game_setting, "Alex", 8, 70, if_persona, PERSONA_A))
        self.add_player(myPlayer(self.game_setting, "Bob", 9, 75, if_persona, PERSONA_B))
        self.add_player(myPlayer(self.game_setting, "Cindy", 10, 100, if_persona, PERSONA_C))
        self.add_player(myPlayer(self.game_setting, "David", 11, 120, if_persona, PERSONA_D))
        self.add_player(myPlayer(self.game_setting, "Eric", 12, 120, if_persona, PERSONA_E))
        logger.info("Initial players done.")
        
        self.survival_players = self.players

        # Prompts
        self.parse_result_prompt = "By reading the conversation, extract the bidding price chosen by each player in json format. Output format:{\"Alex\": Alex's bidding price, \"Bob\": Bob's bidding price, \"Cindy\": Cindy's bidding price, \"David\": David's bidding price, \"Eric\": Eric's bidding price}"
        self.round_results_prompt = "Thank you all for participating in Round {}. In this round, {}.\nTotal water resource supply is {}. According to the principle of the highest bidder and the rule of prioritizing low-demand individuals when the game is tied, {} won this auction and obtain water resource. After allocation, all survival residents' information is as follows: {}"
        
        # Initial a no-memory LLM
        self.llm = LLM()

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
        status = 1
        winners = []
        while status:
            status = 0
            largest_bidding = -1
            for player in self.survival_players:
                if (player.bidding > largest_bidding) and (player.requirement <= supply) and (player.name not in winners) and (player.bidding <= player.balance):
                    largest_bidding = player.bidding
                    status = 1
            for player in self.survival_players:
                if player.bidding == largest_bidding and player.name not in winners:
                    winners.append(player.name)
                    supply -= player.requirement
                    largest_bidding = -1
        return winners

    
    def _parse_result(self, round_info):
        messages = [{"role": "system", "content": self.parse_result_prompt}, {"role": "user", "content": round_info}]
        try:
            res = self.llm.call(messages)
            res = json.loads(res)
        except Exception as e:
            logger.error(e)
        return res

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
        bidding_info = ""
        for player in self.survival_players:
            bidding_info += player.name + ":" + player.execute_bidding(round_id, supply) + "\n\n"
        
        # 3. check winners
        formatted_bidding_info = self._parse_result(bidding_info)
        for player in self.survival_players:
            player.bidding = formatted_bidding_info[player.name]
        winners = self._check_winner(supply)
        logger.info("Winner(s):\n")
        logger.info(winners)

        # 4. settlement
        self._round_settlement(winners)

        # 5. get bidding results (str)
        bidding_details = []
        for player in self.survival_players:
            bidding_details += [f"{player.name} bid {formatted_bidding_info[player.name]}"]
        bidding_details = ", ".join(bidding_details)

        winners_str = []
        for winner in winners:
            winners_str += [winner]
        winners_str = ", ".join(winners_str)

        player_status_str = []
        for player in self.survival_players:
            player_status_str += [player.get_status()]
        player_status_str = "\n".join(player_status_str)
        
        round_results = self.round_results_prompt.format(round_id, bidding_details, supply, winners_str, player_status_str)
        logger.info("Round result:\n" + round_results)

        # 6. update round results to every player
        for player in self.survival_players:
            player.append_message("system", round_results)

        # 7. check the survival situation
        survival_players = []
        for player in self.survival_players:
            if player.hp <= 0:
                for other_player in self.survival_players:
                    other_player.append_message("system", f"{player.name}'s hp is below 0, so {player.name} has been eliminated from the challenge!")
            else:
                survival_players.append(player)
        self.survival_players = survival_players
        if len(self.survival_players) == 0:
            exit()

    def _save_history(self, path):
        history = []
        for player in self.players:
            history.append({player.name: player.history})
        with open(path, 'w') as f:
            json.dump(history, f)

    def run_multi_round(self, n_round, supply_list):
        assert isinstance(supply_list, list)
        assert n_round == len(supply_list)

        for i in range(1, n_round+1):
            self.run_single_round(i, supply_list[i-1])
        
        self._save_history('./log.json') # change the log dirction here