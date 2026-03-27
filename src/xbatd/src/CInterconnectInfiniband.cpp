/**
 * @file CInterconnectEthernet.cpp
 * @brief Class for measuring ethernet usage
 *
 ***********************************************/

#include "CInterconnectInfiniband.hpp"

#include <filesystem>
#include <iostream>

namespace fs = std::filesystem;

/**
 * @brief Construct a new CInterconnectInfiniband::CInterconnectInfiniband object and initialize parameters
 *
 * @param dataQueue Pointer to queue for data
 * @param timestamp Starting timestamp
 * @param interval Interval duration in seconds
 */
CInterconnectInfiniband::CInterconnectInfiniband(CQueue *dataQueue, std::chrono::time_point<std::chrono::system_clock> startTime, uint64_t interval) {
    this->dataQueue = dataQueue;
    this->interval = interval;
    intervalStart = startTime;
    moduleName = "Infiniband";
    launchMutex.unlock();
}

/**
 * @brief Destroy the CInterconnectInfiniband::CInterconnectInfiniband object but only after measurement is completed
 */
CInterconnectInfiniband::~CInterconnectInfiniband(void) {
    /* Destruct only if measure() already returned */
    cleanUpMutex.lock();
    cleanUpMutex.unlock();
}

/**
 * @brief Measure infiniband usage
 *
 * Overwrite measure() of the base class, collect the infiniband usage data during the interval
 * and push it to the data queue.
 *
 */
int CInterconnectInfiniband::measure() {
    logger.setModule(moduleName);
    while (!terminate) {
        synchronizeMeasurement();

        std::map<std::string, uint64_t> previous, current;

        if (terminate)
            return 0;

        if (readInfiniband(previous) != 0)
            return 1;

        sleepUntilIntervalEnd();

        if (terminate)
            return 0;

        if (readInfiniband(current) != 0)
            return 1;

        calculateUsage(previous, current);

        intervalCleanup();
    }
    return 0;
}

void CInterconnectInfiniband::calculateUsage(std::map<std::string, uint64_t> &previous, std::map<std::string, uint64_t> &current) {
    std::map<std::string, uint64_t> difference;
    for (auto &entry : current) {
        std::string key = entry.first;
        difference[key] = current[key] - previous[key];
    }

    double intervalS = interval / 1000;
    for (auto &entry : difference) {
        if (!metricInfo.count(entry.first)) continue;

        auto meta = metricInfo[entry.first];
        double value = (entry.second / intervalS) * meta.scale;

        dataQueue->push(CQueue::BasicMeasurement<double>{meta.label, "node", value, intervalEnd});
    }
}

/**
 * @brief Read infiniband data and summarize across all adapters and ports
 *
 * @return 0 On success
 * @return 1 If no infiniband was detected
 */
int CInterconnectInfiniband::readInfiniband(std::map<std::string, uint64_t> &results) {
    std::string infinibandRoot = "/sys/class/infiniband";

    if (!fs::exists(infinibandRoot)) {
        logger.log(CLogging::debug, "Infiniband not present");
        return 1;
    }

    for (auto &device : fs::directory_iterator(infinibandRoot)) {
        const auto deviceName = device.path().filename().string();

        const auto portsDir = device / fs::path("ports");
        if (fs::exists(portsDir)) {
            for (auto &port : fs::directory_iterator(portsDir)) {
                const auto portNumber = port.path().filename().string();

                const auto counterDir = port / fs::path("counters");
                if (fs::exists(counterDir)) {
                    for (auto &counterName : metricCounters) {
                        const auto metricPath = counterDir / counterName;
                        if (fs::exists(metricPath)) {
                            std::string counterContent;
                            if (Helper::readFileToString(metricPath, counterContent) != 0)
                                return 1;

                            uint64_t value = std::stoull(Helper::trimWhitespaces(counterContent));
                            if (!results.count(counterName))
                                results[counterName] = 0;

                            results[counterName] += value;
                        }
                    }
                }
            }
        }
    }
    return 0;
}
