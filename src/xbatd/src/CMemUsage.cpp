/**
 * @file CMemUsage.cpp
 * @brief Class for measuring memory usage
 *
 ***********************************************/

#include "CMemUsage.hpp"

#include <iostream>

#define MEMINFO "/proc/meminfo" /**< Path to memory usage data*/

/**
 * @brief Construct a new CMemUsage::CMemUsage object and initialize parameters
 *
 * @param dataQueue Pointer to queue for data
 * @param timestamp Starting timestamp
 * @param interval Interval duration in seconds
 */
CMemUsage::CMemUsage(CQueue *dataQueue, std::chrono::time_point<std::chrono::system_clock> startTime, uint64_t interval) {
    this->dataQueue = dataQueue;
    this->interval = interval;
    intervalStart = startTime;
    moduleName = "Memory";
    intervalEnd = std::chrono::system_clock::now();
    launchMutex.unlock();
}

/**
 * @brief Destroy the CMemUsage::CMemUsage object but only after measurement is completed
 *
 */
CMemUsage::~CMemUsage(void) {
    /* Destruct only if measure() already returned */
    cleanUpMutex.lock();
    cleanUpMutex.unlock();
}

/**
 * @brief Measure memory usage
 *
 * Overwrite measure() of the base class, collect the memory usage data as a snapshot within the interval
 * and push it to the data queue.
 *
 * @return 0 Success
 * @return 1 Error
 */
int CMemUsage::measure() {
    logger.setModule(moduleName);
    while (!terminate) {
        synchronizeMeasurement();

        if (terminate)
            return 0;

        if (readProc() != 0) {
            logger.log(CLogging::error, "Error reading " + std::string(MEMINFO));
            return 1;
        }

        sleepUntilIntervalEnd();

        if (terminate)
            return 0;

        intervalCleanup();
        intervalEnd = intervalEnd + std::chrono::seconds(interval / 1000);
    }
    return 0;
}

int CMemUsage::readProc() {
    std::string content;
    if (Helper::readFileToString(MEMINFO, content) != 0) {
        return 1;
    }

    std::vector<std::string> entryNames = {
        "MemTotal",
        "MemFree",
        "MemAvailable",
        "Buffers",
        "Cached",
        "SwapCached",
        "SwapTotal",
        "SwapFree"};

    Helper::filterLinesNotContaining(entryNames, content, true);

    std::vector<std::string> lines;
    Helper::splitStr(content, "\n", lines);

    std::map<std::string, int64_t> values;

    for (auto &line : lines) {
        std::vector<std::string> keyValue;
        Helper::splitStr(line, ":", keyValue);
        if (keyValue.size() != 2) continue;
        std::string key = Helper::trimWhitespaces(keyValue[0]);
        std::string value = Helper::trimWhitespaces(keyValue[1]);
        int factor = 1024;
        if (Helper::endsWith(value, " mB"))
            factor = factor * 1024;
        value.erase(value.length() - 2);

        values[key] = std::stoll(Helper::trimWhitespaces(value)) * factor;
    }

    // Push double measurements (percentages)
    dataQueue->push(CQueue::BasicMeasurement<double>{"mem_usage", "node", 
                                                     ((values["MemTotal"] - values["MemAvailable"]) / (double)values["MemTotal"]) * 100,
                                                     intervalEnd});
    dataQueue->push(CQueue::BasicMeasurement<double>{"mem_swap_usage", "node",
                                                     ((values["SwapTotal"] - values["SwapFree"]) / (double)values["SwapTotal"]) * 100,
                                                     intervalEnd});

    // Push int measurements (bytes)
    dataQueue->push(CQueue::BasicMeasurement<int64_t>{"mem_used", "node",
                                                      values["MemTotal"] - values["MemAvailable"],
                                                      intervalEnd});
    dataQueue->push(CQueue::BasicMeasurement<int64_t>{"mem_swap_used", "node",
                                                      values["SwapTotal"] - values["SwapFree"],
                                                      intervalEnd});
    dataQueue->push(CQueue::BasicMeasurement<int64_t>{"mem_buffers", "node",
                                                      values["Buffers"],
                                                      intervalEnd});
    dataQueue->push(CQueue::BasicMeasurement<int64_t>{"mem_cached", "node",
                                                      values["Cached"],
                                                      intervalEnd});

    return 0;
}