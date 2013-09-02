"""
IMPORTANT: CHANGES HERE WILL HAVE NO EFFECT

    this file is here only for reference, to show what can be changed
    in conf.py and what the default values are.


Create conf/conf.py or ../conf/conf.py like this:

c.debug = True
...
#conf_overrides = ["nextconf.py"]
"""

class Conf: pass

# a global object that every class knows about. just a
# configuration-dictionary.
c = Conf()

# all paths can be absolute ("/home/user/prog/bin/data"), or relative to the exe dir ("../bin/data")


c.joystick_index = 0

# tested on xbox controller on macosx

c.joystick_roll_axis = 0
c.joystick_pitch_axis = 1

c.joystick_b_strafe_left = 13
c.joystick_b_strafe_right = 14
c.joystick_b_move_forward = 11
c.joystick_b_move_backward = 12


#############################################################################

# an internal conf value. after startup points to the exe or main python
# file absolute directory.
c.py_path = ""

# Relative to current conf file dir. No error if file not found.
# Each next file in the list is used only if the previous was not found.
conf_overrides = ["conf.py"] #, "../../conf/conf.py"]
