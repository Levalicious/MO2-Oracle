from mobase import IModList, IModInterface, ModState
import os
from hashlib import sha256, file_digest

def bhash(msg: bytes) -> bytes:
    h = sha256()
    h.update(msg)
    return h.digest()

def get_file_bytes(file_path):
    try:
        with open(file_path, 'rb') as file:
            file_bytes = file.read()
        return file_bytes
    except FileNotFoundError:
        return b''
    except PermissionError:
        return b''
    except Exception as e:
        raise Exception(f'ERR: {file_path} {e}')
    
def get_file_hash(file_path) -> bytes:
    try:
        with open(file_path, 'rb') as file:
            return file_digest(file, sha256).digest()
    except FileNotFoundError:
        return bytes([2, 0])
    except PermissionError:
        return bytes([2, 1])
    except Exception as e:
        raise Exception(f'ERR: {file_path} {e}')

def dirhash(root_dir) -> bytes:
    stack: list[tuple[str, int, list[bytes], int | None]] = [(root_dir, -1, [], None)]
    
    while stack:
        current_dir, pending_result, child_hashes, parent = stack.pop()
        if pending_result == -1:
            items = os.listdir(current_dir)
            stackitems: list[tuple[str, int, list[bytes], int | None]] = []
            for item in items:
                item_path = os.path.join(current_dir, item)
                if os.path.isdir(item_path):
                    stackitems.append((item_path, -1, [], len(stack)))
                else:
                    child_hashes.append(get_file_hash(item_path) + bytes([0]))
            pending_result = len(stackitems)
            stack += ([(current_dir, pending_result, child_hashes, parent)] + stackitems)
        elif pending_result == 0:
            child_hashes.sort()
            if parent is not None:
                stack[parent] = (stack[parent][0], stack[parent][1] - 1, stack[parent][2] + [bhash(len(child_hashes).to_bytes(4, 'little') + b''.join(child_hashes)) + bytes([1])], stack[parent][3])
            else:
                return bhash(len(child_hashes).to_bytes(4, 'little') + b''.join(child_hashes)) + bytes([1])
        else:
            raise Exception('Missing directories? Ephemeral ones? This should not happen.')      
    raise Exception('This should not happen.')

class OMod:
    def __init__(self, mod: IModInterface, mlist: IModList) -> None:
        self.mod = mod
        self.mlist = mlist
        self._hash: None | bytes = None
    
    @property
    def name(self) -> str:
        return self.mod.name()
    
    @property
    def index(self) -> int:
        return self.mlist.priority(self.mod.name())
    
    @index.setter
    def index(self, ind: int) -> None:
        self.mlist.setPriority(self.mod.name(), ind)
    
    @property
    def state(self) -> bool:
        return (self.mlist.state(self.mod.name()) & (ModState.ACTIVE)) != 0
    
    @state.setter
    def state(self, state: bool) -> None:
        self.mlist.setActive(self.mod.name(), state)

    @property
    def essential(self) -> bool:
        return (self.mlist.state(self.mod.name()) & (ModState.ESSENTIAL)) != 0

    def dhash(self) -> None:
        if self._hash is None:
            self._hash = dirhash(self.mod.absolutePath())
    
    @property
    def hash(self) -> bytes:
        if self._hash is None:
            self._hash = dirhash(self.mod.absolutePath())
        return self._hash
    
    def __str__(self) -> str:
        return self.mod.name()
    
    def __hash__(self) -> int:
        return hash(self.mod.name())