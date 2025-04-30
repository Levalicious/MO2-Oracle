#!/bin/python
import re
import os
from enum import Enum

def uget(var: str) -> str:
    val = os.environ.get(var)
    if val is None:
        print(f'{val}')
        print(f'{os.environ}')
        raise ValueError(f'{var} cannot be None')
    return val

class ReleaseType(Enum):
    FINAL = ''
    CANDIDATE = 'rc'
    BETA = 'b'
    ALPHA = 'a'
    PRE_ALPHA = 'pa'

class VersionInfo:
    def __init__(
        self: 'VersionInfo',
        major: int,
        minor: int,
        subminor: int,
        subsubminor: int | None = None,
        release_type: ReleaseType = ReleaseType.FINAL,
    ) -> None:
        self.major: int = major
        self.minor: int = minor
        self.subminor: int = subminor
        self.subsubminor: int | None = subsubminor
        self.release_type: ReleaseType = release_type
    
    def __str__(self: 'VersionInfo') -> str:
        s = f'{self.major}.{self.minor}.{self.subminor}'
        if self.subsubminor is not None:
            s += f'.{self.subsubminor}'
        if self.release_type != ReleaseType.FINAL:
            s += self.release_type.value
        return s


def find_version_str(content: str, key: str) -> list[str]:
    m = re.search(rf'{key}:\sVersionInfo\s*=\s*VersionInfo\(([^)]+)\)', content)
    if not m:
        raise RuntimeError('Failed to extract plugin version')
    a = [x.strip() for x in m.group(1).split(',')]
    return a

def parse_version(a: list[str]) -> VersionInfo:
    r: ReleaseType = ReleaseType.FINAL
    if a[-1].replace('.', '').isalpha():
        r = ReleaseType[a[-1].removeprefix('ReleaseType.')]
        a = a[:-1]
        
    return VersionInfo(
        int(a[0]),
        int(a[1]),
        int(a[2]),
        int(a[3]) if len(a) > 3 else None,
        r)

plugin_name = uget('PLUGINNAME')
path = plugin_name + f'/{plugin_name}.py'.replace('_', '/')

if not os.path.exists(path):
    print(f'File not found: {path}')
    exit(1)
with open(path, encoding='utf-8') as f:
    content = f.read()

v = parse_version(find_version_str(content, '_version'))
min_v = parse_version(find_version_str(content, 'minversion'))
max_v = parse_version(find_version_str(content, 'maxversion'))

github_output = uget('GITHUB_OUTPUT')
with open(github_output, 'a') as out:
    _ = out.write(f'version={v}\n')
    _ = out.write(f'min_support={min_v}\n')
    _ = out.write(f'max_support={max_v}\n')