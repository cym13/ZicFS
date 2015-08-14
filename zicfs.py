#!/usr/bin/env python2

from __future__ import with_statement

import os
import sys
import errno

from fuse import FUSE, FuseOSError, Operations

########################################
# Filesystem
########################################

class Passthrough(Operations):
    """ FUSE filesystem that acts as symlink and does nothing. """

    def __init__(self, root):
        self.root = root

    # Helpers
    # =======

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        if not os.access(self._full_path(path), mode):
            raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        return os.chmod(self._full_path(path), mode)

    def chown(self, path, uid, gid):
        return os.chown(self._full_path(path), uid, gid)

    def getattr(self, path, fh=None):
        st = os.lstat(self._full_path(path))
        return dict((key, getattr(st, key)) for key in
                      ('st_atime', 'st_ctime', 'st_gid', 'st_mode', 'st_mtime',
                       'st_nlink', 'st_size',  'st_uid', 'st_blocks'))

    def readdir(self, path, fh):
        full_path = self._full_path(path)

        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        for r in dirents:
            yield r

    def readlink(self, path):
        pathname = os.readlink(self._full_path(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)
        else:
            return pathname

    def mknod(self, path, mode, dev):
        return os.mknod(self._full_path(path), mode, dev)

    def rmdir(self, path):
        return os.rmdir(self._full_path(path))

    def mkdir(self, path, mode):
        return os.mkdir(self._full_path(path), mode)

    def statfs(self, path):
        stv = os.statvfs(self._full_path(path))
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    def unlink(self, path):
        return os.unlink(self._full_path(path))

    def symlink(self, name, target):
        return os.symlink(name, self._full_path(target))

    def rename(self, old, new):
        return os.rename(self._full_path(old), self._full_path(new))

    def link(self, target, name):
        return os.link(self._full_path(target), self._full_path(name))

    def utimens(self, path, times=None):
        return os.utime(self._full_path(path), times)

    # File methods
    # ============

    def open(self, path, flags):
        return os.open(self._full_path(path), flags)

    def create(self, path, mode, fi=None):
        return os.open(self._full_path(path), os.O_WRONLY | os.O_CREAT, mode)

    def read(self, path, length, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def truncate(self, path, length, fh=None):
        with open(self._full_path(path), 'r+') as f:
            f.truncate(length)

    def flush(self, path, fh):
        return os.fsync(fh)

    def release(self, path, fh):
        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        return self.flush(path, fh)


class ZicFS(Passthrough):
    """ FUSE filesystem managing music file metadata """

    def rename(self, old, new):
        fp_old = self._full_path(old)
        fp_new = self._full_path(new)
        tag_from_path(fp_old, new)
        return os.rename(fp_old, fp_new)

    def create(self, path, mode, fi=None):
        result  = super().create(_full_path(path), mode, fi)
        tag_from_path(path, path)
        return result


########################################
# Tagger
########################################


def tag_from_path(old, new):
    print "Tagging '" + old + "' from path '" + new + "'"


if __name__ == '__main__':
    root       = sys.argv[1]
    mountpoint = sys.argv[2]
    FUSE(ZicFS(root), mountpoint, nothreads=True, foreground=True)
