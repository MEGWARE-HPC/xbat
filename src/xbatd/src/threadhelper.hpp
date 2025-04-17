/**
 * @file threadhelper.hpp
 * @brief Header for threadhelper.cpp
 *
 ***********************************************/

#ifndef THREADHELPER_HPP
#define THREADHELPER_HPP

#include <list>
#include <string>
#include <variant>

#include "CQueue.hpp"
#include "statusinfo.hpp"
#include "topology.hpp"
#include "definitions.hpp"

namespace ThreadHelper {
void init(std::unique_ptr<statusInfo> &, CQueue *, config_map &config, Topology::cpuTopology &);
void stop(std::unique_ptr<statusInfo> &);
bool terminated(std::unique_ptr<statusInfo> &);
}  // namespace ThreadHelper
#endif /* THREADHELPER_HPP */
