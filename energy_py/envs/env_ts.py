import logging
import os

import numpy as np
import pandas as pd

from energy_py.envs import BaseEnv
from energy_py.scripts.spaces import ContinuousSpace, DiscreteSpace, GlobalSpace

logger = logging.getLogger(__name__)

def make_observation(path, horizion=5):
    """
    Creates the state.csv and observation.csv.

    Currently only supports giving the agent a forecast.

    args
        horizion (int)
    """
    print('creating new state.csv and observation.csv')
    raw_state_path = os.path.join(path, 'raw_state.csv')
    print(raw_state_path)
    raw_state = pd.read_csv(raw_state_path, index_col=0, parse_dates=True)

    observations = [raw_state.shift(-i) for i in range(horizion)]
    observation = pd.concat(observations, axis=1).dropna()

    #  we dropped na's we now need to realign
    state, observation = raw_state.align(observation, axis=0, join='inner')

    #  add a counter for agent to learn from
    observation['D_counter'] = np.arange(observation.shape[0]) 

    #  add some datetime features
    observation.index = state.index
    observation['D_hour'] = observation.index.hour

    state_path = os.path.join(path, 'state.csv')
    obs_path = os.path.join(path, 'observation.csv')
    state.to_csv(state_path)
    observation.to_csv(obs_path)
    return state, observation

class TimeSeriesEnv(BaseEnv):
    """
    The base environment class for time series environments

    Most energy problems are time series problems - hence the need for a
    class to give functionality
    """

    def __init__(self, 
                 episode_length,
                 episode_start,
                 episode_random,
                 data_path):

        self.episode_start = episode_start
        self.episode_length = episode_length
        self.episode_random = episode_random

        #  load up the infomation from the csvs once
        #  we do this before we init the BaseEnv so we can reset in
        #  the BaseEnv class
        self.raw_state_ts, self.raw_observation_ts = self.load_ts(data_path)

        super().__init__()

    def load_ts(self, path):
        """
        args
            state_path (str)
            observation_path (str)

        returns
            state (pd.DataFrame)
            observation (pd.DataFrame)
        """
        state_path = os.path.join(path, 'state.csv')
        obs_path = os.path.join(path, 'observation.csv')

        try:
            state = pd.read_csv(state_path, index_col=0)
            observation = pd.read_csv(obs_path, index_col=0)

        except:
            state, observation = make_observation(path)
            
        #  grab the column name so we can index state & obs arrays
        self.state_info = state.columns
        self.observation_info = observation.columns.tolist()

        assert state.shape[0] == observation.shape[0]
        return state, observation 

    def get_state_obs(self):
        """
        The master function for the Time_Series_Env class

        Envisioned that this will be run during the _reset of the child class

        This is to allow different time periods to be sampled
        """
        start, end = self.get_ts_row_idx(self.episode_length,
                                         self.episode_start)

        state_ts = self.raw_state_ts.iloc[start:end, :]
        observation_ts = self.raw_observation_ts.iloc[start:end, :]

        #  creating the observation space list
        observation_space = self.make_env_obs_space(observation_ts)

        assert observation_ts.shape[0] == state_ts.shape[0]
        logger.info('Ep {} starting at {}'.format(self.episode,
                                                        state_ts.index[0]))

        return observation_space, observation_ts, state_ts

    def get_ts_row_idx(self, episode_length, episode_start):
        """
        Gets the integer indicies for selecting the episode
        time period
        """
        ts_length = self.raw_observation_ts.shape[0]

        if self.episode_random:
            end_int_idx = ts_length - episode_length
            episode_start = np.random.randint(0, end_int_idx)

        #  now we can set the end of the episode
        end = episode_start + episode_length
        return episode_start, end

    def make_env_obs_space(self, ts):
        """
        Creates the observation space list
        """
        observation_space = []

        for name, col in ts.iteritems():
            #  pull the label from the column name
            label = str(name[:2])

            if label == 'D_':
                obs_space = DiscreteSpace(col.max())

            elif label == 'C_':
                obs_space = ContinuousSpace(col.min(), col.max())

            else:
                print('time series not labelled correctly')
                assert 1 == 0

            observation_space.append(obs_space)
        assert len(observation_space) == ts.shape[1]

        return observation_space

    def get_state(self, steps, append=[]):
        """
        Helper function to get a state.

        Also takes an optional argument to append onto the end of the array.
        This is so that environment specific info can be added onto the
        state or observation array.

        Repeated code with get_observation but I think having two functions
        is cleaner when using in the child class.
        """
        ts_info = np.array(self.state_ts.iloc[steps, :])
        ts_info = np.append(ts_info, append)
        return ts_info.reshape(1, -1)

    def get_observation(self, steps, append=[]):
        """
        Helper function to get a observation.

        Also takes an optional argument to append onto the end of the array.
        This is so that environment specific info can be added onto the
        state or observation array.
        """
        ts_info = np.array(self.observation_ts.iloc[steps, :])

        ts_info = np.append(ts_info, np.array(append))

        return ts_info.reshape(1, -1)
