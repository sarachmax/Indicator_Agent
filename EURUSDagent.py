# -*- coding: utf-8 -*-
"""
Created on Mon May 28 21:00:56 2018

@author: sarac
"""
import random
import numpy as np
from collections import deque
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import Adam
from keras import backend as K
from keras.layers import LSTM


class DQNAgent:
    def __init__(self, state_size):
        self.memory = deque(maxlen=4000)
        self.learning_rate = 0.001
        self.state_size = state_size
        self.epsilon = 1.0  # exploration rate
        self.gamma = 0.95   # discount rate 
        self.action_size = 3 
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.99
        
        self.model = self._build_model()
        self.target_model = self._build_model()
        
    
    
    def _huber_loss(self, target, prediction):
        # sqrt(1+error^2)-1
        error = prediction - target
        return K.mean(K.sqrt(1+K.square(error))-1, axis=-1)

    def _build_model(self):
        # Neural Net for Deep-Q learning Model
        model = Sequential()
        model.add(Dense(128, input_dim = self.state_size , activation='relu'))
        model.add(Dense(64, activation='relu'))
        model.add(Dense(32, activation='relu'))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss=self._huber_loss,
                      optimizer=Adam(lr=self.learning_rate))
        return model
    

    def update_target_model(self):
        # copy weights from model to target_model
        self.target_model.set_weights(self.model.get_weights())
    
    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))
   
    def act(self, state, train = True, random_action = False):
        if train : 
            if np.random.rand() <= self.epsilon or random_action :
                print('random action')
                return random.randrange(self.action_size)
        act_values = self.model.predict(state)
        print('act : ', act_values)
        return np.argmax(act_values[0]) #return action 
        
    def replay(self, batch_size):
        minibatch = random.sample(self.memory, batch_size)
        
        for state, action, reward, next_state, done in minibatch:
            target = self.model.predict(state)
            if done :
                target[0][action] = reward
            else : 
                t = self.target_model.predict(next_state)[0]
                target[0][action] = reward + self.gamma*np.amax(t)
                
            self.model.fit(state, target, epochs=1, verbose=0)
        
        if self.epsilon > self.epsilon_min : 
            self.epsilon *= self.epsilon_decay
        
    def load(self, name):
        self.model.load_weights(name)

    def save(self, name):
        self.model.save_weights(name)
        
    