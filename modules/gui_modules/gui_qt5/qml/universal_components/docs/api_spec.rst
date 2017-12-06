Universal Components API reference
**********************************

.. contents::
   :depth: 2

Introduction
============

This document specifies the unified API provided by Universal Components. 
Names of the provided elements as well as their properties, signals and methods are listed.

If a backend provides all elements listed in this document with all listed properties,
signals and methods it can be considered as fully supporting the UC API.


Elements
========

Button 
------

A button with text label.

Properties
^^^^^^^^^^

**text** : string
    The button label.

**pressed** : bool
    True if button is pressed, else false.

Signals
^^^^^^^

**clicked()**
    Triggered when the button has been clicked.


IconButton 
----------

A button with an image instead of text.

Properties
^^^^^^^^^^

**iconSource** : url
    URL to the icon image to be shown on the button.

**pressed** : bool
    True if button is pressed, else false.

Signals
^^^^^^^

**clicked()**
    Triggered when the button has been clicked.


ApplicationWindow 
-----------------

The main application window.

Properties
^^^^^^^^^^

**title** : string
    Window title - will be displayed on window header on platforms that have one.

**inProtrait** : bool
    True if the application window is in portrait, else false (landscape).

**inverted** : bool
    True if the application window is in inverted portrait or inverted landscape, else false.

**rotatesOnOrientationChange** : bool
    True if the *ApplicationWindow* itself rotates on device orientation change, else not.

    In general even if the *ApplicationWindow* does not rotate, the page stack and it's content does.

    At the moment:

    - QtQuick Controls *ApplicationWindow* rotates
    - Sailfish silica *ApplicationWindow* does not rotate

**pageStack** : native page stack
    This property provides access to the native page stack - currently *StackView*
    for the Controls backend and *PageStack* for the Silica backend.
    While both elements share a considerable amount of properties and methods
    (push(), pop(), clear(), find(), the busy property, etc.), they are not
    100% API compatible and even the method signatures might differ.
    And it is also possible that a future backend might introduce yet another
    page stack implementation with yet another slightly different API.


Methods
^^^^^^^

**pushPage**\(Item *pageInstance*, object *pageProperties*, bool *animate*)
    Push *pageInstance* to the page stack. The optional *properties* parameter specifies
    a map of properties to be set on the page. The *animate* parameter controls if the
    page push should be animated (true) or not (false).
    Also note that the **pushPage()** method returns the page instance that has been pushed. 


Page 
----

The Page type provides a container for the contents of a single page within an application.

Properties
^^^^^^^^^^

**isActive** : bool
    This property reports if the given page is the current active page - it is visible 
    and can be interacted with.
    A few things to note about the **isActive** property:

    - stays true even if device screen is turned off with Silica backend
    - it has not yet been tested if the same thing happens with Controls 2 on Android

    If you want stop processing when *the application* is not active, use the
    *Qt.application.state* property, possibly combined with the **isActive**
    page property.

**isInactive** : bool
    If true the page is not the active page, is not visible and can't be interacted with.

**isActivating** : bool
    If true the page is about to become the currently active page.

**isDeactivating** : bool
    If true the page is about to become inactive.

PageHeader 
----------

A header for use in a Page.

Properties
^^^^^^^^^^

**title** : string
    The text to display in the header.

**color** : color
    Header color.

**titlePixelSize** : int
    Pixel size of the title text.

**headerHeight**: int
    Height of the header in pixels.

NOTE: The **color**, **headerHeight** and **titlePixelSize** properties currently
don't do anything effect with the Silica backend and are provided for compatibility 
with the Controls backed PageHeader, where all these properties are effective.


Screen 
------

Provides device display attributes.

Properties
^^^^^^^^^^

**width** : int
    Display width.

**heigh** : int
    Display height.

NOTE: Currently with the Controls backend **width** is always 800
and **height** is always 600.


ProgressBar 
-----------

A progress indicator.

Properties
^^^^^^^^^^

**indeterminate** : real
    This property toggles indeterminate mode. When the actual progress is unknown,
    use this option. The progress bar will be animated as a busy indicator instead.
    The default value is false.

**maximumValue** : real
    The maximum value of the progress bar (default: 1.0).

**minimumValue** : real
    The minimum value of the progress bar (default: 0.0)    

**value** : real
    The current value of the progress bar.

BusyIndicator
-------------

Indicates background activity, for example, while content is being loaded.

Properties
^^^^^^^^^^

**running** : bool
    This property holds whether the busy indicator is currently indicating activity.

Slider 
------

A horizontal slider.

Properties
^^^^^^^^^^

**maximumValue** : real
    This property holds the maximum value of the slider. The default value is 1.0.

**minimumValue** : real
    This property holds the minimum value of the slider. The default value is 0.0.

**stepSize** : real
    This property indicates the slider step size.

    A value of 0 indicates that the value of the slider operates in a continuous range between minimumValue and maximumValue.

    Any non 0 value indicates a discrete stepSize. The following example will generate a slider with integer values in the range [0-5].
    
    ::

        Slider {
            maximumValue: 5.0
            stepSize: 1.0
        }
        
    The default value is 0.0.

**value**: real
    This property holds the current value of the slider. The default value is 0.0.

**pressed** : bool
    True if the slider is being pressed, else false.


Switch 
------

A Switch is a toggle button that can be switched on (checked) or off (unchecked).

Properties
^^^^^^^^^^

**checked** : bool
    This property is true if the control is checked. The default value is false.


TextSwitch 
----------

Like a **Switch**, but with a text label.

Properties
^^^^^^^^^^

**checked** : bool
    This property is true if the control is checked. The default value is false.

**text** : string
    The text shown alongside the switch.


Label 
-----

In addition to the normal QtQuick 2 **Text** element, Label follows the font and color scheme of the given platform.
Use the text property to assign a text to the label. For other properties check the **Text** element.

Properties
^^^^^^^^^^

**text** : string
    Text to be displayed on the label.

SectionHeader
-------------

Heading text for the start of a section on a page. Uses the **SectionHeader** element with Silica backend
and a bold horizontally centered **Label** with the Controls backend.

Properties
^^^^^^^^^^

**text** : string
    Text to be displayed on the section header.

TextArea 
--------

Displays multiple lines of editable formatted text.

The **TextArea** width and height should generally be set, otherwise the area will be sized to fit the entered text.

Properties
^^^^^^^^^^

**text** : string
    The text to be displayed in the **TextArea**.

**readOnly** : bool
    Holds whether the text field is in read-only mode.
    If set to true, the user cannot edit the text.

**validator** : Validator
    A Validator that validates any entered text. By default, a text field does not have a validator.
    
**acceptableInput** : bool
    Returns true if the text field contains acceptable text.

    If a validator was set, this property will return true if the current text satisfies the validator as a final string (not as an intermediate string).

    The default value is true.


TODO: The *assured* API currently provided by UC for the **TextArea** is quite basic at the moment and it would
be a good idea to extend it in the future - while keeping requirements realistic given backend variations.


TextField 
---------

Displays a single line of editable plain text.


Properties
^^^^^^^^^^

**text** : string
    The text to be displayed in the **TextField**

**readOnly** : bool
    Holds whether the text field is in read-only mode.
    If set to true, the user cannot edit the text.

**validator** : Validator
    A Validator that validates any entered text. By default, a text field does not have a validator.
    
**acceptableInput** : bool
    Returns true if the text field contains acceptable text.

    If a validator was set, this property will return true if the current text satisfies the validator 
    as a final string (not as an intermediate string).

    The default value is true.


TODO: The *assured* API currently provided by UC for the **TextField** is quite basic at the moment and it would
be a good idea to extend it in the future - while keeping requirements realistic given backend variations.


SearchField 
-----------

A text field for entering a text search query.

NOTE: Currently this provides access to a native **SearchField** (has a search & clear buttons) on Silica and is 
just a normal **TextField** on Controls. It might be a good idea to add the clear buttons also on Controls and
other backends that don't provide a native **SearchField** equivalent.

Properties
^^^^^^^^^^

**text** : string
    The text to be displayed in the **TextField**

**readOnly** : bool
    Holds whether the text field is in read-only mode.
    If set to true, the user cannot edit the text.

**validator** : Validator
    A Validator that validates any entered text. By default, a text field does not have a validator.
    
**acceptableInput** : bool
    Returns true if the text field contains acceptable text.

    If a validator was set, this property will return true if the current text satisfies the validator 
    as a final string (not as an intermediate string).

    The default value is true.


Dialog 
------

A dialog element.

TODO: Specify a common UC dialog API.

Properties
^^^^^^^^^^

**TBD**

Signals
^^^^^^^

**TBD**

Methods
^^^^^^^

**TBD**


ComboBox 
--------

A combo box control for selecting from a list of options.

Menu items are added with a **ListModel** to the
model property, which dynamically adds them to the
context menu. Once an item is clicked, its underlying
**ListElement** is returned so *onCurrentItemChanged*
is triggered.

Example:

::

    ComboBox {
        currentIndex: 2
        model: ListModel {
            id: cbItems
            ListElement { text: "Banana"; color: "Yellow" }
            ListElement { text: "Apple"; color: "Green" }
            ListElement { text: "Coconut"; color: "Brown" }
        }
        width: 200
        onCurrentIndexChanged: console.debug(cbItems.get(currentIndex).text + ", " + cbItems.get(currentIndex).color)
    }

The Universal Components **ComboBox** also supports localization via the *QT_TRANSLATE_NOOP* macro
with a default *"ComboBox"* context. The translation context can be overridden via the **translationContext**
property as long as the corresponding *QT_TRANSLATE_NOOP macros use the same custom context.


Using just the *QT_TR_NOOP* macro would give the string context
of the file where it has been found, which would not work as the **ComboBox** element is defined
in a different file.

**ComboBox** localization example:

::

    ComboBox {
        currentIndex: 1
        translationContext : "FooComboBox"
        model: ListModel {
            id: cbItems
            ListElement { text: QT_TRANSLATE_NOOP("FooComboBox", "foo"); color: "white" }
            ListElement { text: QT_TRANSLATE_NOOP("FooComboBox", "bar"); color: "black" }
        }
        width: 200
        onCurrentIndexChanged: console.debug(cbItems.get(currentIndex).text + ", " + cbItems.get(currentIndex).color)
    }

Two strings - "foo" and "bar" will be marked for translation with the *"ComboBox"* context,
which makes sure the qsTranslate() call in the **ComboBox** implementation matches them correctly.

Properties
^^^^^^^^^^

**label** : string
    A short single-line label describing the combobox.

**description** : string
    A longer (possibly multi-line) description of the combo-box. Can be useful
    for describing the currently selected element by switching between description
    texts when the selected item changes.

**model** : var
    Data model for the **ComboBox**.

**currentIndex** : int
    Index of the selected item in the data model.

**currentItem** : var
    Currently selected item.

**translationContext** : str
    Translation context combo box item text properties. "ComboBox" by default.

TopMenu 
-------

The **TopMenu** element provides a multi platform menu that will generally be shown somewhere
at the top of a Page using the appropriate native presentation method.
Currently this translates to a **PullDownMenu** with with the Silica backend and to a Menu in popup
mode with Controls. In the future the advanced Glacier pull down menu should also be supported.

The easiest way to use the **TopMenu** is to place **PageHeader** into a **PlatformFlickable** or
**PlatformListView** in your **Page** and assign the **TopMenu** into its menu property:

::

    import UC 1.0
    Page {
        PlatformFlickable {
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
    }

The top menu makes sure that the **TopMenu** can be activated when needed,
either in a platform specific way (pull down gesture with Silica) or by showing a 
button (with Controls).

The **TopMenu** can be also used inside a standalone **PlatformFlickable** or **PlatformListView**,
but users will need to provide custom triggering for the **TopMenu** (calling its popup() method)
when not using the Silica backend.

Methods
^^^^^^^

**popup**\()
    Opens the menu.

    NOTE: Only actually does something on the Controls backend and is currently provided 
    in onther backends only due to API compatibility.


MenuItem 
--------

A menu item for use with the **TopMenu**.

Properties
^^^^^^^^^^

**text** : string
    Text displayed in the menu item.

Signals
^^^^^^^

**clicked()**
    Triggered when the Menu item has been clicked.


BackgroundRectangle 
-------------------

A simple item inheriting **MouseArea** that can be used as
as a clickable background item with press highlighting for 
items in a **ListView**, special buttons or other interactive
user interface elements.

When when preset, the color of the **BackgroundRectangle**
will switch to **highlightedColor** and back to **NormalColor**
when no longer pressed.

Properties
^^^^^^^^^^

**highlightedColor** : color
    Color used when the background rectangle is pressed. 

**normalcolor** : color
    Color used when the background rectangle is not pressed.

**pressed_override** : bool
    Makes it possible to simulate pressed state even if background rectangle is not physically pressed.

VerticalScrollDecorator 
-----------------------

Adds a vertical scroll decorator to flickables and list views.

Example:

::

    ListView {
        id: listView
        model: myModel
        delegate: myDelegate

         VerticalScrollDecorator {}
    }

Scrollbar
---------

Adds a vertical scroll decorator to flickables and list views.

NOTE: Currently only provides functional scroll bar with the Controls backend,
      the Silica implementation is just an API compatible shim without any functionality.

Example:

::

    ListView {
        id: listView
        model: myModel
        delegate: myDelegate

         VerticalScrollDecorator {}
    }

Properties
^^^^^^^^^^

**horizontal** : Scrollbar
    Used to automatically attach a horizontal Scrollbar to a Flickable.

**vertical** : Scrollbar
    Used to automatically attach a horizontal Scrollbar to a Flickable.

Popup 
-----

A notification popup.

NOTE: The popup will automatically close when clicked.

Properties
^^^^^^^^^^

**title** : string
    Text of the notification popup.

**timeout** : int
    How long should the popup by displayed in milliseconds.
    The default value is 5000 milliseconds.

**background** : color
    Color of the notification popup background.
    
Methods
^^^^^^^

**hide**\()
    Hides the popup.

**show**\()
    Shows the popup.

**notify**\(text, color)
    A shortcut function for showing a popup notification with given **text** and **color**.


PlatformFlickable 
-----------------

This element provide access to an enhanced platform specific flickable (**SilicaFlickable** can have a pull-down menu attached, etc.). 
With backends that don't have such enhancements a normal Flickable is used.


PlatformListView
----------------

This element provide access to an enhanced platform specific list view (**SilicaListView** has fast scroll support, etc.).
With backends that don't have such enhancements a normal ListView is used.


Adding a new element
====================

When a new element is to be added to Universal Components, the following actions should be done:

- add the element to all backends or at least to as many as possible
- add the element the **qmldir** files for all backend where it was added
- add the element specification to this document, but only if supported by all non-experimental backends

Backends currently considered non-experimental:

- Controls
- Silica

Experimental backends:

- Glacier
- Ubuntu Components


Adding a new element property/signal/method
===========================================

When a new property/signal/method is to be added to the Universal Component API,
it should be added to the element in all backends if possible.

If should be also added to this document, but only if implemented by all non-experimental
backends (see the section above for a list of non-experimental backends).
