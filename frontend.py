from __future__ import division
from multiprocessing import Pool, cpu_count
from os.path import isfile
from sys import exit
from pylab import *
from scipy.misc import imsave, toimage
from _routines import ffi, lib


BATCH_SIZE = 1000000 * 1


def iterate(args):
    seed, width, height, center_x, center_y, zoom, spot_x, spot_y, spot_zoom, source_x, source_y, source_zoom, iterations, samples = args
    lib.srand(seed)
    buf = ffi.new("double[]", 3 * width * height)
    lib.buddhabrot(buf, width, height, center_x, center_y, zoom, spot_x, spot_y, spot_zoom, source_x, source_y, source_zoom, iterations, samples, 1)
    im = array(list(buf)).reshape(height, width, 3)
    return im


def iterate_parallel(width, height, center_x, center_y, zoom, spot_x, spot_y, spot_zoom, source_x, source_y, source_zoom, iterations, samples):
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
    width = 192 * 1
    height = 108 * 1
    # width, height = height, width
    center_x = 0
    center_y = 0
    zoom = 0
    spot_x = -0.747
    spot_y = -0.08
    spot_zoom = 10
    # spot_zoom = float("inf")
    source_x = 0
    source_y = 0
    source_zoom = 0
    # source_zoom = float("inf")
    iterations = 40
    samples = BATCH_SIZE * 16 * 1
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
    # width = 128 * 10
    # height = 72 * 10
    width = 854
    height = 480
    center_x = -0.165965
    center_y = -1.039991
    zoom = -1.5
    spot_x = center_x
    spot_y = center_y
    spot_zoom = -1.5
    source_x = 0
    source_y = 0
    source_zoom = float("inf")
    iterations = 1000
    samples = BATCH_SIZE * 16 * 5
    normalizer = 70 / samples
    # normalizer *= 0.5

    num_frames = 2000
    for n in range(num_frames):
        filename = "frames/out_%04d.tiff" % n
        dumpname = "frames/out_%04d.dump" % n
        if isfile(filename):
            print "Skipping frame %04d." % n
            continue
        t = n / (num_frames - 1)
        zoom = -2.2 + t * 22.2
        spot_zoom = zoom - 2
        im = iterate_parallel(
            width, height,
            center_x, center_y, zoom,
            spot_x, spot_y, spot_zoom,
            source_x, source_y, source_zoom,
            iterations, samples,
        )
        if isfile("terminate.txt"):
            print "Terminating animation rendering..."
            exit()
        # pim = load(dumpname)
        # im += pim
        im.dump(dumpname)
        im *= normalizer * (1 + 2 * t*t)
        im = im ** 0.5
        im = tanh(exp(im) - 1)
        toimage(im).save(filename)
        print "Frame %04d done." % n

if __name__ == '__main__':
    print "Using {} cores to render a Buddhabrot...".format(cpu_count())
    render_image()
    # render_animation()
