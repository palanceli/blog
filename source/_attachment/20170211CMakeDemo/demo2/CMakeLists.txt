cmake_minimum_required (VERSION 2.6)

project(CMakeDemo)

add_subdirectory(mylib)
add_subdirectory(myexe)
add_subdirectory(googletest)

# 构建unittest的可执行项目
include_directories(${PROJECT_SOURCE_DIR}/googletest/googletest/include)
include_directories(${PROJECT_SOURCE_DIR}/include)

# 收集各子项的*.cpp、*.h文件
foreach ( folder myexe mylib)
  file(GLOB_RECURSE SRC "${PROJECT_SOURCE_DIR}/${folder}/*.cpp" "${PROJECT_SOURCE_DIR}/${folder}/*.h")
  list(APPEND ALL_SRC ${SRC})
endforeach(folder)
# 屏蔽main函数，因为gtest_main已经有了
LIST(REMOVE_ITEM ALL_SRC "${PROJECT_SOURCE_DIR}/myexe/main.cpp")

add_executable(myexe_test ${ALL_SRC})
target_link_libraries(myexe_test gtest_main)
