QT += quick core gui
CONFIG += c++11

# The following define makes your compiler emit warnings if you use
# any feature of Qt which as been marked deprecated (the exact warnings
# depend on your compiler). Please consult the documentation of the
# deprecated API in order to know how to port your code away from it.
DEFINES += QT_DEPRECATED_WARNINGS

# You can also make your code fail to compile if you use deprecated APIs.
# In order to do so, uncomment the following line.
# You can also select to disable deprecated APIs only up to a certain version of Qt.
#DEFINES += QT_DISABLE_DEPRECATED_BEFORE=0x060000    # disables all the APIs deprecated before Qt 6.0.0

SOURCES += \
        main.cpp

# handle platform specific stuff
sailfish {
    # For Sailfish OS:
    # - tell the C++ code to use the correct ifdefs
    # - default to useing the silica UC backend
    # - add sailfishapp to CONFIG
    DEFINES += SAILFISH
    DEFAULT_UC_BACKEND = silica
    CONFIG += sailfishapp
    TARGET = harbour-modrana
} else {
    DEFAULT_UC_BACKEND = controls
    TARGET = modrana
}

isEmpty(PREFIX) {
    PREFIX = /usr/local/share
}

# default Universal Components backend
isEmpty(UC_BACKEND) {
    UC_BACKEND = $$DEFAULT_UC_BACKEND
}

# path to the modRana main.qml
DEFINES += MODRANA_MAIN_QML=\\\"$${PREFIX}/$${TARGET}/modules/gui_modules/gui_qt5/qml/main.qml\\\"

# Python path for modRana
DEFINES += PYTHON_PATH=\\\"$${PREFIX}/$${TARGET}/\\\"

# define Universal Components set root folder path
# - it ie expected this gets combined with the backend folder name and put to QML import path,
#   so that the respective backend gets used on runtime
DEFINES += UC_ROOT_PATH=\\\"$${PREFIX}/$${TARGET}/modules/gui_modules/gui_qt5/qml/universal_components/\\\"

# define default Universal Components folder name
DEFINES += UC_BACKEND_FOLDER_NAME=\\\"$${UC_BACKEND}\\\"

# deploy the resulting library into /usr/bin
target.path = /usr/bin/
target.files = $$TARGET

INSTALLS += target
