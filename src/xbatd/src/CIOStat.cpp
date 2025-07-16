/**
 * @file CIOStat.cpp
 * @brief Class for measuring I/O usage
 *
 ***********************************************/

#include "CIOStat.hpp"

#include <math.h>

#include <iostream>

#include "nlohmann/json.hpp"

/**
 * @brief Construct a new CIOStat::CIOStat object and initialize parameters
 *
 * @param dataQueue Pointer to queue for data
 * @param timestamp Starting timestamp
 * @param interval Interval duration in seconds
 */
CIOStat::CIOStat(CQueue *dataQueue, std::chrono::time_point<std::chrono::system_clock> startTime, uint64_t interval) {
    this->dataQueue = dataQueue;
    this->interval = interval;
    intervalStart = startTime;
    moduleName = "Disk";
    launchMutex.unlock();
}

/**
 * @brief Destroy the CIOStat::CIOStat object but only after measurement is completed
 */
CIOStat::~CIOStat(void) {
    /* Destruct only if measure() already returned */
    cleanUpMutex.lock();
    cleanUpMutex.unlock();
}

/**
 * @brief Measure I/O usage
 *
 * Overwrite measure() of the base class, collect the I/O usage data during the interval
 * and push it to the data queue.
 *
 */
int CIOStat::measure() {
    logger.setModule(moduleName);
    while (!terminate) {
        synchronizeMeasurement();

        if (terminate)
            return 0;

        if (parseIOStat() != 0)
            return 1;

        intervalCleanup();
    }
    return 0;
}

// TODO read from /proc/diskstats instead of relying on third party tool
int CIOStat::parseIOStat() {
    /* Iostat -o(output) JSON -d(devices only) -e(extended) -y(omit first report which shows statistics since boot) <Intervalsize> <Iterations>.
     * Iostat will take <timeLeft> to return thus no further sleep is required.
     */
    std::string result;
    if (Helper::getCommandOutput("iostat -o JSON -dx -y " + std::to_string(int(timeLeft / 1000)) + " 1", result) != 0) {
        if (!terminate)
            logger.log(CLogging::error, "Error executing iostat - iostat may not be installed");
        return 1;
    }

    nlohmann::json iostat = nlohmann::json::parse(result);
    if (!iostat.contains("sysstat") || !iostat["sysstat"].contains("hosts") || (iostat["sysstat"]["hosts"].size() < 1))
        return 1;

    auto disks = iostat["sysstat"]["hosts"][0]["statistics"][0]["disk"];

    for (auto const &disk : disks) {
        std::string device = disk["disk_device"];
        if (device.find("loop") != std::string::npos) continue;
        for (auto &entry : disk.items()) {
            std::string key = entry.key();
            if (key == "disk_device") continue;
            double value = entry.value();
            if (!metricInfo.count(key)) continue;

            auto meta = metricInfo[key];

            // Push to device measurement queue with scaled value
            dataQueue->push(CQueue::DeviceMeasurement<double>{meta.label, "device", device, value * meta.scale, intervalEnd});
        }
    }
    return 0;
}