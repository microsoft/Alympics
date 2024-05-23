import numpy as np
from waterAllocation import waterAllocation
import argparse

game_setting = "\n\nAttention, all W-Town residents, welcome to the Water Allocation Challenge!\nIn this challenge, you are tasked with ensuring your survival over a period of 20 days by acquiring the necessary water resources to maintain your health. You will participate in daily auctions to bid for water resources to meet your individual needs.\nHere are the game rules and settings:\n1. You are one of five residents with different water requirements, budgets, and health points.\n2. Your goal is to survive until the end of the 20 days.\n3. Each resident has a maximum of 10 health points and starts with 8 health points. If your health points drop below or equal to 0, you will be considered dead and eliminated from the game! All your accumulated money will be reset to Zero! \n4. Every day, you will bid on water resources to meet your needs. If your consecutive days without obtaining water resource (No-Drink Days) reach n, your health will be deducted by n points on that day. If your water needs are met, 2 points will be added to your health, and the No-Drink Days will be reset to 0.\n5. The total daily water supply will vary between LOWER and UPPER units. The specific amount will be announced before daily auction.\n6. Each resident has a different daily water requirement and budget for bidding on water resources:\n   -Alex: Water requirement - 8 units/day; Daily Salary- $70/day\n   -Bob: Water requirement - 9 units/day; Daily Salary- $75/day\n   -Cindy: Water requirement - 10 units/day; Daily Salary- $100/day\n   -David: Water requirement - 11 units/day; Daily Salary- $120/day\n   -Eric: Water requirement - 12 units/day; Daily Salary- $120/day\n7. To allocate water resources, a sealed-bid auction will be conducted daily. Each resident submits a single bid for their entire water need. The town government will allocate water resources according to the principle of highest bidder until the remaining water resources are insufficient to meet anyone's requirement. 8.If a tie occurs and the remaining water resources are not sufficient to meet the needs of the residents involved in the tie, priority will be given to residents with lower needs. For example, A and B bid $100 at the same time, B's need will be met first considering B's need 9 units is lower than A's need 10 units. All bidding information will be made public after the allocation of water resources on the same day.\n\nRemember, the key to success is effective bidding and strategizing to ensure your survival. Good luck!!"

def generate_data(lower, upper, round):
    data = []
    for i in range(round):
        data.append(np.random.randint(lower, upper))
    return data

def main():
    parser = argparse.ArgumentParser(description='Water Allocation Challenge')
    parser.add_argument('--round', type=int, default=20, help='Number of rounds')
    parser.add_argument('--lower', type=int, default=10, help='Lower limit of water supply')
    parser.add_argument('--upper', type=int, default=20, help='Upper limit of water supply')
    args = parser.parse_args()

    WA = waterAllocation(game_setting)
    WA.run_multi_round(args.round, generate_data(args.lower, args.upper, args.round))

if __name__ == '__main__':
    main()