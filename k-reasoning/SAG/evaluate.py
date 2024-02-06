import json
import re
import os
from glob import glob

import numpy as np

def survival_rate(status, soft=True):
    rounds = [str(r) for r in range(1, len(status)+1)]
    players = {}
    for r in rounds:
        for player in status[r]:
            players[player] = r
    for player in players:
        if soft:
            players[player] = int(players[player])/len(rounds)
        else:
            players[player] = 1 if int(players[player])==len(rounds) else 0
    return players

def AverageSurvivalRound(players, opponents, result_dir, latex_output=False):
    def interpolate_color(colorA, colorB, colorC, alpha, beta=0.5):
        if alpha>beta:
            alpha = (alpha-beta)/(1-beta)
            return tuple(np.array(colorB)*(1-alpha) + np.array(colorA)*(alpha))
        else:
            low = 0.4
            alpha = (alpha-low)/(beta-low)
            return tuple(np.array(colorC)*(1-alpha) + np.array(colorB)*(alpha))


    asr_result = {}

    for agent, agent_alias in players.items():
        asr_result.setdefault(agent, {})
        for computer, computer_alias in opponents.items():
            exp = f"{result_dir}/{agent_alias}_VS_{computer_alias}*.json"
            cots = glob(exp)

            wins = {}
            for result in cots:
                with open(result) as fin:
                    result = json.load(fin)["status"]
                    sr = survival_rate(result, soft=True)
                    for player in sr:
                        wins.setdefault(player, [])
                        wins[player].append(sr[player])

            win_rate = sum(wins["Alex"])/len(wins["Alex"])
            asr_result[agent][computer] = win_rate
    
    average = {}
    for i, agent in enumerate(asr_result):
        average[agent] = list(asr_result[agent].values())
        average[agent] = sum(average[agent])/len(average[agent])
    
    if not latex_output:
        print(f"{'':7s}\t"+"\t".join([f"{agent:7s}" for agent in players.keys()]))
        for computer in opponents:
            print(f"{computer:7s}",end="\t")
            print("\t".join([f"{asr_result[agent][computer]*10:<7.2f}" if asr_result[agent][computer]>=0 else f"{'':7s}"  for agent in asr_result]))

        print(f"{'Average':7s}",end="\t")
        print("\t".join([f"{average[agent]*10:<7.2f}" if average[agent]>=0 else f"{'':7s}"  for agent in average]))
   
    else:
        print(f"{'':7s}\t"+"\t &".join([f"{agent:7s}" for agent in players.keys()]))
        wrc = lambda x : ",".join([f"{x:.2f}" for x in  interpolate_color([126/255,171/255,85/255],[1,1,1],[235/255,94/255,87/255], x, beta=0.64)])
        for computer in opponents:
            print(f"{computer:12s}",end="\t& ")
            print("\t&".join([f"\cellcolor[rgb]{{{wrc(asr_result[agent][computer])}}} {asr_result[agent][computer]*10:<.2f}" if asr_result[agent][computer]>=0 else f"{'':.2s}"  for agent in asr_result]), "\\\\")

        print(f"{'Average':7s}",end="\t")
        for i, agent in enumerate(players):
            print("\t&", end=" ")
            rate = average[agent]
            print(f"\cellcolor[rgb]{{{wrc(rate)}}} {rate*10:<.2f}" if rate>=0 else f"{'':.2s}", end = " ")
    
    print()

def AdaptionIndex(players, opponents, result_dir="result", latex_output=False):
    adaption_result = {}

    def mean(a):
        if not a:
            return -1
        return sum(a)/len(a)

    for oppo in opponents:
        exp_result = {}
        for agent in players:
            exps = glob(f"{result_dir}/{players[agent]}_VS_{opponents[oppo]}*.json")
            for exp in exps:
                with open(exp) as fin:
                    logs = json.load(fin)
                    exp_ground = logs["biddings"]
                target_div = {"first":[],"second":[]}
                for r in range(0, 10):
                    if r>=len(exp_ground["Alex"]): 
                        break
                    second_bid=0
                    player_bid=exp_ground["Alex"][r]
                    for p in exp_ground:
                        if r>=len(exp_ground[p]): continue
                        if p!="Alex" and exp_ground[p][r]>second_bid:
                            second_bid=exp_ground[p][r]
                    if r>=5:
                        target_div["second"].append(abs(player_bid-second_bid))
                    else:
                        target_div["first"].append(abs(player_bid-second_bid))
                exp_result.setdefault(agent, [])
                if not target_div["second"] or not target_div["first"]:
                    continue
                exp_result[agent].append(mean(target_div["second"])/mean(target_div["first"]))
        adaption_result[oppo]=exp_result
    

    agent_sum = {}
    for agent in players:
        agent_sum[agent]=[]
        for oppo in opponents:
            agent_oppo_learning = adaption_result[oppo].get(agent,[])
            if agent_oppo_learning:
                agent_sum[agent].append(sum(agent_oppo_learning)/len(agent_oppo_learning))

    def bold(x):
        # return f"{x:<.2f}"
        if x==maxrate[0]:
            return f"\\textbf{{{x:<.2f}}}"
        elif x==maxrate[1]:
            return f"\\underline{{{x:<.2f}}}"
        else:
            return f"{x:<.2f}"

    if latex_output:
        print(f"{'':2s}\t"+"\t& ".join([f"{agent:2s}" for agent in players.keys()]), "\\\\")
        print("\midrule")
    else:
        print(f"{'':8s}\t"+"\t".join([f"{agent:8s}" for agent in players.keys()]))

    for oppo in opponents:
        exp_result = adaption_result[oppo]
        

        maxrate = list(set([sum(exp_result[agent])/len(exp_result[agent]) if exp_result.get(agent) else 10 for agent in players]))
        maxrate.sort()
        if latex_output:
            print(f"{oppo:8s}", end='\t& ')
            print('\t& '.join([bold(sum(exp_result[agent])/len(exp_result[agent])) if exp_result.get(agent) else f"{'-':2s}" for agent in players]),"\\\\")
        else:
            print(f"{oppo:8s}", end='\t')
            print('\t'.join([f"{sum(exp_result[agent])/len(exp_result[agent]):<8.2f}" if exp_result.get(agent) else f"{'':8s}" for agent in players]))
    
    if latex_output:
        print("\midrule")
        print(f"{'Average':8s}", end='\t& ')
        print('\t& '.join([f"{sum(agent_sum[agent])/len(agent_sum[agent]):<.2f}" if len(agent_sum.get(agent, []))==len(opponents) else f"{'':2s}" for agent in players]),"\\\\")
    else:
        print(f"{'Average':8s}", end='\t')
        print('\t'.join([f"{sum(agent_sum[agent])/len(agent_sum[agent]):<8.2f}" if len(agent_sum.get(agent, []))==len(opponents) else f"{'':8s}" for agent in players]))

def PredictionAccuracy(opponents, result_dir, output_dir, print_value=False):
    import re
    import json
    from glob import glob
    if print_value:
        print(f"{'':7s}\t"+"\t".join([f"{r:<4}" for r in range(10)]))

    kr_max_div_dict={}

    for oppoName in opponents:
        oppo = opponents[oppoName]
        kr_avg_div = {}
        kr_exps = glob(f"{result_dir}/kr_VS_*.json")
        for exp in kr_exps:
            m = re.match(f"{result_dir}/kr_VS_{oppo}_(\d).json", exp)
            if not m: continue
            exp_num = m.groups()[0]
            with open(exp) as fin:
                logs = json.load(fin)
                exp_ground = logs["biddings"]
                result = logs["logs"]["Alex"]
            # print(exp_ground)
            for r in range(0, len(exp_ground["Alex"])):
                try:
                    prediction = result[f'round{r+1}']["prediction"]
                except:
                    continue
                if not prediction: continue
                round_ground = {p: exp_ground[p][r] for p in exp_ground if p!="Alex" and len(exp_ground[p])>r}
                # print(r, prediction, round_ground)
                predict_avg = max(prediction.values())
                ground_avg = max(round_ground.values())
                kr_avg_div.setdefault(r, [])
                kr_avg_div[r].append(abs(predict_avg-ground_avg))

        if print_value:
            print(f"{oppo:7s}",end="\t")
            print("\t".join([f"{sum(kr_avg_div.get(r, [0]))/len(kr_avg_div.get(r, [0])):<7.2f}"  if kr_avg_div.get(r) else f"{'-':7s}"  for r in range(10)]))
        kr_max_div_dict[oppo] = kr_avg_div
    
    if print_value:
        print(f"{'':7s}\t"+"\t".join([f"{r:<4}" for r in range(10)]))
    pcot_max_div_dict = {}
    for oppoName in opponents:
        oppo = opponents[oppoName]
        kr_avg_div = {}
        kr_exps = glob(f"{result_dir}/pcot_VS_*.json")
        for exp in kr_exps:
            m = re.match(f"{result_dir}/pcot_VS_{oppo}_(\d).json", exp)
            if not m: continue
            exp_num = m.groups()[0]
            with open(exp) as fin:
                logs = json.load(fin)
                exp_ground = logs["biddings"]
                result = logs["message"]["Alex"]
            # print(exp_ground)
            for i in range(len(result)):
                content = result[i]["content"]
                if not content.startswith("Hello, Alex! Today is the Day"): continue
                # print(result[i]["content"])
                # print("======")
                r = int(content[:content.index("of")].strip().split()[-1])
                output = result[i+1]["content"]
                if r>1:
                    oppo_nums = len(logs["status"][str(r-1)])
                    for p in logs["status"][str(r-1)]:
                        status = logs["status"][str(r-1)][p]
                        if p=="Alex": 
                            oppo_nums-=1
                        else:
                            if "POINT:-" in status or "POINT:0" in status:
                                oppo_nums-=1
                    if oppo_nums==0:
                        continue

                if output.startswith("Predict:"):
                    prediction = output.split("\n\n")[0]
                    prediction = prediction.split("\n")[1:]
                    ops = {}
                    try:
                        for p in prediction:
                            split="$" if "$" in p else ": " 
                            if "Bob" in p:
                                ops["Bob"]=int(p.split(split)[-1])
                            elif "Cindy" in p:
                                ops["Cindy"]=int(p.split(split)[-1])
                            elif "David" in p:
                                ops["David"]=int(p.split(split)[-1])
                            elif "Eric" in p:
                                ops["Eric"]=int(p.split(split)[-1])
                        for p in prediction:
                            split="$" if "$" in p else ": " 
                            if "Player 1" in p or "Player1" in p:
                                ops["Bob"]=int(p.split(split)[-1])
                            elif "Player 2" in p or "Player2" in p:
                                ops["Cindy"]=int(p.split(split)[-1])
                            elif "Player 3" in p or "Player3" in p:
                                ops["David"]=int(p.split(split)[-1])
                            elif "Player 4" in p or "Player4" in p:
                                ops["Eric"]=int(p.split(split)[-1])
                    except BaseException as e:
                        # print("!!!!!!!!!")
                        continue
                else:
                    # print(output)
                    pass
                prediction = ops
                # except BaseException as e:
                #     print(e)
                #     continue
                round_ground = {p: exp_ground[p][r-1] for p in exp_ground if p!="Alex" and len(exp_ground[p])>=r}
                # print(round_ground)
                # print(r, prediction, round_ground)
                predict_avg = max(prediction.values())
                ground_avg = max(round_ground.values())
                kr_avg_div.setdefault(r-1, [])
                kr_avg_div[r-1].append(abs(predict_avg-ground_avg))

        # print(json.dumps(kr_avg_div, indent=4))

        # print(kr_avg_div)
        if print_value:
            print(f"{oppo:7s}",end="\t")
            print("\t".join([f"{sum(kr_avg_div.get(r, [0]))/len(kr_avg_div.get(r, [0])):<7.2f}" if kr_avg_div.get(r) else f"{'-':7s}"  for r in range(10)]))
        pcot_max_div_dict[oppo] = kr_avg_div
    

    import matplotlib.pyplot as plt

    for oppoName in opponents:
        oppo = opponents[oppoName]
        pcot_avg_div = pcot_max_div_dict[oppo]
        kr_avg_div = kr_max_div_dict[oppo]
        # Sample data
        x1 = [f"R{i+1}" for i in sorted(pcot_avg_div.keys())]
        y1 = [sum(pcot_avg_div[r])/len(pcot_avg_div[r]) for r in sorted(pcot_avg_div.keys())]

        x2 = [f"R{i+1}" for i in sorted(kr_avg_div.keys())]
        y2 = [sum(kr_avg_div[r])/len(kr_avg_div[r]) for r in sorted(kr_avg_div.keys())]

        # Create the plot
        plt.figure(figsize=(4, 3))

        # Plot the first line
        plt.plot(x1, y1, label=f'PCoT vs {oppoName}', linewidth=2, color='#1f77b4')
        for i in range(len(x1)):
            plt.plot(x1[i], y1[i], marker='s', color='#1f77b4')

                # Plot the second line
        plt.plot(x2, y2, label=f'K-R vs {oppoName}', color='#ff7f0e')
        for i in range(len(x2)):
            plt.plot(x2[i], y2[i], marker='s', color='#ff7f0e')

        plt.xticks(fontsize=12)
        plt.yticks(fontsize=14)

        # Show the legend
        plt.legend(fontsize=12)
        plt.ylim(top=150)

        # Show the plot

        plt.savefig(f'{output_dir}/PA_{oppo}.pdf', format='pdf', bbox_inches='tight')


def main(args):
    players = {
        "Direct": "agent",
        "CoT": "cot",
        "Persona": "persona",
        "Reflect": "reflect",
        "Refine": "refine",
        "PCoT": "pcot",
        "K-R": "kr",
    }
    opponents = {
        "Direct": "agent",
        "CoT": "cot",
        "Persona": "persona",
        "Reflect": "reflect",
        "Refine": "refine",
        "PCoT": "pcot",
        "K-R": "kr"
    }

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir, exist_ok=True)

    print("="*40+" Average Survival Round "+"="*40)
    AverageSurvivalRound(players, opponents,  result_dir=args.result_dir, latex_output=args.latex_output)
    print()

    print("="*40+" Adaption Index "+"="*40)
    AdaptionIndex(players, opponents, result_dir=args.result_dir, latex_output=args.latex_output)
    print()

    PredictionAccuracy(opponents, result_dir=args.result_dir, output_dir=args.output_dir)
    print("="*20+f" Prediction Accuracy Metric has been exported to \"{args.output_dir}\" "+"="*20)
    

if __name__=="__main__":
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("--result_dir", type=str, default="result")
    parser.add_argument("--output_dir", type=str, default="output")
    parser.add_argument("--latex_output", action='store_true')
    parser.add_argument('--exp_rnd', type=int, default=10)
    parser.add_argument('--exp_num', type=int, default=10)

    args = parser.parse_args()
    main(args)