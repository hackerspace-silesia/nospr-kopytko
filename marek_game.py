from math import sin, cos, radians
from time import time
import sys

from pygame.locals import QUIT
import pygame

from marek import MarekSolution

try:
    IMAGE = sys.argv[1]
except IndexError:
    IMAGE = 'images/c.jpg'

# set up pygame
pygame.init()

# set up the window
WIDTH, HEIGHT = 1000, 500
window = pygame.display.set_mode((WIDTH, HEIGHT), 0, 32)
pygame.display.set_caption('MUZYKA ZIOMEK')

# set up the colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

basic_font = pygame.font.SysFont('monospace', 12)

window.fill(BLACK)

# get data from image
print('computing...', end=' ')
t0 = time()
solution = MarekSolution(IMAGE, scale=0.25)
solution.crop_image(with_img=True)
blocks = solution.find_blocks()
data = solution.transform_blocks_to_json(blocks)
t1 = time()
print('time:', '%.3fs' % (t1 - t0))


# draw cropped image
print('draw image...')
pix = pygame.PixelArray(window)
for x in range(WIDTH):  # todo - SLOW
    for y in range(HEIGHT):
        rgb = solution.crop_img[y, x, :] * 255
        r = int(rgb[0])
        g = int(rgb[1])
        b = int(rgb[2])
        pix[x][y] = (r, g, b)
del pix

if data['type'] != 'marek-solution':
    sys.exit()

def get_color_from_obj(obj):
    o_color = obj['color']
    if o_color == 'yellow':
        return YELLOW
    elif o_color == 'green':
        return GREEN
    else:
        return WHITE

def draw_text(text, color, x, y):
    text = basic_font.render(text, True, color)
    text_rect = text.get_rect()
    text_rect.left = x
    text_rect.centery = y + 30
    window.blit(text, text_rect)


print('draw objs...')
for obj in data['objs']:  # draw objs
    color = get_color_from_obj(obj)
    length = obj['length']
    angle = obj['angle']
    rad = radians(angle)
    sx = int(obj['x'])
    sy = int(obj['y'])
    ex = int(sx + sin(rad) * length)
    ey = int(sy - cos(rad) * length)
    pygame.draw.line(window, color, (sx, sy), (ex, ey), 5)
    pygame.draw.circle(window, color, (sx, sy), 7) 
    draw_text(f'L:{length: 6.2f}', color, sx, sy)
    draw_text(f'A:{angle: 6.2f}°', color, sx, sy + 15)

# draw the window onto the screen
pygame.display.update()

# run the game loop
while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
