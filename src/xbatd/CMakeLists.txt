cmake_minimum_required(VERSION 3.12)
project(xbatd)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Optionally set default build type
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()


# Enable OpenSSL support for clickhouse-cpp
set(WITH_OPENSSL ON CACHE BOOL "Enable OpenSSL support" FORCE)

# Add clickhouse-cpp submodule
add_subdirectory(src/external/clickhouse-cpp)

# Explicit list of source files (avoids accidental inclusion of external dependencies)
set(SOURCES
  src/CAMDGPU.cpp
  src/CCpuStat.cpp
  src/CDataCollectionBase.cpp
  src/CEnergyIpmi.cpp
  src/CIOStat.cpp
  src/CInterconnectEthernet.cpp
  src/CInterconnectInfiniband.cpp
  src/CLikwidPerfctr.cpp
  src/CLogging.cpp
  src/CMemUsage.cpp
  src/CNvidiaGPU.cpp
  src/CXilinx.cpp
  src/ClickHouseWriter.cpp
  src/CurlClient.cpp
  src/helper.cpp
  src/main.cpp
  src/threadhelper.cpp
  src/topology.cpp
)

# Add executable
add_executable(${PROJECT_NAME} ${SOURCES})

# Third-party libraries bundled with xbatd
set(XBAT_ROOT_DIR "/usr/local/share/xbatd")
set(XBAT_LIB_DIR "${XBAT_ROOT_DIR}/lib")
set(XBAT_LIB64_DIR "${XBAT_ROOT_DIR}/lib64")

# LIKWID provides its own CMake package configuration
set(LIKWID_ROOT_DIR "${XBAT_ROOT_DIR}" CACHE PATH "Path to LIKWID installation")

find_package(likwid CONFIG REQUIRED
  COMPONENTS hwloc lua
  PATHS "${XBAT_ROOT_DIR}/share/likwid"
  NO_DEFAULT_PATH
)

# Find NVML headers from the installed CUDA version.
file(GLOB CUDA_INCLUDE_DIRS
  "/usr/local/cuda*/targets/x86_64-linux/include"
  "/usr/local/cuda*/include"
)

find_path(NVML_INCLUDE_DIR
  NAMES nvml.h
  PATHS ${CUDA_INCLUDE_DIRS}
  REQUIRED
)

message(STATUS "Found NVML headers: ${NVML_INCLUDE_DIR}")

# Include directories
target_include_directories(${PROJECT_NAME} PRIVATE
  src
  src/external/clickhouse-cpp
  src/external/clickhouse-cpp/contrib/absl
  src/external/nlohmann-json/include
  src/external/clipp/include
  /usr/local/share/xbatd/include
  /opt/rocm/include
  ${NVML_INCLUDE_DIR}
  ${LIKWID_INCLUDE_DIRS}
)

# TODO find better way of suppressing warnings for clickhouse-cpp submodule
set_source_files_properties(src/ClickHouseWriter.cpp PROPERTIES COMPILE_FLAGS "-w")

# Find Boost
# Boost.Log on older distros (e.g. el8/Boost 1.66) requires BOOST_ALL_DYN_LINK
# because the CMake FindBoost fallback module does not set it in the imported
# target's INTERFACE_COMPILE_DEFINITIONS, causing undefined reference errors.
set(Boost_USE_STATIC_LIBS OFF)
set(Boost_USE_MULTITHREADED ON)
set(Boost_USE_STATIC_RUNTIME OFF)
find_package(Boost REQUIRED COMPONENTS log log_setup system thread)

target_compile_definitions(${PROJECT_NAME} PRIVATE BOOST_ALL_DYN_LINK)

# Core libraries that are provided by the system (except for clickhouse-cpp)
target_link_libraries(${PROJECT_NAME} PRIVATE
  clickhouse-cpp-lib
  curl
  crypto
  pthread
  stdc++fs
  Boost::log
  Boost::log_setup
  Boost::system
  Boost::thread
)

# Use full paths to libraries since they are copied to specific locations in RPM build
target_link_libraries(${PROJECT_NAME} PRIVATE
  likwid::likwid
  ${XBAT_LIB64_DIR}/libnvidia-ml.so
  ${XBAT_LIB_DIR}/libamd_smi.so
)

# Install target (optional)
install(TARGETS ${PROJECT_NAME} DESTINATION /usr/local/bin)
install(FILES xbatd.service DESTINATION /etc/systemd/system)
