#!/usr/bin/env python2
# coding: utf8

"""
ZicFS: Music tagging filesystem

Usage: zicfs [-hf] MUSIC_DIR MOUNT_POINT

Arguments:
    MUSIC_DIR       Path to your music directory
    MOUNT_POINT     Where to mount ZicFS

Options:
    -h, --help              Print this help and exit
    -f, --foreground        Do not daemonize ZicFS
    -p, --pattern PATTERN   Uses the directory architecture PATTERN
                            instead of the default one.

Patterns:
    Pattern defines how directories are laid out.
    Note that a file's name is always considered the tracks title.
    The default pattern is:

        artist/album

    Available format tags are:
        artist:    Musician's name
        album:     Album's title
        year:      Year of release
        genre:     Style of music
        any other: Ignore this layer's name
"""

from __future__ import with_statement, unicode_literals

import os
import errno

from docopt import docopt
from fuse import FUSE, FuseOSError, Operations
from mutagen.id3 import ID3, TIT2, TALB, TPE1, TDRC, TCON

########################################
# Filesystem
########################################

class Passthrough(Operations):
    """ FUSE filesystem that acts as symlink to its root and does nothing. """

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

    def __init__(self, root, pattern):
        self.pattern = pattern
        return Passthrough.__init__(self, root)

    def rename(self, old, new):
        result = Passthrough.rename(self, old, new)
        tag_from_path(self._full_path(new), self.pattern)
        return result

    def write(self, path, buf, offset, fh):
        result = Passthrough.write(self, path, buf, offset, fh)
        tag_from_path(self._full_path(path), self.pattern)
        return result



########################################
# Tagger
########################################


def tag_from_path(path, pattern):
    print "Path: " + path

    if not path.endswith(".mp3"):
        return

    audio = ID3(path)
    infos = parse_path(path, pattern)

    mp3_fields = { "artist": TPE1,
                   "album":  TALB,
                   "track":  TIT2,
                   "genre":  TCON,
                   "date":   TDRC }

    for field in mp3_fields:
        value = infos.get(field) or "None"
        print field + ":" + value
        if value:
            audio.add(mp3_fields[field](encoding=3, text=value))

    audio.save()


def parse_path(path, pattern):
    split_path    = [ x for x in path.split("/")[1:] if x ]
    split_pattern = [ x for x in pattern.split("/")  if x ]

    infos = { "track" : split_path.pop().rsplit(".", 1)[0] }

    while split_path and split_pattern:
        infos[ split_pattern[0] ] = split_path[0]

        split_path    = split_path[1:]
        split_pattern = split_pattern[1:]

    return infos


########################################
# Command Line Interface
########################################


def main():
    args = docopt(__doc__)

    args["--pattern"] = args.get("--pattern", "artist/album")

    FUSE(ZicFS(args["MUSIC_DIR"], args["--pattern"]),
         args["MOUNT_POINT"],
         nothreads=True,
         foreground=args["--foreground"])

if __name__ == '__main__':
    main()
