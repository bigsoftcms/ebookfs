import fuse
import stat
from time import time

class MyStat(fuse.Stat):
    def __init__(self, mode = stat.S_IFDIR, mask = 0o755):
        current_time = int(time())

        self.st_mode = mode | mask
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 1 if mode == stat.S_IFLNK else 2
        self.st_uid = 0
        self.st_gid = 0
        self.st_size = 4096
        self.st_atime = current_time
        self.st_mtime = current_time
        self.st_ctime = current_time
