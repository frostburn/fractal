from __future__ import division
from multiprocessing import Pool, cpu_count
from os.path import isfile
from sys import exit
from pylab import *
from scipy.misc import imsave, toimage
from _routines import ffi, lib


BATCH_SIZE = 1000000 * 30 * 6


def iterate(args):
    seed, width, height, center_x, center_y, zoom, spot_x, spot_y, spot_zoom, source_x, source_y, source_zoom, iterations, samples = args
    lib.srand(seed)
    buf = ffi.new("double[]", 3 * width * height)
    lib.buddhabrot(buf, width, height, center_x, center_y, zoom, spot_x, spot_y, spot_zoom, source_x, source_y, source_zoom, iterations, samples)
    im = array(list(buf)).reshape(height, width, 3)
    return im


def iterate_parallel(width, height, center_x, center_y, zoom, spot_x, spot_y, spot_zoom, source_x, source_y, source_zoom, iterations, samples):
    im = zeros((height, width, 3))

    pool_size = cpu_count()
    pool = Pool(pool_size)
    batch_num = 0
    while samples > 0:
        if isfile("terminate.txt"):
            print "Terminating..."
            pool.close()
            pool.join()
            return im
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
            [source_x] * pool_size,
            [source_y] * pool_size,
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
    # width, height = height, width
    center_x = -0.125
    center_y = -0.92
    zoom = 2
    spot_x = -0.125
    spot_y = -0.8
    spot_zoom = 2
    source_x = 0
    source_y = 0
    source_zoom = float("inf")
    iterations = 400
    samples = BATCH_SIZE * 16 * 10
    im = iterate_parallel(
        width, height,
        center_x, center_y, zoom,
        spot_x, spot_y, spot_zoom,
        source_x, source_y, source_zoom,
        iterations, samples,
    )
    # pim = load("out.dump")
    # im += pim
    im.dump("out.dump")
    im /= im.max()
    im = im ** 0.5
    im *= 3
    im = tanh(exp(im) - 1)

    imshow(im, interpolation="none", cmap="gray")
    show()
    toimage(im).save("out.tiff")


def render_animation():
    width = 192 * 3
    height = 108 * 3
    center_x = -0.5
    center_y = 0
    zoom = -1.5
    spot_x = -0.7
    spot_y = 0.2
    spot_zoom = 3
    source_x = 1
    source_y = 0.2
    source_zoom = 3
    iterations = 200
    samples = BATCH_SIZE * 16 * 2
    normalizer = 15 / samples

    num_frames = 1000
    for n in range(num_frames):
        if isfile("terminate.txt"):
            print "Terminating animation rendering..."
            exit()
        filename = "frames/out_%03d.png" % n
        if isfile(filename):
            print "Skipping frame %03d." % n
            continue
        t = n / (num_frames - 1)
        t *= 2*pi
        spot_x = cos(7 * t) * (0.5 + 0.5 * cos(t)) * 0.8 - 0.5
        spot_y = sin(7 * t) * (0.5 + 0.5 * cos(t)) * 0.8 + 0.07
        source_x = sin(5 * t) * (0.5 - 0.5 * cos(t)) * 0.8 + 0.05
        source_y = cos(5 * t) * (0.5 - 0.5 * cos(t)) * 0.8 - 0.1
        im = iterate_parallel(
            width, height,
            center_x, center_y, zoom,
            spot_x, spot_y, spot_zoom,
            source_x, source_y, source_zoom,
            iterations, samples,
        )
        im *= normalizer
        im = minimum(im, 1)
        toimage(im).save(filename)
        # TODO: Dump the raw data too.
        print "Frame %03d done." % n

if __name__ == '__main__':
    print "Using {} cores to render a Buddhabrot...".format(cpu_count())
    render_image()
    # render_animation()