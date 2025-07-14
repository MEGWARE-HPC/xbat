cmake_minimum_required(VERSION 3.12)
project(xbatd)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Optionally set default build type
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

# Prevent clickhouse-cpp from building unnecessary targets
if(NOT DEFINED BUILD_BENCHMARK)
  set(BUILD_BENCHMARK OFF CACHE BOOL "Disable benchmarks in clickhouse-cpp")
endif()

if(NOT DEFINED BUILD_TESTS)
  set(BUILD_TESTS OFF CACHE BOOL "Disable tests in clickhouse-cpp")
endif()

# Add clickhouse-cpp submodule
add_subdirectory(src/external/clickhouse-cpp)

# Collect sources
file(GLOB_RECURSE SOURCES
  src/*.cpp
)

# Add executable
add_executable(${PROJECT_NAME} ${SOURCES})

# Include directories
target_include_directories(${PROJECT_NAME} PRIVATE
  src
  src/external/clickhouse-cpp
  src/external/clickhouse-cpp/contrib/absl
  /usr/local/share/xbatd/include
  /usr/local/cuda-12.2/targets/x86_64-linux/include
  /opt/rocm-6.4.1/include
)

# Link libraries
target_link_libraries(${PROJECT_NAME} PRIVATE
  clickhouse-cpp-lib
  likwid
  curl
  questdb_client
  stdc++fs
  nvidia-ml
  crypto
  amd_smi
  pthread
  Boost::log
  Boost::log_setup
  Boost::system
  Boost::thread
)

# Find Boost
find_package(Boost REQUIRED COMPONENTS log log_setup system thread)

# Compiler warnings
target_compile_options(${PROJECT_NAME} PRIVATE -Wall -Wextra -Wpedantic)

# Install target (optional)
install(TARGETS ${PROJECT_NAME} DESTINATION /usr/local/bin)
install(FILES xbatd.service DESTINATION /etc/systemd/system)
