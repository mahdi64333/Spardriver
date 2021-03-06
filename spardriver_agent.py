from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
import numpy as np


class ReplayBuffer:
    def __init__(self, max_size, input_dims):
        self.mem_size = max_size
        self.mem_counter = 0

        self.state_memory = np.zeros((self.mem_size, *input_dims), dtype=np.float64)
        self.new_state_memory = np.zeros((self.mem_size, *input_dims), dtype=np.float64)
        self.action_memory = np.zeros(self.mem_size, dtype=np.int8)
        self.reward_memory = np.zeros(self.mem_size, dtype=np.int16)
        self.terminal_memory = np.zeros(self.mem_size, dtype=np.int8)

    def store_transition(self, state, action, reward, state_, done):
        index = self.mem_counter % self.mem_size
        self.state_memory[index] = state
        self.new_state_memory[index] = state_
        self.action_memory[index] = action
        self.reward_memory[index] = reward
        self.terminal_memory[index] = 1 - int(done)
        self.mem_counter += 1

    def sample_buffer(self, batch_size):
        max_mem = min(self.mem_counter, self.mem_size)
        batch = np.random.choice(max_mem, batch_size, replace=False)

        states = self.state_memory[batch]
        states_ = self.new_state_memory[batch]
        rewards = self.reward_memory[batch]
        actions = self.action_memory[batch]
        terminal = self.terminal_memory[batch]

        return states, states_, rewards, actions, terminal


def build_dqn(lr, n_actions, input_dims, fc1_dims, fc2_dims):
    model = Sequential([
        Dense(fc1_dims, input_dim=sum(input_dims), activation='relu'),
        Dense(fc2_dims, activation='relu'),
        Dense(n_actions, activation='linear')])
    model.compile(optimizer=Adam(learning_rate=lr), loss='mse')

    return model


class Agent:
    def __init__(self, lr, gamma, n_actions, epsilon, batch_size, input_dims,
                 epsilon_decay=0.001, epsilon_end=0.01, mem_size=1_000_000, fname='dqn_model.h5'):
        self.gamma = gamma
        self.action_space = [i for i in range(n_actions)]
        self.epsilon = epsilon
        self.batch_size = batch_size
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_end
        self.model_file = fname
        self.memory = ReplayBuffer(mem_size, input_dims)
        self.q_eval = build_dqn(lr, n_actions, input_dims, 64, 64)

    def store_transition(self, state, action, reward, new_state, done):
        self.memory.store_transition(state, action, reward, new_state, done)

    def choose_action(self, observation):
        if np.random.random() < self.epsilon:
            action = np.random.choice(self.action_space)
        else:
            state = np.array([observation])
            actions = self.q_eval.predict(state)
            action = np.argmax(actions)

        return action

    def learn(self):
        if self.memory.mem_counter < self.batch_size:
            return

        states, states_, rewards, actions, dones = self.memory.sample_buffer(self.batch_size)

        q_eval = self.q_eval.predict(states)
        q_next = self.q_eval.predict(states_)

        q_target = np.copy(q_eval)
        batch_index = np.arange(self.batch_size, dtype=np.int32)

        q_target[batch_index, actions] = rewards + self.gamma * np.max(q_next, axis=1) * dones
        self.q_eval.train_on_batch(states, q_target)

        self.epsilon = max(self.epsilon - self.epsilon_decay, self.epsilon_min)

    def save_model(self):
        self.q_eval.save(self.model_file)

    def load_model(self):
        self.q_eval = load_model(self.model_file)
