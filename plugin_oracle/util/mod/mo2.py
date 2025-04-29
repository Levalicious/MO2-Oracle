from mobase import IModList, IModInterface, ModState, IOrganizer # pyright: ignore [reportMissingModuleSource]
import os
from hashlib import sha256, file_digest
import pathlib
from plugin_oracle.util.mod.emap import efiles, ehashes
from PyQt6.QtCore import qInfo

def allMods(mlist: IModList) -> list[IModInterface]:
    return [mlist.getMod(mod) for mod in mlist.allMods()]

def nonEssentialMods(mlist: IModList) -> list[IModInterface]:
    return list(filter(lambda mod: not isEssential(mod, mlist),  allMods(mlist)))

def activeMods(mlist: IModList) -> list[IModInterface]:
    return list(filter(lambda mod: isActive(mod, mlist) and not isEssential(mod, mlist),  allMods(mlist)))

def isActive(mod: IModInterface, mlist: IModList) -> bool:
    return (mlist.state(mod.name()) & ModState.ACTIVE) != 0

def isEssential(mod: IModInterface, mlist: IModList) -> bool:
    return (mlist.state(mod.name()) & ModState.ESSENTIAL) != 0

def modhash(mod: IModInterface, organizer: IOrganizer) -> bytes:
    path: str = mod.installationFile()
    
    if '/' not in path:
        path = organizer.downloadsPath() + '/' + path
    else:
        username = os.getlogin()
        path = path.replace('USERNAME', username)
    with open(path, 'rb') as f:
        return file_digest(f, sha256).digest()

def essfiles(mod: IModInterface) -> list[str]:
    mn = mod.name().replace('Creation Club: ', '').replace('DLC: ', '')
    bpath = mod.absolutePath() + '/' + mn + '.'

    out: list[str] = []
    if mn in efiles:
        for suf in efiles[mn]:
            out.append(bpath + suf)
        return out
    
    matrix = [
        'bsa',
        'esl',
        'esm',
        'esp'
    ]
    
    vmat: list[str] = []
    for suf in matrix:
        if os.path.exists(bpath + suf):
            out.append(bpath + suf)
            vmat.append(suf)
    qInfo(f'{mn}: {vmat}')
    return out

def esshash(mod: IModInterface) -> bytes:
    mn = mod.name().replace('Creation Club: ', '').replace('DLC: ', '')
    if mn in ehashes:
        return ehashes[mn]
    files: list[str] = essfiles(mod)
    qInfo(f'{mod.name()} : {files}')
    if len(files) < 1:
        raise Exception(f'Missing files for {mod.name()}')
    hashes: list[bytes] = []
    for path in files:
        with open(path, 'rb') as f:
            hashes.append(f.read())
    combined = b''.join(hashes)
    o = sha256(combined).digest()
    qInfo(f'{mn}: bytes.fromhex(\'{o.hex()}\')')
    return o

def setHash(mod: IModInterface, hash: bytes) -> None:
    path: str = mod.absolutePath() + '/' + f'{hash.hex()}.oid.mohidden'
    with open(path, 'wb') as f:
        _ = f.write(hash)

def getHash(mod: IModInterface) -> bytes | None:
    files = list(pathlib.Path(mod.absolutePath()).glob('*.oid.mohidden'))
    if len(files) < 1:
        return None
    if len(files) > 1:
        raise Exception('Too many hashes')
    with open(files[0], 'rb') as f:
        return f.read()

    