include(CMake Force)

set(CMAKE_C_COMPILER /usr/bin/gcc)

project(luci-app-rnas)

cmake_minimum_required(VERSION 3.5)

find_package(Git QUIET)

set(PKG_VERSION 1.0)
set(PKG_RELEASE 1)

option(BUILD_LUCI "Build LuCI interface" ON)
option(BUILD_UTILS "Build utility scripts" ON)

if(BUILD_LUCI)
	message(STATUS "Building LuCI interface")
endif()

if(BUILD_UTILS)
	message(STATUS "Building utility scripts")
endif()

message(STATUS "Package: luci-app-rnas v${PKG_VERSION}-${PKG_RELEASE}")
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "Install prefix: ${CMAKE_INSTALL_PREFIX}")
