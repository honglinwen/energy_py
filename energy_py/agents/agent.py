import logging

import tensorflow as tf

from energy_py.common.memories import memory_register

logger = logging.getLogger(__name__)


class BaseAgent(object):
    """ The energy_py base agent class """

    def __init__(
            self,
            env,
            total_steps=0,
            sess=None,
            memory_type='deque',
            memory_length=10000,
            min_reward=-10,
            max_reward=10,
            act_path='./act_path',
            learn_path='./learn_path'
    ):

        self.sess = sess
        self.env = env

        self.observation_space = env.observation_space
        self.action_space = env.action_space

        self.memory_type = memory_type
        self.memory = memory_register[memory_type](
            memory_length,
            self.observation_space.shape,
            self.action_space.shape
        )

        #  reward clipping
        self.min_reward = min_reward
        self.max_reward = max_reward

        self.act_step = 0
        self.learn_step = 0

        #  TODO replace the lists with defaultdict(list)
        self.act_summaries = []
        self.act_writer = tf.summary.FileWriter(act_path)

        self.learn_summaries = []
        self.learn_writer = tf.summary.FileWriter(learn_path)

    def reset(self):
        """
        Resets the agent internals
        """
        logger.debug('Resetting the agent internals')
        self.memory.reset()
        self.act_step = 0
        self.learn_step = 0

        return self._reset()

    def act(self, observation, explore=1.0):
        """
        Action selection by agent

        args
            observation (np array) shape=(1, observation_dim)
            explore (float) 0.0 = 100% greedy, 1.0 = 100% explore

        return
            action (np array) shape=(1, num_actions)
        """
        logger.debug('Agent is acting')
        self.act_step += 1

        return self._act(
            observation.reshape(1, *self.observation_space.shape),
            explore=explore
        )

    def learn(self, **kwargs):
        """
        Agent learns from experience

        args
            batch (dict) batch of experience
            sess (tf.Session)

        return
            training_history (object) info about learning (i.e. loss)
        """
        logger.debug('Agent is learning')
        self.learn_step += 1

        return self._learn(**kwargs)

    def remember(self, observation, action, reward, next_observation, done):
        """
        Store experience in the agent's memory

        args
            observation (np.array)
            action (np.array)
            reward (np.array)
            next_observation (np.array)
            done (np.array)
        """
        logger.debug('Agent is remembering')

        if self.min_reward and self.max_reward:
            reward = max(self.min_reward, min(reward, self.max_reward))

        return self.memory.remember(
            observation, action, reward, next_observation, done
        )
