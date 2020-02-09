from functools import reduce
from math import degrees, sin, cos
from time import time

from skimage import img_as_float
from skimage.io import imread
from skimage.color import rgb2hsv, label2rgb
from skimage.morphology import dilation, erosion, disk
from skimage.transform import ProjectiveTransform, resize, warp
from skimage.measure import label, regionprops
from numpy import logical_and, array
import matplotlib.pyplot as plt

from utils import make_colormap, show_images


class MarekSolution:
    WIDTH, HEIGHT = 1000, 500
    mini_selem = disk(3)
    selem = disk(6)
    
    COLOR_BLOCKS = {
        #'name': (hue_start, hue_end)
        'green': (0.4, 0.6),
        'yellow': (0.05, 0.18),
    }
    
    def __init__(self, filename, scale=None):
        img = imread(filename)
        if scale:
            h = img.shape[0] * scale
            w = img.shape[1] * scale
            img = resize(img, (w, h), anti_aliasing=True)
        self.img = img_as_float(img)
        self.hsv = rgb2hsv(self.img)
        
    def crop_image(self, debug=False, with_img=False):
        t0 = time()
        corners = self._find_corners()
        t1 = time()
        corner_points = self._get_positions_of_corners(corners)
        t2 = time()
        center_points = self._get_center_of_image(corner_points)
        t3 = time()
        
        if debug:
            print('find corners: %8.3f' % (t1 - t0))
            print('get positions of corners: %8.3f' % (t2 - t1))
            print('find center: %8.3f' % (t3 - t2))
            
            plt.figure(figsize=(20, 10))
            plt.imshow(label2rgb(corners, self.img))
            plt.plot([x for x,y in corner_points], [y for x,y in corner_points], '.w')
            plt.plot(center_points[0], center_points[1], '+w')
            plt.show()
            
        t4 = time()
        tform = self._make_transform_to_crop(corner_points, center_points)
        t5 = time()
        if with_img:
            self.crop_img = warp(self.img, tform, output_shape=(self.HEIGHT, self.WIDTH))
        self.crop_hsv = warp(self.hsv, tform, output_shape=(self.HEIGHT, self.WIDTH))
        t6 = time()
        
        if debug:
            print('make transform to crop: %8.3f' % (t5 - t4))
            print('crop and transform: %8.3f' % (t6 - t5))
            print('total: %8.3f' % (t3 - t0 + t6 - t4))

        
    def find_blocks(self, debug=False, debug_small=False):
        hue = self.crop_hsv[:,:,0]
        sat = self.crop_hsv[:,:,1]
        val = self.crop_hsv[:,:,2]
        
        blocks_mask = logical_and(sat > 0.2, val > 0.3)
        blocks_mask = erosion(blocks_mask, self.mini_selem)
        blocks_mask = dilation(blocks_mask, self.selem)

        def seek_color(hue_start, hue_end):
            mask = logical_and(
                blocks_mask, 
                logical_and(hue > hue_start, hue < hue_end)
            )
            mask = erosion(mask, self.mini_selem)
            return mask
        
        masks = {
            name: seek_color(hue_start, hue_end)
            for name, (hue_start, hue_end) in self.COLOR_BLOCKS.items()
        }

        if debug:
            show_images([
                ('all', blocks_mask, 'gray'),
            ] + [
                (name, mask, make_colormap(name))
                for name, mask in masks.items()
            ])
            
        labels = {
            name: label(mask)
            for name, mask in masks.items()
        }
        return labels
    
    @staticmethod
    def transform_blocks_to_json(blocks):
        objs = []
        for color_name, labels in blocks.items():
            for region in regionprops(labels):
                cy, cx = region.centroid
                angle = abs(region.orientation)
                length = region.major_axis_length
                sx = cx - sin(angle) * 0.5 * length
                sy = cy - cos(angle) * 0.5 * length
                objs.append({
                    'color': color_name,
                    'angle': degrees(angle),
                    'x': sx,
                    'y': sy,
                    'length': length,
                })
            
        return {
            'type': 'marek-solution',
            'objs': objs,
        }
        
    def _find_corners(self):
        hsv = self.hsv
        h = hsv[:,:,0]
        s = hsv[:,:,1]
        v = hsv[:,:,2]
        
        corners_mask = logical_and(
            logical_and(s > 0.2, v > 0.3), 
            logical_and(h > 0.8, h < 0.95),
        )
        corners_mask = dilation(corners_mask, self.selem)
        corners = label(corners_mask)
        return corners
        
    def _get_positions_of_corners(self, corners):
        tmp_points = []
        for region in regionprops(corners):
            y, x = region.centroid
            tmp_points.append((x, y))
        assert len(tmp_points) >= 4, 'not enough corners!'
        return tmp_points
    
    def _get_center_of_image(self, points):
        len_points = len(points)
        sx, sy = reduce(
            lambda a, b: (a[0] + b[0], a[1] + b[1]),
            points, 
        )
        return sx / len_points , sy / len_points
    
    def _get_points_to_transform(self, points, center_points):
        cenx, ceny = center_points
        dst_points = array([(0, 0)] * 4)
        
        UP_LEFT, DOWN_LEFT, DOWN_RIGHT, UP_RIGHT = range(4)
        def get_corner_index(x, y):
            if y < ceny:
                return UP_LEFT if x < cenx else UP_RIGHT
            else:
                return DOWN_LEFT if x < cenx else DOWN_RIGHT

        for x, y in points:
            corner_index = get_corner_index(x, y)
            dst_points[corner_index] = (x, y)
        return dst_points
            
    def _make_transform_to_crop(self, points, center_points):
        dst_points = self._get_points_to_transform(points, center_points)
        src_points = array([
            (0, 0),
            (0, self.HEIGHT),
            (self.WIDTH, self.HEIGHT),
            (self.WIDTH, 0),
        ])
        tform = ProjectiveTransform()
        tform.estimate(src_points, dst_points)
        return tform
