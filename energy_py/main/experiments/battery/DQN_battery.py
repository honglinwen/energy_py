"""
This experiment script uses the DQN agent
to control the battery environment.
"""

import sys

import argparse

from energy_py.agents import DQN
from energy_py.agents.function_approximators import Keras_ActionValueFunction

from energy_py.envs import Battery_Env
from energy_py.main.scripts.experiment_blocks import run_single_episode
from energy_py.main.scripts.visualizers import Eternity_Visualizer

#  can probably make this into an episode block
parser = argparse.ArgumentParser(description='battery REINFORCE experiment')
parser.add_argument('--ep', type=int, default=10,
                    help='number of episodes to run (default: 10)')
parser.add_argument('--len', type=int, default=48,
                    help='length of a single episode (default: 48)')
parser.add_argument('--bs', type=int, default=64,
                    help='batch size (default: 64)')
parser.add_argument('--gamma', type=float, default=0.999,
                    help='discount rate (default: 0.999)')
parser.add_argument('--out', type=int, default=50,
                    help='output results every n episodes (default: 50')

args = parser.parse_args()

EPISODES = args.ep
EPISODE_LENGTH = args.len
BATCH_SIZE = args.bs
DISCOUNT = args.gamma
OUTPUT_RESULTS = args.out

import csv
def save_args(args, path):
    with open(path, 'w') as outfile:
        writer = csv.writer(outfile)
        for k, v in vars(args).items():
            print('{} : {}'.format(k, v))
            writer.writerow([k] + [v])
    return writer

writer = save_args(args,
                   path='DQN_results/args.txt')

#  first we create our environment
env = Battery_Env(lag            = 0,
                  episode_length = EPISODE_LENGTH,
                  episode_start  = 0,
                  power_rating   = 2,  #  in MW
                  capacity       = 2,  #  in MWh
                  initial_charge = 0,  #  in % of capacity
                  round_trip_eff = 1.0, #  in % - 80-90% in practice
                  verbose        = False)

#  create two action value functions Q(s,a)
Q_actor = Keras_ActionValueFunction
Q_target = Keras_ActionValueFunction

#  set up some hyperparameters using ratios from DeepMind 2015 Atari
total_steps = EPISODES * env.state_ts.shape[0]
epsilon_decay_steps = total_steps / 2
update_target_net = int(total_steps / (env.state_ts.shape[0] * 100))
memory_length = int(total_steps/10)

print('update target net {}'.format(update_target_net))

#  now we create our agent
agent = DQN(env,
            Q_actor,
            Q_target,
            discount=DISCOUNT,
            epsilon_decay_steps=epsilon_decay_steps,
            update_target_net=update_target_net,
            memory_length=memory_length,
            verbose=False)

for episode in range(1, EPISODES):

    #  initialize before starting episode
    done, step = False, 0
    observation = env.reset(episode)

    #  while loop runs through a single episode
    while done is False:
        #  select an action
        action = agent.act(observation=observation)
        #  take one step through the environment
        next_observation, reward, done, info = env.step(action)
        #  store the experience
        agent.memory.add_experience(observation, action, reward, next_observation, step, episode)
        step += 1
        observation = next_observation

        #  get a batch to learn from
        obs, actions, rewards, next_obs = agent.memory.get_random_batch(batch_size=BATCH_SIZE)

    #  train the model
    if episode > 100:
        loss = agent.learn(observations=obs,
                           actions=actions,
                           rewards=rewards,
                           next_observations=next_obs,
                           episode=episode)

        if episode % OUTPUT_RESULTS == 0:
            #  collect data from the agent & environment
            global_history = Eternity_Visualizer(episode, agent, env,
                                                 results_path='DQN_results/')
            outputs = global_history.output_results(save_data=False)