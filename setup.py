from cx_Freeze import setup, Executable
import asyncio
from glob import iglob as glob
from os.path import dirname, basename

# Dependencies are automatically detected, but it might need
# fine tuning.
packages = ["discord", "aiohttp", "websockets", "asyncio", "asyncio.compat"]

asyncio_location = dirname(asyncio.__file__)

for file_path in glob(f"{asyncio_location}/*"):
    file_name = basename(file_path).rstrip(".py")
    if not file_name.startswith("__"):
        packages.append(f"asyncio.{file_name}")
print (packages)

buildOptions = dict(packages=packages, excludes=[])

base = 'Console'

executables = [
    Executable('activityReader.py', base=base)
]

setup(name='ActivityReader',
      version='1.0',
      description='',
      options=dict(build_exe=buildOptions),
      executables=executables)
