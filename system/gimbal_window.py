import logging
logg = logging.getLogger(__name__)

import sys
import time

t = time.time()
import OpenGL
from OpenGL import GL
logg.info("import duration: %.2f seconds (PyOpenGL)", time.time() - t)
#OpenGL.FULL_LOGGING = True
logg.info("PyOpenGL version %s", OpenGL.__version__)

t = time.time()
from sdl2 import *
logg.info("import duration: %.2f seconds (sdl2)", time.time() - t)

t = time.time()
import ctypes
logg.info("import duration: %.2f seconds (ctypes)", time.time() - t)

t = time.time()
from modules.pyrexopengl import *
from modules.pyrexopenglconstans import *
logg.info("import duration: %.2f seconds (pyrexopengl)", time.time() - t)

t = time.time()
import modules.gltext as gltext
logg.info("import duration: %.2f seconds (gltext)", time.time() - t)
t = time.time()
import gimbal1
logg.info("import duration: %.2f seconds (gimbal)", time.time() - t)
t = time.time()
import vector
import coordinate_system
import axial_frame
import camera
import cube2
import fps_counter
import vbo
logg.info("import duration: %.2f seconds (other)", time.time() - t)

#from pyglet.gl import *
#import pyglet.gl


# Define a simple function to create ctypes arrays of floats:
#def vec(*args):
#    return (GLfloat * len(args))(*args)
#
#def vecl(lst):
#    return (GLfloat * len(lst))(*lst)

def int16_to_float(int16):
    return int16 / 32768.


class GimbalWindow:
    # active object and active mode
    MODE_HELICOPTER      = 1
    MODE_GIMBAL_RELATIVE = 2
    MODE_GIMBAL_ABSOLUTE = 3

    def __init__(self, conf): #*args, **kwds):
        #super(CrabWindow, self).__init__()
        # TODO: is this better than this?:
        #window.Window.__init__(self, *args, **kwds)

        self.conf = conf

        self.joystick = None

    def init(self):

        self.mode = self.MODE_GIMBAL_ABSOLUTE
        #self._mode = self.MODE_GIMBAL_ABSOLUTE

#        self.keys = pyglet.window.key.KeyStateHandler()
#        self.push_handlers(self.keys)
#        self.exclusive_mouse = False

#        self.w, self.h = 0, 0
        self.camera = camera.Camera()
        # init camera ocs
        o = self.camera.ocs; a = o.a_frame
        o.pos.set([1.3386966254250741, 3.2763409412621058, 1.9619633593798795])
        a.x_axis.set([-0.80351677958418577, -2.4980018054066027e-16, 0.59528210533045522])
        a.y_axis.set([-0.37248195158463354, 0.78004500411750555, -0.50277926299224318])
        a.z_axis.set([-0.46434683230357221, -0.62572341457813496, -0.62677924963923115])

        self.fps_counter = fps_counter.FpsCounter()

        self.selected_obj = self.camera

        self.gimbal = gimbal1.Gimbal1()
        self.gimbal.ocs.pos.set((0., 2., 0.))


        self.suncube = cube2.Cube()
        dist = 100.
        self.suncube.ocs.pos.set((2.*dist, 5.*dist, 2.*dist))
        self.suncube.size = 0.1
        self.suncube.color = (1., 1., 0., 1.)

        # current orientation directly from joystick (or mouse or keyboard if no joystick is present).
        # converted to desired orientation and sent to gimbal.
        self.out_yaw   = 0.
        self.out_pitch = 0.
        self.out_roll  = 0.

        # for remembering what we wanted from the gimbal
        self.abs_yaw = self.abs_pitch = self.abs_roll = 0.
        self.rel_yaw = self.rel_pitch = self.rel_roll = 0.
        self.hel_yaw = self.hel_pitch = self.hel_roll = 0.

        self.gl_init()

        self.gltext = gltext.GLText("data/font_proggy_opti_small.txt")
        self.gltext.init()

        # under macosx snow leopard, a joystick object is returned even if no joystick is connected.
        # and that screws up rotations with the mouse/trackpad.
#        self.joystick = self.open_first_joystick()
        #self.joystick = None

        # take a screenshot every minute. but start at 10 seconds
        self._screenshot_call_counter = -1
#        if not hasattr(sys, "frozen"):
#            pyglet.clock.schedule_interval(self.save_autoscreenshot, 10.)


    def run(self):

        if SDL_Init(SDL_INIT_VIDEO|SDL_INIT_JOYSTICK) != 0:
            logg.error(SDL_GetError())
            return -1

        n = SDL_NumJoysticks()
        logg.info("num joysticks: %u" % (n))
        for i in range(n):
            logg.info("  %s%s" % (SDL_JoystickNameForIndex(i), " (gamecontroller)"*SDL_IsGameController(i)))

        joy = None
        if n:
            #j = SDL_GameControllerOpen(self.conf.joystick_index)
            #if not j:
            #    print("Could not open gamecontroller %i: %s" % (i, SDL_GetError()));

            joy = SDL_JoystickOpen(self.conf.joystick_index);

            if joy:
                logg.info("")
                logg.info("opened joystick %i (%s)" % (self.conf.joystick_index, SDL_JoystickName(joy)))
                logg.info("  num axes   : %d" % SDL_JoystickNumAxes(joy))
                logg.info("  num buttons: %d" % SDL_JoystickNumButtons(joy))
                logg.info("  num balls  : %d" % SDL_JoystickNumBalls(joy))
                logg.info("")
            else:
                logg.info("Could not open Joystick %i: %s" % (i, SDL_GetError()))

            self.joystick = joy

        SDL_GL_SetAttribute(SDL_GL_MULTISAMPLEBUFFERS, 1);
        SDL_GL_SetAttribute(SDL_GL_MULTISAMPLESAMPLES, 4);

        self.w = 800
        self.h = 600

        window = SDL_CreateWindow(b"OpenGL demo", SDL_WINDOWPOS_UNDEFINED,
                                  SDL_WINDOWPOS_UNDEFINED, self.w, self.h,
                                  SDL_WINDOW_OPENGL)
        if not window:
            logg.error(SDL_GetError())
            return -1

        context = SDL_GL_CreateContext(window)

        if SDL_GL_SetSwapInterval(-1):
            logg.error(SDL_GetError())
            if SDL_GL_SetSwapInterval(1):
                logg.error(SDL_GetError())
                logg.error("vsync failed completely. will munch cpu for lunch.")

        self.keys = SDL_GetKeyboardState(None)
        self.init()

        #SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR,
        #                     "Missing file",
        #                     "File is missing. Please reinstall the program.",
        #                     None);

        # get initial values
        if joy:
            roll_axis  = int16_to_float(SDL_JoystickGetAxis(joy, self.conf.joystick_roll_axis))
            pitch_axis = int16_to_float(SDL_JoystickGetAxis(joy, self.conf.joystick_pitch_axis))
        else:
            roll_axis  = 0.
            pitch_axis = 0.

        joy_axis_changed = True

        t = time.time()

        event = SDL_Event()
        running = True
        while running:
            while SDL_PollEvent(ctypes.byref(event)) != 0:
                if event.type == SDL_QUIT:
                    running = False

                if event.type == SDL_JOYAXISMOTION:
                    if event.jaxis.axis == self.conf.joystick_roll_axis:
                        joy_axis_changed = True
                        roll_axis = int16_to_float(event.jaxis.value)
                    elif event.jaxis.axis == self.conf.joystick_pitch_axis:
                        joy_axis_changed = True
                        pitch_axis = int16_to_float(event.jaxis.value)

                if event.type == SDL_JOYBUTTONDOWN:
                    logg.info("joy button %i pressed", event.jbutton.button)

                if event.type == SDL_KEYDOWN:
                    if event.key.keysym.scancode == SDL_SCANCODE_ESCAPE:
                        running = False

            if joy_axis_changed:
                logg.info("pitch %5.2f roll %5.2f" % (pitch_axis, roll_axis))
                joy_axis_changed = False

                self.out_yaw   = 0. # -self.joystick.x * 180.
                self.out_pitch = pitch_axis * 90.
                self.out_roll  = roll_axis * 90.

                self.gimbal.set_raw_orientation_angles(self.out_yaw, self.out_roll, self.out_pitch)
                self.rel_yaw, self.rel_pitch, self.rel_roll = self.out_yaw, self.out_pitch, self.out_roll

            last_t = t
            t = time.time()
            self.tick(t - last_t)

            #glFinish()
            SDL_GL_SwapWindow(window)
            #SDL_Delay(10)

        #if joy:
        #    if SDL_JoystickGetAttached(joy):
        #        SDL_JoystickClose(joy)

        SDL_GL_DeleteContext(context)
        SDL_DestroyWindow(window)
        SDL_Quit()
        logg.info("quit ok")
        return 0


    def close(self):
        pass


#    def _set_mode(self, mode):
#        self._mode = mode
#        self.out_yaw = self.out_pitch = self.out_roll = 0.
#    def _get_mode(self): return self._mode
#    mode = property(_get_mode, _set_mode)

    def open_first_joystick(self):
        joys = pyglet.input.get_joysticks()
        print "num joysticks: %i" % len(joys)
        for i, joy in enumerate(joys):
            print "trying joystick", i
            joy.open()
            if joy.buttons and len(joy.buttons) < 33:
                print "returning joystick.."
                return joy
            #joy.close() # Carbon error :S
        print "no suitable joysticks found"
        return None

        # find a joystick that says nothing to the stdout
        #old_write = sys.stdout.write
        #numchars = [0]
        #def new_write(t):
        #    numchars[0] += len(t)
        #    old_write("teehee: " + t)

        #for joy in pyglet.input.get_joysticks():
        #    try:
        #        print "trying joystick.."
        #        numchars[0] = 0
        #        sys.stdout.write = new_write
        #        joy.open()
        #        sys.stdout.write = old_write
        #        if numchars[0] == 0 and joy.buttons and len(joy.buttons) < 33:
        #            print "returning joystick.."
        #            return joy
        #        #joy.close() # Carbon error :S
        #    except:
        #        sys.stdout.write = old_write
        #        traceback.print_exc()
        #print "no joysticks found"
        #return None

    def gl_init(self):

        glShadeModel(GL_SMOOTH)
        glEnable(GL_POINT_SMOOTH)
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST);

        glEnable(GL_FOG)

#        glFogi(GL_FOG_MODE, GL_EXP2) # GL_EXP, GL_EXP2, GL_LINEAR
#        glFogfv(GL_FOG_COLOR, (.1, .1, .1, 1.))
        #glFogf(GL_FOG_DENSITY, .00008)
#        glFogf(GL_FOG_DENSITY, .000009)
#        glHint(GL_FOG_HINT, GL_DONT_CARE)
        #glEnable(GL_RESCALE_NORMAL)

        glDisable(GL_TEXTURE_2D)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_FOG)
        glDisable(GL_DITHER)
        glDisable(GL_LIGHTING)
        #glShadeModel(GL_FLAT)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)
        glDisable(GL_LINE_STIPPLE)
        glDisable(GL_LIGHT1)
        glFrontFace(GL_CW)
        glEnable(GL_CULL_FACE)

        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0., 0., 0., 1.))
        glLightModeli(GL_LIGHT_MODEL_LOCAL_VIEWER, 1)
        #glDisable(GL_COLOR_MATERIAL)


    def tick(self, dt):

        self.handle_controls(dt)
        self.gimbal.tick(dt)

        glClearColor(0.8, 0.8, 1.8, 1.0)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)

        glViewport(0, 0, self.w, self.h)

        self.camera.set_window_size(self.w, self.h)
        self.camera.set_z(.1, 1000.)
        self.camera.update_fovy()
        self.camera.set_opengl_projection()

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glScalef(1.,1.,-1.)

        camocs = self.camera.ocs
        ### project the world into camera space
        ##ocs = camera.ocs.proj_in( coordinate_system.CoordinateSystem() )
        ##glMultMatrixf(ocs.get_opengl_matrix2())
        glMultMatrixf(camocs.a_frame.get_opengl_matrix())
        glTranslated(-camocs.pos[0], -camocs.pos[1], -camocs.pos[2])

        glDisable(GL_TEXTURE_2D)

        # setup lighting
        lp = self.suncube.ocs.pos
        glLightfv(GL_LIGHT0, GL_POSITION, (lp[0], lp[1], lp[2], 1.))
        glLightfv(GL_LIGHT0, GL_AMBIENT,  (1., 1., 1., 1.))
        glLightfv(GL_LIGHT0, GL_DIFFUSE,  (1., 1., 1., 1.))
        glLightfv(GL_LIGHT0, GL_SPECULAR, (1., 1., 1., 1.))
        glEnable(GL_LIGHT0)


        # what the color value in vertex should be
        #glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glColorMaterial(GL_FRONT, GL_DIFFUSE)
        #glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)
        glEnable(GL_COLOR_MATERIAL)


        self.render_world()
        self.render_floor()

        self.camera.set_opengl_pixel_projection()
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glScalef(1.,1.,-1.)

        glDisable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)

        self.fps_counter.tick(dt)
        self.render_hud_text()

#        self.flip()

    def render_hud_text(self):

        y = 5.
        x = self.w - 6.
        t = self.gltext
        #t.drawtr(" manual offsets:", x, y, bgcolor=(1.0,1.0,1.0,.9), fgcolor=(0.,0.,0.,1.), z=100.); y+=t.height
        # if self.gimbal.mode != self.gimbal.MODE_TRACK:
        #     if self.gimbal.mode == self.gimbal.MODE_RELATIVE:
        #         s = "relative"
        #         yaw, pitch, roll = self.rel_yaw, self.rel_pitch, self.rel_roll
        #     if self.gimbal.mode == self.gimbal.MODE_ABSOLUTE:
        #         s = "absolute"
        #         yaw, pitch, roll = self.abs_yaw, self.abs_pitch, self.abs_roll
        #     t.drawtr(" desired (%s) camera orientation:" % s, x, y, fgcolor=(0.,0.,0.,1.), bgcolor=(1.0,1.0,1.0,.9), z=100.); y+=t.height
        #     t.drawtr(" yaw  : %6.1f  " % (yaw),   x, y, bgcolor=(.9,.9,.9,.9)); y+=t.height
        #     t.drawtr(" pitch: %6.1f  " % (pitch), x, y); y+=t.height
        #     t.drawtr(" roll : %6.1f  " % (roll),  x, y); y+=t.height
        y += t.height
        t.drawtr(" gimbal motor angles:", x, y, bgcolor=(1.0,1.0,1.0,.9), fgcolor=(0.,0.,0.,1.), z=100.); y+=t.height
        t.drawtr(" yaw  : %6.1f  " % (self.gimbal.yaw),   x, y, bgcolor=(.9,.9,.9,.9)); y+=t.height
        t.drawtr(" roll : %6.1f  " % (self.gimbal.roll),  x, y); y+=t.height
        t.drawtr(" pitch: %6.1f  " % (self.gimbal.pitch), x, y); y+=t.height
        #y += t.height
        #t.drawtr(" mode : %s " % s,  x, y); y+=t.height

        fgcolor     = (0.4,0.4,0.4,1.0); bgcolor     = (1.,1.,1.,.8)
        hifgcolor   = (0.0,0.0,0.0,1.0); hibgcolor   = (.65,.85,1.,.9)
        headfgcolor = (0.0,0.0,0.0,1.0); headbgcolor = (1.,1.,1.,.95)
        fgcolors = [fgcolor]*3; bgcolors = [bgcolor]*3
        i = [self.MODE_GIMBAL_RELATIVE, self.MODE_GIMBAL_ABSOLUTE, self.MODE_HELICOPTER].index(self.mode)
        fgcolors[i] = hifgcolor; bgcolors[i] = hibgcolor

        x, y = 5., 5.
        #t.drawtl(" select mode:                                         ", x, y, headfgcolor, headbgcolor, z=100.); y+=t.height
        #t.drawtl("   1, jb5 - change desired relative camera orientation", x, y, fgcolors[0], bgcolors[0]); y+=t.height
        #t.drawtl("   2, jb7 - change desired absolute camera orientation", x, y, fgcolors[1], bgcolors[1]); y+=t.height
        #t.drawtl("   3, jb6 - change helicopter (imu) orientation       ", x, y, fgcolors[2], bgcolors[2]); y+=t.height
        t.drawtl(" change gimbal orientation:                           ", x, y, headfgcolor, headbgcolor); y+=t.height
        t.drawtl("   joystick, mouse, mousewheel                        ", x, y, fgcolor, bgcolor); y+=t.height
        t.drawtl("   (mouse: remove joystick and hold down 1,2,3)       ", x, y); y+=t.height
        t.drawtl(" spectator movement                                   ", x, y, headfgcolor, headbgcolor); y+=t.height
        t.drawtl("   wsad, arrows                                       ", x, y, fgcolor, bgcolor); y+=t.height

        t.drawbr("fps: %.0f" % (self.fps_counter.fps), self.w, self.h, fgcolor = (0., 0., 0., 1.), bgcolor = (0.7, 0.7, 0.7, .9), z = 100.)

    def render_world(self):

        glEnable(GL_LIGHTING)
        self.gimbal.render()
        glDisable(GL_LIGHTING)
        self.suncube.render_normal()


    def render_floor(self):

        # build the floor
        tile_size = 1.
        ntiles = 20
        w2 = ntiles * tile_size / 2.

        if "_floor_vertex_list" not in self.__dict__:
            v = []; ts = tile_size
            for i in range(ntiles + 1):
                v.extend([i*ts-w2,0.,w2,  i*ts-w2,0.,-w2,  -w2,0.,i*ts-w2,  w2,0.,i*ts-w2])

            #self._floor_vertex_list = pyglet.graphics.vertex_list((ntiles+1) * 4, ('v3f/static', v))
            self._floor_vertex_list = vbo.VBO(v)


        glLineWidth(2.)
        glColor4f(0.7, 0.7, 0.7, 1.0)

        self._floor_vertex_list.draw(GL.GL_LINES)
        #self._floor_vertex_list.draw(GL.GL_TRIANGLES)
        #self._floor_vertex_list.draw(pyglet.gl.GL_LINES)

        if 1:
            glBegin(GL_QUADS)
            glColor4f(0.5, 0.5, 0.5, 0.6)
            glVertex3f(-w2, 0.,  w2)
            glVertex3f( w2, 0.,  w2)
            glVertex3f( w2, 0., -w2)
            glVertex3f(-w2, 0., -w2)
            glEnd()

    def _create_euler_ocs(self, yaw, pitch, roll):
        ocs = coordinate_system.CoordinateSystem()
        a_frame = ocs.a_frame
        a_frame.rotate(a_frame.y_axis, yaw)
        a_frame.rotate(a_frame.x_axis, pitch)
        a_frame.rotate(a_frame.z_axis, roll)
        return ocs

    def handle_controls(self, dt):

        if 0 and self.joystick:

            #print "joy: %.2f %.2f %.2f : %s" % (self.joystick.x, self.joystick.y, self.joystick.z, self.joystick.buttons)

            self.out_yaw   = -self.joystick.x * 180.
            self.out_pitch =  self.joystick.y * 90.
            self.out_roll  =  self.joystick.z * 90.

            if len(self.joystick.buttons) > 6:
                if   self.joystick.buttons[4]: self.mode = self.MODE_GIMBAL_ABSOLUTE
                elif self.joystick.buttons[6]: self.mode = self.MODE_GIMBAL_RELATIVE
                elif self.joystick.buttons[5]: self.mode = self.MODE_HELICOPTER

        # ocs = self._create_euler_ocs(self.out_yaw, self.out_pitch, self.out_roll)
        # if self.mode == self.MODE_GIMBAL_ABSOLUTE:
        #     # set gimbal absolute desired orientation
        #     self.gimbal.set_abs_desired_camera_orientation(ocs.a_frame)
        #     self.abs_yaw, self.abs_pitch, self.abs_roll = self.out_yaw, self.out_pitch, self.out_roll
        # elif self.mode == self.MODE_GIMBAL_RELATIVE:
        #     # set gimbal relative desired orientation
        #     self.gimbal.set_rel_desired_camera_orientation(ocs.a_frame)
        #     self.rel_yaw, self.rel_pitch, self.rel_roll = self.out_yaw, self.out_pitch, self.out_roll
        # elif self.mode == self.MODE_HELICOPTER:
        #     # set imu orientation
        #     ocs = self._create_euler_ocs(self.out_yaw, self.out_pitch, self.out_roll)
        #     ocs.pos.set(self.gimbal.ocs.pos)
        #     self.gimbal.set_imu_ocs(ocs)
        #     self.hel_yaw, self.hel_pitch, self.hel_roll = self.out_yaw, self.out_pitch, self.out_roll

        keys = self.keys
        #k = key
        speed    = 5.
        rotspeed = 120.

        cp = self.selected_obj.ocs.pos
        ca = self.selected_obj.ocs.a_frame

        if keys[SDL_SCANCODE_A]: cp.add(-ca.x_axis * speed * dt)
        if keys[SDL_SCANCODE_D]: cp.add( ca.x_axis * speed * dt)
        if keys[SDL_SCANCODE_E]: cp[1] += speed * dt
        if keys[SDL_SCANCODE_Q]: cp[1] -= speed * dt
        if keys[SDL_SCANCODE_W]: cp.add( ca.z_axis * speed * dt)
        if keys[SDL_SCANCODE_S]: cp.add(-ca.z_axis * speed * dt)

        up = vector.Vector((0., 1., 0.))

        if keys[SDL_SCANCODE_LEFT]:      ca.rotate(up,  rotspeed * dt)
        if keys[SDL_SCANCODE_RIGHT]:     ca.rotate(up, -rotspeed * dt)
        if keys[SDL_SCANCODE_UP]:        ca.rotate(ca.x_axis, -rotspeed * dt)
        if keys[SDL_SCANCODE_DOWN]:      ca.rotate(ca.x_axis,  rotspeed * dt)
        # if keys[k.MOTION_NEXT_PAGE]: ca.rotate(ca.z_axis,  rotspeed * dt)
        # if keys[k.MOTION_DELETE]:    ca.rotate(ca.z_axis, -rotspeed * dt)

        #if keys[SDL_SCANCODE_ESCAPE]: self.has_exit = True
        if self.joystick:
            if SDL_JoystickGetButton(self.joystick, self.conf.joystick_b_strafe_left):
                cp.add(-ca.x_axis * speed * dt)
            if SDL_JoystickGetButton(self.joystick, self.conf.joystick_b_strafe_right):
                cp.add( ca.x_axis * speed * dt)
            if SDL_JoystickGetButton(self.joystick, self.conf.joystick_b_move_forward):
                cp.add( ca.z_axis * speed * dt)
            if SDL_JoystickGetButton(self.joystick, self.conf.joystick_b_move_backward):
                cp.add(-ca.z_axis * speed * dt)



    def save_autoscreenshot(self, dt):
        self._screenshot_call_counter += 1
        if self._screenshot_call_counter % 6 == 0:
            self.save_screenshot("autoscreenshot_")

    def save_screenshot(self, filename_prefix="screenshot_"):
        """saves screenshots/filename_prefix20090404_120211_utc.png"""
        utc = time.gmtime(time.time())
        filename = filename_prefix + "%04i%02i%02i_%02i%02i%02i_utc.png" % \
                   (utc.tm_year, utc.tm_mon, utc.tm_mday,                  \
                    utc.tm_hour, utc.tm_min, utc.tm_sec)
        print "saving screenshot '%s'" % filename
        pyglet.image.get_buffer_manager().get_color_buffer().save("screenshots/" + filename)

    def on_resize(self, width, height):
        self.w, self.h = width, height

    #def on_mouse_press(self, x, y, button, modifiers): pass

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if self.joystick: return
        keys = self.keys; k = key
        if keys[k._1] or keys[k._2] or keys[k._3]:
            self._add_angles(0., 0., scroll_y * 3.)

    def on_mouse_release(self, x, y, button, modifiers):
        if self.exclusive_mouse and (button & mouse.LEFT):
            self.exclusive_mouse = False
            self.set_exclusive_mouse(False)

    def _limit_angles(self):
        self.out_yaw   %= 360.
        self.out_pitch %= 360.
        self.out_roll  %= 360.
        if self.out_yaw   > 180.: self.out_yaw   -= 360.
        if self.out_pitch > 180.: self.out_pitch -= 360.
        if self.out_roll  > 180.: self.out_roll  -= 360.
        if self.out_pitch >  90.: self.out_pitch  =  90.
        if self.out_pitch < -90.: self.out_pitch  = -90.
        if self.out_roll  >  90.: self.out_roll   =  90.
        if self.out_roll  < -90.: self.out_roll   = -90.

    def on_mouse_motion(self, x, y, dx, dy):
        if self.joystick: return
        keys = self.keys; k = key
        if keys[k._1] or keys[k._2] or keys[k._3]:
            self._add_angles(-dx, -dy, 0.)

    def _add_angles(self, yaw, pitch, roll):
            self.out_yaw += yaw
            self.out_pitch += pitch
            self.out_roll += roll
            self._limit_angles()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons & mouse.LEFT:

            #if not self.exclusive_mouse:
            #    self.exclusive_mouse = True
            #    self.set_exclusive_mouse(True)

            ocs = self.camera.ocs
            camera_turn_speed = 0.5 # degrees per mouseixel
            up = vector.Vector((0., 1., 0.))

            ocs.a_frame.rotate(ocs.a_frame.x_axis,  camera_turn_speed * dy)
            ocs.a_frame.rotate(up,                 -camera_turn_speed * dx)

    def on_key_press(self, symbol, modifiers):
        if symbol == key.F12:
            self.save_screenshot()

        if symbol == key.C:
            print "camera ocs (pos, x_axis, y_axis, z_axis)"
            print self.camera.ocs.pos
            print self.camera.ocs.a_frame.x_axis
            print self.camera.ocs.a_frame.y_axis
            print self.camera.ocs.a_frame.z_axis

        if   symbol == key._1: self.mode = self.MODE_GIMBAL_RELATIVE
        elif symbol == key._2: self.mode = self.MODE_GIMBAL_ABSOLUTE
        elif symbol == key._3: self.mode = self.MODE_HELICOPTER

        if symbol == key._7:
            self.selected_obj = self.camera
            print "camera selected"
        if symbol == key._8:
            self.selected_obj = self.gimbal
            print "gimbal selected", self.selected_obj, self.gimbal
        if symbol == key._9:
            self.selected_obj = self.suncube
            print "suncube selected", self.selected_obj, self.suncube

