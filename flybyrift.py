import sys
import os

# version has to be incremented manually. but GITREV should be set by the deployment script
VERSION = "0.6.0"
GITREV = "not set"


if sys.hexversion < 0x2060000:
    print "python version >=2.6 required. you have", sys.version
    sys.exit(1)


# if under py2exe, sys.path[0] is sometimes really wrong. here's a foolproof way to get the exe dir.
# http://www.py2exe.org/index.cgi/WhereAmI
if hasattr(sys, "frozen"):
    # this only works with pyinstaller.
    g_py_path = sys._MEIPASS
#    g_py_path = os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding()))
    # if frozen, enable source/hybrid distribution.. (meaning we can use python source files with the
    # standalone exe without having to have python installed)
#    sys.path.insert(0, os.path.normpath(g_py_path))
else:
    g_py_path = sys.path[0] # can't use os.path.dirname. last dir is without the slash :S


#os.environ["PYSDL2_DLL_PATH"] = os.path.join(os.getcwd(), 'py')
os.environ["PYSDL2_DLL_PATH"] = g_py_path


import logging
log = logging.getLogger("flybyrift")

import time
import system.logging_setup as logging_setup

log_folder = os.path.join(g_py_path, "./log")
t = time.time()

logging_setup.start_logging_system(t, log_folder, "log_flybyrift.txt")

# print introductory lines
log.info("")
log.info("flybyrift start. version %s", VERSION)
#log.info("git hash %s", GITREV)

log.info("log file: %s", os.path.normpath(os.path.join(log_folder, "log_flybyrift.txt")))

utc = time.gmtime(t)
log.info("utc        : " + time.asctime( utc               ))
log.info("local time : " + time.asctime( time.localtime(t) ))
log.info("------------------------------------------------------------------------------")
log.info("")

# ---------------------------------------------------------------------------

# run the program

try:
    import system.main
    system.main.main(g_py_path)
except:
    logging.exception("")


# print some closing lines

ts  = t
t   = time.time()
utc = time.gmtime(t)
total_time = t - ts

log.info("")
log.info("------------------------------------------------------------------------------")
log.info("utc        : " + time.asctime( utc                ))
log.info("local time : " + time.asctime( time.localtime(t)  ))
log.info("total time : %i days %i hours %i minutes %i seconds",
        total_time // (60*60*24), total_time // (60*60) % 24,
        total_time // 60 % 60, total_time % 60)
