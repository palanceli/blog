cmake_minimum_required (VERSION 2.6)

include_directories(${PROJECT_SOURCE_DIR}/include)
set(SRC MyDemo.cpp MyDemo.h main.cpp ${PROJECT_SOURCE_DIR}/include/MyLib.h)
add_executable(myexe ${SRC})
target_link_libraries(myexe mylib_shared) # 静态链接mylib