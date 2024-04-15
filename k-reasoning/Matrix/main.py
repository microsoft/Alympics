import os
import json

from player import *
from game import MatrixGame


# Fill in your config information to conduct experiments.
openai.api_type = ""
openai.api_base = ""
openai.api_version = ""
openai.api_key = ""
ENGINE = ""


def build_player(strategy, name, persona, k_level):
    """
    Player Factory
    """

    if strategy=="agent":
        return AgentPlayer(name, ENGINE, persona)
    elif strategy=="kr":
        return KLevelReasoningPlayer(name, ENGINE, persona, k_level)
    else:
        raise NotImplementedError


def main(args):
    # Predefined character information
    PERSONA_A = "You are Alex, currently playing a strategy game. "
    PERSONA_B = "You are Bob, currently playing a strategy game. "

    for exp_no in range(args.start_exp, args.exp_num):
        players = []

        # build player
        A = build_player(args.player_strategy, "Alex", PERSONA_A, args.player_k)
        # Modify PlayerA's settings for ablation experiments.
        if args.player_engine: A.engine = args.player_engine
        players.append(A)

        # build opponent
        for program_name, persona in [("Bob", PERSONA_B)]:
            players.append(build_player(args.computer_strategy, program_name, persona, args.computer_k))
        print("Initial players done.")

        # run multi-round game (default 1)
        WA = MatrixGame(players)
        WA.run_multi_round(args.max_round)

        # Export game records
        player_strategy = args.player_strategy
        computer_strategy = args.computer_strategy
        if player_strategy=="kr" and args.player_k!=2:
            player_strategy+="-"+str(args.player_k)
        if computer_strategy=="kr" and args.computer_k!=2:
            computer_strategy+="-"+str(args.computer_k)
        prefix = f"{player_strategy}_VS_{computer_strategy}_{exp_no}"
        output_file = f"{args.output_dir}/{prefix}.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file,"w") as fout:
            messages = {}
            actions = {}
            logs = {}
            for agent in WA.players:
                if agent.is_agent:
                     messages[agent.name] = agent.message
                actions[agent.name] = agent.actions
                if agent.logs:
                    logs[agent.name] = agent.logs

            debug_info = {
                "actions": actions,
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
    parser.add_argument('--max_round', type=int, default=1)
    parser.add_argument('--start_exp', type=int, default=0)
    parser.add_argument('--exp_num', type=int, default=1)
    parser.add_argument('--player_engine', type=str, default=None, help="player's OpenAI api engine")
    parser.add_argument('--player_k', type=int, default=2, help="player's k-level (default 2)")
    parser.add_argument('--computer_k', type=int, default=2, help="computer's k-level (default 2)")

    args = parser.parse_args()
    main(args)