# a gimbal plus the chopper itself

import math
from math import degrees, radians, sin, cos, atan2, asin
import random

#from modules.pyrexopengl import *
#from modules.pyrexopenglconstans import *

import vector
import axial_frame
import coordinate_system

from OpenGL.GL import *


import cube
import cubes_vbo



# Define a simple function to create ctypes arrays of floats:
def vec(*args):
    return list(args)
    #return (c_float * len(args))(*args)

#def vecl(lst):
#    return (GLfloat * len(lst))(*lst)

# set_imu_ocs(
# set_abs_desired_camera_orientation(
# set_rel_desired_camera_orientation(
# set_camera_trackpoint(
# tick(

class Gimbal1:
    MODE_ABSOLUTE = 1 # tries to keep the camera steady in world-space
    MODE_RELATIVE = 2 # direct manual manipulation of gimbal motor angles
    MODE_TRACK    = 3 # keeps the camera pointed at the given world-coordinate
    MODE_RAW      = 4 # just take yaw/roll/pitch directly
    def __init__(self):

        self.mode = self.MODE_RAW

        self.ocs = coordinate_system.CoordinateSystem()
        self.camera_desired_orientation = axial_frame.AxialFrame()
        self.camera_trackpoint = vector.Vector()
        self.camera_trackpoint_normal = vector.Vector()

        # calculated motor angles
        self.yaw = 0.
        self.roll = 0.
        self.pitch = 0.

        cubes_lists, ocs_list = self._build_gimbal()
        cubes_yaw   = cubes_lists[0]
        cubes_roll  = cubes_lists[1]
        cubes_pitch = cubes_lists[2]
        self.ocs_yaw   = ocs_list[0]
        self.ocs_roll  = ocs_list[1]
        self.ocs_pitch = ocs_list[2]

        # vertex_lists = self._build_body()
        # self.vertex_lists_blade = vertex_lists[0]
        # self.vertex_lists_body  = vertex_lists[1]

        cubes_body = self._build_body()
        self.cubes_vbo_body = cubes_vbo.CubesVbo(len(cubes_body))
        self.cubes_vbo_body.update_cubes(0, cubes_body)

        self.cubes_vbo_yaw = cubes_vbo.CubesVbo(len(cubes_yaw))
        self.cubes_vbo_yaw.update_cubes(0, cubes_yaw)
        self.cubes_vbo_roll = cubes_vbo.CubesVbo(len(cubes_roll))
        self.cubes_vbo_roll.update_cubes(0, cubes_roll)
        self.cubes_vbo_pitch = cubes_vbo.CubesVbo(len(cubes_pitch))
        self.cubes_vbo_pitch.update_cubes(0, cubes_pitch)

        self.color = (1., 0., 0.2, 1.)

    def set_imu_ocs(self, ocs):
        self.ocs.set(ocs)

    def set_raw_orientation_angles(self, yaw, roll, pitch):
        self.yaw = yaw
        self.roll = roll
        self.pitch = pitch
        self.mode = self.MODE_RAW

    def set_abs_desired_camera_orientation(self, a_frame):
        self.camera_desired_orientation.set(a_frame)
        self.mode = self.MODE_ABSOLUTE

    def set_rel_desired_camera_orientation(self, a_frame):
        self.camera_desired_orientation.set(a_frame)
        self.mode = self.MODE_RELATIVE

    def set_camera_trackpoint(self, trackpoint, normal):
        self.camera_trackpoint.set(trackpoint)
        self.camera_trackpoint_normal.set(normal)
        self.mode = self.MODE_TRACK

    def _calc_gimbal_angles(self, gimbal_uav_aframe):

        # works if desired gimbal orient is not rolled near 90 degrees
        gxa = gimbal_uav_aframe.x_axis
        gza = gimbal_uav_aframe.z_axis

        yaw  = -atan2(gxa[0], gxa[2]) + radians(90.)
        roll = -asin(gxa[1])

        z_axis_without_pitch = vector.Vector((sin(-yaw), 0., cos(-yaw)))
        y_axis_without_pitch = gxa.cross(z_axis_without_pitch)

        pitch = atan2(y_axis_without_pitch.dot(gza), z_axis_without_pitch.dot(gza))

        return degrees(yaw), degrees(roll), degrees(pitch)


    def _build_blade(self, ofs):
        cubes = []

        blade_col = (.15,  .15,  .15,  1.)
        blade_len = 1.1
        blade_width = blade_len * 0.08
        blade_thickness = 0.008
        angle = random.uniform(0., 360.)

        # two tited halves of a quad-blade.
        c = cube.Cube(blade_len / 2., blade_thickness, blade_width)
        c.ocs.a_frame.rotate(c.ocs.a_frame.y_axis, angle)
        c.ocs.a_frame.rotate(c.ocs.a_frame.x_axis, 5.)
        c.ocs.pos.add(c.ocs.a_frame.x_axis * blade_len / 4.)
        c.ocs.pos.add(ofs)
        c.set_color_f(*blade_col)
        cubes.append(c)

        c = cube.Cube(blade_len / 2., blade_thickness, blade_width)
        c.ocs.a_frame.rotate(c.ocs.a_frame.y_axis, angle)
        c.ocs.a_frame.rotate(c.ocs.a_frame.x_axis, -5.)
        c.ocs.pos.add(c.ocs.a_frame.x_axis * -blade_len / 4.)
        c.ocs.pos.add(ofs)
        c.set_color_f(*blade_col)
        cubes.append(c)

        # two tited halves of a quad-blade. same as before, but rotated 90 degrees.
        c = cube.Cube(blade_len / 2., blade_thickness, blade_width)
        c.ocs.a_frame.rotate(c.ocs.a_frame.y_axis, angle - 90.)
        c.ocs.a_frame.rotate(c.ocs.a_frame.x_axis, 5.)
        c.ocs.pos.add(c.ocs.a_frame.x_axis * blade_len / 4.)
        c.ocs.pos.add(ofs)
        c.set_color_f(*blade_col)
        cubes.append(c)

        c = cube.Cube(blade_len / 2., blade_thickness, blade_width)
        c.ocs.a_frame.rotate(c.ocs.a_frame.y_axis, angle - 90.)
        c.ocs.a_frame.rotate(c.ocs.a_frame.x_axis, -5.)
        c.ocs.pos.add(c.ocs.a_frame.x_axis * -blade_len / 4.)
        c.ocs.pos.add(ofs)
        c.set_color_f(*blade_col)
        cubes.append(c)

        return cubes

    def _build_body(self):

        cubes = []

        # body
        c = cube.Cube(0.6, 0.03, 0.6)
        body_ocs = coordinate_system.CoordinateSystem()
        body_ocs.set(c.ocs)
        c.ocs.a_frame.rotate(c.ocs.a_frame.y_axis, 45.)
        c.set_color_f(.7,  .7,  .7,  1.)
        cubes.append(c)

        # support beams
        beam_len = 1.9
        beam_width = 0.05
        beam_color = (.1,  .1,  .1,  1.)
        c = cube.Cube(beam_len, beam_width, beam_width)
        beam1_ocs = c.ocs
        c.set_color_f(*beam_color)
        cubes.append(c)

        c = cube.Cube(beam_len, beam_width, beam_width)
        c.ocs.a_frame.rotate(c.ocs.a_frame.y_axis, 90.)
        c.set_color_f(*beam_color)
        cubes.append(c)

        beam_len = 1.9
        blade_yofs = 0.1

        # blades
        cubes += self._build_blade( body_ocs.a_frame.x_axis * beam_len * 0.5 + c.ocs.a_frame.y_axis * blade_yofs)
        cubes += self._build_blade(-body_ocs.a_frame.x_axis * beam_len * 0.5 + c.ocs.a_frame.y_axis * blade_yofs)
        cubes += self._build_blade( body_ocs.a_frame.z_axis * beam_len * 0.5 + c.ocs.a_frame.y_axis * blade_yofs)
        cubes += self._build_blade(-body_ocs.a_frame.z_axis * beam_len * 0.5 + c.ocs.a_frame.y_axis * blade_yofs)

        return cubes

    def _build_gimbal(self):

        scale = 0.5

        # yaw platform
        ocs_yaw = coordinate_system.CoordinateSystem()
        s  = .05 * scale # pipe base radius
        h = .5 * scale

        gimbal_color = (1., 0., 0.2, 1.)

        cubes_yaw = [self._gen_box(-s, s, -s,  s, -h-s, s)]
        for c in cubes_yaw:
            c.set_color_f(*gimbal_color)

        # roll platform (top view)

        #       0    x1
        #       |    |
        #  O    |    O--z2
        #  O    |    O
        #  O    |    O
        #  OOOOOOOOOOO--z1
        #       O
        #       O-------0
        #

        ocs_roll = coordinate_system.CoordinateSystem()
        ocs_roll.pos.set((0., -h, 0.))

        s1 = s*.8; s2 = s; s3 = s*.9
        x1 = .5 * scale; z1 = .2 * scale; z2 = z1 + .5 * scale
        cubes_roll = [
            self._gen_box(   -s1,  s1,   -s1,      s1,  -s1, z1+s1), #   0 .. z1
            self._gen_box(-x1-s2,  s2, z1-s2,   x1+s2,  -s2, z1+s2), # -x1 .. x1
            self._gen_box(-x1-s3,  s3, z1+s3,  -x1+s3,  -s3, z2+s3), #  z1 .. z2 (left)
            self._gen_box( x1-s3,  s3, z1+s3,   x1+s3,  -s3, z2+s3)] #  z1 .. z2 (right)
        for c in cubes_roll:
            c.set_color_f(*gimbal_color)

        # pitch platform (top view)

        #         0   x1 x2
        #         |   |  |
        #     OOOOOOOOO--|--z1
        #     O       O  |
        #  OOOO       OOOO--0
        #     O       O
        #     OOOOOOOOO
        #

        ocs_pitch = coordinate_system.CoordinateSystem()
        ocs_pitch.pos.set((0., 0., z2))

        s1 = s*.3 # pole radius
        s2 = s*.4 # platform thickness
        x2 = x1; x1 = x1*.8; z1 = (z2-z1)*.8
        cubes_pitch = [
            self._gen_box( -x2-s1, s1, -s1,  x2+s1, -s1, s1), # pole
            self._gen_box(    -x1, s2, -z1,     x1, -s2, z1)] # platform
        for c in cubes_pitch:
            c.set_color_f(*gimbal_color)

        return (cubes_yaw, cubes_roll, cubes_pitch), (ocs_yaw, ocs_roll, ocs_pitch)

    def _rotate_motors_to(self, yaw, roll, pitch):
        self.ocs_yaw.a_frame.reset()
        self.ocs_yaw.a_frame.rotate(self.ocs_yaw.a_frame.y_axis, yaw)
        self.ocs_roll.a_frame.reset()
        self.ocs_roll.a_frame.rotate(self.ocs_roll.a_frame.z_axis, roll)
        self.ocs_pitch.a_frame.reset()
        self.ocs_pitch.a_frame.rotate(self.ocs_pitch.a_frame.x_axis, pitch)

    def _gen_box(self, x1, y1, z1, x2, y2, z2):
        """ x1, y1, z1 - top-left-close point. x2, y2, z2 - bottom-right-far point """
        assert x2>x1 and y1>y2 and z2>z1, "%f %f %f %f %f %f" % (x1, x2, y1, y2, z1, z2)

        c = cube.Cube(x2 - x1, y1 - y2, z2 - z1)
        c.ocs.pos.add(((x1 + x2) / 2., (y1 + y2) / 2., (z1 + z2) / 2.))
        return c

        # normal list is a kludge. normal of the last quad vertex is used.
        # vl = pyglet.graphics.vertex_list_indexed(8,
        #     # front   right    back      left     top     bottom
        #     [0,1,2,3, 1,5,6,2, 5,4,7,6, 3,7,4,0, 0,4,5,1, 3,2,6,7],
        #     ('v3f/static', (x2,y1,z2,  x1,y1,z2,  x1,y2,z2,  x2,y2,z2,  x2,y1,z1,  x1,y1,z1,  x1,y2,z1,  x2,y2,z1)),
        #     ('n3f/static', (1,0,0,  0,1,0,  -1,0,0,  0,0,1,  2,2,2,  2,2,2,  0,0,-1,  0,-1,0)))
        #     #('n3f/static', (-1,0,0,  0,1,0,  1,0,0,  0,0,-1,  2,2,2,  2,2,2,  0,0,1,  0,-1,0)))
        # return vl

    # def _gen_box_center(self, x, y, z, xs, ys, zs):
    #     """ generate a box given its center pos and dimensions """
    #     xs *= .5; ys *= .5; zs *= .5
    #     vl = [-xs,ys,-zs,  xs,ys,-zs,  xs,-ys,-zs,  -xs,-ys,-zs,  -xs,ys,zs,  xs,ys,zs,  xs,-ys,zs,  -xs,-ys,zs]
    #     vl = [d + [x,y,z][i%3] for i, d in enumerate(vl)]
    #     # normal list is a kludge. normal of the last quad vertex is used.
    #     vl = pyglet.graphics.vertex_list_indexed(8,
    #         # front   right    back      left     top     bottom
    #         [0,1,2,3, 1,5,6,2, 5,4,7,6, 3,7,4,0, 0,4,5,1, 3,2,6,7],
    #         ('v3f/static', vl),
    #         ('n3f/static', (-1,0,0,  0,1,0,  1,0,0,  0,0,-1,  2,2,2,  2,2,2,  0,0,1,  0,-1,0)))
    #     return vl

    def tick(self, dt):
        if self.mode == self.MODE_RAW:
            pass
        elif self.mode == self.MODE_ABSOLUTE:
            gimbal_rel_aframe = self.ocs.a_frame.proj_in(self.camera_desired_orientation)
            self.yaw, self.roll, self.pitch = self._calc_gimbal_angles(gimbal_rel_aframe)
        elif self.mode == self.MODE_RELATIVE:
            self.yaw, self.roll, self.pitch = self._calc_gimbal_angles(self.camera_desired_orientation)
        elif self.mode == self.MODE_TRACK:
            viewdirection = self.camera_trackpoint - self.ocs.pos
            self.camera_desired_orientation.look_direction2(viewdirection, self.camera_trackpoint_normal)
            self.yaw, self.roll, self.pitch = self._calc_gimbal_angles(self.camera_desired_orientation)

        self._rotate_motors_to(self.yaw, self.roll, self.pitch)

    def render(self):

#        return
        r, g, b, a = self.color[0], self.color[1], self.color[2], self.color[3]
        # if glColorMaterial is set to GL_AMBIENT_AND_DIFFUSE, then these GL_AMBIENT and GL_DIFFUSE here have no
        # effect, because the ambient and diffuse values are being taken from vertices themselves.
        #glMaterialfv(GL_FRONT, GL_AMBIENT,   (GLfloat*4)(.0, .0, .0, 1.))
        #glMaterialfv(GL_FRONT, GL_DIFFUSE,   (GLfloat*4)(1., .1, 1., 1.)) # has no effect if using GL_COLOR_MATERIAL

        glMaterialfv(GL_FRONT, GL_AMBIENT,   vec(0.1, 0.1, 0.1, 1.))
        glMaterialfv(GL_FRONT, GL_DIFFUSE,   vec(1.,  1.,  1.,  1.))
#        glMaterialfv(GL_FRONT, GL_DIFFUSE,   vec(r,  g,  b,  1.))
        glMaterialfv(GL_FRONT, GL_EMISSION,  vec(0., 0., 0., 1.))
        #glMaterialfv(GL_FRONT, GL_EMISSION,  vec(0., 0., 0., 1.))
        glMaterialfv(GL_FRONT, GL_SPECULAR,  vec(0., 0., 0., 1.))
        glMaterialf(GL_FRONT, GL_SHININESS, 100.)

#        glMaterialfv(GL_FRONT, GL_SPECULAR,  (GLfloat*4)( .2,  .2,  .2, 1.))
#        glMaterialfv(GL_FRONT, GL_SHININESS, (GLfloat)(30.))

#        glColor4f(r, g, b, a) # works in case of glDisable(GL_LIGHTING)

        glColor4f(0., 0., 0., 0.) # works in case of glDisable(GL_LIGHTING)

        glPushMatrix()
        glMultMatrixf(self.ocs.get_opengl_matrix2())
        #GL.glMaterialfv(GL.GL_FRONT, GL.GL_DIFFUSE,   vec(.9,  .9,  .9,  1.))

        self.cubes_vbo_body.render()

        #for v in self.vertex_lists_body: v.draw(pyglet.gl.GL_QUADS)

        # glPushMatrix()
        # glMaterialfv(GL_FRONT, GL_DIFFUSE,   vec(.2,  .2,  .2,  1.))
        # glRotatef(45., 0., 1., 0.)
        # for v in self.vertex_lists_blade: v.draw(pyglet.gl.GL_QUADS)
        # glTranslatef(0., 0.01, 0.)
        # glRotatef(90., 0., 1., 0.)
        # for v in self.vertex_lists_blade: v.draw(pyglet.gl.GL_QUADS)
#        glPopMatrix()



#        return
        r, g, b, a = self.color[0], self.color[1], self.color[2], self.color[3]
        # glMaterialfv(GL_FRONT, GL_AMBIENT,   vec(0., 0., 0., 1.))
        # glMaterialfv(GL_FRONT, GL_DIFFUSE,   vec(r,  g,  b,  1.))
        # glMaterialfv(GL_FRONT, GL_EMISSION,  vec(0.15, 0.15, 0.15, 1.))
        # glMaterialfv(GL_FRONT, GL_SPECULAR,  vec(0., 0., 0., 1.))
        # glMaterialf(GL_FRONT, GL_SHININESS, 100.)

        #glColor4f(r, g, b, a) # works in case of glDisable(GL_LIGHTING)

        # glPushMatrix()
        # glMultMatrixf2(self.ocs.get_opengl_matrix2())
        # glMaterialfv(GL_FRONT, GL_DIFFUSE,   vec(.9,  .9,  .9,  1.))
        # for v in self.vertex_lists_body: v.draw(pyglet.gl.GL_QUADS)

        # glPushMatrix()
        # glMaterialfv(GL_FRONT, GL_DIFFUSE,   vec(.2,  .2,  .2,  1.))
        # glRotatef(45., 0., 1., 0.)
        # for v in self.vertex_lists_blade: v.draw(pyglet.gl.GL_QUADS)
        # glTranslatef(0., 0.01, 0.)
        # glRotatef(90., 0., 1., 0.)
        # for v in self.vertex_lists_blade: v.draw(pyglet.gl.GL_QUADS)
        # glPopMatrix()

        if 1:
            glPushMatrix()
            glMultMatrixf(self.ocs_yaw.get_opengl_matrix2())
            glMaterialfv(GL_FRONT, GL_DIFFUSE,   vec(r,  g,  b,  1.))
            #for v in self.vertex_lists_yaw: v.draw(pyglet.gl.GL_QUADS)
            self.cubes_vbo_yaw.render()
            #self._draw_axis(2.)

            if 1:
                glPushMatrix()
                glMultMatrixf(self.ocs_roll.get_opengl_matrix2())
                #for v in self.vertex_lists_roll: v.draw(pyglet.gl.GL_QUADS)
                self.cubes_vbo_roll.render()
                #self._draw_axis(2.)

                if 1:
                    glPushMatrix()
                    glMultMatrixf(self.ocs_pitch.get_opengl_matrix2())
                    #for v in self.vertex_lists_pitch: v.draw(pyglet.gl.GL_QUADS)
                    self.cubes_vbo_pitch.render()
                    self._draw_axis_engineers(1.)

                    glPopMatrix()
                glPopMatrix()
            glPopMatrix()
        glPopMatrix()

    def _draw_axis(self, r):
        glPushAttrib(GL_ENABLE_BIT)
        glDisable(GL_LIGHTING)
        glLineWidth(4.)
        glBegin(GL_LINES)
        # x-axis. red
        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(0., 0., 0.)
        glVertex3f( r, 0., 0.)
        # y-axis. green
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(0., 0., 0.)
        glVertex3f(0.,  r, 0.)
        # z-axis. blue
        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(0., 0., 0.)
        glVertex3f(0., 0.,  r)
        glEnd()
        glPopAttrib()

    def _draw_axis_engineers(self, r):
        """ x (red) is forward, y (green) is left, z (blue) is up """
        glPushAttrib(GL_ENABLE_BIT)
        glDisable(GL_LIGHTING)
        glLineWidth(2.)
        glBegin(GL_LINES)
        # x-axis. red
        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(0., 0., 0.)
        glVertex3f(0., 0.,  r)
        # y-axis. green
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f( 0., 0., 0.)
        glVertex3f(-r, 0., 0.)
        # z-axis. blue
        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(0., 0., 0.)
        glVertex3f(0.,  r, 0.)
        glEnd()
        glPopAttrib()
