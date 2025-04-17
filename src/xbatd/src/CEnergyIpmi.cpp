/**
 * @file CEnergyIpmi.cpp
 * @brief Class for measuring energy usage via IPMI
 *
 ***********************************************/

#include "CEnergyIpmi.hpp"

#include <iostream>
#include <regex>

/**
 * @brief Construct a new CEnergyIpmi::CEnergyIpmi object and initialize parameters
 *
 * @param dataQueue Pointer to queue for data
 * @param timestamp Starting timestamp
 * @param interval Interval duration in seconds
 */
CEnergyIpmi::CEnergyIpmi(CQueue *dataQueue, std::chrono::time_point<std::chrono::system_clock> startTime, uint64_t interval) {
    this->dataQueue = dataQueue;
    this->interval = interval;
    intervalStart = startTime;
    moduleName = "IPMI";
    launchMutex.unlock();
}

/**
 * @brief Destroy the CEnergyIpmi::CEnergyIpmi object but only after measurement is completed
 */
CEnergyIpmi::~CEnergyIpmi(void) {
    /* Destruct only if measure() already returned */
    cleanUpMutex.lock();
    cleanUpMutex.unlock();
}

/**
 * @brief Measure energy usage.
 *
 * Overwrite measure() of the base class, collect the energy usage data as a snapshot wihtin the interval
 * and push it to the data queue.
 *
 */
int CEnergyIpmi::measure() {
    logger.setModule(moduleName);
    std::vector<std::string> entryList = {
        "Instantaneous power reading"};

    bool bridged = false;

    while (!terminate) {
        synchronizeMeasurement();

        if (terminate)
            return 0;

        std::string result;
        // try standard command first
        if (bridged || Helper::getCommandOutput("ipmitool dcmi power reading", result) != 0) {
            // try with bridged request for intel boards
            if (Helper::getCommandOutput("ipmitool -b 0x06 -t 0x2c dcmi power reading", result) != 0) {
                logger.log(CLogging::error, "Error reading power usage - are IPMI and ipmitool available on this machine?");
                return 1;
            }
            bridged = true;
        }

        Helper::filterLinesNotContaining(entryList, result);
        if (parse(result) != 0)
            return 1;

        sleepUntilIntervalEnd();

        if (terminate)
            return 0;

        intervalCleanup();
    }
    return 0;
}

int CEnergyIpmi::parse(std::string &result) {
    std::vector<std::string> split;
    Helper::splitStr(result, ":", split);
    if (split.size() != 2) return 1;
    std::string valueStr = Helper::extractNumber(split[1]);

    if (!valueStr.length()) return 1;
    int64_t value = std::stoll(valueStr);
    std::map<std::string, std::string> tags = {{"level", "node"}};
    CQueue::ILP<int64_t> ilp = {
        "ipmi_power_system",
        tags,
        value,
        intervalEnd};

    dataQueue->pushSingle<int64_t>(ilp);

    return 0;
}
