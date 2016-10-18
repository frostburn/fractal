from __future__ import division
from multiprocessing import Pool, cpu_count
from os.path import isfile
from sys import exit
from pylab import *
from scipy.misc import imsave, toimage
from _routines import ffi, lib


BATCH_SIZE = 1000000


def iterate(args):
    seed, width, height, center_x, center_y, zoom, spot_x, spot_y, spot_zoom, iterations, samples = args
    lib.srand(seed)
    buf = ffi.new("double[]", 3 * width * height)
    lib.buddhabrot(buf, width, height, center_x, center_y, zoom, spot_x, spot_y, spot_zoom, iterations, samples)
    im = array(list(buf)).reshape(height, width, 3)
    return im


def iterate_parallel(width, height, center_x, center_y, zoom, spot_x, spot_y, spot_zoom, iterations, samples):
    im = zeros((height, width, 3))

    pool_size = cpu_count()
    pool = Pool(pool_size)
    batch_num = 0
    while samples > 0:
        if isfile("terminate.txt"):
            print "Terminating..."
            pool.close()
            pool.join()
            exit()
        ims = pool.map(iterate, zip(
            list(arange(pool_size) + batch_num * pool_size),
            [width] * pool_size,
            [height] * pool_size,
            [center_x] * pool_size,
            [center_y] * pool_size,
            [zoom] * pool_size,
            [spot_x] * pool_size,
            [spot_y] * pool_size,
            [spot_zoom] * pool_size,
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
    width = 192
    height = 108
    width, height = height, width
    center_x = -1.25
    center_y = 0
    zoom = 0
    spot_x = -1
    spot_y = 1
    spot_zoom = -0.5
    iterations = 2000
    samples = BATCH_SIZE * 16
    im = iterate_parallel(
        width, height,
        center_x, center_y, zoom,
        spot_x, spot_y, spot_zoom,
        iterations, samples,
    )
    im.dump("out.dump")
    im /= im.max()
    im *= 1.5
    im = tanh(exp(im) - 1)

    im = im.swapaxes(0, 1)
    imshow(im, interpolation="none", cmap="gray")
    show()
    toimage(im).save("out.png")


def render_animation():
    width = 640
    height = 480
    center_x = -0.25
    center_y = 0
    zoom = -1.5
    spot_x = -0.5
    spot_y = 0
    spot_zoom = 1
    iterations = 1000
    samples = 200000000
    normalizer = 10 / samples

    num_frames = 1000
    for n in range(num_frames):
        filename = "frames/out_%03d.png" % n
        if isfile(filename):
            print "Skipping frame %03d." % n
            continue
        t = n / (num_frames - 1)
        spot_x = 1.7 - 4.6 * t
        im = iterate_parallel(
            width, height,
            center_x, center_y, zoom,
            spot_x, spot_y, spot_zoom,
            iterations, samples,
        )
        im *= normalizer
        im = minimum(im, 1)
        toimage(im).save(filename)
        # TODO: Dump the raw datat too.
        print "Frame %03d done." % n

if __name__ == '__main__':
    print "Using {} cores to render a Buddhabrot...".format(cpu_count())
    render_image()