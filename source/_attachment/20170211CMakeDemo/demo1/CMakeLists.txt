cmake_minimum_required (VERSION 2.6)

project(CMakeDemo)
set(src_list main.cpp demo.cpp demo.h)
message(STATUS "This is Binary dir " ${PROJECT_BINARY_DIR})
message(STATUS "This is Source dir " ${PROJECT_SOURCE_DIR})
add_executable(Demo1 ${src_list})
