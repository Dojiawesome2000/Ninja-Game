### NOTE: THIS CLASS IS NOT USED IN FINAL VERSION... UNLESS I WANT TO CHANGE THE WHOLE SETUP

class Tile:
    def __init__(self, type:str, variant:int, pos:tuple):
        """
        Tile obj (stores tile type, variant, and position)
        type - the type of tile (e.g. 'grass', 'dirt', etc.)
        variant - the variant of the tile (e.g. 1, 2, 3, etc.)
        pos - the position of the tile in (x, y) format (e.g. (0,0), (1, 10), (9999,0), etc.)
        """
        self.type = type
        self.variant = variant
        self.pos = pos

    def get_type(self):
        'returns tile type (str)'
        return self.type

    def get_variant(self):
        'returns tile variant (int)'
        return self.variant
    
    def get_pos(self):
        'returns tile position (x,y)'
        return self.pos