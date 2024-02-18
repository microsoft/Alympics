import json
import re
import os
from glob import glob

import matplotlib.pyplot as plt

import numpy as np

class SAGEvaluator(object):
    def __init__(self, players, opponents, result_dir, output_dir) -> None:
        self.players = players.split(",")
        self.opponents = opponents.split(",")
        self.result_dir = result_dir
        self.output_dir = output_dir

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)

    def survival_rate(self, status, soft=True):
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

    def average_survival_round(self, ):
        print("="*40+" Average Survival Round "+"="*40)

        players, opponents = self.players, self.opponents
        def interpolate_color(colorA, colorB, colorC, alpha, beta=0.5):
            if alpha>beta:
                alpha = (alpha-beta)/(1-beta)
                return tuple(np.array(colorB)*(1-alpha) + np.array(colorA)*(alpha))
            else:
                low = 0.4
                alpha = (alpha-low)/(beta-low)
                return tuple(np.array(colorC)*(1-alpha) + np.array(colorB)*(alpha))

        asr_result = {}

        for agent in players:
            asr_result.setdefault(agent, {})
            for computer in opponents:
                exp = f"{self.result_dir}/{agent}_VS_{computer}*.json"
                cots = glob(exp)

                wins = {}
                for result in cots:
                    with open(result) as fin:
                        result = json.load(fin)["status"]
                        sr = self.survival_rate(result, soft=True)
                        for player in sr:
                            wins.setdefault(player, [])
                            wins[player].append(sr[player])

                win_rate = sum(wins["Alex"])/len(wins["Alex"])
                asr_result[agent][computer] = win_rate
        
        average = {}
        for i, agent in enumerate(asr_result):
            average[agent] = list(asr_result[agent].values())
            average[agent] = sum(average[agent])/len(average[agent])
        
        print(f"{'':7s}\t"+"\t".join([f"{agent:7s}" for agent in players]))
        for computer in opponents:
            print(f"{computer:7s}",end="\t")
            print("\t".join([f"{asr_result[agent][computer]*10:<7.2f}" if asr_result[agent][computer]>=0 else f"{'':7s}"  for agent in asr_result]))

        print(f"{'Average':7s}",end="\t")
        print("\t".join([f"{average[agent]*10:<7.2f}" if average[agent]>=0 else f"{'':7s}"  for agent in average]))
        
        print()

    def adaption_index(self):
        print("="*40+" Adaption Index "+"="*40)

        players, opponents = self.players, self.opponents
        adaption_result = {}

        def mean(a):
            if not a:
                return -1
            return sum(a)/len(a)

        for oppo in opponents:
            exp_result = {}
            for agent in players:
                exps = glob(f"{self.result_dir}/{agent}_VS_{oppo}*.json")
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

        print(f"{'':8s}\t"+"\t".join([f"{agent:8s}" for agent in players]))

        for oppo in opponents:
            exp_result = adaption_result[oppo]
            

            maxrate = list(set([sum(exp_result[agent])/len(exp_result[agent]) if exp_result.get(agent) else 10 for agent in players]))
            maxrate.sort()
            print(f"{oppo:8s}", end='\t')
            print('\t'.join([f"{sum(exp_result[agent])/len(exp_result[agent]):<8.2f}" if exp_result.get(agent) else f"{'':8s}" for agent in players]))
        
        print(f"{'Average':8s}", end='\t')
        print('\t'.join([f"{sum(agent_sum[agent])/len(agent_sum[agent]):<8.2f}" if len(agent_sum.get(agent, []))==len(opponents) else f"{'':8s}" for agent in players]))

        print()

    def prediction_accuracy(self, print_value=False):
        opponents = self.opponents
        if print_value:
            print(f"{'':7s}\t"+"\t".join([f"{r:<4}" for r in range(10)]))

        kr_max_div_dict={}

        for oppo in opponents:
            kr_avg_div = {}
            kr_exps = glob(f"{self.result_dir}/kr_VS_*.json")
            for exp in kr_exps:
                m = re.match(f"{self.result_dir}/kr_VS_{oppo}_(\d).json", exp)
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



        """
        Parse the prediction result of PCoT from the response.
        """
        for oppo in opponents:
            kr_avg_div = {}
            kr_exps = glob(f"{self.result_dir}/pcot_VS_*.json")
            for exp in kr_exps:
                m = re.match(f"{self.result_dir}/pcot_VS_{oppo}_(\d).json", exp)
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
                    round_ground = {p: exp_ground[p][r-1] for p in exp_ground if p!="Alex" and len(exp_ground[p])>=r}
                    # print(round_ground)
                    # print(r, prediction, round_ground)
                    predict_avg = max(prediction.values())
                    ground_avg = max(round_ground.values())
                    kr_avg_div.setdefault(r-1, [])
                    kr_avg_div[r-1].append(abs(predict_avg-ground_avg))


            if print_value:
                print(f"{oppo:7s}",end="\t")
                print("\t".join([f"{sum(kr_avg_div.get(r, [0]))/len(kr_avg_div.get(r, [0])):<7.2f}" if kr_avg_div.get(r) else f"{'-':7s}"  for r in range(10)]))
            pcot_max_div_dict[oppo] = kr_avg_div
        

        #Export the prediction accuracy chart.

        for oppo in opponents:
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
            plt.plot(x1, y1, label=f'PCoT vs {oppo}', linewidth=2, color='#1f77b4')
            for i in range(len(x1)):
                plt.plot(x1[i], y1[i], marker='s', color='#1f77b4')

                    # Plot the second line
            plt.plot(x2, y2, label=f'K-R vs {oppo}', color='#ff7f0e')
            for i in range(len(x2)):
                plt.plot(x2[i], y2[i], marker='s', color='#ff7f0e')

            plt.xticks(fontsize=12)
            plt.yticks(fontsize=14)

            # Show the legend
            plt.legend(fontsize=12)
            plt.ylim(top=150)

            # Show the plot

            plt.savefig(f'{self.output_dir}/PA_{oppo}.pdf', format='pdf', bbox_inches='tight')

        print("="*20+f" Prediction Accuracy Metric has been exported to \"{self.output_dir}\" "+"="*20)


def main(args):
    evaluator = SAGEvaluator(args.players, args.opponents, args.result_dir, args.output_dir)
    evaluator.average_survival_round()
    evaluator.adaption_index()

    # the calculation of Prediction Accuracy is used only for pcot and kr.
    # evaluator.prediction_accuracy()
    

if __name__=="__main__":
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("--players", type=str, default="kr")
    parser.add_argument("--opponents", type=str, default="agent")
    parser.add_argument("--result_dir", type=str, default="result")
    parser.add_argument("--output_dir", type=str, default="output")
    parser.add_argument('--exp_rnd', type=int, default=10)
    parser.add_argument('--exp_num', type=int, default=10)

    args = parser.parse_args()
    main(args)