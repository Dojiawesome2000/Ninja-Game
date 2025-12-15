import pygame

from scripts.entities import Enemy, Player


class HealthBar:
    def __init__(self, game, entity, color:tuple=(255, 0, 0), shrink_factor=5):
        self.game = game
        self.entity = entity
        self.center = (self.entity.pos[0], self.entity.pos[1] - 5)
        self.color = color
        self.shrink_factor = shrink_factor

    def update(self):
        self.center = (self.entity.pos[0] + self.entity.rect().width / 2, self.entity.pos[1] - 5)

    def render(self, surface, offset=(0, 0)):
        render_points = [
            (self.center[0] - self.entity.max_hp/2/self.shrink_factor - offset[0], self.center[1] + 1 - offset[1]),
            (self.center[0] - self.entity.max_hp/2/self.shrink_factor + self.entity.hp/self.shrink_factor - offset[0], self.center[1] + 1 - offset[1]),
            (self.center[0] - self.entity.max_hp/2/self.shrink_factor + self.entity.hp/self.shrink_factor - offset[0], self.center[1] - offset[1]),
            (self.center[0] - self.entity.max_hp/2/self.shrink_factor - offset[0], self.center[1] - offset[1]),
        ]
        outline_render_points = (render_points[3][0] - 1, render_points[3][1] - 1, self.entity.max_hp/self.shrink_factor + 3, 4) # (x, y, width, height)
        
        pygame.draw.rect(surface, (0, 0, 0), outline_render_points, width=0)
        pygame.draw.polygon(surface, self.color, render_points)
        