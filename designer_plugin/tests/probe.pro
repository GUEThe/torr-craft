QT += core gui widgets designer
TEMPLATE = app
CONFIG += console c++17 release
CONFIG -= debug_and_release
TARGET = probe
DESTDIR = $$PWD/build
OBJECTS_DIR = $$PWD/build/obj
MOC_DIR = $$PWD/build/moc

SOURCES += probe.cpp
