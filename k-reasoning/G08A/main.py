import os
import json

from player import *
from game import G08A

# Fill in your config information to conduct experiments.
openai.api_type = ""
openai.api_base = ""
openai.api_version = ""
openai.api_key = ""

ENGINE = "gpt4-32k"

def build_player(strategy, name, persona, mean=50, std=0, player_names = []):
    """
    Player Factory
    """
    if strategy=="agent":
        return AgentPlayer(name, persona, ENGINE)
    elif strategy=="cot":
        return CoTAgentPlayer(name, persona, ENGINE)
    elif strategy=="persona":
        return PersonaAgentPlayer(name, persona, ENGINE)
    elif strategy=="reflect":
        return ReflectionAgentPlayer(name, persona, ENGINE)
    elif strategy=="refine":
        return SelfRefinePlayer(name, persona, ENGINE)
    elif strategy=="pcot":
        return PredictionCoTAgentPlayer(name, persona, ENGINE)
    elif strategy=="kr":
        return KLevelReasoningPlayer(name, persona, ENGINE, player_names)
    elif strategy=="spp":
        return SPPAgentPlayer(name, persona, ENGINE)
    elif strategy in ["fix", "last", "mono", "monorand"]:
        return ProgramPlayer(name, strategy, mean, std)
    else:
        raise NotImplementedError


def main(args):
    #Predefined Persona information
    PERSONA_A = "You are Alex and involved in a survive challenge. "
    PERSONA_B = "You are Bob and involved in a survive challenge. "
    PERSONA_C = "You are Cindy and involved in a survive challenge. " 
    PERSONA_D = "You are David and involved in a survive challenge. "
    PERSONA_E = "You are Eric and involved in a survive challenge. "

    for exp_no in range(args.start_exp, args.exp_num):
        players=[]
        player_names = ["Alex", "Bob", "Cindy", "David", "Eric"]

        # build player
        A = build_player(args.player_strategy, "Alex", PERSONA_A, player_names=player_names)
        # Modify PlayerA's settings for ablation experiments.
        if args.player_engine: A.engine = args.player_engine
        if args.player_k:  A.k_level = args.player_k
        players.append(A)

        # build opponent
        for program_name, persona in [("Bob", PERSONA_B), ("Cindy", PERSONA_C), ("David", PERSONA_D), ("Eric", PERSONA_E)]:
            players.append(build_player(args.computer_strategy, program_name, persona, args.init_mean, args.norm_std, player_names=player_names))

        # run multi-round game (default 10)
        Game = G08A(players)
        Game.run_multi_round(args.max_round)

        # export game records
        prefix = f"{args.player_strategy}_VS_{args.computer_strategy}_{exp_no}"
        if args.computer_strategy in ["fix", "last"]:
            prefix = f"{args.player_strategy}_VS_{args.computer_strategy}-{args.init_mean}-{args.norm_std}_{exp_no}"

        output_file = f"{args.output_dir}/{prefix}.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
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
    parser.add_argument("--output_dir", type=str, default="result")
    parser.add_argument("--init_mean", type=int, default=40, help="init mean value for computer player")
    parser.add_argument("--norm_std", type=int, default=5, help="standard deviation of the random distribution of computer gamers")
    parser.add_argument('--max_round', type=int, default=10)
    parser.add_argument('--start_exp', type=int, default=0)
    parser.add_argument('--exp_num', type=int, default=10)
    parser.add_argument('--player_engine', type=str, default=None, help="player's OpenAI api engine")
    parser.add_argument('--player_k', type=int, default=None, help="player's k-level (default 2)")

    args = parser.parse_args()
    main(args)