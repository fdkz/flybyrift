# -*- mode: python -*-
a = Analysis(['flybyrift.py'],
             pathex=['.'],
             hiddenimports=["conf/conf_base.py"],
             hookspath=None,
             runtime_hooks=None)

a.datas += Tree("conf", "conf", excludes=["*.pyc"]) + Tree("data", "data")
a.datas += [("msvcp110.dll", "msvcp110.dll", "DATA"), ("msvcr110.dll", "msvcr110.dll", "DATA"), ("SDL2.dll", "SDL2.dll", "DATA")]

print a.datas

pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='flybyrift.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='flybyrift')

# create the log dir. i found no other way to get an empty log dir to the dist.
os.makedirs(os.path.join(coll.name, "log"))
