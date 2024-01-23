# ALYMPICS: Language Agents Meet Game Theory

**Alympics** is a platform that leverages Large Language Model (LLM) agents to facilitate investigations in game theory.

See our paper: [<font size=5>ALYMPICS: LLM Agents Meet Game Theory -- Exploring Strategic Decision-Making with AI Agents</font>](https://arxiv.org/pdf/2311.03220)

## Architecture of Alympics

<img src="./assets/playground.png" alt="playground" width="800"/>

The architecture of Alympics comprises the Sandbox Playground and Players. The Sandbox Playground creates an environment where game settings, as specified by researchers, are executed. Agent players, along with the optional human players, actively engage in the game within this environment.

- Sandbox Playground: The Sandbox Playground serves as the environment for conducting games, providing a versatile and controlled space for agent players interactions.
- Agent Players: Agent Players constitute an indispensable component of the Alympics framework, embodying LLM-powered agent entities that participate in strategic interactions within the Sandbox Playground.


## Contributions

- The proposal of an original, LLM agent-based framework to facilitate game theory research.
- The demonstration of Alympics’s application through a comprehensive pilot case study.
- The emphasis on the significance of leveraging LLM agents to scrutinize strategic decision-making within a controlled and reproducible environment. This endeavor not only enriches the field of game theory but also has the potential to inspire research in other domains where decision-making assumes a pivotal role.

## Directory Structure
The code directory structure is
```
$src
 ├─ run.py
 ├─ Utils.py  # The basic Playground class, the Player class and the LLM API
 └─ waterAllocation.py # An example of using playground
```
**Please complete the configuration of LLM in the Utils.py first.**


## Example
Alympics provides a research platform for conducting experiments on complex strategic gaming problems. As a pilot demonstration, we developed a game called the ’Water Allocation Challenge’ to illustrate how it can be leveraged for game theory research.

The details can be found in our paper.

## Citation

```
@misc{mao2023alympics,
      title={ALYMPICS: Language Agents Meet Game Theory}, 
      author={Shaoguang Mao and Yuzhe Cai and Yan Xia and Wenshan Wu and Xun Wang and Fengyi Wang and Tao Ge and Furu Wei},
      year={2023},
      eprint={2311.03220},
      archivePrefix={arXiv},
      primaryClass={cs.CL}
}
```
