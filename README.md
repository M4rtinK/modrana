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

* QtQuick Controls 2 - fully supported

The QtQuick Controls are part of Qt 5 since 5.7 and are a
fully supported UC backend. Therefore any application
using UC should run with just Qt 5.7+ being available.

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

API Documentation
-----------------

Universal Components API documentation is available in the [docs/api_spec.rst](docs/api_spec.rst)
file.

Component usage notes
---------------------

**PlatformFlickable** and **PlatformListView**

These two components provide access to enhanced platform specific Flickables
and ListViews (SilicaListView has fast scroll support, etc.).
With backends that don't have such enhancements a normal Flickable or ListView
is used.

**TopMenu**

The TopMenu element provides a multi platform menu that will generally be shown
somewhere at the top of a Page using the appropriate native presentation method.
Currently this translates to a PullDownMenu with with the Silica backend and to
a Menu in popup mode with Controls. In the future the advanced Glacier pull down
menu should also be supported.

The easiest way to use the TopMenu is to place PageHeader on top of your Page
and assing the TopMenu into its *menu* property:

```QML
import UC 1.0
Page {
    PageHeader {
        anchors.top : parent.top
        menu : TopMenu {
            MenuItem {
                text : "option 1"
                onClicked : {console.log("1 clicked!")}
            }
            MenuItem {
                text : "option 2"
                onClicked : {console.log("2 clicked!")}
            }
        }
    }
}
```

The top menu makes sure that the TopMenu can be activated when needed, either in a
platform specific way (pull down gesture with Silica) or by showing a button
(with Controls).

The TopMenu can be also used inside the PlatformFlickable or PlatformListView,
but users will need to provide custom triggering for the TopMenu (calling its popup() method)
when not using the Silica backend.


Applications using Universal Components
-------------------------------------

* [modRana flexible navigation system](https://github.com/M4rtinK/modrana)
* [the Tensor Matrix client](https://github.com/davidar/tensor)


TODO
----

* Glacier backend


LICENSE
-------

Universal Components are distributed under the terms of the [3-clause BSD license](http://opensource.org/licenses/BSD-3-Clause).
