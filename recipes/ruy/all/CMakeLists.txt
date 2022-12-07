cmake_minimum_required(VERSION 3.15)
project(cmake_wrapper)

find_package(cpuinfo REQUIRED CONFIG)
if(NOT TARGET cpuinfo)
    add_library(cpuinfo INTERFACE IMPORTED)
    set_property(TARGET cpuinfo PROPERTY INTERFACE_LINK_LIBRARIES cpuinfo::cpuinfo)
endif()
if(NOT TARGET clog)
    add_library(clog INTERFACE IMPORTED)
    set_property(TARGET clog PROPERTY INTERFACE_LINK_LIBRARIES cpuinfo::cpuinfo)
endif()

set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)

add_subdirectory(src)
