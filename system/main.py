import logging
log = logging.getLogger(__name__)


# install a logging filter that removes some of these messages when using logging and "from OpenGL import GL":
#     OpenGL.acceleratesupport No OpenGL_accelerate module loaded: No module named OpenGL_accelerate
#     OpenGL.formathandler Unable to load registered array format handler numeric:
#         ImportError: No Numeric module present: No module named Numeric

class PyOpenGLLogNoiseFilter(logging.Filter):
    def filter(self, record):
        try:
            if record.msg == "Unable to load registered array format handler %s:\n%s" and record.args[0] == "numeric":
                #record.msg = record.msg[:-4]
                #record.args = record.args[:-1]
                return 0 # log the message. 0 for no, nonzero for yes.
            return 1
        except:
            log.exception("")
            return 1

logging.getLogger('OpenGL.formathandler').addFilter(PyOpenGLLogNoiseFilter())


import os
import time
import random

import conf_reader
import gimbal_window

log.info("------------------------------------------------- importing modules done")


def main(py_path):
    """
    py_path : full absolute path of the main py file. or of the exe.
    """

    conf = conf_reader.read_conf(os.path.join(py_path, "conf/conf_base.py"))
    conf.py_path = py_path

    random.seed()

    gimbal_window_proc = None

    try:
        gimbal_window_proc = gimbal_window.GimbalWindow(conf)

        gimbal_window_proc.run()

    except KeyboardInterrupt:
        log.info("")
        log.info("*" * 17)
        log.info("KeyboardInterrupt")
        log.info("*" * 17)

    finally:
        if gimbal_window_proc:
            gimbal_window_proc.close()
