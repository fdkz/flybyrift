#import pyglet

from modules.pyrexopengl import *
from modules.pyrexopenglconstans import *

import vector
import coordinate_system


# Define a simple function to create ctypes arrays of floats:
#def vec(*args):
#    return (GLfloat * len(args))(*args)

#def vecl(lst):
#    return (GLfloat * len(lst))(*lst)


class Cube:

    def __init__(self):

        self.size  = 0.7 # halfsize
        self.color = (1., 0., 0.2, 1.)
        self.ocs   = coordinate_system.CoordinateSystem()

        self.parent = None
        self.children = []

        # normal list is a kludge. normal of the last quad vertex is used.
                                                                   # front   right    back      left     top     bottom
       # self.vertex_list = pyglet.graphics.vertex_list_indexed(8, [0,1,2,3, 1,5,6,2, 5,4,7,6, 3,7,4,0, 0,4,5,1, 3,2,6,7],
       #     ('v3f/static', (-1.,1.,-1.,  1.,1.,-1.,  1.,-1.,-1.,  -1.,-1.,-1.,  -1.,1.,1.,  1.,1.,1.,  1.,-1.,1.,  -1.,-1.,1.)),
       #     ('n3f/static', (-1.,0.,0.,   0.,1.,0.,   1.,0.,0.,    0.,0.,-1.,    2.,2.,2.,   2.,2.,2.,  0.,0.,1.,   0.,-1.,0.))
       # )

        # updated every frame from the outside
        self.target_ocs = coordinate_system.CoordinateSystem()


    def render_normal(self):
        return

        glPushMatrix()
        glPushAttrib(GL_ENABLE_BIT)

        r, g, b, a = self.color[0], self.color[1], self.color[2], self.color[3]
#        glMaterialfv(GL_FRONT, GL_AMBIENT,   vec(0., 0., 0., 1.))
#        glMaterialfv(GL_FRONT, GL_DIFFUSE,   vec(r,  g,  b,  1.))
#        glMaterialfv(GL_FRONT, GL_EMISSION,  vec(0.15, 0.15, 0.15, 1.))
#        glMaterialfv(GL_FRONT, GL_SPECULAR,  vec(0., 0., 0., 1.))
#        glMaterialfv(GL_FRONT, GL_SHININESS, 100.)
#        glMaterialfv(GL_FRONT, GL_SHININESS, GLfloat(100.))
        glMaterialfv(GL_FRONT, GL_AMBIENT,   (0., 0., 0., 1.))
        glMaterialfv(GL_FRONT, GL_DIFFUSE,   (r,  g,  b,  1.))
        glMaterialfv(GL_FRONT, GL_EMISSION,  (0.15, 0.15, 0.15, 1.))
        glMaterialfv(GL_FRONT, GL_SPECULAR,  (0., 0., 0., 1.))
        glMaterialfv(GL_FRONT, GL_SHININESS, 100.)


        glColor3f(r, g, b) # works in case of glDisable(GL_LIGHTING)

        ocs = self.ocs
        glMultMatrixf(ocs.get_opengl_matrix2())

        s = self.size
        glScalef(s,s,s)

        # clockwise

        self.vertex_list.draw(pyglet.gl.GL_QUADS)

        # draw the axis(es? 's? s?)

        r = 2.

        glDisable(GL_LIGHTING)
        glLineWidth(4.)

        if 1:
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

        for c in self.children: c.render_normal()

        glPopMatrix()

