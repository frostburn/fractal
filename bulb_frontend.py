from __future__ import division
from multiprocessing import Pool, cpu_count
from os.path import isfile
from sys import exit
from pylab import *
from scipy.misc import imsave, toimage
from _routines import ffi, lib


BATCH_SIZE = 1000000 * 10 * 10


def iterate(args):
    seed, width, height, center_x, center_y, center_z, zoom, spot_x, spot_y, spot_z, spot_zoom, source_x, source_y, source_z, source_zoom, iterations, samples = args
    lib.srand(seed)
    buf = ffi.new("double[]", 3 * width * height)
    lib.buddhabulb(buf, width, height, center_x, center_y, center_z, zoom, spot_x, spot_y, spot_z, spot_zoom, source_x, source_y, source_z, source_zoom, iterations, samples)
    im = array(list(buf)).reshape(height, width, 3)
    return im


def iterate_parallel(width, height, center_x, center_y, center_z, zoom, spot_x, spot_y, spot_z, spot_zoom, source_x, source_y, source_z, source_zoom, iterations, samples):
    im = zeros((height, width, 3))

    pool_size = cpu_count()
    pool = Pool(pool_size)
    batch_num = 0
    base_seed = randint(100000000)
    while samples > 0:
        if isfile("terminate.txt"):
            print "Terminating..."
            pool.close()
            pool.join()
            return im
        ims = pool.map(iterate, zip(
            list(arange(pool_size) + batch_num * pool_size + base_seed),
            [width] * pool_size,
            [height] * pool_size,
            [center_x] * pool_size,
            [center_y] * pool_size,
            [center_z] * pool_size,
            [zoom] * pool_size,
            [spot_x] * pool_size,
            [spot_y] * pool_size,
            [spot_z] * pool_size,
            [spot_zoom] * pool_size,
            [source_x] * pool_size,
            [source_y] * pool_size,
            [source_z] * pool_size,
            [source_zoom] * pool_size,
            [iterations] * pool_size,
            [BATCH_SIZE] * pool_size,
        ))
        for im_ in ims:
            im += im_
        samples -= pool_size * BATCH_SIZE
        batch_num += 1
    pool.close()
    pool.join()
    return im


def render_image():
    width = 192 * 10
    height = 108 * 10
    width, height = height, width
    center_x = 0.6
    center_y = -0.5
    center_z = 0
    zoom = -1
    spot_x = 0.5
    spot_y = 0.3
    spot_z = -0.4
    spot_zoom = 3
    # spot_zoom = float("inf")
    source_x = 0
    source_y = 0
    source_z = 0
    source_zoom = float("inf")
    # source_zoom = 0
    iterations = 6 * 5
    samples = BATCH_SIZE * 16 * 6
    im = iterate_parallel(
        width, height,
        center_x, center_y, center_z, zoom,
        spot_x, spot_y, spot_z, spot_zoom,
        source_x, source_y, source_z, source_zoom,
        iterations, samples,
    )
    im = im.swapaxes(0, 1)
    pim = load("out.dump")
    im += pim
    im.dump("out.dump")
    im /= im.max()
    im = im ** 0.5
    im *= 0.7
    im = tanh(exp(im) - 1)
    im /= im.max()

    imshow(im, interpolation="none", cmap="gray")
    show()
    toimage(im).save("out.tiff")

if __name__ == '__main__':
    render_image()
