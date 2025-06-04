#!/bin/python
import os
import shutil
import subprocess
from time import sleep

os.environ['PLUGINPATH'] = 'plugin_oracle'

def uget(var: str) -> str:
    val = os.environ.get(var)
    if val is None:
        print(f'{val}')
        print(f'{os.environ}')
        raise ValueError(f'{var} cannot be None')
    return val

def check_appdata() -> str | None:
    path = uget('LOCALAPPDATA')
    path += os.path.sep + 'ModOrganizer'
    if not os.path.exists(path):
        return None
    path += os.path.sep + 'nxmhandler.ini'
    if not os.path.exists(path):
        return None
    with open(path, 'r') as f:
        for line in f:
            if 'executable' in line:
                return line[line.index('=') + 1:].rstrip()
    return None             

def remove_pycache(root: str) -> None:
    for dirpath, dirnames, _ in os.walk(root):
        if '__pycache__' in dirnames:
            shutil.rmtree(os.path.join(dirpath, '__pycache__'), ignore_errors=True)

binpath = check_appdata()
if not binpath:
    print('Can\'t find MO2')
    exit(1)
path = binpath.removesuffix(r'\\ModOrganizer.exe')

path += os.path.sep + 'plugins'
if not os.path.exists(path):
    os.makedirs(path, exist_ok=True)

remove_pycache(uget('PLUGINPATH'))
shutil.rmtree(path + os.path.sep + uget('PLUGINPATH'), ignore_errors=True)

print(shutil.copytree(uget('PLUGINPATH'), path + os.path.sep + uget('PLUGINPATH'), dirs_exist_ok=True))

sleep(3)
cmd: list[str] = [binpath, 'reload-plugin', uget('PLUGINPATH')]
_ = subprocess.run(cmd)
