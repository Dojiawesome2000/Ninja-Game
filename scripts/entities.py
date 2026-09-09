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
        self.spawn_pos = self.pos
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

    def rect(self, offset=(0,0)):
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

    # def physics_only_update(self, tilemap, movement=(0, 0)):
    #     # self.update(tilemap, movement=movement)
    #     super().update(tilemap, movement=movement)

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

        self.physics_only_update(tilemap, movement=movement)

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
                
    def physics_only_update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

    def render(self, surface, offset=(0,0)):
        super().render(surface=surface, offset=offset)

        # render a gun
        if self.type == 'enemy':
            if self.flip:
                surface.blit(pygame.transform.flip(self.game.assets['gun2'], True, False), (self.rect().centerx - self.gun_dist - self.game.assets['gun2'].get_width() - offset[0], self.rect().centery - offset[1]))
                # width of gun used here to place gun based on top right corner of enemy instead of top left
            else:
                surface.blit(self.game.assets['gun2'], (self.rect().centerx + self.gun_dist - offset[0], self.rect().centery - offset[1]))

class Boss(Enemy):
    # Ranges are in pixels
    ATTACK_RANGE = 20
    DETECTION_RANGE = 100
    SLASH_COOLDOWN = 75
    
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, e_type='boss', max_hp=500, dmg=10)

        self.anim_offset = (-2, -3)
        self.in_combat = False
        self.transition_timer = 0
        self.slashing_timer = 0
        self.slash_cooldown = 0
        self.show_hitbox = self.slashing_timer > 0
        self.sword_hitbox = Hitbox(game, self, width=20, height=20, color=(255, 0, 0, 50))
        
    def update(self, tilemap, movement=(0, 0)):
        if not self.in_combat: # move normally
            if self.walking and self.transition_timer <= 0:
                if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                    if (self.collisions['right'] or self.collisions['left']): # If hit wall
                        self.flip = not self.flip
                    else:
                        movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
                else:
                    self.flip = not self.flip
                self.walking = max(0, self.walking - 1)
                # no shooting logic for boss
            elif random.random() < 0.01:
                self.walking = random.randint(30, 120)
        
        else: # ATTACK mode :roar:
            # Flip based on player's x position relative to boss IF IN COMBAT
            self.flip = self.game.player.rect().centerx < self.rect().centerx
            movement = (movement[0]-.5 if self.flip else 0.5, movement[1]) # always move unless...
            # stop moving if hit wall, not done transitioning, or close enough to player
            # -------------------MORE TELEMETRY-------------------
            # print("can hit player?: ", self.can_hit_player())
            # print("Hit wall?: ", self.collisions['right'] or self.collisions['left'])
            # print("IN trnasition: ", self.transition_timer > 0)
            if self.collisions['right'] or self.collisions['left'] or self.transition_timer > 0 or self.can_hit_player():
                movement = (0, movement[1])
                # NOTE it would be cool to add a jump mechanic here (getting over obtacles?)
                
        #telemetry
        # print("self.centery - player.centery", abs(self.rect().centery - self.game.player.rect().centery))
            
        self.physics_only_update(tilemap, movement=movement)

        # Animation logic (if move, then animate, else no)
        # if movement[0] != 0:
        #     self.set_action('run')
        # elif not self.in_combat:
        #     self.set_action('idle')
        # else:
        #     self.set_action('idle_combat')

        if self.transition_timer <= 0:
            if not self.in_combat:
                if movement[0] != 0:
                    self.set_action('run')
                else:
                    self.set_action('idle')
            else:
                if self.slashing_timer <= 0:
                    if movement[0] != 0:
                        self.set_action('run_combat')
                    else:
                        self.set_action('idle_combat')
                else:
                    self.slashing_timer -= 1
                    self.set_action('slash')
                    if self.slashing_timer == 0:
                        self.slash_cooldown = self.SLASH_COOLDOWN
        else:
            self.transition_timer -= 1
            self.set_action('unsheath_sword')
            # if self.in_combat:
            #     self.set_action('unsheath_sword') #for testing
            # else:
            #     self.set_action('sheath_sword')
            
        # always lower slash_cooldown and update show_hitbox #TODO optimize/code better 😭
        self.slash_cooldown -= 1
        self.show_hitbox = self.slashing_timer > 0

        # override animation / trigger for combat mode (may be changed later)
        dist = self.get_dist_to_player()
        if dist < self.DETECTION_RANGE:
            if self.transition_timer <= 0 and not self.in_combat:
                # print(self.transition_timer)
                self.transition_timer = self.game.assets['boss/unsheath_sword'].len_imgs * self.game.assets['boss/unsheath_sword'].img_dur
            # print(self.transition_timer)
            self.set_combat(True)
            if self.can_hit_player(): # also slash
                self.slash()
        else:
            self.set_combat(False)
            
        # override animation / always follow through sword slash

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
                
        # always show hitbox
        self.sword_hitbox.update()
                
    def get_closest_player(self):
        """currently not needed/NO IMPLEMENTATION
        """
        pass
    
    def get_dist_to_player(self):
        return pygame.math.Vector2(self.game.player.rect().center).distance_to(pygame.math.Vector2(self.rect().center))
    
    def can_hit_player(self, attack_range:int=ATTACK_RANGE) -> bool: # assume like 10 pixels away to start slash
        dist = self.get_dist_to_player()
        # print("dist: ", dist)
        return (dist < attack_range) and (abs(self.rect().centery - self.game.player.rect().centery) < attack_range/2) # not to high, not too low :D 

    # TODO
    def slash(self):
        """
        Sets action to slash and updates slashing timer
        """
        if self.slashing_timer <= 0 and self.slash_cooldown <= 0:
            self.set_action('slash')
            self.slashing_timer = self.game.assets['boss/slash'].len_imgs * self.game.assets['boss/slash'].img_dur

    def set_combat(self, in_combat:bool):
        self.transition() if (in_combat and not self.in_combat) else None
        self.in_combat = in_combat

    def transition(self):
        """
        Transitions boss from sheathed animation to unsheathed animation based on self.in_combat
        
        :param self: if ykyk
        """
        self.set_action("unsheath_sword")
        
    def render(self, surface, offset=(0, 0)):
        if self.show_hitbox:
            self.sword_hitbox.render(surface, offset=(offset[0] + (10 if self.flip else -10), offset[1]))
            
        pygame.draw.rect(surface, (20, 40, 0, 50), self.sword_hitbox.rect())
        return super().render(surface, offset) # currently same as enemy, but will be changed later
        # pretty much make the gun/weapon different

class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size, max_hp=100, dmg=50)
        self.air_time = 0
        self.max_jumps = 2
        self.jumps = self.max_jumps
        self.wall_slide = False
        self.dashing = 0

        self.speed_multiplier = 1.5

        # self.hpbar_render_points = [
        #     (10, self.game.display.get_height() - 20),
        #     (10 + self.hp, self.game.display.get_height() - 20),
        #     (10 + self.hp, self.game.display.get_height() - 10),
        #     (10, self.game.display.get_height() - 10),
        # ]

        # self.hpbar_bg_rect_coords = (9, self.game.display.get_height() - 21, self.max_hp + 2, 12) # (x, y, width, height)

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
            pygame.draw.rect(surface, (50, 50, 50, 50), self.rect())
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
                
    def die(self):
        self.game.sfx['death'].play()
        self.game.dead_timer += 1
        
    def get_hit(self, spark_amount:int):
        """Adds sparks around character showing that it was hit

        Args:
            spark_amount (_int_): amount of sparks around character when hit
        """
        for _ in range(spark_amount): # 30 SPARKS??? ... yes
            angle = random.random() * math.pi * 2
            speed = random.random() * 5
            self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
            self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed], frame=random.randint(0, 7)))
            
    def process_hit(self):
        """Call this after you know player gets hit this will check if a player dies and the add sparks as needed
        """
        if self.hp <= 0:
            self.die()
            spark_amount = 30
        else:
            spark_amount = random.randint(5, 10)
        self.get_hit(spark_amount=spark_amount)
                
class Hitbox:
    """
    A generic hitbox class for extra/extended hitboxes (like for swords :D)
    """
    
    def __init__(self, game, entity:PhysicsEntity, width:float=5, height:float=5, color:tuple=(255, 0, 0, 128)):
        self.game = game
        self.entity = entity
        self.center = (self.entity.rect().centerx, self.entity.rect().centery) # TODO add x offset
        self.size = [width, height]
        self.color = color
        
    def rect(self, offset=(0,0)):
        'returns pygame.Rect() generic hitbox'
        return pygame.Rect(self.center[0] - self.size[0]/2 - offset[0], self.center[1] - self.size[1]/2 - offset[1], self.size[0], self.size[1]) # (x, y, width, height)
    
    def update(self):
        self.center = (self.entity.rect().centerx, self.entity.rect().centery)
    
    def render(self, surface, offset=(0, 0)):
        pygame.draw.rect(surface, self.color, self.rect(offset), width=0)
    