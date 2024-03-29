# -*- coding: utf-8 -*-
"""
Created on Mon May 28 22:11:15 2018

@author: sarac
"""

from EURUSDagent import DQNAgent
import datetime
import numpy as np
import pandas as pd 
import matplotlib.pyplot as plt 

# init conts.
############################################

EPISODES = 1
MARGIN = 1000
state_size = 60

###########################################

#start_index = 45    #2010.01.01 00:00
#end_index = 3161+1  #2011.12.30 20:00

start_index = 8322+1    # 2011.12.16 16:00 start at 2012.01.02 00:00
end_index = 11423+1  #2012.12.30 16:00
dataset = pd.read_csv('EURUSD_4H.csv')
train_data = dataset.iloc[start_index:end_index,5:6]

train_data = np.array(train_data)
state_size = 5 
num_data = 60
X_train = [] 
all_index = end_index-start_index
for i in range(num_data, all_index):
    X_train.append(train_data[i-num_data:i,0])
X_train = np.array(X_train)

class Indicator:
    def __init__(self):
        # number of scatter plot.
        self.rsi_period = 30    # 5 days
        self.sd_period= 30       # 5 days 
        self.ma_period = 60    # 10 days
    
    def RSI_index(self, prices):
        gain = 0 
        loss = 0 
        for i in range(1,self.rsi_period):
            index = num_data - i
            change =  prices[index]-prices[index-1]
            if change > 0 :
                gain += change
            else :
                loss += change
        avg_gain = gain/self.rsi_period
        avg_loss = abs(loss)/self.rsi_period
        rs = avg_gain/avg_loss
        rsi = 100 - 100/(1+rs)
        print('RSI :', rsi)
        return rsi 
    
    def standard_devation(self, prices):
        use_data = prices[num_data - self.sd_period : num_data] 
        use_data = np.array(use_data)
        sd = np.std(use_data)
        print('SD :', sd)
        return sd 
    
    def moving_average(self, prices):
        use_data = prices[num_data-self.ma_period :num_data]
        use_data = np.array(use_data)
        x_bar = np.mean(use_data)
        print('mean :', x_bar)
        return x_bar
        
class TrainEnvironment:
    def __init__(self, data, num_index):
        self.indicator = Indicator()
        self.train_data = data
        self.train_index = 0 
        self.end_index = num_index-1
        self.loss_limit = 0.3 # force sell
        self.profit_limit = 0.05
        
        self.profit = 0
        self.reward = 0
        self.mem_reward = 0
        
        # portfolio 
        self.cost_price = 0 
        self.mem_action = 0
        
    def get_state(self):
        current_price = self.train_data[self.train_index,59:60]
        prices = self.train_data[self.train_index]
        rsi = self.indicator.RSI_index(prices)
        sd = self.indicator.standard_devation(prices)
        ma = self.indicator.moving_average(prices)
        state = [current_price,rsi,sd,ma,self.profit]
        state = np.array(state)
        return state
        
    def reset(self):
        self.train_index = 0 
        self.profit = 0
        self.reward = 0 
        self.cost_price = 0 
        self.mem_action = 0
        self.mem_reward = 0
        init_state = self.get_state()
        return init_state
    
    def get_action(self,action):
        if action == 1 :
            # buy 
            return 1
        elif action == 2 : 
            # sell 
            return -1
        else : 
            # noaction 
            return 0 
    
    def calculate_reward(self, action):
        action = self.get_action(action)
        current_price = self.train_data[self.train_index,59:60]
        if action == self.mem_action :
            self.profit = action*(current_price - self.cost_price)
            self.reward = self.mem_reward + self.profit
            print('new/mem action : ', action, ' / ', self.mem_action)
        else :  
            if action == 0 : 
                self.profit = self.mem_action*(current_price - self.cost_price)    
            else :
                self.profit = current_price*(-0.001) + self.mem_action*(current_price - self.cost_price)
            self.reward = self.profit + self.mem_reward
            self.mem_reward = self.reward 
            self.cost_price = current_price
            print('new/mem action : ', action, ' / ', self.mem_action)
            self.mem_action = action
        
         

    def done_check(self):
        if self.cost_price != 0 : 
            loss = -self.loss_limit*self.cost_price
        else : 
            loss = -self.loss_limit*self.train_data[self.train_index,59:60]
        if self.train_index + 1 == self.end_index :
            if self.reward > 0 : 
                if self.reward <= 0.05*self.train_data[self.train_index,59:60]:
                    self.reward = -1
            print('Full End !')
            return True 
        elif self.reward <= loss : 
            print('------------------------------------------------------------')
            print('loss limit: ', loss)
            print('reward : ', self.reward)
            print('Cut Loss !')
            self.reward = -3
            return True
        else :
            return False
        
    def step(self,action):
        skip = 1  # half day 
        self.train_index += skip
        if self.train_index >= self.end_index-1 : 
            self.train_index = self.end_index-1 
        ns = self.get_state()
        if self.profit_limit*self.cost_price >= self.profit and self.profit > 0 : 
            self.calculate_reward(0)    #close position
        self.calculate_reward(action)   
        done = self.done_check()
        return ns, self.reward*MARGIN, done


#########################################################################################################
# Train     
#########################################################################################################         
def watch_result(episode ,s_time, e_time, c_index, all_index, action, reward, profit):
    print('-------------------- Check -------------------------')
    print('start time: ' + s_time)  
    print('counter : ', c_index,'/', all_index,' of episode : ', episode, '/', EPISODES)
    print('action : ', action)
    print('current profit : ', profit*MARGIN)
    print('reward (all profit): ', reward)
    print('end_time: ' + e_time)
    print('-------------------End Check -----------------------')

    
if __name__ == "__main__":
    
    agent = DQNAgent(state_size)
    agent.load("agent_model.h5")
    num_index = all_index - state_size
    env = TrainEnvironment(X_train, num_index)
    batch_size = 20
    test_profit = []
    test_action = [] 
    
    for e in range(EPISODES):
        state = env.reset()
        state = np.reshape(state, [1, state_size]) 
        test_profit = []
        test_action = [] 
        for t in range(end_index-start_index):
            start_time = str(datetime.datetime.now().time())
            action = agent.act(state, train = False)
            print('action output :', action)
            next_state, reward, done = env.step(action)
            
            next_state = np.reshape(next_state, [1, state_size])
            agent.remember(state, action, reward, next_state, done)
            state = next_state       
            if done:
                agent.update_target_model()
                print('----------------------------- Episode Result -----------------------')
                print("episode: {}/{}, time: {}, e: {:.2}"
                      .format(e, EPISODES, t, agent.epsilon))
                print('----------------------------- End Episode --------------------------')
                break
            
            if len(agent.memory) > batch_size:
                agent.replay(batch_size)
            
            end_time = str(datetime.datetime.now().time())
            
            watch_result(e , start_time, end_time, env.train_index, end_index-start_index, env.get_action(action), reward ,env.profit)  
            
            test_profit.append(env.reward*1000)
            test_action.append(action*10)
    test_profit = np.array(test_profit)
    test_action = np.array(test_action)
    
    # agent.save("agent_model.h5")
    plt.plot(test_profit, color = 'blue', label = 'Profit')
    plt.plot(test_action, color = 'red', label = 'Actions')
    plt.title('Profit&Action')
    plt.xlabel('Time')
    plt.ylabel('Profit')
    plt.legend()
    plt.show()

                      
    