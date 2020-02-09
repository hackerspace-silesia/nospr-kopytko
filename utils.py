import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb, ListedColormap

def show_images(data, small=False, colormap=False):
    ldata = len(data)
    if small:
        fig = plt.figure(figsize=(20, 10))
    else:
        fig = plt.figure(figsize=(20, 10 * ldata))

    for i, (name, im, cmap) in enumerate(data, start=1):
        if small:
            ax = fig.add_subplot(1, ldata, i, xticks=[], yticks=[])
        else:
            ax = fig.add_subplot(ldata, 1, i, xticks=[], yticks=[])
        ax.set_title(name)
        _img = ax.imshow(im, cmap=cmap)
        if colormap:
            plt.colorbar(_img, fraction=0.046, pad=0.04, shrink=1.0)
    fig.show()


def make_colormap(colorname):
    color = to_rgb(colorname)
    return ListedColormap([[0, 0, 0], color])
