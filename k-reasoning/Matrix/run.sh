#!/bin/bash

for player in {1..4}; do
    for computer in {1..4}; do
        if [ $player -gt $computer ]; then
            continue
        fi
        player_strategy=kr
        computer_strategy=kr
        if [ $player -eq 1 ]; then
            player_strategy=agent
        fi

        if [ $computer -eq 1 ]; then
            computer_strategy=agent
        fi
        python main.py  --player_strategy $player_strategy --computer_strategy $computer_strategy --exp_num 5 --player_k $player --computer_k $computer
    done
done
