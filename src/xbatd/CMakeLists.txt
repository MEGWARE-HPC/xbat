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

# Include directories
target_include_directories(${PROJECT_NAME} PRIVATE
  src
  src/external/clickhouse-cpp
  src/external/clickhouse-cpp/contrib/absl
  src/external/nlohmann-json/include
  src/external/clipp/include
  /usr/local/share/xbatd/include
  /usr/local/cuda-12.2/targets/x86_64-linux/include
  /opt/rocm-6.4.1/include
)

# TODO find better way of suppressing warnings for clickhouse-cpp submodule
set_source_files_properties(src/ClickHouseWriter.cpp PROPERTIES COMPILE_FLAGS "-w")

# Define library paths based on environment (RPM build vs local development)
set(XBAT_LIB_DIR "/usr/local/share/xbatd/lib")
set(XBAT_LIB64_DIR "/usr/local/share/xbatd/lib64")

# Add library search paths
link_directories(
  ${XBAT_LIB_DIR}
  ${XBAT_LIB64_DIR}
  /opt/rocm/lib
  /usr/lib64
  /usr/local/lib
)

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
  ${XBAT_LIB_DIR}/libquestdb_client.so
  ${XBAT_LIB64_DIR}/libnvidia-ml.so
  ${XBAT_LIB_DIR}/libamd_smi.so
  ${XBAT_LIB_DIR}/liblikwid.so
)

# Find Boost
find_package(Boost REQUIRED COMPONENTS log log_setup system thread)

# Install target (optional)
install(TARGETS ${PROJECT_NAME} DESTINATION /usr/local/bin)
install(FILES xbatd.service DESTINATION /etc/systemd/system)
