flybyrift
=========

This is shaping up to be a FPV flight control system to experiment with the Oculus Rift.

http://www.reddit.com/r/fpv/


modules to be:

    video capture
    gimbal control with an xbox 360 controller
    oculus rift rendering
    delay removal system (image recognition? need a reference point on the video)


dependencies:

    libgltext : https://github.com/fdkz/libgltext
        copy the compiled gltext.so or gltext.pyd to flybyrift/system/modules/


creating a standalone dist:

    1. get the dll and compiled module bundle from .. where? i should upload those somewhere..

    2. copy gltext.so/pyd to system/modules/
    3. copy 32-bit msvcp110.dll, msvcr110.dll to ./
       comes with Visual Studio 2012, found in c:/Windows/SysWOW64/ (yes, 32-bit version in SysWOW64)
    4. copy SDL2.dll and zlib1.dll to ./
    5. pyinstaller.py flybyrift_win32.spec

    and ./dist/flybyrift/ should be ready to be sent out
