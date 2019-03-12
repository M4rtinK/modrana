The modRana launcher
====================

This is a simple Qt 5/C++ launcher used
for modRana, to get something that can be installed into $PATH
from packages and used by Flatpak.

The general idea is that you will get a binary called "modrana"
(or harbour-modrana on Sailfish OS) that you would put into
a suitable location, such as `/usr/bin`, enabling easy launching
of modRana by just typing the binary name to the terminal
or putting it to the Exec line of a desktop file.

What the launcher does
----------------------

There are three main things a launcher needs to do:

- append a *Universal Components* backend into QML import path
- append the main modRana folder to the Python import path
  via the `PYTHONPATH` environment variable
- load the main modRana QML file and run it

Setting the paths
-----------------

The launcher has a reasonable set of paths defined in its `pro` file,
which can be overridden by passing arguments to `qmake` when the launcher
is being built.

By default the expected modRana installation path prefix is pointing to
`/usr/local/share` and the PREFIX `qmake` variable can be used to override
this:

`"PREFIX=/usr/share"`

This will automatically resolve by default into `/usr/share/modrana` and 
to `/user/share/harbour-modrana` on Sailfish OS.

Launcher variants
-----------------

There are currently two variants of the launcher built from the same source
code via if-defs and `pro` file options. A *plain* Qt 5 based launcher and
a launcher using the `libsailfishapp` library specific to Sailfish OS.

To build the Sailfish OS specific launcher variant, append `"CONFIG+=sailfish"`
to your `qmake` invocation.

The resulting launcher binary is called `modrana` by default and `harbour-modrana`
on Sailfish OS.
