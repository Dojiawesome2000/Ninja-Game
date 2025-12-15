import os

import pygame

BASE_IMG_PATH = "data/images/"

def load_image(path):
    # note, there is a base image path for this function which is "data/images/"
    img = pygame.image.load(BASE_IMG_PATH + path).convert() #note: .convert() optimizes performance of images (why? idk)
    img.set_colorkey((0, 0, 0)) # sets black pixels of img to transparent
    return img

def load_images(path):
    images = []
    for img_name in sorted(os.listdir(BASE_IMG_PATH + path)):
        images.append(load_image(path + '/' + img_name))
    return images

class Animation:
    def __init__(self, imgs, img_dur=5, loop=True):
        self.imgs = imgs
        self.len_imgs = len(imgs)
        self.img_dur = img_dur
        self.loop = loop
        self.done = False
        self.frame = 0 # of the game... NOT of the animation

    def copy(self):
        '''returns copy of Animation object'''
        return Animation(self.imgs, self.img_dur, self.loop)
    
    def update(self):
        '''updates animation (moves along animation by one frame)'''
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_dur * self.len_imgs)
        else:
            self.frame = min(self.frame + 1, self.img_dur * self.len_imgs - 1) # added minus 1 to account index out of range
            if self.frame >= self.img_dur * self.len_imgs - 1:
                self.done = True

    def img(self):
        '''returns img of current frame'''
        return self.imgs[int(self.frame / self.img_dur)]
    


test = ''
print(len(test))