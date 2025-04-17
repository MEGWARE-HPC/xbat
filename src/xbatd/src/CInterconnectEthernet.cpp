/**
 * @file CInterconnectEthernet.cpp
 * @brief Class for measuring ethernet usage
 *
 ***********************************************/

#include "CInterconnectEthernet.hpp"

#include <iostream>

#define DATAPATH "/proc/net/dev" /**< Path to ethernet usage data*/

/**
 * @brief Construct a new CInterconnectEthernet::CInterconnectEthernet object and initialize parameters
 *
 * @param dataQueue Pointer to queue for data
 * @param timestamp Starting timestamp
 * @param interval Interval duration in seconds
 */
CInterconnectEthernet::CInterconnectEthernet(CQueue *dataQueue, std::chrono::time_point<std::chrono::system_clock> startTime, uint64_t interval) {
    this->dataQueue = dataQueue;
    this->interval = interval;
    intervalStart = startTime;
    moduleName = "Ethernet";
    launchMutex.unlock();
}

/**
 * @brief Destroy the CInterconnectEthernet::CInterconnectEthernet object but only after measurement is completed
 */
CInterconnectEthernet::~CInterconnectEthernet(void) {
    cleanUpMutex.lock();
    cleanUpMutex.unlock();
}

/**
 * @brief Measure ethernet usage
 *
 * Overwrite measure() of the base class, collect the ethernet usage data during the interval
 * and push it to the data queue.
 *
 */
int CInterconnectEthernet::measure() {
    logger.setModule(moduleName);
    while (!terminate) {
        synchronizeMeasurement();

        if (terminate)
            return 0;

        std::map<std::string, uint64_t> previous, current;

        if (readProc(previous) != 0)
            return 1;

        sleepUntilIntervalEnd();

        if (terminate)
            return 0;

        if (readProc(current) != 0)
            return 1;

        calculateUsage(previous, current);

        intervalCleanup();
    }
    return 0;
}

// TODO share code with other interconnection calculations
void CInterconnectEthernet::calculateUsage(std::map<std::string, uint64_t> &previous, std::map<std::string, uint64_t> &current) {
    std::map<std::string, uint64_t> difference;
    for (auto &entry : current) {
        difference[entry.first] = entry.second - previous[entry.first];
    }

    double intervalS = interval / 1000;
    for (auto &entry : difference) {
        if (!metricInfo.count(entry.first))
            continue;

        auto meta = metricInfo[entry.first];
        double value = (entry.second / intervalS) * meta.scale;
        std::map<std::string, std::string> tags = {
            {"level", "node"}};

        CQueue::ILP<double> ilp = {
            meta.label,
            tags,
            value,
            intervalEnd};
        dataQueue->pushSingle(ilp);
    }
}

int CInterconnectEthernet::readProc(std::map<std::string, uint64_t> &results) {
    std::string raw;
    if (Helper::readFileToString(DATAPATH, raw) != 0)
        return 1;

    Helper::eraseLinesFromStart(raw, 1);

    std::istringstream iss(raw);
    std::string line;
    std::vector<std::string> headers;
    while (std::getline(iss, line)) {
        line = Helper::trimWhitespaces(line);

        // header
        if (line.find("|") != std::string::npos) {
            std::vector<std::string> s;
            Helper::splitStr(line, "|", s);
            Helper::splitStr(s[1] + " " + s[2], " ", headers);
            continue;
        }

        size_t start = line.find(":");

        if (Helper::startsWith(line, "lo") || start == std::string::npos)
            continue;

        line = line.substr(start + 1, line.length());

        std::vector<std::string> values;
        Helper::splitStr(line, " ", values);

        size_t half = values.size() / 2;

        // aggregate over all interfaces
        for (size_t i = 0; i < values.size(); i++) {
            std::string prefix = i < half ? "rcv" : "xmit";
            std::string name = prefix + "_" + headers[i];
            if (!results.count(name))
                results[name] = 0;
            results[name] += std::stoull(values[i]);
        }
    }
    return 0;
}