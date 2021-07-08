import numpy as np
import spardriver_env
import spardriver_agent
import tensorflow as tf

tf.compat.v1.disable_eager_execution()
env = spardriver_env.Env()
lr = 0.001
agent = spardriver_agent.Agent(lr, 0.85, 3, 1.0, 256, env.observation_space.shape)
scores = []
epsilon_history = []
mode = input('1. train\n2. test\n')
if mode == '1':
    load = input('load previous data? (Y/n)')
    if load != 'n':
        print('model loaded.')
        agent.load_model()
else:
    env = spardriver_env.Env(True, 60)
    agent.load_model()
    agent.epsilon = 0
i = 0
while True:
    done = False
    score = 0
    observation = env.reset()
    while not done:
        action = agent.choose_action(observation)
        observation_, reward, done = env.step(action)
        score += reward
        agent.store_transition(observation, action, reward, observation_, done)
        observation = observation_
        if mode == '1':
            agent.learn()
    epsilon_history.append(agent.epsilon)
    scores.append(score)
    avg_score = np.mean(scores[-100:])
    print('episode', i,
          'score %.2f' % score,
          'average score %.2f' % avg_score,
          'epsilon %.2f' % agent.epsilon)
    i += 1
    if mode == '1' and i % 100 == 0:
        agent.save_model()
        print('model saved.')
        if i % 500 == 0:
            agent.epsilon = 1
            print('epsilon reset.')
