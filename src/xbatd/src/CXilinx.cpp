/**
 * @file CXilinx.cpp
 * @brief Class for measuring Xilinx FPGA power usage
 *
 ***********************************************/

#include "CXilinx.hpp"

#include <filesystem>
#include <iostream>
#include <regex>

namespace fs = std::filesystem;

/**
 * @brief Construct a new CXilinx::CXilinx object and initialize parameters
 *
 * @param dataQueue Pointer to queue for data
 * @param timestamp Starting timestamp
 * @param interval Interval duration in seconds
 */
CXilinx::CXilinx(CQueue *dataQueue, std::chrono::time_point<std::chrono::system_clock> startTime, uint64_t interval) {
    this->dataQueue = dataQueue;
    this->interval = interval;
    intervalStart = startTime;
    moduleName = "XilinxFPGA";
    launchMutex.unlock();
}

/**
 * @brief Destroy the CXilinx::CXilinx object but only after measurement is completed
 *
 */
CXilinx::~CXilinx() {
    /* Destruct only if measure() already returned */
    cleanUpMutex.lock();
    cleanUpMutex.unlock();
}

/**
 * @brief Measure FPGA power usage
 *
 *
 */
int CXilinx::measure() {
    logger.setModule(moduleName);
    if (prepare() <= 0)
        return 1;

    while (!terminate) {
        synchronizeMeasurement();
        if (readUsage() <= 0)
            return 1;

        sleepUntilIntervalEnd();

        if (terminate)
            return 0;

        intervalCleanup();
    }
    return 0;
}

int CXilinx::readUsage() {
    int devicesFound = 0;
    for (std::string &bdf : bdfs) {
        std::string path = "/sys/bus/pci/devices/0000:" + bdf + "/hwmon/";

        if (!fs::exists(path)) {
            logger.log(CLogging::error, "Error '" + path + "' not found");
            return 1;
        }

        // filesystem does not support wildcards (hwmon*) -> iterate over directory and use first one
        for (auto &hwmon : fs::directory_iterator(path)) {
            path = hwmon / fs::path("power1_input");
            break;
        }

        std::string valueStr;
        if (Helper::readFileToString(path, valueStr) != 0) {
            logger.log(CLogging::error, "Error reading '" + path + "'");
            continue;
        }

        // values are stored in uW
        double value = std::stoll(valueStr) / 1000000.0;
        dataQueue->push(CQueue::DeviceMeasurement<double>{"fpga_power", "device", bdf, value, intervalEnd});
        devicesFound++;
    }
    return devicesFound;
}

// retrieve board definition files (bdfs)
int CXilinx::prepare() {
    std::string result;
    std::string cmd = "lspci | grep -i 'Processing accelerators: Xilinx'";
    if (Helper::getCommandOutput(cmd, result) != 0) {
        logger.log(CLogging::error, "Error reading device info for Xilinx FPGA");
        return -1;
    }
    std::vector<std::string> entries;
    Helper::splitStr(result, "\n", entries);
    for (std::string &entry : entries) {
        entry = Helper::trimWhitespaces(entry);
        std::vector<std::string> split;
        Helper::splitStr(entry, " ", split);
        std::string bdf = split[0];
        /* FPGAs may consist of multiple bdfs but monitoring only one is sufficient -> use .1 suffix */
        if (Helper::endsWith(bdf, ".1")) {
            bdfs.push_back(bdf);
            logger.log(CLogging::debug, "[CXilinx] adding bdf " + bdf);
        }
    }

    return bdfs.size();
}