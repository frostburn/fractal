from cffi import FFI

ffibuilder = FFI()

ffibuilder.cdef(
    "void srand(unsigned int seed);"
    "int mandelbrot(double *out, size_t width, size_t height, double center_x, double center_y, double zoom);"
    "int buddhabrot(double *out, size_t width, size_t height, double center_x, double center_y, double zoom, double spot_x, double spot_y, double spot_zoom, double source_x, double source_y, double source_zoom, size_t iterations, size_t samples);"
)

ffibuilder.set_source(
    "_routines",
    """
    int escape_time(double cx, double cy) {
        double x_ = 0;
        double y  = 0;
        for (int i = 0; i < 10000; i++) {
            double x = x_;
            if (x*x + y*y > 128) {
                return i;
            }
            x_ = x*x - y*y + cx;
            y  = 2 * x*y + cy;
        }
        return 10000;
    }

    double gauss(void) {
        double r = 0;
        for (int i = 0; i < 12; i++) {
            r += rand();
        }
        return r / RAND_MAX - 6;
    }

    int mandelbrot(double *out, size_t width, size_t height, double center_x, double center_y, double zoom) {
        zoom = pow(2, -zoom) / height;
        for (size_t i = 0; i < width * height; i++) {
            double x = (i % width);
            double y = (i / width);
            x = (2 * x - width) * zoom + center_x;
            y = (2 * y - height) * zoom + center_y;

            out[i] = escape_time(x, y);
        }
        return 0;
    }

    int buddhabrot(double *out, size_t width, size_t height, double center_x, double center_y, double zoom, double spot_x, double spot_y, double spot_zoom, double source_x, double source_y, double source_zoom, size_t iterations, size_t samples) {
        zoom = pow(2, zoom) * height;
        spot_zoom = pow(2, -spot_zoom);
        source_zoom = pow(2, -source_zoom);
        for (size_t i = 0; i < width * height * 3; i++) {
            out[i] = 0;
        }

        double* trajectory = malloc(sizeof(double) * 2 * iterations);
        for (size_t j = 0; j < samples; j++) {
            double cx = gauss() * spot_zoom + spot_x;
            double cy = gauss() * spot_zoom + spot_y;
            double x_ = gauss() * source_zoom + source_x;
            double y  = gauss() * source_zoom + source_y;
            size_t i;
            for (i = 0; i < iterations; i++) {
                double x = x_;
                x_ = x*x - y*y + cx;
                y  = 2 * x*y + cy;
                trajectory[2*i + 0] = x_;
                trajectory[2*i + 1] = y;

                if (x_*x_ + y*y > 128) {
                    break;
                }
            }
            if (x_*x_ + y*y > 128) {
                for (size_t k = 0; k < i; k++) {
                    x_ = trajectory[2*k + 0];
                    y  = trajectory[2*k + 1];
                    double index_x = (x_ - center_x) * zoom + width  * 0.5;
                    double index_y = (y  - center_y) * zoom + height * 0.5;
                    if (index_x >= 0 && index_x < width && index_y >= 0 && index_y < height) {
                        double *red   = out + 0 + 3 * ((int)index_x + ((int)index_y) * width);
                        double *green = out + 1 + 3 * ((int)index_x + ((int)index_y) * width);
                        double *blue  = out + 2 + 3 * ((int)index_x + ((int)index_y) * width);
                        double r = 0;
                        double g = 0;
                        double b = 0;
                        if (k % 3 == 0) {
                            r += 1;
                        }
                        else if (k % 3 == 1) {
                            g += 1;
                        }
                        else {
                            b += 1;
                        }
                        r += 0.3 * ((k + 1) % 5);
                        g += 0.1 * (k % 7);
                        b += 0.2 * (k % 11);

                        r *= tanh(k * 0.007);
                        g *= tanh(k * 0.01);
                        b *= tanh(k * 0.02);

                        *red += r;
                        *green += g;
                        *blue += b;
                    }
                }
            }
        }
        free(trajectory);
        return 0;
    }
    """
)

if __name__ == '__main__':
    ffibuilder.compile(verbose=True)
