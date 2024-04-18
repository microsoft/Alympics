import re
import json
import os
from glob import glob

import matplotlib.pyplot as plt

class G08AEvaluator():

    def __init__(self, players, opponents, exp_rnd, exp_num, result_dir, output_dir) -> None:
        self.players = players.split(",")
        self.opponents = opponents.split(",")

        self.exp_rnd = exp_rnd
        self.exp_num = exp_num

        self.result_dir = result_dir
        self.output_dir = output_dir

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)

    def win_rate(self):
        print("="*40+" Win Rate "+"="*40)

        players, opponents = self.players, self.opponents
        win_result = {}

        for agent in players:
            win_result.setdefault(agent, {})
            for computer in opponents:
                exp = f"{self.result_dir}/{agent}_VS_{computer}*.json"
                cots = glob(exp)

                wins = {}
                total_round = 0
                for result in cots:
                    with open(result) as fin:
                        result = json.load(fin)["winners"]
                        total_round = len(cots)*len(result)
                        for rnd in result:
                            if int(rnd)>self.exp_rnd: continue
                            for player in result[rnd]:
                                wins.setdefault(player, [0]*(len(result)))
                                wins[player][int(rnd)-1]+=1

                win_rate = sum(wins.get("Alex", [0]))/(total_round)
                win_result[agent][computer] = win_rate

        average = {}
        for i, agent in enumerate(win_result):
            average[agent] = list(win_result[agent].values())
            average[agent] = sum(average[agent])/len(average[agent])

        print(f"{'':12s}\t"+"\t".join([f"{agent:7s}" for agent in players]))
        for computer in opponents:
            print(f"{computer:12s}",end="\t")
            print("\t".join([f"{win_result[agent][computer]:<7.2f}" if win_result[agent][computer]>=0 else f"{'':7s}"  for agent in win_result]))

        print(f"{'Average':12s}",end="\t")
        print("\t".join([f"{average[agent]:<7.2f}" if average[agent]>=0 else f"{'':7s}"  for agent in win_result]))

        print()

    def adaption_index(self):
        print("="*40+" Adaption Index "+"="*40)

        players, opponents = self.players, self.opponents
        learning_result = {}

        for oppo in opponents:
            exp_result = {}
            for agent in players:
                exps = glob(f"{self.result_dir}/{agent}_VS_{oppo}*.json")
                for exp in exps:
                    with open(exp) as fin:
                        logs = json.load(fin)
                        exp_ground = logs["biddings"]
                    target_div = []
                    for r in range(0, self.exp_rnd):
                        bids = [exp_ground[p][r] for p in exp_ground]
                        target = sum(bids)/len(bids)*0.8
                        player_bid = exp_ground["Alex"][r]
                        target_div.append(abs(player_bid-target))
                    exp_result.setdefault(agent, [])
                    exp_result[agent].append(sum(target_div[5:])/sum(target_div[:5])) # [Target Deviation @ (second half)] / [Target Deviation @ (first half)]
            learning_result[oppo]=exp_result

        print(f"{'':8s}\t"+"\t".join([f"{agent:2s}" for agent in players]))
        
        for oppo in opponents:
            exp_result = learning_result[oppo]
            
            maxrate = list(set([sum(exp_result[agent])/len(exp_result[agent]) if exp_result.get(agent) else 10 for agent in players]))
            maxrate.sort()

            print(f"{oppo:8s}", end='\t')
            print('\t'.join([f"{sum(exp_result[agent])/len(exp_result[agent]):<.2f}" if exp_result.get(agent) else f"{'':2s}" for agent in players]))

        agent_sum = {}
        for agent in players:
            agent_sum[agent]=[]
            for oppo in opponents:
                agent_oppo_learning = learning_result[oppo].get(agent,[])
                if agent_oppo_learning:
                    agent_sum[agent].append(sum(agent_oppo_learning)/len(agent_oppo_learning))

        print(f"{'Average':8s}", end='\t')
        print('\t'.join([f"{sum(agent_sum[agent])/len(agent_sum[agent]):<.2f}" if len(agent_sum.get(agent,[]))==len(opponents) else f"{'':2s}" for agent in players]))
        
        print()

    def extract_PCoT_prediction(self):
        """
        Parse the prediction result of PCoT from the response.
        """

        import openai
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
                        engine=ENGINE,
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

        pcot_exps = glob(f"{self.result_dir}/pcot_VS_*.json")
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

        with open(f"{self.output_dir}/pcot_prediction.json","w") as fout:
            new_result = {}
            for exp in exps_result:
                new_result[os.path.basename(exp)[:-5]] = exps_result[exp]
            json.dump(new_result, fout, indent=4)

    def prediction_accuracy(self):
        opponents = self.opponents
        for oppo in opponents:
            with open(f"{self.output_dir}/pcot_prediction.json") as fin:
                new_result = json.load(fin)

            pcot_avg_div = {}

            for exp in new_result:
                m = re.match(f"pcot_VS_{oppo}_(\d)", exp)
                if not m: continue
                exp_num = m.groups()[0]
                with open(f"{self.result_dir}/{exp}.json") as fin:
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
            kr_exps = glob(f"{self.result_dir}/kr_VS_*.json")
            for exp in kr_exps:
                m = re.match(f"{self.result_dir}/kr_VS_{oppo}_(\d).json", exp)
                if not m: continue
                exp_num = m.groups()[0]
                with open(exp) as fin:
                    logs = json.load(fin)
                    exp_ground = logs["biddings"]
                    result = logs["logs"]["Alex"]
                for r in range(0, self.exp_rnd):
                    try:
                        prediction = result[f'round{r+1}']["prediction"]
                    except:
                        continue
                    round_ground = {p: exp_ground[p][r] for p in exp_ground if p!="Alex"}
                    predict_avg = sum(prediction.values())/len(prediction)
                    ground_avg = sum(round_ground.values())/len(round_ground)
                    kr_avg_div.setdefault(r, [])
                    kr_avg_div[r].append(abs(predict_avg-ground_avg))


            #Export the prediction accuracy chart.

            x = [f"R{i+1}" for i in range(self.exp_rnd)]
            y1 = [sum(pcot_avg_div[r])/len(pcot_avg_div[r]) for r in range(self.exp_rnd)]
            y2 = [sum(kr_avg_div[r])/len(kr_avg_div[r])  for r in range(self.exp_rnd)]

            # Create the plot
            plt.figure(figsize=(4, 3))

            # Plot the first line
            plt.plot(x, y1, label=f'PCoT vs {oppo}', linewidth=2)
            for i in range(len(x)):
                plt.plot(x[i], y1[i], marker='s', color='#1f77b4')

            # Plot the second line
            plt.plot(x, y2, label=f'K-R vs {oppo}')
            for i in range(len(x)):
                plt.plot(x[i], y2[i], marker='s', color='#ff7f0e')

            plt.xticks(fontsize=12)
            plt.yticks(fontsize=14)
            plt.ylim(top=20)

            # Show the legend
            plt.legend(fontsize=12)

            # Show the plot
            plt.savefig(f'{self.output_dir}/PA_{oppo}.pdf', format='pdf', bbox_inches='tight')

        print("="*20+f" Prediction Accuracy Metric has been exported to \"{self.output_dir}\" "+"="*20)


def main(args):

    evaluator = G08AEvaluator(args.players, args.opponents, args.exp_rnd, args.exp_num, args.result_dir, args.output_dir)

    evaluator.win_rate()
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