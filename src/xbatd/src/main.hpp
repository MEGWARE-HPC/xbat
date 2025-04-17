/**
 * @file main.hpp
 * @brief main header
 ***********************************************/

#ifndef MAIN_HPP
#define MAIN_HPP

#include <atomic>
#include <list>
#include <string>
#include <variant>
#include <vector>

#include "statusinfo.hpp"
#include "topology.hpp"
#include "definitions.hpp"

void sigHandler(int);
void watchdog(std::unique_ptr<statusInfo> &);
int measure(config_map &, Topology::cpuTopology &);

std::vector<std::string> flopBenchmarks = {
    "peakflops_sp",
    "peakflops_sp_sse",
    "peakflops_sp_avx",
    "peakflops_sp_avx_fma",
    "peakflops_sp_avx512",
    "peakflops_sp_avx512_fma",
    "peakflops",
    "peakflops_sse",
    "peakflops_avx",
    "peakflops_avx_fma",
    "peakflops_avx512",
    "peakflops_avx512_fma"};

#endif