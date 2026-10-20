QT += core gui widgets designer

TEMPLATE = lib
CONFIG += plugin c++17 release
CONFIG -= debug_and_release

TARGET = torr_craft_designer
DESTDIR = $$PWD/build/designer
OBJECTS_DIR = $$PWD/build/obj
MOC_DIR = $$PWD/build/moc

SOURCES += \
    src/torr_preview_widget.cpp \
    src/torr_widget_plugins.cpp

HEADERS += \
    src/torr_preview_widget.h \
    src/torr_widget_plugins.h

INCLUDEPATH += $$PWD/src

win32 {
    QMAKE_CXXFLAGS += /utf-8
    QMAKE_TARGET_PRODUCT = "Torr Craft Designer Plugin"
    QMAKE_TARGET_DESCRIPTION = "Qt Designer preview widgets for Torr Craft"
}

DISTFILES += README.md
