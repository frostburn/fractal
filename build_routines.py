from cffi import FFI

ffibuilder = FFI()

ffibuilder.cdef(
    "void srand(unsigned int seed);"
    "int mandelbrot(double *out, size_t width, size_t height, double center_x, double center_y, double zoom);"
    "int buddhabrot(double *out, size_t width, size_t height, double center_x, double center_y, double zoom, double spot_x, double spot_y, double spot_zoom, double source_x, double source_y, double source_zoom, size_t iterations, size_t samples, int interior);"
    "int buddhabulb(double *out, size_t width, size_t height, double center_x, double center_y, double center_z, double zoom, double spot_x, double spot_y, double spot_z, double spot_zoom, double source_x, double source_y, double source_z, double source_zoom, size_t iterations, size_t samples);"
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

    int buddhabrot(double *out, size_t width, size_t height, double center_x, double center_y, double zoom, double spot_x, double spot_y, double spot_zoom, double source_x, double source_y, double source_zoom, size_t iterations, size_t samples, int interior) {
        zoom = pow(2, zoom) * height;
        spot_zoom = pow(2, -spot_zoom);
        source_zoom = pow(2, -source_zoom);
        double x_shift = 0.5 * width  - center_x * zoom;
        double y_shift = 0.5 * height - center_y * zoom;
        for (size_t i = 0; i < width * height * 3; i++) {
            out[i] = 0;
        }

        double* trajectory = malloc(sizeof(double) * 2 * iterations);
        for (size_t j = 0; j < samples; j++) {
            double cx = gauss() * spot_zoom + spot_x;
            double cy = gauss() * spot_zoom + spot_y;
            double x = gauss() * source_zoom + source_x;
            double y = gauss() * source_zoom + source_y;
            double xsqr = x*x;
            double ysqr = y*y;
            size_t i;
            for (i = 0; i < iterations; i++) {
                y = 2*x*y + cy;
                x = xsqr - ysqr + cx;
                trajectory[2*i + 0] = x;
                trajectory[2*i + 1] = y;

                xsqr = x*x;
                ysqr = y*y;
                if (xsqr + ysqr > 128) {
                    break;
                }
            }
            if (interior || xsqr + ysqr > 128) {
                for (size_t k = 0; k < i; k++) {
                    x = trajectory[2*k + 0];
                    y = trajectory[2*k + 1];
                    double index_x = x * zoom + x_shift;
                    double index_y = y * zoom + y_shift;
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

    int buddhabulb(
        double *out, size_t width, size_t height,
        double center_x, double center_y, double center_z, double zoom,
        double spot_x, double spot_y, double spot_z, double spot_zoom,
        double source_x, double source_y, double source_z, double source_zoom,
        size_t iterations, size_t samples
    ) {
        zoom = pow(2, zoom) * height;
        spot_zoom = pow(2, -spot_zoom);
        source_zoom = pow(2, -source_zoom);
        double x_shift = 0.5 * width  - center_x * zoom;
        double y_shift = 0.5 * height - center_y * zoom;
        for (size_t i = 0; i < width * height * 3; i++) {
            out[i] = 0;
        }

        for (size_t j = 0; j < samples; j++) {
            double cx = gauss() * spot_zoom + spot_x;
            double cy = gauss() * spot_zoom + spot_y;
            double cz = gauss() * spot_zoom + spot_z;

            double x = gauss() * source_zoom + source_x;
            double y = gauss() * source_zoom + source_y;
            double z = gauss() * source_zoom + source_z;
            for (size_t i = 0; i < iterations; i++) {
                double x2 = x*x;
                double y2 = y*y;
                double rxy = x2 + y2;
                // double r = rxy + z*z;  // For bailout.

                // Special case for n=6
                double x4 = x2 * x2;
                double x6 = x2 * x4;
                double y4 = y2 * y2;
                double y6 = y2 * y4;
                double z2 = z * z;
                double z4 = z2 * z2;
                if (rxy > 0.000001) {
                    double q = pow(rxy, -2.5);
                    y = 4*x*y*(3*x4 - 10*x2*y2 + 3*y4)*z*(x2 + y2 - 3*z2)*(3*(x2 + y2) - z2) * q + cy;
                    x = 2*(x6 - 15*x4*y2 + 15*x2*y4 - y6)*z*(x2 + y2 - 3*z2)*(3*(x2 + y2) - z2) * q + cx;
                }
                else {
                    y = cy;
                    x = cx;
                }
                z = -(rxy - z2)*(rxy * (rxy - 14*z2) + z4) + cz;

                if (i == 0) {
                    continue;
                }
                // TODO: Rotations that make the center coordinates matter.
                double index_x = (0.98 * x - 0.19 * z) * zoom + x_shift;
                double index_y = (0.19 * y + 0.98 * z) * zoom + y_shift;
                if (index_x >= 0 && index_x < width && index_y >= 0 && index_y < height) {
                    double *red   = out + 0 + 3 * ((int)index_x + ((int)index_y) * width);
                    double *green = out + 1 + 3 * ((int)index_x + ((int)index_y) * width);
                    double *blue  = out + 2 + 3 * ((int)index_x + ((int)index_y) * width);
                    double r = 0;
                    double g = 0;
                    double b = 0;
                    size_t i6 = i % 6;
                    if (i6 == 0) {
                        r += 1;
                    }
                    else if (i6 == 1) {
                        r += 0.5;
                        g += 0.5;
                    }
                    else if (i6 == 2) {
                        g += 1;
                    }
                    else if (i6 == 3) {
                        g += 0.5;
                        b += 0.5;
                    }
                    else if (i6 == 4) {
                        b += 1;
                    }
                    else {
                        b += 0.5;
                        r += 0.5;
                    }

                    double magnitude = log(1 + x*x + y*y + z*z);

                    r *= magnitude / (5.0 + i);
                    g *= magnitude / (4.0 + i);
                    b *= magnitude / (3.0 + i);
                    if (j == -1) {
                        printf("%g, %g, %g, %g\\n", magnitude, r, g, b);
                    }

                    *red += r;
                    *green += g;
                    *blue += b;
                }
            }
        }
        return 0;
    }
    """
)

if __name__ == '__main__':
    ffibuilder.compile(verbose=True)
