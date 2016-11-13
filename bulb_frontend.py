from __future__ import division
from multiprocessing import Pool, cpu_count
from os.path import isfile
from sys import exit
from pylab import *
from scipy.misc import imsave, toimage
from _routines import ffi, lib


BATCH_SIZE = 1000000 * 5


def iterate(args):
    seed, width, height, proj_xx, proj_yx, proj_zx, proj_xy, proj_yy, proj_zy, shift_x, shift_y, spot_x, spot_y, spot_z, spot_zoom, source_x, source_y, source_z, source_zoom, iterations, samples = args
    lib.srand(seed)
    buf = ffi.new("double[]", 3 * width * height)
    lib.buddhabulb(buf, width, height, proj_xx, proj_yx, proj_zx, proj_xy, proj_yy, proj_zy, shift_x, shift_y, spot_x, spot_y, spot_z, spot_zoom, source_x, source_y, source_z, source_zoom, iterations, samples)
    im = array(list(buf)).reshape(height, width, 3)
    return im


def iterate_parallel(width, height, proj_xx, proj_yx, proj_zx, proj_xy, proj_yy, proj_zy, shift_x, shift_y, spot_x, spot_y, spot_z, spot_zoom, source_x, source_y, source_z, source_zoom, iterations, samples):
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
            [proj_xx] * pool_size,
            [proj_yx] * pool_size,
            [proj_zx] * pool_size,
            [proj_xy] * pool_size,
            [proj_yy] * pool_size,
            [proj_zy] * pool_size,
            [shift_x] * pool_size,
            [shift_y] * pool_size,
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


def look_to_proj(look_from, look_at, up, zoom):
    look_from = array(look_from, dtype="double")
    look_at = array(look_at, dtype="double")
    up = array(up, dtype="double")
    zoom = pow(2, zoom)

    forward = look_at - look_from
    right = cross(forward, up)
    up = cross(right, forward)
    right *= zoom / sqrt(dot(right, right))
    up *= zoom / sqrt(dot(up, up))

    shift = -dot(array([right, up]), look_at)

    proj_x = tuple(right)
    proj_y = tuple(up)
    shift = tuple(shift)
    return proj_x + proj_y + shift


LOCATIONS_N7 = {
    "bulb_0": (0.75, 0.42, 0.37),
    "bulb_0_subbulb_0": (0.715, 0.3, 0.47),
}


def render_image():
    width = 192 * 10
    height = 108 * 10
    # width = 200
    # height = 200
    # width, height = height, width
    # proj_xx, proj_yx, proj_zx = (0.2, 0, 0)
    # proj_xy, proj_yy, proj_zy = (0, 0, 0.2)
    # shift_x, shift_y = (0, 0)
    x = 0.715
    y = 0.3
    z = 0.47
    look_from = (x, -2, z)
    #look_at = (1.4, 0.15, 0.5)
    look_at = (x, y, z)
    up = (0, 0, 1)
    # up = (0, 1, 0)
    zoom = 3.75
    proj_xx, proj_yx, proj_zx, proj_xy, proj_yy, proj_zy, shift_x, shift_y = look_to_proj(look_from, look_at, up, zoom)
    spot_x, spot_y, spot_z = look_at
    spot_zoom = zoom + 1.6
    # spot_zoom = float("inf")
    source_x = 0
    source_y = 0
    source_z = 0
    source_zoom = float("inf")
    # source_zoom = 0
    iterations = 6 * 6 + 1
    samples = BATCH_SIZE * 16 * 6
    im = iterate_parallel(
        width, height,
        proj_xx, proj_yx, proj_zx,
        proj_xy, proj_yy, proj_zy,
        shift_x, shift_y,
        spot_x, spot_y, spot_z, spot_zoom,
        source_x, source_y, source_z, source_zoom,
        iterations, samples,
    )
    # im = im.swapaxes(0, 1)
    pim = load("out.dump")
    im += pim
    im.dump("out.dump")
    print im.max(), im.mean()
    im /= im.max()
    im = im ** 0.5
    im *= 1.0
    im = tanh(exp(im) - 1)
    im /= im.max()

    imshow(im, interpolation="none", cmap="gray")
    show()
    toimage(im).save("out.tiff")


def render_animation():
    width = 854
    height = 480

    look_at = LOCATIONS_N7["bulb_0_subbulb_0"]
    up = (0, 0, 1)
    zoom = -1
    spot_x, spot_y, spot_z = look_at
    spot_zoom = 0
    # spot_zoom = float("inf")
    source_x = 0
    source_y = 0
    source_z = 0
    source_zoom = float("inf")
    # source_zoom = 0
    iterations = 4 * 6 + 1
    samples = BATCH_SIZE * 16
    brightness = 0.2

    accumulate = True

    num_frames = 100
    for n in range(num_frames):
        filename = "frames/out_%04d.tiff" % n
        dumpname = "frames/out_%04d.dump" % n
        if not accumulate and isfile(filename):
            print "Skipping frame %04d." % n
            continue
        # t = n / (num_frames - 1)
        t = n / num_frames
        phi = 2 * pi * t
        look_from = (sin(0.25 * phi), -cos(0.1 * phi), 0.2 + 0.1 * cos(0.2 * phi))
        zoom = 11 * t - 2
        spot_zoom = zoom + 1
        proj_xx, proj_yx, proj_zx, proj_xy, proj_yy, proj_zy, shift_x, shift_y = look_to_proj(look_from, look_at, up, zoom)
        im = iterate_parallel(
            width, height,
            proj_xx, proj_yx, proj_zx,
            proj_xy, proj_yy, proj_zy,
            shift_x, shift_y,
            spot_x, spot_y, spot_z, spot_zoom,
            source_x, source_y, source_z, source_zoom,
            iterations, samples,
        )
        if isfile("terminate.txt"):
            print "Terminating animation rendering..."
            exit()
        if accumulate and isfile(dumpname):
            print "Accumulating on previous frame %04d." % n
            pim = load(dumpname)
            im += pim
        im.dump(dumpname)
        im /= im.mean()
        im *= brightness
        im = im ** 0.5
        im = tanh(exp(im) - 1)
        toimage(im).save(filename)
        print "Frame %04d done." % n


if __name__ == '__main__':
    # render_image()
    render_animation()
