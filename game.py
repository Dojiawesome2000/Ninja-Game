### Remember: (0,0) on pygame coordinate system is TOP LEFT

import os
import sys
import pygame
import random
import math

from scripts.entities import PhysicsEntity, Player, Enemy, Boss
from scripts.utils import load_image, load_images, Animation
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle
from scripts.spark import Spark
from scripts.health_bar import HealthBar

class Game:
    
    def __init__(self):
        
        pygame.init()

        pygame.display.set_caption("Ninja Platformer Test Game")
        self.screen = pygame.display.set_mode((640, 480)) # the window for the game
        self.display = pygame.Surface((320, 240), pygame.SRCALPHA) # stuff to draw on
        self.display_2 = pygame.Surface((320, 240))

        self.clock = pygame.time.Clock()

        self.fps = 60 # frame rate (frames per second)

        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'player': load_image('entities/player.png'),
            'background': load_image('background.png'),
            'clouds': load_images('clouds'),
            'enemy/idle': Animation(load_images('entities/enemy/idle'), img_dur=6),
            'enemy/run': Animation(load_images('entities/enemy/run'), img_dur=4),
            'player/idle': Animation(load_images('entities/player/idle'), img_dur=6),
            'player/jump': Animation(load_images('entities/player/jump')),
            'player/run': Animation(load_images('entities/player/run'), img_dur=4),
            'player/slide': Animation(load_images('entities/player/slide')),
            'player/wall_slide': Animation(load_images('entities/player/wall_slide')),
            'boss/idle':Animation(load_images('entities/boss/idle'), img_dur=6),
            'boss/run':Animation(load_images('entities/boss/run')),
            'boss/jump':Animation(load_images('entities/boss/jump')),
            'boss/slash':Animation(load_images('entities/boss/slash')),
            'particles/leaf': Animation(load_images('particles/leaf'), img_dur=20, loop=False),
            'particles/particle': Animation(load_images('particles/particle'), img_dur=6, loop=False),
            'gun': load_image('gun.png'),
            'gun2': pygame.transform.flip(pygame.transform.scale(load_image('gun2.png'), (8, 4)), True, False),
            'projectile': load_image('projectile.png'),
        }

        self.sfx = {
            'jump': pygame.mixer.Sound('data/sfx/jump.wav'),
            'dash': pygame.mixer.Sound('data/sfx/dash.wav'),
            'hit': pygame.mixer.Sound('data/sfx/hit.wav'),
            'death': pygame.mixer.Sound('data/sfx/death.wav'),
            'shoot1': pygame.mixer.Sound('data/sfx/shoot1.wav'),
            'shoot2': pygame.mixer.Sound('data/sfx/shoot2.wav'),
            'ambience': pygame.mixer.Sound('data/sfx/ambience.wav'),
            'slash1': pygame.mixer.Sound('data/sfx/slash1.wav'),
            'slash2': pygame.mixer.Sound('data/sfx/slash2.wav'),
            'slash3': pygame.mixer.Sound('data/sfx/slash3.wav'),
        }

        self.sfx['slash1'].set_volume(0.5)
        self.sfx['slash2'].set_volume(0.6)
        self.sfx['slash3'].set_volume(0.6)
        self.sfx['ambience'].set_volume(0.2)
        self.sfx['shoot1'].set_volume(0.4)
        self.sfx['shoot2'].set_volume(0.4)
        self.sfx['hit'].set_volume(1)
        self.sfx['death'].set_volume(1)
        self.sfx['dash'].set_volume(0.3)
        self.sfx['jump'].set_volume(0.7)

        self.clouds = Clouds(self.assets['clouds'], count=32)

        self.player = Player(self, (50, 50), (8, 15))
        
        self.tilemap = Tilemap(self, tile_size=16)

        self.screenshake = 0
            
        # weird vars bc need to be initialized before self.run()
        self.enemies = []
        self.transition = -30
        self.dead_timer = 0

        self.map_name = 'test3.json' # or map.json
        # self.map_id = 0
        self.testing = True

        self.level = 0 if not self.testing else self.map_name
        try:
            # self.load_level(self.level)
            self.load_level(self.level) # make sure I edit self.testing whenever I switch between testing and playing
        except FileNotFoundError as e:
            print(f"Map file not found: {e}")
            # consider loading default map?
        print(self.map_name)

        self.movement = [False, False]

        self.use_wasd = False

        print("Controls start as arrow keys")

    def load_level(self, map_id):
        if self.testing:
            self.tilemap.load(map_id) # load map (for testing)
        else:
            self.tilemap.load('data/maps/' + str(map_id) + '.json') # load map (actual level)

        self.healthbars = []

        # reset all entities and particles
        self.leaf_spawners = [] # for particle effects
        for tree in self.tilemap.extract([('large_decor', 2)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + tree['pos'][0], 4 + tree['pos'][1], 23, 13))

        # self.enemies = []
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1), ('spawners', 2)]):
            if spawner['variant'] == 0: # spawner is for player
                self.player.pos = spawner['pos']
                self.player.air_time = 0
                self.healthbars.append(HealthBar(self, self.player, color=(0, 255, 0), shrink_factor=5))
            elif spawner['variant'] == 1: # spawner is for enemy
                enemy = Enemy(self, spawner['pos'], size=(8, 15))
                self.enemies.append(enemy)
                self.healthbars.append(HealthBar(self, enemy, color=(255, 0, 0), shrink_factor=5))
            else: #spawner is boss
                boss = Boss(self, spawner['pos'], size=(8, 15))
                self.enemies.append(boss)
                self.healthbars.append(HealthBar(self, boss, color=(255, 0, 0), shrink_factor=5))
        
        self.projectiles = []
        self.particles = []
        self.sparks = []

        self.scroll = [0,0]
        self.dead_timer = 0
        self.transition = -30

        # Reset hp and hp bar
        self.player.hp = self.player.max_hp
        self.player.hpbar_render_points = [
            (10, self.display.get_height() - 20),
            (10 + self.player.hp, self.display.get_height() - 20),
            (10 + self.player.hp, self.display.get_height() - 10),
            (10, self.display.get_height() - 10),
        ]


    def run(self):
        pygame.mixer.music.load('data/music.wav')
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)

        self.sfx['ambience'].play(-1)

        while True:
            self.display.fill((0, 0, 0, 0)) # everything rendered with this will have an outline (and rendered in the front/on self.display_2)
            # Clear Screen (by filling it with background img (or color))
            self.display_2.blit(self.assets['background'], (0, 0)) # anything rendered with this will have no outline (but rendered in the back/behind self.display)

            self.screenshake = max(0, self.screenshake - 1)

            if not len(self.enemies): # if all enemies are dead
                self.transition += 1
                if self.transition > 30:
                    if self.testing:
                        self.load_level(self.level) # restart
                    else:
                        self.level = min(self.level + 1, len(os.listdir('data/maps')) - 1)
                        self.load_level(self.level) # move to next level
            if self.transition < 0:
                self.transition += 1

            if self.dead_timer:
                self.dead_timer += 1
                if self.dead_timer >= 10:
                    self.transition = min(30, self.transition + 1)
                if self.dead_timer > 40:
                    self.load_level(self.level)

            # Update scroll
            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 30
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 30
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            # Spawn particles (not rendered yet)
            for rect in self.leaf_spawners:
                if random.random() * 29999 < rect.width * rect.height: # produces a random chance to spawn particles
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    self.particles.append(Particle(self, 'leaf', pos, velocity=[random.choice([-.1, .1]), 0.3], frame=random.randint(0, 20)))
            
            # Render clouds before tiles
            self.clouds.update()
            self.clouds.render(self.display_2, offset=render_scroll)

            # Render tiles before physics entities
            self.tilemap.render(self.display, offset=render_scroll)

            # Update/Render Enemies before player
            for enemy in self.enemies.copy():
                kill = True if (enemy.hp <= 0) else False
                enemy.update(self.tilemap, (0,  0))
                enemy.render(self.display, offset=render_scroll)
                if kill:
                    self.enemies.remove(enemy)
                    self.sparks.append(Spark(enemy.rect().center, 0, 5 + random.random()))
                    self.sparks.append(Spark(enemy.rect().center, math.pi, 5 + random.random()))

            # Update/Render player
            if not self.dead_timer:
                self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0)) # (self.movement[1]-self.movement[0] is change to X axis, 0 is change to Y axis)
                self.player.render(self.display, offset=render_scroll)
                # self.player.render_hp_bar(self.display_2, offset=render_scroll)

            # Update/Render projectiles (bullets) NOTE projectile format: projectile = [[x, y], direction, timer, dmg]
            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1] # changes projectile_x by direction
                projectile[2] += 1 # progresses timer
                
                # display the bullet
                img = self.assets['projectile']
                self.display.blit(img, (projectile[0][0] - img.get_width() / 2 - render_scroll[0], projectile[0][1] - img.get_height() / 2 - render_scroll[1]))
                
                # check if bullet hits wall
                if self.tilemap.solid_check(projectile[0]):
                    self.projectiles.remove(projectile) # deletes bullet if hits wall
                    for i in range(4):
                        self.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random())) # the + math.pi will make the spark go left instead of right
                elif projectile[2] > 360: # or if timer is greater than 360 (6 seconds)
                    self.projectiles.remove(projectile)
                elif abs(self.player.dashing) < 50: # or player is not actively dashing
                    if self.player.rect().collidepoint(projectile[0]): # and hits player
                        self.sfx['hit'].play()
                        self.projectiles.remove(projectile)
                        self.player.hp -= projectile[3] # projectile[3] should be the dmg of the projectile
                        self.screenshake = max(16, self.screenshake) # add screenshake
                        # update hp bar
                        self.player.hpbar_render_points = [
                            (10, self.display.get_height() - 20),
                            (10 + self.player.hp, self.display.get_height() - 20),
                            (10 + self.player.hp, self.display.get_height() - 10),
                            (10, self.display.get_height() - 10),
                        ]
                        if self.player.hp <= 0:
                            self.sfx['death'].play()
                            self.dead_timer += 1
                            spark_amount = 30
                        else:
                            spark_amount = random.randint(5, 10)
                        for i in range(spark_amount): # 30 SPARKS??? ... yes
                                angle = random.random() * math.pi * 2
                                speed = random.random() * 5
                                self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random()))
                                self.particles.append(Particle(self, 'particle', self.player.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed], frame=random.randint(0, 7)))

            # Update/Render Sparks
            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display, offset=render_scroll)
                if kill:
                    self.sparks.remove(spark)

            display_mask = pygame.mask.from_surface(self.display)
            display_sillhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))
            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.display_2.blit(display_sillhouette, offset)

            # Update/Render Healthbars
            for healthbar in self.healthbars.copy():
                if not healthbar.entity.hp <= 0:
                    healthbar.update()
                    healthbar.render(self.display, render_scroll)

            # Update/Render Particles
            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)
                if particle.type == 'leaf':
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                if kill:
                    self.particles.remove(particle)


            ## ----------------------------------------User Input---------------------------------------- ##
            for event in pygame.event.get():
                ## Quit Button
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN: # On key press/hold
                    if not self.use_wasd:
                        if event.key == pygame.K_LEFT: # move left
                            self.movement[0] = True
                        
                        if event.key == pygame.K_RIGHT: # move right
                            self.movement[1] = True

                        if event.key == pygame.K_UP: # jump
                            if self.player.jump():
                                self.sfx['jump'].play()

                        if event.key == pygame.K_DOWN: # force down
                            self.player.gravity_vel_change = 0.3

                        if event.key == pygame.K_x: # dash
                            self.player.dash()

                    else:
                        if event.key == pygame.K_a: # move left
                            self.movement[0] = True
                        
                        if event.key == pygame.K_d: # move right
                            self.movement[1] = True

                        if event.key == pygame.K_w: # jump
                            if self.player.jump():
                                self.sfx['jump'].play()

                        if event.key == pygame.K_s: # force down
                            self.player.gravity_vel_change = 0.3

                        if event.key == pygame.K_SPACE: # dash
                            self.player.dash()

                    if event.key == pygame.K_c: # toggle controls
                        self.use_wasd = not self.use_wasd
                        self.movement[0] = False
                        self.movement[1] = False
                        if self.use_wasd:
                            print("Controls changed to WASD")
                        else:
                            print("Controls changed to arrow keys")
                if event.type == pygame.KEYUP: # On key release
                    if not self.use_wasd:
                        if event.key == pygame.K_LEFT: # move left
                            self.movement[0] = False
                        
                        if event.key == pygame.K_RIGHT: # move right
                            self.movement[1] = False

                        if event.key == pygame.K_DOWN: # force down
                            self.player.gravity_vel_change = 0.1

                    else:
                        if event.key == pygame.K_a: # move left
                            self.movement[0] = False
                        
                        if event.key == pygame.K_d: # move right
                            self.movement[1] = False

                        if event.key == pygame.K_s: # force down
                            self.player.gravity_vel_change = 0.1
                
            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surf, (255, 255, 255), (self.display.get_width() // 2, self.display.get_height() // 2), (30 - abs(self.transition)) * 8)
                transition_surf.set_colorkey((255, 255, 255)) # makes the circle on the transition_surf transparent
                self.display.blit(transition_surf, (0, 0))

            self.display_2.blit(self.display, (0, 0))

            ## Update Screen
            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2)
            self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()), screenshake_offset)
            pygame.display.update()
            self.clock.tick(self.fps)


Game().run() # begins running the game