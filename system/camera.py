
import math

import OpenGL
from OpenGL.GL import *

import coordinate_system
import vector


class Camera:
    """
    camera = Camera()
    camera.mode = Camera.ORTHOGONAL
    camera.set_window_size(800, 600)

    camera.set_opengl_projection()
    .. draw 3d stuff ..

    camera.set_opengl_pixel_projection()
    sx, sy, sz = camera.screenspace(vector)
    .. draw text/icons at pixel (sx, sy) with depth sz ..

    -----------------------

    forward-z should be positive, unlike in opengl.. methods like
    screenspace, window_ray.. may not work otherwise. don't know.
    """

    ORTHOGONAL  = 1 # screen center is (0, 0)
    PERSPECTIVE = 2

    def __init__(self):

        self.mode = self.PERSPECTIVE
        self.ocs  = coordinate_system.CoordinateSystem()

        self.pixel_aspect_w_h = 1.

        #--------------------
        # read-only from here
        #--------------------

        self.fovx   = 80.
        self.fovy   = 80.

        self.orthox = 5000. # window width in opengl units
        self.orthoy = 5000.

        self.z_near = 50.
        self.z_far  = 500. * 1000.

        self.w_pixels = 1
        self.h_pixels = 1

        self._tanfovx_2 = 0.
        self._tanfovy_2 = 0.
        self.set_fovx(self.fovx)
        self.set_fovy(self.fovy)


    def set_window_size(self, w_pixels, h_pixels):

        self.w_pixels = float(w_pixels)
        self.h_pixels = float(h_pixels)


    def set_pixel_aspect(self, pixel_aspect_w_h = 1.):

        self.pixel_aspect_w_h = float(pixel_aspect_w_h)


    def set_z(self, z_near = 50., z_far = 500 * 1000.):

        self.z_near = float(z_near)
        self.z_far  = float(z_far)


    def set_fovx(self, fovx):

        self.fovx = fovx
        self._tanfovx_2 = math.tan(math.radians(self.fovx / 2.))


    def set_fovy(self, fovy):

        self.fovy = fovy
        self._tanfovy_2 = math.tan(math.radians(self.fovy / 2.))


    def update_fovx(self):
        """
        keep fovy and orthoy as they are and recalculate fovx and orthox
        according to window size and pixel aspect ratio.
        """

        physical_window_w_h = self.w_pixels / self.h_pixels * self.pixel_aspect_w_h

        self._tanfovx_2 = self._tanfovy_2 * physical_window_w_h
        self.fovx       = math.degrees(2. * math.atan(self._tanfovx_2))
        self.orthox     = self.orthoy * physical_window_w_h


    def update_fovy(self):

        physical_window_w_h = self.w_pixels / self.h_pixels * self.pixel_aspect_w_h

        self._tanfovy_2 = self._tanfovx_2 / physical_window_w_h
        self.fovy       = math.degrees(2. * math.atan(self._tanfovy_2))
        self.orthoy     = self.orthox / physical_window_w_h


    def set_orthox(self, orthox):

        self.orthox = orthox


    def set_orthoy(self, orthoy):

        self.orthoy = orthoy


    def set_opengl_projection(self):
        """
        setup opengl projection matrix with camera settings
        """

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        if self.mode == self.ORTHOGONAL:

            glOrtho(-self.orthox / 2., self.orthox / 2., \
                    -self.orthoy / 2., self.orthoy / 2., self.z_near, self.z_far)

        elif self.mode == self.PERSPECTIVE:

            #gluPerspective(self.fovy, self._tanfovx_2 / self._tanfovy_2, self.z_near, self.z_far)
            glFrustum(-self.z_near * self._tanfovx_2, self.z_near * self._tanfovx_2, -self.z_near * self._tanfovy_2, self.z_near * self._tanfovy_2, self.z_near, self.z_far)


    def set_opengl_pixel_projection(self, z_near = None, z_far = None):
        """
        top-left is (0, 0). (top-left tip of the top-left pixel)
        """

        if z_near is None: z_near = self.z_near
        if z_far  is None: z_far  = self.z_far

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        glOrtho(0., self.w_pixels, self.h_pixels, 0., z_near, z_far)


    def look_direction(self, direction_vector, up_hint_vector):
        """
        turn camera to look in direction_vector, up points to
        up_hint_vector.
        """

        self.ocs.a_frame.look_direction2(direction_vector, up_hint_vector)


    def screenspace(self, vect):
        """ 
        NB! beware that vect.z has to be positive ( vect[2] > 0 )

        return values for current projection mode.. (doesn't have to
        be the same as self.mode)

        project vect (has to be already in camera-space) to screen-space
        return: (0, 0, z) in pixels. up-left of the given window

        the returned z: vect.z if the camera is in orthogonal projection
        mode. if in perspective mode, return modified vect.z that generates
        the same z-buffer values in pixel-projection that vect.z would
        generate in perspective projection mode.

        (glOrtho & glFrustum (gluPerspective) use z-buffer differently)

        """

        if self.mode == self.ORTHOGONAL:

            return  self.w_pixels / self.orthox * vect[0] + self.w_pixels / 2., \
                   -self.h_pixels / self.orthoy * vect[1] + self.h_pixels / 2., vect[2]

        elif self.mode == self.PERSPECTIVE:

            sx =  vect[0] * (self.w_pixels / 2.) / vect[2] / self._tanfovx_2 + self.w_pixels / 2.
            sy = -vect[1] * (self.h_pixels / 2.) / vect[2] / self._tanfovy_2 * self.pixel_aspect_w_h + self.h_pixels / 2.
            sz = self.z_far + self.z_near - self.z_far * self.z_near / vect[2]
            if vect[2] < 0.: sz = -sz
            return sx, sy, sz


    def screenspace_z(self, z):
        """
        return only the z-component of self.screenspace(..)
        z has to be positive, greater than zero, here!
        """

        if self.mode == self.ORTHOGONAL:
            return z
        elif self.mode == self.PERSPECTIVE:
            return self.z_far + self.z_near - self.z_far * self.z_near / z


    def window_ray(self, x, y):
        """
        return a ray that goes through the given pixel-coordinate,
        in camera-space. NOT normalized.

        return: start, direction (vectors. world-space coordinates)
                ("start" is necessary in case of orthogonal projection)
        """

        if self.mode == self.ORTHOGONAL:

            # TODO: untested
            xx = self.orthox * (float(x) / self.w_pixels - .5)
            yy = self.orthoy * (float(y) / self.h_pixels - .5)

            return vector.Vector((xx, -yy, 0.)), vector.Vector((0., 0., 1.))

        elif self.mode == self.PERSPECTIVE:

            w, h = self.w_pixels, self.h_pixels
            #  TODO: aspect ratio.. or already in tanfov*?
            xx = x - w / 2.
            yy = (y - h / 2.) * w / h * self._tanfovy_2 / self._tanfovx_2
            zz = w / 2. / self._tanfovx_2

            return vector.Vector(), vector.Vector((xx, -yy, zz))

        return None, None


    def get_ocs_to(self, dest_object = None):
        """
        TODO: move this to object3d subclass. and make it work with hierarchies deeper than 1 :)
        return an ocs where projv_out projects vectors into dest_object space.
        dest_object None is the root object. the purest world-space there is..
        """

        assert dest_object == None, "not implemented :("

        ocs = coordinate_system.CoordinateSystem()
        ocs.set(self.ocs)
        return ocs
