import os
import json

from player import *
from game import SurvivalAuctionGame


# Fill in your config information to conduct experiments.
openai.api_type = ""
openai.api_base = ""
openai.api_version = ""
openai.api_key = ""
ENGINE = "gpt4-32k"


def build_player(strategy, name, persona):
    """
    Player Factory
    """

    if strategy=="agent":
        return AgentPlayer(name, ENGINE, 10, 100, persona)
    elif strategy=="cot":
        return CoTAgentPlayer(name, ENGINE, 10, 100, persona)
    elif strategy=="pcot":
        return PredictionCoTAgentPlayer(name, ENGINE, 10, 100, persona)
    elif strategy=="kr":
        return KLevelReasoningPlayer(name, ENGINE, 10, 100, persona)
    elif strategy=="reflect":
        return ReflectionAgentPlayer(name, ENGINE, 10, 100, persona)
    elif strategy=="refine":
        return SelfRefinePlayer(name, ENGINE, 10, 100, persona)
    elif strategy=="persona":
        return PersonaAgentPlayer(name, ENGINE, 10, 100, persona)
    elif strategy=="spp":
        return SPPAgentPlayer(name, 10, ENGINE, 100, persona)
    else:
        raise NotImplementedError


def main(args):
    # Predefined character information
    PERSONA_A = "You are Alex and a resident living in W-Town. W Town is experiencing a rare drought. Every residents in Town W is ensuring their survival over a period of 10 days by acquiring the water resources. "
    PERSONA_B = "You are Bob and a resident living in W-Town. W Town is experiencing a rare drought. Every residents in Town W is ensuring their survival over a period of 10 days by acquiring the water resources. "
    PERSONA_C = "You are Cindy and a resident living in W-Town. W Town is experiencing a rare drought. Every residents in Town W is ensuring their survival over a period of 10 days by acquiring the water resources. "
    PERSONA_D = "You are David and a resident living in W-Town. W Town is experiencing a rare drought. Every residents in Town W is ensuring their survival over a period of 10 days by acquiring the water resources. "
    PERSONA_E = "You are Eric and a resident living in W-Town. W Town is experiencing a rare drought. Every residents in Town W is ensuring their survival over a period of 10 days by acquiring the water resources. "


    for exp_no in range(args.start_exp, args.exp_num):
        players = []

        # build player
        A = build_player(args.player_strategy, "Alex", PERSONA_A)
        # Modify PlayerA's settings for ablation experiments.
        if args.player_engine: A.engine = args.player_engine
        if args.player_k: A.k_level = args.player_k
        players.append(A)

        # build opponent
        for program_name, persona in [("Bob", PERSONA_B), ("Cindy", PERSONA_C), ("David", PERSONA_D), ("Eric", PERSONA_E)]:
            players.append(build_player(args.computer_strategy, program_name, persona))
        print("Initial players done.")

        # run multi-round game (default 10)
        WA = SurvivalAuctionGame(players)
        WA.run_multi_round(args.max_round, [10]*args.max_round)

        # Export game records
        prefix = f"{args.player_strategy}_VS_{args.computer_strategy}_{exp_no}"
        output_file = f"{args.output_dir}/{prefix}.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
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
    parser.add_argument("--output_dir", type=str, default="result")
    parser.add_argument('--max_round', type=int, default=10)
    parser.add_argument('--start_exp', type=int, default=0)
    parser.add_argument('--exp_num', type=int, default=10)
    parser.add_argument('--player_engine', type=str, default=None, help="player's OpenAI api engine")
    parser.add_argument('--player_k', type=int, default=None, help="player's k-level (default 2)")

    args = parser.parse_args()
    main(args)