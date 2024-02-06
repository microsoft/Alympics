import re
import json
from glob import glob

import numpy as np


def WinRate(players, opponents, result_dir="result", exp_num=10, exp_rnd=10, latex_output=False):
    win_result = {}

    for agent, agent_alias in players.items():
        win_result.setdefault(agent, {})
        for computer, computer_alias in opponents.items():
            exp = f"{result_dir}/{agent_alias}_VS_{computer_alias}*.json"
            cots = glob(exp)
            if len(cots) < exp_num:
                win_result[agent][computer] = -1
                continue
            else:
                cots=cots[:exp_num]

            wins = {}
            total_round = 0
            for result in cots:
                with open(result) as fin:
                    result = json.load(fin)["winners"]
                    total_round = len(cots)*len(result)
                    for rnd in result:
                        if int(rnd)>exp_rnd: continue
                        for player in result[rnd]:
                            wins.setdefault(player, [0]*(len(result)))
                            wins[player][int(rnd)-1]+=1

            win_rate = sum(wins.get("Alex", [0]))/(total_round)
            win_result[agent][computer] = win_rate

    average = {}
    for i, agent in enumerate(win_result):
        average[agent] = list(win_result[agent].values())
        average[agent] = sum(average[agent])/len(average[agent])

    if not latex_output:
        print(f"{'':12s}\t"+"\t".join([f"{agent:7s}" for agent in players.keys()]))
        for computer in opponents:
            print(f"{computer:12s}",end="\t")
            print("\t".join([f"{win_result[agent][computer]:<7.2f}" if win_result[agent][computer]>=0 else f"{'':7s}"  for agent in win_result]))

        print(f"{'Average':12s}",end="\t")
        print("\t".join([f"{average[agent]:<7.2f}" if average[agent]>=0 else f"{'':7s}"  for agent in win_result]))

    else:
        def interpolate_color(colorA, colorB, colorC, alpha, beta=0.5):
            if alpha>beta:
                alpha = (alpha-beta)/(1-beta)
                return tuple(np.array(colorB)*(1-alpha) + np.array(colorA)*(alpha))
            else:
                alpha = alpha/(beta)
                return tuple(np.array(colorC)*(1-alpha) + np.array(colorB)*(alpha))
        wrc = lambda x : ",".join([f"{x:.2f}" for x in  interpolate_color([126/255,171/255,85/255],[1,1,1],[235/255,94/255,87/255], x, beta=0.4)])

        print(f"{'':7s}\t"+"\t &".join([f"{agent:7s}" for agent in players.keys()]))
        for computer in opponents:
            print(f"{computer:12s}",end="\t& ")
            print("\t&".join([f"\cellcolor[rgb]{{{wrc(win_result[agent][computer])}}} {win_result[agent][computer]:<.2f}" if win_result[agent][computer]>=0 else f"{'':.2s}"  for agent in win_result]), "\\\\")

        print(f"{'Average':12s}",end="\t& ")
        print("\t&".join([f"\cellcolor[rgb]{{{wrc(average[agent])}}} {average[agent]:<.2f}" if average[agent]>=0 else f"{'':.2s}"  for agent in win_result]), "\\\\")


def AdaptionIndex(players, opponents, result_dir="result", latex_output=False):
    learning_result = {}

    for oppo in opponents:
        exp_result = {}
        for agent in players:
            exps = glob(f"{result_dir}/{players[agent]}_VS_{opponents[oppo]}*.json")
            for exp in exps:
                with open(exp) as fin:
                    logs = json.load(fin)
                    exp_ground = logs["biddings"]
                target_div = []
                for r in range(0, 10):
                    bids = [exp_ground[p][r] for p in exp_ground]
                    target = sum(bids)/len(bids)*0.8
                    player_bid = exp_ground["Alex"][r]
                    target_div.append(abs(player_bid-target))
                exp_result.setdefault(agent, [])
                exp_result[agent].append(sum(target_div[5:])/sum(target_div[:5]))
        learning_result[oppo]=exp_result

    if latex_output:
        print(f"{'':8s}\t"+"\t& ".join([f"{agent:8s}" for agent in players.keys()]))
    else:
        print(f"{'':8s}\t"+"\t".join([f"{agent:2s}" for agent in players.keys()]))
    
    def bold(x):
        if x==maxrate[0]:
            return f"\\textbf{{{x:<.2f}}}"
        elif x==maxrate[1]:
            return f"\\underline{{{x:<.2f}}}"
        else:
            return f"{x:<.2f}"

    for oppo in opponents:
        exp_result = learning_result[oppo]
        
        maxrate = list(set([sum(exp_result[agent])/len(exp_result[agent]) if exp_result.get(agent) else 10 for agent in players]))
        maxrate.sort()

        if latex_output:
            print(f"{oppo:8s}", end='\t& ')
            print('\t& '.join([bold(sum(exp_result[agent])/len(exp_result[agent])) if exp_result.get(agent) else f"{'':8s}" for agent in players]),"\\\\")
        else:
            print(f"{oppo:8s}", end='\t')
            print('\t'.join([f"{sum(exp_result[agent])/len(exp_result[agent]):<.2f}" if exp_result.get(agent) else f"{'':2s}" for agent in players]))

    agent_sum = {}
    for agent in players:
        agent_sum[agent]=[]
        for oppo in opponents:
            agent_oppo_learning = learning_result[oppo].get(agent,[])
            if agent_oppo_learning:
                agent_sum[agent].append(sum(agent_oppo_learning)/len(agent_oppo_learning))

    if latex_output:
        print(f"{'Average':8s}", end='\t& ')
        print('\t& '.join([f"{sum(agent_sum[agent])/len(agent_sum[agent]):<.2f}" if len(agent_sum.get(agent,[]))==len(opponents) else f"{'':2s}" for agent in players]),"\\\\")
    else:
        print(f"{'Average':8s}", end='\t')
        print('\t'.join([f"{sum(agent_sum[agent])/len(agent_sum[agent]):<.2f}" if len(agent_sum.get(agent,[]))==len(opponents) else f"{'':2s}" for agent in players]))
    


def extract_PCoT_prediction(result_dir="result", output_dir="output"):
    import os
    import openai
    import re
    import time

    # Fill in your config information to conduct experiments.
    openai.api_type = ""
    openai.api_base = ""
    openai.api_version = ""
    openai.api_key = ""
    ENGINE = "gpt4-32k"

    def re_extract(message):
        matchs = re.finditer("Player (\d)(\s\(\w+\))?:\s*(\d+)", message)
        matchs = list(matchs)
        try:
            assert 5>=len(matchs) >=4, message
        except BaseException:
            return {}
        result = [m.groups()[2] for m in matchs]
        if len(result)==5:
            return {p: n for p, n in zip(['Alex', 'Bob', 'Cindy', 'David', 'Eric'], result)}
        else:
            return {p: n for p, n in zip([ 'Bob', 'Cindy', 'David', 'Eric'], result)}

    def gpt_extract(message):
        status = 0
        times = 0
        while status != 1:
            try:
                response = openai.ChatCompletion.create(
                    engine="devgpt4-32k",
                    messages = [{"role":"system", "content":"""Read the following statement and extract a prediction of the number chosen by each player in json format. Output format:{"Player": Player's number}"}"""}, {"role": "user", "content": message}],
                    temperature=0.7,
                    max_tokens=80,
                    top_p=0.95,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop=None)
                response = response['choices'][0]['message']['content']
                bidding_info = json.loads(response)
                status = 1
                return bidding_info
            except Exception as e:
                print(e)
                times+=1
                if times>=2:
                    return {}
                time.sleep(15)

    pcot_exps = glob(f"{result_dir}/pcot_VS_*.json")
    error_r = []
    flag = False

    exps_result = {}
    for exp in pcot_exps:
        with open(exp) as fin:
            messages=json.load(fin)["message"]["Alex"]
            exps_result[exp]={}
            for i in range(2, min(len(messages), 41), 4):
                message=messages[i]["content"]
                result = re_extract(message)
                if not result:
                    result = gpt_extract(message)
                if not result:
                    print(message)
                    error_r.append(message)
                    flag = True
                    break
                exps_result[exp][(i-2)//4]=result
        if flag:
            break
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    with open(f"{output_dir}/pcot_prediction.json","w") as fout:
        new_result = {}
        for exp in exps_result:
            new_result[os.path.basename(exp)[:-5]] = exps_result[exp]
        json.dump(new_result, fout, indent=4)

def PredictionAccuracy(opponents, result_dir="result", output_dir="output"):
    for OppoName in opponents:
        oppo = opponents[OppoName]

        with open(f"{output_dir}/pcot_prediction.json") as fin:
            new_result = json.load(fin)

        pcot_avg_div = {}

        for exp in new_result:
            m = re.match(f"pcot_VS_{oppo}_(\d)", exp)
            if not m: continue
            exp_num = m.groups()[0]
            with open(f"{result_dir}/{exp}.json") as fin:
                exp_ground = json.load(fin)["biddings"]
            result = new_result[exp]
            for r in result:
                try:
                    prediction = {p:int(result[r][p]) for p in result[r] if p!="Alex"}
                except:
                    continue
                round_ground = {p: exp_ground[p][int(r)] for p in exp_ground if p!="Alex"}
                predict_avg = sum(prediction.values())/len(prediction)
                ground_avg = sum(round_ground.values())/len(round_ground)
                pcot_avg_div.setdefault(int(r), [])
                pcot_avg_div[int(r)].append(abs(predict_avg-ground_avg))

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
            for r in range(0, 10):
                try:
                    prediction = result[f'round{r+1}']["prediction"]
                except:
                    continue
                round_ground = {p: exp_ground[p][r] for p in exp_ground if p!="Alex"}
                predict_avg = sum(prediction.values())/len(prediction)
                ground_avg = sum(round_ground.values())/len(round_ground)
                kr_avg_div.setdefault(r, [])
                kr_avg_div[r].append(abs(predict_avg-ground_avg))


        import matplotlib.pyplot as plt
        # print(kr_avg_div)
        # print(oppo)

        # Sample data
        x = [f"R{i+1}" for i in range(10)]
        y1 = [sum(pcot_avg_div[r])/len(pcot_avg_div[r]) for r in range(10)]
        y2 = [sum(kr_avg_div[r])/len(kr_avg_div[r])  for r in range(10)]

        # Create the plot
        plt.figure(figsize=(4, 3))

        # Plot the first line
        plt.plot(x, y1, label=f'PCoT vs {OppoName}', linewidth=2)
        for i in range(len(x)):
            plt.plot(x[i], y1[i], marker='s', color='#1f77b4')

        # Plot the second line
        plt.plot(x, y2, label=f'K-R vs {OppoName}')
        for i in range(len(x)):
            plt.plot(x[i], y2[i], marker='s', color='#ff7f0e')

        plt.xticks(fontsize=12)
        plt.yticks(fontsize=14)
        plt.ylim(top=20)

        # Show the legend
        plt.legend(fontsize=12)

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
        # computer players
        # "1-Level(Fix)":    "fix-40-0",
        # "1-Level(Var)": "fix-40-5",
        # "MonoTrend(Fix)": "mono_",
        # "MonoTrend(Var)": "monorand",
        # "LastBids(Fix)":   "last-40-0",
        # "LastBids(Var)": "last-40-5",

        "Direct": "agent",
        "CoT": "cot",
        "Persona": "persona",
        "Reflect": "reflect",
        "Refine": "refine",
        "PCoT": "pcot",
        "K-R": "kr"
    }

    print("="*40+" Win Rate "+"="*40)
    WinRate(players, opponents, exp_num=args.exp_num, exp_rnd=args.exp_rnd, result_dir=args.result_dir, latex_output=args.latex_output)
    print()

    print("="*40+" Adaption Index "+"="*40)
    AdaptionIndex(players, opponents, result_dir=args.result_dir, latex_output=args.latex_output)
    print()

    opponents = {
        "CoT": "cot",
        "Persona": "persona",
        "Reflect": "reflect",
        "Refine": "refine",
        "PCoT": "pcot",
        "K-R": "kr"
    }

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