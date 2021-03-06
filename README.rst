Description
===========

ZicFS is a FUSE filesystem to auto-tag music files based on where they are
stored.

It is written in python2 (because of fusepy dependance).

**Work in progress**

Documentation
=============

Basics
------

ZicFS's primary function is to tag files based on where they are placed in
the directory structure. The default structure is as such:

    zicfs/artist_name/album_title/track_title

Moving a file *baz* to *zicfs/foo/bar/baz* will automatically tag it with foo
as author, bar as album title and baz as track_title. Those tags are set in
the file metadata (ID3 for mp3, vorbis comment for the rest). That means that
if you copy it to your phone for example, it will recognize the tags too.

As this is a file system, you can use whatever you feel comfortable with to
manage your files, it will still work.

Tags are set from top to bottom. If you are using the default structure and
have a file *zicfs/some_band/cool.mp3* then its artist will be set to
some_band and its album_name will not be set to anything.

A track's title is extracted from the file name. It it delimited between the
last occurence of " - " (if there is one) and the last "." prepending the
extension. If the first field delimited by " - " is numeric, it is considered
the tracks position in the album. It is possible to replace " - " by another
operator using *.meta* files. This means it will extract the title from the
following file names as such:

::

    01 - My band - My Song.mp3  -> title: My Song ; position: 01
    01 - My Song.mp3            -> title: My Song ; position: 01
    my-song.mp3                 -> title: my-song

Meta files
----------

Such tagging is easy but limited. If you want to add more informations to
your files, zicfs provides another way: add a *.meta* file containing
additional tag informations somewhere in a zicfs directory and all files in
the subdirectories will be tagged with those tags as well. Note that the
deeper a *.meta* file is, the more it prevails over other informations. A
.meta file cannot overload a directory-based information.

For example, let's say we have the following directory structure:

::

    zicfs -+- LukHash -+- Psyche -+- DUB.mp3
           |           |
           |           +- .meta -> style="electro", album="Dead Pixels"
           |
           +- .meta -> style="Jazz", year=2007

Then DUB.mp3 will have the following tags:

::

    author = "LukHash"
    album  = "Psyche"
    title  = "DUB"
    style  = "electro"
    year   = 2007

Notice how the style was assigned from the nearest *.meta* file and the album
wasn't changed.

Other directory structures
--------------------------

We understand that this directory structure doesn't fit everybody's needs so
there is a way to specify your own pattern. Check the CLI documentation below
for more information.

Info files
----------

In order to get additional data about your filebase ZicFS provides a last
trick: an *INFO* file. Those files are not real files in that you can copy
or write to them. In fact an INFO file holds no data. When read, an *INFO*
file in a directory will dynamically fetch informations about all files in
subdirectories such as the complete list of existing tags.

Command-line interface documentation
====================================

::

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
            style:     Style of music
            any other: Ignore this layer's name

Dependencies
============

- Linux as ZicFS depends on FUSE which is Linux only.
- fusepy  (https://github.com/terencehonles/fusepy)
- mutagen
- docopt

Roadmap
=======

::

    [+] Write a FUSE base mocking tagging functions
    [+] Build mp3's ID3 by-directory tagging
    [ ] Build Vorbis comments by-directory tagging
    [ ] Add file-based additional tagging
    [ ] Get info files to work
    [+] Add the possibility to specify a directory pattern
    [ ] Have fun!

License
=======

This program is under the GPLv3 License.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

Acknowledgement
===============

The Passthrough FUSE base comes (with modifications) from
http://www.stavros.io/posts/python-fuse-filesystem/ (BSD licensed).

Contact
=======

::

    Main developper: Cédric Picard
    Email:           cedric.picard@efrei.net
    Twitter:         @Cym13
    GPG:             383A 76B9 D68D 2BD6 9D2B  4716 E3B9 F4FE 5CED 42CB
