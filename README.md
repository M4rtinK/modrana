Universal Components
====================

The Universal Components provide a QtQuick 2.0 component set
with a single interface that can use different backends.

Like application GUI code can be used written once and used
everywhere where one of the supported backends is available.

The backends take care of a native look, so the application
should not only run on the given platform but also look 
reasonably good.

Backends
--------

* QtQuick Controls - fully supported

The QtQuick Controls are part of Qt 5 since 5.1 and are a 
fully supported UC backend. Therefore any application
using UC should run with just Qt 5.1+ being available.

* Sailfish Silica - fully supported

The default component set of Sailfish OS by Jolla.

* Nemo Mobile Glacier - planed


How does it work
----------------

Universal Components provide a unified interface with all supported backends.
This is represented by a qmldir file and the elements themselves.

All individual backends have the same qmldirs and the same elements that
also provide the same properties and function.

All platform specific functionality that is deemed worthwhile & doable
is reimplemented in the other backends so that it can be part of the
unified interface.


Usage
-----

First you need to make sure the UC directory you want to use is in your
QML plugin search path. Uhen just import the UC plugin and use the provided
elements:

import UC 1.0

If you can't manipulate your QML plugin import path, you can also import the
UC plugin directly:

import "./UC"


Applications using Universal Controls
-------------------------------------

* [modRana flexible navigation system](https://github.com/M4rtinK/modrana)


TODO
----

* add pull-down menu
* remove some modRana rWin dependencies from the QtQuick Controls backend

LICENSE
-------

Universal Components are distributed under the terms of the [3-clause BSD license](http://opensource.org/licenses/BSD-3-Clause).
