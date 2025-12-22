### Remember: (0,0) on pygame coordinate system is TOP LEFT

import sys

import pygame

from scripts.utils import load_images
from scripts.tilemap import Tilemap

RENDER_SCALE = 2.0

class Editor:
    
    def __init__(self):
        
        pygame.init()

        pygame.display.set_caption("Ninja Platformer Level Editor")
        self.screen = pygame.display.set_mode((640, 480)) # the window for the game
        self.display = pygame.Surface((320, 240)) # stuff to draw on

        self.clock = pygame.time.Clock()

        self.fps = 60 # frame rate (frames per second)

        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'spawners': load_images('tiles/spawners'),
        }

        self.movement = [False, False, False, False]
        
        self.tilemap = Tilemap(self, tile_size=16)
        self.tilemap.load('map.json') # default is: 'map.json'

        # try:
        #     self.tilemap.load("map.json")
        # except FileNotFoundError:
        #     pass

        self.scroll = [0, 0]

        self.tile_list = list(self.assets)
        self.tile_list_len = len(self.tile_list)
        self.tile_group = 0 # 0 is decor i think
        self.tile_variant = 0

        self.left_clicking = False
        self.right_clicking = False
        self.shift = False
        self.on_grid = True

    def run(self):
        while True:
            # Clear Screen (by filling it with background img (or color))
            self.display.fill((0, 0, 0))

            # Update camera movement
            self.scroll[0] += (self.movement[1] - self.movement[0]) * 2
            self.scroll[1] += (self.movement[3] - self.movement[2]) * 2

            # Set up camera offset (render_scroll)
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            # Render TileMap
            self.tilemap.render(self.display, offset=render_scroll)

            # Get current/active tile
            current_tile_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy()
            current_tile_img.set_alpha(100)

            # Get tile pos from mouse pos
            mpos = pygame.mouse.get_pos()
            mpos = (mpos[0] / RENDER_SCALE, mpos[1] / RENDER_SCALE)
            tile_pos = (int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size), int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size))

            # Display placing position in real time
            if self.on_grid:
                if self.tile_group == 4 and self.tile_variant == 2: # if displaying boss
                    self.display.blit(current_tile_img, (tile_pos[0] * self.tilemap.tile_size - self.scroll[0] - 3, tile_pos[1] * self.tilemap.tile_size - self.scroll[1] - 4))
                else:
                    self.display.blit(current_tile_img, (tile_pos[0] * self.tilemap.tile_size - self.scroll[0], tile_pos[1] * self.tilemap.tile_size - self.scroll[1]))
            else:
                self.display.blit(current_tile_img, mpos)

            
            # If left clicking, place tile
            if self.left_clicking and self.on_grid:
                self.tilemap.tilemap[str(tile_pos[0]) + ';' + str(tile_pos[1])] = {'type': self.tile_list[self.tile_group], 'variant': self.tile_variant, 'pos': tile_pos}
            
            # If right clicking and hovering over tile, delete tile
            if self.right_clicking:
                tile_loc = str(tile_pos[0]) + ';' + str(tile_pos[1])
                if tile_loc in self.tilemap.tilemap:
                    del self.tilemap.tilemap[tile_loc]
                for tile in self.tilemap.offgrid_tiles.copy():
                    tile_img = self.assets[tile['type']][tile['variant']]
                    tile_r = pygame.Rect(tile['pos'][0] - self.scroll[0], tile['pos'][1] - self.scroll[1], tile_img.get_width(), tile_img.get_height())
                    if tile_r.collidepoint(mpos):
                        self.tilemap.offgrid_tiles.remove(tile)


            # Display img (preview of current tile being placed in top left corner)
            self.display.blit(current_tile_img, (5, 5))
        
            ## User Input
            for event in pygame.event.get():
                ## Quit Button
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN: # On mouse activation (click or scroll)
                    if event.button == 1: # left click
                        self.left_clicking = True
                        if not self.on_grid:
                            self.tilemap.offgrid_tiles.append({'type': self.tile_list[self.tile_group], 'variant': self.tile_variant, 'pos': (mpos[0] + self.scroll[0], mpos[1] + self.scroll[1])})
                    
                    if event.button == 3: # right click
                        self.right_clicking = True

                    if self.shift:
                        if event.button == 4: # scroll up
                            self.tile_variant = (self.tile_variant - 1) % len(self.assets[self.tile_list[self.tile_group]])

                        if event.button == 5: # scroll down?
                            self.tile_variant = (self.tile_variant + 1) % len(self.assets[self.tile_list[self.tile_group]])
                    else:
                        if event.button == 4: # scroll up
                            self.tile_group = (self.tile_group - 1) % self.tile_list_len
                            self.tile_variant = 0

                        if event.button == 5: # scroll down?
                            self.tile_group = (self.tile_group + 1) % self.tile_list_len
                            self.tile_variant = 0

                if event.type == pygame.MOUSEBUTTONUP: # On mouse de-activation
                    if event.button == 1: # left click
                        self.left_clicking = False
                    
                    if event.button == 3: # right click
                        self.right_clicking = False


                if event.type == pygame.KEYDOWN: # On key press/hold
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.movement[0] = True
                    
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.movement[1] = True

                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.movement[2] = True

                    if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.movement[3] = True

                    if event.key == pygame.K_t:
                        self.tilemap.autotile()

                    if event.key == pygame.K_o:
                        self.tilemap.save('test.json')

                    if event.key == pygame.K_g: # Toggle on_grid
                        self.on_grid = not self.on_grid

                    if event.key == pygame.K_LSHIFT:
                        self.shift = True

                if event.type == pygame.KEYUP: # On key release
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.movement[0] = False
                    
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.movement[1] = False

                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.movement[2] = False

                    if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.movement[3] = False

                    if event.key == pygame.K_LSHIFT:
                        self.shift = False

                

            ## Update Screen
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(self.fps)

editor = Editor()
if __name__ == "__main__":
    editor.run()