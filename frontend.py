from __future__ import division
from multiprocessing import Pool, cpu_count
from os.path import isfile
from pylab import *
from scipy.misc import imsave, toimage
from _routines import ffi, lib

sample_multiplier = 128

def iterate(args):
    seed, zoom = args
    lib.srand(seed)
    width = 640
    height = 480
    buf = ffi.new("double[]", width * height)
    iterations = 5000
    samples = 100000 * sample_multiplier
    # x, y = -0.6499808115557543, -0.47773981772389296
    # zoom = 7.2

    x, y = 0.3211629613494776,-0.03713232439656387
    # zoom = 11.5
    lib.buddhabrot(buf, width, height, x, y, zoom, x, y, zoom + 1, iterations, samples)
    im = array(list(buf)).reshape(height, width)
    return im


if __name__ == '__main__':
    pool_size = cpu_count()
    print "Using {} cores to render a Buddhabrot...".format(pool_size)
    pool = Pool(pool_size)

    num_frames = 100
    normalizer = 100 * sample_multiplier
    brightness = 1
    initial_zoom = -1.5
    final_zoom = 15
    for i in range(num_frames):
        if isfile("terminate.txt"):
            print "Terminating..."
            break

        t = i / num_frames
        zoom = initial_zoom + t * (final_zoom - initial_zoom)
        ims = pool.map(iterate, zip(range(pool_size), [zoom] * pool_size))
        im = ims[0]
        for im_ in ims[1:]:
            im += im_
        im *= 20 ** t
        print im.max()
        # imshow(im, interpolation="none", cmap="gray")
        # show()
        filename = "frames/out_%03d.png" % i
        toimage(im, cmin=0, cmax=normalizer).save(filename)
        print "Frame %03d done." % i
