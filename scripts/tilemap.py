# from tile import Tile
import json

import os

import pygame

import sys


AUTOTILE_MAP = {
    tuple(sorted([(1, 0), (0, 1)])): 0, # if bottom and right tiles are occupied, variant = top left
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1, # if all but top are occupired, variant = top
    tuple(sorted([(-1, 0), (0, 1)])): 2, # if bottom and left tiles are occupied, variant = top right
    tuple(sorted([(-1, 0), (0, 1), (0, -1)])): 3, # if all but right are occupied, variant = right
    tuple(sorted([(-1, 0), (0, -1)])): 4, # if top and left tiles are occupied, variant = bottom right
    tuple(sorted([(1, 0), (0, -1), (-1, 0)])): 5, # if all but bottom are occupied, variant = bottom
    tuple(sorted([(1, 0), (0, -1)])): 6, # if top and right tiles are occupied, variant = bottom left
    tuple(sorted([(1, 0), (0, 1), (0, -1)])): 7, # if all but left are occupied, variant = left
    tuple(sorted([(1, 0), (0, 1), (0, -1), (-1, 0)])): 8, # if all are occupied, variant = middle 
}
### General-ish of simple tilemap: {'xcor;ycor': 'block_type/tile_type', 'xcor;ycor': 'block_type/tile_type'}
### Example: {'0;0': 'grass', '0;1': 'dirt', '9999;0': 'grass'}
NEIGHBOR_OFFSETS = [(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (0, 0), (-1, 1), (0, 1), (1, 1)]
AUTOTILE_OFFSETS = [(1, 0), (-1, 0), (0, -1), (0, 1)]
PHYSICS_TILES = {'grass', 'stone'}
AUTOTILE_TYPES = {'grass', 'stone'}

class Tilemap:
    def __init__(self, game, tile_size=16):
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {}
        self.offgrid_tiles = []

        self.save_counter = 0

        # # Create sample tile map
        # for i in range(10):
        #     self.tile_map[str(3 + i) + ';10'] = {'type': 'grass', 'variant': 1, 'pos': (3 + i, 10)}
        #     self.tile_map['10;' + str(5 + i)] = {'type': 'stone', 'variant': 1, 'pos': (10, 5 + i)}

    def extract(self, id_pairs:list, keep=False):
        # Finds all tiles with same 'type' and 'variant' as pairs specified in id_pairs:list
        matches = []
        for tile in self.offgrid_tiles.copy():
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                if not keep:
                    self.offgrid_tiles.remove(tile)
        
        for loc in self.tilemap.copy():
            tile = self.tilemap[loc]
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                # Need to change cords now from pixels to tile_size bc these are on_grid tiles
                matches[-1]['pos'] = matches[-1]['pos'].copy() # the reason this is copied is so that we don't actually move the tiles..
                matches[-1]['pos'][0] *= self.tile_size
                matches[-1]['pos'][1] *= self.tile_size
                if not keep:
                    del self.tilemap[loc]

        return matches

    def tiles_around(self, pos:list):
        tiles = []
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for offset in NEIGHBOR_OFFSETS:
            check_loc = str(tile_loc[0] + offset[0]) + ';' + str(tile_loc[1] + offset[1])
            if check_loc in self.tilemap:
                tiles.append(self.tilemap[check_loc])
        return tiles
    
    def save(self, path:str):
        print(path)
        if path[-5:] == '.json':
            if os.path.exists(path): # if the path exists
                # strip the .json
                print("MAP ALREADY EXISTS")
                save_path = path.rstrip(".json")
                
                # if no trailing digits (add a '0' to the end)
                if not save_path[-1].isdigit():
                    save_path += '0.json'
                    print('attempting to save ' + save_path)
                    # begone() #breakpoint
                    self.save(save_path)

                else: # but if there are trailing digits...
                    # get last digits
                
                    last_digits = ''
                    
                    while save_path[-1].isdigit():# and counter < 10:
                        
                        last_digits = save_path[-1] + last_digits
                        save_path = save_path[:-1]
                        
                    # set new save path to last digits + 1 (save path should now be words w/ no trailing nums)
                    save_path = save_path + str(int(last_digits) + 1) + '.json'
                    
                    self.save(save_path)
                # save the new save path
                with open(save_path, 'w') as f:
                    print('attempting to save ' + save_path)
                    json.dump({'tilemap': self.tilemap, 'tile_size': self.tile_size, 'offgrid': self.offgrid_tiles}, f)
                    begone()
            else:
                with open(path, 'w') as f:
                    print('attempting to save ' + path)
                    json.dump({'tilemap': self.tilemap, 'tile_size': self.tile_size, 'offgrid': self.offgrid_tiles}, f, check_circular=False, allow_nan=False)
        else:
            print("file not saveable (file type must be .json)")

    def load(self, path):
        f = open(path, 'r')
        map_data = json.load(f)
        f.close()

        self.tilemap = map_data['tilemap']
        self.tile_size = map_data['tile_size']
        self.offgrid_tiles = map_data['offgrid']

    def solid_check(self, pos):
        tileloc = str(int(pos[0] // self.tile_size)) + ';' + str(int(pos[1] // self.tile_size))
        if tileloc in self.tilemap:
            if self.tilemap[tileloc]['type'] in PHYSICS_TILES:
                return self.tilemap[tileloc]

    def physics_rects_around(self, pos):
        rects = []
        for tile in self.tiles_around(pos):
            if tile['type'] in PHYSICS_TILES:
                rects.append(pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size))
        return rects
    
    def autotile(self):
        for loc in self.tilemap: # for each tile in the tilemap
            tile = self.tilemap[loc]
            neighbors = set()
            for shift in AUTOTILE_OFFSETS: # for each neighbor
                check_loc = str(tile['pos'][0] + shift[0]) + ';' + str(tile['pos'][1] + shift[1])
                if check_loc in self.tilemap:
                    if self.tilemap[check_loc]['type'] == tile['type']: # make sure we only autotile tiles of the same group (i.e grass only autotiles with grass, stone only autotiles with stone)
                        neighbors.add(shift)
            neighbors = tuple(sorted(neighbors))
            if (tile['type'] in AUTOTILE_TYPES) and (neighbors in AUTOTILE_MAP):
                tile['variant'] = AUTOTILE_MAP[neighbors]

    def render(self, surface, offset=(0,0)):
        
        # Render off-grid tiles (first so that they're behind the on-grid tiles)
        for tile in self.offgrid_tiles:
            surface.blit(self.game.assets[tile['type']][tile['variant']], (tile['pos'][0] - offset[0], tile['pos'][1] - offset[1]))

        # Render on-grid tiles
        for x in range(offset[0] // self.tile_size, (offset[0] + surface.get_width()) // self.tile_size + 1): #top left to top right corner of visible screen
            for y in range(offset[1] // self.tile_size, (offset[1] + surface.get_height()) // self.tile_size + 1): #top to bottom of visible screen
                loc = str(x) + ';' + str(y)
                if loc in self.tilemap:
                    tile = self.tilemap[loc]
                    # if tile['type'] == 'spawners':
                    #     pass
                    # else:
                    #     surface.blit(self.game.assets[tile['type']][tile['variant']], (tile['pos'][0] * self.tile_size - offset[0], tile['pos'][1] * self.tile_size - offset[1]))
                    if tile['type'] == 'spawners' and tile['variant'] == 2: # if displaying boss, render with offset bc boss = weird
                        surface.blit(self.game.assets[tile['type']][tile['variant']], (x * self.tile_size - offset[0] - 3, y * self.tile_size - offset[1] - 4))
                    else:
                        surface.blit(self.game.assets[tile['type']][tile['variant']], (x * self.tile_size - offset[0], y * self.tile_size - offset[1]))
        # Older on-grid rendering (less efficient for large amounts of tiles)
        #  for loc in self.tile_map:
        #     tile = self.tile_map[loc]
        #     surface.blit(self.game.assets[tile['type']][tile['variant']], (tile['pos'][0] * self.tile_size - offset[0], tile['pos'][1] * self.tile_size - offset[1]))

def begone():
    pygame.quit()
    sys.exit()