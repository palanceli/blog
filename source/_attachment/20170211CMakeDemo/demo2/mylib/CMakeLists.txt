cmake_minimum_required (VERSION 2.6)

MESSAGE(STATUS "operation system is ${CMAKE_SYSTEM_NAME}")
include_directories(${PROJECT_SOURCE_DIR}/include)
set(SRC MyLib.cpp ${PROJECT_SOURCE_DIR}/include/MyLib.h)

if(APPLE)
  set(CMAKE_MACOSX_RPATH 1)
endif()

add_library(mylib_static STATIC ${SRC})
add_library(mylib_shared SHARED ${SRC})