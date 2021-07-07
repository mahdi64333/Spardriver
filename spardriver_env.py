import numpy as np
import pygame
from time import time
from random import randint


class PygameObject:
    def __init__(self, x, y, speed, image: pygame.surface.Surface, centered=False, lane=None):
        self.x = x
        self.y = y
        self.speed = speed
        self.image = image
        self.lane = lane
        self.height = self.image.get_height()
        self.width = self.image.get_width()
        if centered:
            self.x -= self.width / 2

    def get_pos(self):
        return self.x, self.y

    def get_pos_center(self):
        return self.x + self.width / 2, self.y + self.height / 2

    def set_x_center(self, x):
        self.x = x - self.width / 2

    def set_y_center(self, y):
        self.y = y - self.height / 2


class Env:
    def __init__(self, visual=False, fps=1, human=False):
        # base game stuff
        self.visual = visual
        if self.visual:
            pygame.init()
            self.screen = pygame.display.set_mode((800, 600))
            pygame.display.set_caption('Spardriver')
            pygame.display.set_icon(pygame.image.load('icon.png'))
            self.background = PygameObject(0, -1800, 10, pygame.image.load('background.png'))
            self.score_font = pygame.font.Font('freesansbold.ttf', 16)
        self.clock = pygame.time.Clock()
        self.score = 0
        self.FPS = fps
        self.dt = 1
        self.human = human
        self.player = PygameObject(320, 470, 9, pygame.image.load('car.png'), True, 2)
        self.observation_space = np.zeros(19)

        self.CAR_IMAGES = []
        for i in range(5):
            self.CAR_IMAGES.append(pygame.image.load('car' + str(i) + '.png'))
        self.CAR_SPEEDS = [4.02, 3.98, 4.04, 3.96, 4.0]
        self.other_cars = []
        self.done = False
        self.prev_time = 0

    def update_observation_space(self):
        for i in range(1, 5):
            self.observation_space[i - 1] = 1 if i == self.player.lane else 0
        for i in range(1, 4):
            t_index = 5 * i - 1
            self.observation_space[t_index] = self.other_cars[i - 1].y / 760
            for j in range(1, 5):
                self.observation_space[t_index + j] = 1 if j == self.other_cars[i - 1].lane else 0

    def reset(self):
        self.background.y = -1800
        self.player.lane = randint(1, 4)
        self.player.set_x_center(self.player.lane * 160)
        self.player.y = 470
        self.other_cars = []
        for i in range(3):
            car_no = randint(0, 4)
            self.other_cars.append(PygameObject(0, -i * 320 - 120,
                                                self.CAR_SPEEDS[car_no],
                                                self.CAR_IMAGES[car_no]))
            self.other_cars[i].lane = randint(1, 4)
            self.other_cars[i].set_x_center(self.other_cars[i].lane * 160)
        self.score = 0
        self.update_observation_space()
        self.done = False
        self.prev_time = time()
        return np.copy(self.observation_space)

    def check_danger(self):
        danger = 0
        for car in self.other_cars:
            if car.lane == self.player.lane:
                if 150 <= car.y < self.player.y:
                    danger += 1

        return danger

    def world_change(self):
        self.background.y += self.background.speed * self.dt * self.FPS
        for car in self.other_cars:
            car.y += car.speed * self.dt * self.FPS
            if car.y > 600:
                car.y -= 960
                car.lane = randint(1, 4)
                car.set_x_center(160 * car.lane)
                car_no = randint(0, 4)
                car.image = self.CAR_IMAGES[car_no]
                car.speed = self.CAR_SPEEDS[car_no]
                self.score += 1
        if self.background.y >= -600:
            self.background.y -= 1200

    def draw(self):
        self.screen.blit(self.background.image, self.background.get_pos())
        self.screen.blit(self.player.image, self.player.get_pos())
        for car in self.other_cars:
            self.screen.blit(car.image, (car.x, car.y))
        score_surface = self.score_font.render('Score: ' + str(self.score), True, (255, 255, 255))
        self.screen.blit(score_surface, (4, 4))
        pygame.display.update()

    def game_over(self):
        g_o_font = pygame.font.Font('freesansbold.ttf', 72)
        g_o_txt = PygameObject(400, 300, 0, g_o_font.render('GAME OVER!', True, (255, 255, 255)))
        g_o_txt.x -= g_o_txt.width / 2
        g_o_txt.y -= g_o_txt.height / 2
        self.screen.fill((0, 0, 0),
                         (400 - 10 - g_o_txt.width / 2,
                          300 - 10 - g_o_txt.height / 2,
                          g_o_txt.width + 20,
                          g_o_txt.height + 20))
        self.screen.blit(g_o_txt.image, (g_o_txt.x, g_o_txt.y))
        pygame.display.update()

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                    running = False

    def step(self, action=None):
        danger = self.check_danger()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.done = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    action = 1
                if event.key == pygame.K_RIGHT:
                    action = 2
        if action == 1:
            self.player.lane -= 1
            while self.player.get_pos_center()[0] > self.player.lane * 160:
                if self.visual:
                    self.clock.tick(self.FPS)
                    self.draw()
                    now = time()
                    self.dt = now - self.prev_time
                    self.prev_time = now
                self.player.x -= self.player.speed * self.dt * self.FPS
                self.world_change()
        if action == 2:
            self.player.lane += 1
            while self.player.get_pos_center()[0] < self.player.lane * 160:
                if self.visual:
                    self.clock.tick(self.FPS)
                    self.draw()
                    now = time()
                    self.dt = now - self.prev_time
                    self.prev_time = now
                self.player.x += self.player.speed * self.dt * self.FPS
                self.world_change()
        if self.player.lane < 1 or self.player.lane > 4:
            self.done = True
        for car in self.other_cars:
            if self.player.lane == car.lane and car.y - 120 <= self.player.y <= car.y + 120:
                self.done = True
        if self.visual:
            self.clock.tick(self.FPS)
            now = time()
            self.dt = now - self.prev_time
            self.prev_time = now
        self.world_change()
        if self.visual:
            self.draw()

        if self.human and self.done:
            self.game_over()

        self.update_observation_space()

        _reward = 1

        if done:
            _reward = -50
        elif action == 0:
            _reward = 5
        elif danger > self.check_danger():
            _reward = 10
        elif danger < self.check_danger():
            _reward = -5

        return np.copy(self.observation_space), _reward, self.done


if __name__ == '__main__':
    while True:
        env = Env(True, 60, True)
        env.reset()
        done = False
        while not done:
            _, _, done = env.step()
