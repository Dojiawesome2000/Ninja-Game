import pygame

from scripts.entities import Enemy, Player


class HealthBar:
    def __init__(self, game, entity, color:tuple=(255, 0, 0), shrink_factor=5, size_multiplier=1):
        self.game = game
        self.entity = entity
        self.center = (self.entity.rect().centerx - 1, self.entity.rect().top - 5)
        self.color = color
        self.shrink_factor = shrink_factor
        self.size = (18*size_multiplier, 2)  # width, height
        self.size_multiplier = size_multiplier

    def update(self):
        self.center = (self.entity.rect().centerx - 1, self.entity.rect().top - 5)

    def render(self, surface, offset=(0, 0)):
        hp_multiplier = self.entity.hp / self.entity.max_hp

        render_rect = (self.center[0] - self.size[0]/2 - offset[0] + self.size_multiplier, self.center[1] - self.size[1]/2 - offset[1] - self.size_multiplier, self.size[0] * hp_multiplier, self.size[1]) # (x, y, width, height)
        outline_render_rect = (render_rect[0] - 1, render_rect[1] - 1, self.size[0] + 2, self.size[1] + 2) # (x, y, width, height)
        # render_points = [
        #     (self.center[0] - self.entity.max_hp/2/self.shrink_factor - offset[0], self.center[1] + 1 - offset[1]),
        #     (self.center[0] - self.entity.max_hp/2/self.shrink_factor + self.entity.hp/self.shrink_factor - offset[0], self.center[1] + 1 - offset[1]),
        #     (self.center[0] - self.entity.max_hp/2/self.shrink_factor + self.entity.hp/self.shrink_factor - offset[0], self.center[1] - offset[1]),
        #     (self.center[0] - self.entity.max_hp/2/self.shrink_factor - offset[0], self.center[1] - offset[1]),
        # ]
        # outline_render_rect = (render_points[3][0] - 1, render_points[3][1] - 1, self.entity.max_hp/self.shrink_factor + 3, 4) # (x, y, width, height)
        
        pygame.draw.rect(surface, (0, 0, 0), outline_render_rect, width=0)
        pygame.draw.rect(surface, self.color, render_rect, width=0)
        # pygame.draw.polygon(surface, self.color, render_points)
        