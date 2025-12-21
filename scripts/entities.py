import math
import random

import pygame

from scripts.particle import Particle
from scripts.spark import Spark

class PhysicsEntity:
    def __init__(self, game, entity_type, pos, size, max_hp=100, dmg=50):
        self.game = game
        self.type = entity_type
        self.pos = list(pos)
        self.size = size
        self.max_hp = max_hp
        self.hp = max_hp
        self.dmg = dmg
        self.velocity = [0, 0] #[x, y] 

        self.last_movement = [0, 0] #[x, y]
        
        self.gravity_vel_change = 0.1

        self.speed_multiplier = 1.0 # note: only meant for left-right movement

        self.img = None
        self.collisions = {'up': False, 'down': False, 'left': False, 'right': False}

        self.action = ''
        self.anim_offset = (-3, -3) # this is here so that the dif animations can be applied without making hitboxes seem weird
        self.flip = False
        self.set_action('idle')

    def rect(self):
        'returns pygame.Rect() hitbox of entity'
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
    
    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + "/" + self.action].copy()
    
    def print_collisions(self):
        print(f"left: {self.collisions['left']}")
        print(f"right: {self.collisions['right']}")
        print(f"up: {self.collisions['up']}")
        print(f"down: {self.collisions['down']}")

    def update(self, tilemap, movement=(0, 0)):
        self.collisions = {'up': False, 'down': False, 'left': False, 'right': False}

        frame_movement = (self.speed_multiplier * (movement[0] + self.velocity[0]), movement[1] + self.velocity[1]) # apply movement to velocity

        self.pos[0] += frame_movement[0] # apply left-right movement
        entity_rect = self.rect()
        # Detect left-right collision
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x

        self.pos[1] += frame_movement[1] # apply up-down movement
        entity_rect = self.rect()
        # Detect up-down collision
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y

        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True

        self.last_movement = movement
        
        self.velocity[1] = min(5, self.velocity[1] + self.gravity_vel_change ) # normalize gravity / y-axis velocity

        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0

        self.animation.update()

        # Collision Telemetry
        # self.print_collisions()
        # print(self.velocity[1])
        # print(entity_rect.right)

    def render(self, surface, offset=(0,0)):
        surface.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))


class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size, e_type = 'enemy', max_hp=75, dmg=25):
        super().__init__(game, e_type, pos, size, max_hp=max_hp, dmg=dmg)
        
        self.walking = 0 # walking timer

        self.speed_multiplier = 1.0

        self.gun_dist = 4 # gun distance away from body (for display purposes)

        self.projectile_speed = 2

    def update(self, tilemap, movement=(0, 0)):
        if self.walking:
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                if (self.collisions['right'] or self.collisions['left']): # If hit wall
                    self.flip = not self.flip
                else:
                    movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
            else:
                self.flip = not self.flip
            self.walking = max(0, self.walking - 1)
            if not self.walking: # if not walking
                dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
                if (abs(dis[1])) < 16: # and if player not above or below enemy
                    if self.flip and dis[0] < 0: # and if enemy if facing player (in this case, if facing left and enemy is to the left)
                        # then shoot
                        self.game.sfx['shoot2'].play() # play sound
                        self.game.projectiles.append([[self.rect().centerx - 7, self.rect().centery], -self.projectile_speed, 0, self.dmg]) # -7 is added to make bullet spawn to the left of the enemy rather than inside the enemy
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5 + math.pi, 2 + random.random())) # the + math.pi will make the spark go left instead of right
                    if (not self.flip and dis[0] > 0): # or if player is to the right and the enemy is looking to the right)
                        # then shoot
                        self.game.sfx['shoot2'].play() # play sound
                        self.game.projectiles.append([[self.rect().centerx + 7, self.rect().centery], self.projectile_speed, 0, self.dmg]) # +7 is added to make bullet spawn to the right of the enemy rather than inside the enemy
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5, 2 + random.random()))
        elif random.random() < 0.01:
            self.walking = random.randint(30, 120)

        super().update(tilemap, movement=movement)

        # Animation logic (if move, then animate, else no)
        if movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')

        if abs(self.game.player.dashing) >= 50: # if player is dashing
            if self.rect().colliderect(self.game.player.rect()): # and enemy collides with player
                self.hp -= self.game.player.dmg # take dmg from player
                self.game.screenshake = max(16, self.game.screenshake) # add screenshake
                self.game.sfx['slash3'].play()
                spark_amount = 30 if (self.hp <= 0) else random.randint(4, 7)
                for i in range(spark_amount): # EFFECTS :D ----> 30 SPARKS??? ... yes
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
                    self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed], frame=random.randint(0, 7)))
                # always show hit/slash mark
                

    def render(self, surface, offset=(0,0)):
        super().render(surface=surface, offset=offset)

        # render a gun
        if self.flip:
            surface.blit(pygame.transform.flip(self.game.assets['gun2'], True, False), (self.rect().centerx - self.gun_dist - self.game.assets['gun2'].get_width() - offset[0], self.rect().centery - offset[1]))
            # width of gun used here to place gun based on top right corner of enemy instead of top left
        else:
            surface.blit(self.game.assets['gun2'], (self.rect().centerx + self.gun_dist - offset[0], self.rect().centery - offset[1]))

class Boss(Enemy):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, e_type='boss', max_hp=500, dmg=10)

        self.anim_offset = (-5, -5)
        
    def update(self, tilemap, movement=(0, 0)):
        # # only same mvmt as enemy for now
        # if self.walking:
        #     if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
        #         if (self.collisions['right'] or self.collisions['left']): # If hit wall
        #             self.flip = not self.flip
        #         else:
        #             movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
        #     else:
        #         self.flip = not self.flip
        #     self.walking = max(0, self.walking - 1)
            # if not self.walking: # if not walking
            #     dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
            #     if (abs(dis[1])) < 16: # and if player not above or below enemy
            #         if self.flip and dis[0] < 0: # and if enemy if facing player (in this case, if facing left and enemy is to the left)
            #             # then shoot
            #             self.game.sfx['shoot2'].play() # play sound
            #             self.game.projectiles.append([[self.rect().centerx - 7, self.rect().centery], -self.projectile_speed, 0, self.dmg]) # -7 is added to make bullet spawn to the left of the enemy rather than inside the enemy
            #             for i in range(4):
            #                 self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5 + math.pi, 2 + random.random())) # the + math.pi will make the spark go left instead of right
            #         if (not self.flip and dis[0] > 0): # or if player is to the right and the enemy is looking to the right)
            #             # then shoot
            #             self.game.sfx['shoot2'].play() # play sound
            #             self.game.projectiles.append([[self.rect().centerx + 7, self.rect().centery], self.projectile_speed, 0, self.dmg]) # +7 is added to make bullet spawn to the right of the enemy rather than inside the enemy
            #             for i in range(4):
            #                 self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5, 2 + random.random()))
        # elif random.random() < 0.01:
        #     self.walking = random.randint(30, 120)

        super().update(tilemap, movement=movement)

        # Animation logic (if move, then animate, else no)
        if movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')
    
    def render(self, surface, offset=(0, 0)):
        return super().render(surface, offset) # currently same as enemy, but will be changed later
        # pretty much make the gun different

class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size, max_hp=100, dmg=50)
        self.air_time = 0
        self.max_jumps = 2
        self.jumps = self.max_jumps
        self.wall_slide = False
        self.dashing = 0

        self.speed_multiplier = 1.5

        self.hpbar_render_points = [
            (10, self.game.display.get_height() - 20),
            (10 + self.hp, self.game.display.get_height() - 20),
            (10 + self.hp, self.game.display.get_height() - 10),
            (10, self.game.display.get_height() - 10),
        ]

        self.hpbar_bg_rect_coords = (9, self.game.display.get_height() - 21, self.max_hp + 2, 12) # (x, y, width, height)

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement)

        if not self.wall_slide:
            self.air_time += 1

        if self.air_time > 150:
            self.game.dead_timer += 1
            self.game.screenshake = max(16, self.game.screenshake)

        if self.collisions['down']:
            self.air_time = 0
            self.jumps = self.max_jumps

        # Wall slide logic (and animation wall slide logic)
        self.wall_slide = False
        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4:
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1], 0.5) # caps the downward velocity
            if self.collisions['right']:
                self.flip = False
            else:
                self.flip = True
            self.set_action('wall_slide')

        # Most Animation Action Logic
        if not self.wall_slide:
            if self.air_time > 4:
                self.set_action('jump')
            elif movement[0] != 0:
                self.set_action('run')
            else:
                self.set_action('idle')

        # Dashing Logic
        if abs(self.dashing) in {60, 50}: # add 20 random direction particles at beginning and end of dash
            for i in range(20):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                particle_vel = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=particle_vel, frame=random.randint(0,7)))
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        elif self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)
        if abs(self.dashing) > 50:
            self.velocity[0] = (abs(self.dashing) / self.dashing) * 8
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1
            # add particles during dash
            particle_vel = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
            self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=particle_vel, frame=random.randint(0,7)))


        # Normalize x-axis velocity (only on player bc player can wall-jump)
        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)

    def render(self, surface, offset=(0,0)):
        # if you're a player and dashing, you become invisible (if you aren't dashing, you render)
        if abs(self.dashing) <= 50:
            super().render(surface=surface, offset=offset)

    # def render_hp_bar(self, surface, offset=(0,0)):
    #     pygame.draw.polygon(surface, (0, 255, 0), self.hpbar_render_points)
    #     pygame.draw.rect(surface, (0, 0, 0), self.hpbar_bg_rect_coords, width=1)

    def jump(self):
        if self.wall_slide:
            if self.flip and self.last_movement[0] < 0:
                self.velocity[0] = 2.75 # right movement
                self.velocity[1] = -2.75 # up movement
                self.air_time = 5 # to trigger animation
                self.jumps = 1#max(0, self.jumps - 1)
                return True
            elif not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = -2.75 # left movement
                self.velocity[1] = -2.75 # up movement
                self.air_time = 5 # to trigger animation
                self.jumps = 1#max(0, self.jumps - 1)
                return True
            
        elif self.jumps:
            self.velocity[1] = -3
            self.jumps -= 1
            self.air_time = 5
            self.game.sfx['jump'].play()
            
    def dash(self):
        if not self.dashing:
            self.game.sfx['dash'].play()
            if self.flip:
                self.dashing = -60
            else:
                self.dashing = 60