/**
 * @file threadhelper.hpp
 * @brief Helper functions for xbatd thread handling
 *
 ***********************************************/

#include "threadhelper.hpp"

#include <chrono>
#include <iostream>
#include <locale>
#include <sstream>

#include "CCpuStat.hpp"
#include "CEnergyIpmi.hpp"
#include "CIOStat.hpp"
#include "CInterconnectEthernet.hpp"
#include "CInterconnectInfiniband.hpp"
#include "CLikwidPerfctr.hpp"
#include "CMemUsage.hpp"
#include "CNvidiaGPU.hpp"
#include "CAMDGPU.hpp"
#include "CXilinx.hpp"
#include "topology.hpp"

/**
 * @brief Signals all measurement threads of current job to stop
 *
 * Iterates over all classes of the latest statusList entry and
 * signals them to stop their measurements.
 *
 */
void ThreadHelper::stop(std::unique_ptr<statusInfo> &statusList) {
    for (auto &entry : statusList->classList) {
        entry->stopMeasurement();
    }
}

/**
 * @brief Checks whether all threads are terminated
 *
 */
bool ThreadHelper::terminated(std::unique_ptr<statusInfo> &statusList) {
    int threadCount = statusList->classList.size();
    int stopped = 0;
    for (auto &entry : statusList->classList) {
        if (entry->getThreadStatus() != THREAD_RUNNING)
            stopped++;
    }
    return stopped == threadCount;
}

/**
 * @brief Initialize measurements
 *
 * TODO
 *
 * @param TODO
 */
void ThreadHelper::init(std::unique_ptr<statusInfo> &statusList, CQueue *queue, config_map &config, Topology::cpuTopology &topology) {
    /* Use StartTime of job as common synchronisation point across nodes */
    std::string output;
    std::chrono::time_point<std::chrono::system_clock> startTime;
    if (Helper::getCommandOutput("scontrol show job " + std::to_string(std::get<uint>(config["jobId"])) + " | grep StartTime ", output) == 0) {
        output = Helper::trimWhitespaces(output);
        std::vector<std::string> times;
        Helper::splitStr(output, " ", times);
        std::vector<std::string> values;
        Helper::splitStr(times[0], "=", values);
        startTime = Helper::parseTime(values[1]);
    } else {
        // fallback (mainly used for local testing)
        startTime = std::chrono::system_clock::now();
    }

    int interval = std::get<uint>(config["interval"]) * 1000;  // ms

    if (std::get<bool>(config["enableLikwid"]))
        statusList->classList.push_back(new CLikwidPerfctr(queue, startTime, interval, topology));
    statusList->classList.push_back(new CCpuStat(queue, startTime, interval, topology));
    statusList->classList.push_back(new CInterconnectEthernet(queue, startTime, interval));
    statusList->classList.push_back(new CInterconnectInfiniband(queue, startTime, interval));
    statusList->classList.push_back(new CIOStat(queue, startTime, interval));
    statusList->classList.push_back(new CEnergyIpmi(queue, startTime, interval));
    statusList->classList.push_back(new CMemUsage(queue, startTime, interval));
    statusList->classList.push_back(new CXilinx(queue, startTime, interval));
    statusList->classList.push_back(new CNvidiaGPU(queue, startTime, interval));
    statusList->classList.push_back(new CAMDGPU(queue, startTime, interval));

    for (auto &cls : statusList->classList)
        cls->startMeasurement();
}