cmake_minimum_required(VERSION 3.19)

# Set policy CMP0177 to NEW
if(POLICY CMP0177)
  cmake_policy(SET CMP0177 NEW)
endif()

# Define project name
set(PROJECT_NAME "QtLean")
project(${PROJECT_NAME})

# Set the C++ standard to C++17
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Enable automatic invocation of MOC, UIC, and RCC
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

# Set CMAKE_PREFIX_PATH to help CMake find Qt6
set(CMAKE_PREFIX_PATH "C:/Qt/6.9.0/mingw_64/lib/cmake")

# Set environment variables
set(USERNAME $ENV{USERNAME})

# Define required Qt components
set(QT_VERSION 6)
set(REQUIRED_LIBS Core Gui Widgets)
set(REQUIRED_LIBS_QUALIFIED Qt6::Core Qt6::Gui Qt6::Widgets)

# Set asset directories
set(ASSETS src/assets)
set(ASSET_DIR "${CMAKE_BINARY_DIR}/home/${USERNAME}/.${PROJECT_NAME}/assets")
set(ASSET_DIR_DEB "${CMAKE_BINARY_DIR}/home/${USERNAME}/.${PROJECT_NAME}/assets")

# Include packaging information
include(FindPackageHandleStandardArgs)
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "QtLean -- a GUI interface to the Lean trading engine.")
set(CPACK_PACKAGE_VENDOR "Aaron Janeiro Stone")
set(CPACK_PACKAGE_CONTACT "ajstone@uwaterloo.ca")
set(CPACK_PACKAGE_VERSION_MAJOR "0")
set(CPACK_PACKAGE_VERSION_MINOR "7")
set(CPACK_PACKAGE_VERSION_PATCH "2")
set(CPACK_COMPONENT_LIBRARIES_DEPENDS "mono-native;python3.6;qt6")
set(CPACK_DEBIAN_PACKAGE_DEPENDS "mono-native;python3.6;qt6")
include(CPack)

# Find required packages
find_package(Qt${QT_VERSION} REQUIRED COMPONENTS ${REQUIRED_LIBS})

# Specify paths to external libraries
set(Python3_LIBRARY "C:/Users/losth/AppData/Local/Programs/Python/Python313/libs/python313.lib")
set(Python3_INCLUDE_DIR "C:/Users/losth/AppData/Local/Programs/Python/Python313/include")
set(MONO_INCLUDE_DIR "C:/Program Files/Mono/include/mono-2.0")
set(MONO_LIBRARY "C:/Program Files/Mono/lib/mono-2.0-sgen.lib")
set(MONOSGEN
::contentReference[oaicite:32]{index=32}