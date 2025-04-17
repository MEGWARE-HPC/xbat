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

    std::map<std::string, std::string> tags = {{"level", "node"}};
    std::vector<CQueue::ILP<double>> usage = {
        {"mem_usage",
         tags,
         ((values["MemTotal"] - values["MemAvailable"]) / (double)values["MemTotal"]) * 100,
         intervalEnd},
        {"mem_swap_usage",
         tags,
         ((values["SwapTotal"] - values["SwapFree"]) / (double)values["SwapTotal"]) * 100,
         intervalEnd},
    };

    dataQueue->pushMultiple<double>(usage);

    std::vector<CQueue::ILP<int64_t>> used = {
        {"mem_used",
         tags,
         values["MemTotal"] - values["MemAvailable"],
         intervalEnd},
        {"mem_swap_used",
         tags,
         values["SwapTotal"] - values["SwapFree"],
         intervalEnd},
        {"mem_buffers",
         tags,
         values["MemBuffers"],
         intervalEnd},
        {"mem_cached",
         tags,
         values["MemCached"],
         intervalEnd},
    };

    dataQueue->pushMultiple<int64_t>(used);

    return 0;
}