# Environment setup libraries
import gymnasium as gym
from gym import spaces
import numpy as np

# DQN libraries 
import tensorflow as tf 
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten
from tensorflow.keras.optimizers import Adam

# Training model libarires
from stable_baselines3 import DQN
from stable_baselines3.common.env_check import check_env

start_price = 5

# Creating the environment for the model
class TradingEnv(gym.Env):
    def __init__ (self, intial_wealth=6000, inital_asset=600):
        super(TradingEnv, self).__init__()

        # Define actions and observation space 
        self.action_space = spaces.Discrete(3) #0: hold, 1: buy, 2:sell
        self.observation_space = spaces.Box(low=0, high=np.inf, shape=(5,), dtype=np.float32)
        
        self.initial_wealth = intial_wealth
        self.initial_asset = inital_asset
        self.reset()
    
    def reset(self):
        self.balance = self.initial_wealth
        self.capital = self.initial_asset
        self.net_worth = self.initial_wealth + (start_price * self.initial_asset)
        self.prev_net_worth = self.initial_wealth + (start_price * self.initial_asset)
        self.trade_count = 0

        self.curren_step = 0
        return self._next_observation()
    
    def _next_observation(self):
        #Returns a dummy observation for now
        return np.random.random(5)
    
    def step(self, action):
        self.curren_step += 1

        if action == 1: # Buy
            pass        # Place Buy logic here
        elif action == 2: # Sell
            pass        # Place Sell logic here
    
        self.net_worth = self.balance # Update with new balance after action 
        self.trade_count += 1

        reward = self.net_worth - self.prev_net_worth
        self.prev_net_worth = self.net_worth

        done = self.curren_step >= 1000 # needs to also have a step to end the environment if the agent makes too much of a profit or a loss, aim for percentage? 
        obs = self._next_observation()

        return obs, reward, done, {}

# Creating the model
def build_dqn_model(state_shape, action_shape):
    model = Sequential()
    model.add(Flatten(input_shape=(1, state_shape)))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(action_shape, activation='linear'))
    return model

state_shape = 5 # Shape of observation spaces
action_shape = 3 # NUmber of possible actions 
model = build_dqn_model(state_shape, action_shape)

# Training the model
env = TradingEnv()
check_env(env)

model = DQN('Trading', env, verbose=1)
model.learn(total_timesteps=10000)

# Code for the simulator
obs = env.reset()
for _ in range(1000):
    action, _states = model.predict(obs)
    obs, rewards, done, info = env.step(action)
    if done:
        pbs = env.reset()
    
env.close()