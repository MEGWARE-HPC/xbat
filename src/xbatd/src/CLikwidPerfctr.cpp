/**
 * @file CLikwidPerfctr.cpp
 * @brief Class for measurement via LIKWID
 *
 ***********************************************/

#include "CLikwidPerfctr.hpp"

#include <likwid.h>
#include <math.h>
#include <unistd.h>

#include <algorithm>
#include <iostream>
#include <numeric>
#include <regex>
#include <thread>

#include "nlohmann/json.hpp"

/**
 * @brief Construct a new CLikwidPerfctr::CLikwidPerfctr object and initialize parameters
 *
 * @param dataQueue Pointer to queue for data
 * @param timestamp Starting timestamp
 * @param interval Interval duration in seconds
 */
CLikwidPerfctr::CLikwidPerfctr(CQueue *dataQueue, std::chrono::time_point<std::chrono::system_clock> startTime, uint64_t interval, const Topology::cpuTopology &topology) {
    this->dataQueue = dataQueue;
    this->interval = interval;
    this->topology = topology;
    intervalStart = startTime;
    moduleName = "LIKWID";
    launchMutex.unlock();
}

/**
 * @brief Destroy the CLikwidPerfctr::CLikwidPerfctr object but only after measurement is completed
 *
 * TODO improve termination behaviour in respect to LIKWID!
 */
CLikwidPerfctr::~CLikwidPerfctr(void) {
    /* Destruct only if measure() already returned */
    cleanUpMutex.lock();
    cleanUpMutex.unlock();
}

/**
 * @brief Measure via LIKWID
 *
 * Overwrite measure() of the base class, collect the usage data based on the LIKWID sets during the interval
 * and push it to the data queue.
 *
 * @return 0 Success
 * @return 1 Error
 */
int CLikwidPerfctr::measure() {
    logger.setModule(moduleName);
    // TODO check for failure
    parseMetrics();

    if (prepareMeasurements() != 0)
        return 1;

    while (!terminate) {
        synchronizeMeasurement();

        if (terminate) {
            perfmon_finalize();
            return 0;
        }

        if (measureSets() != 0)
            return 1;

        intervalCleanup();
    }
    return 0;
}

void CLikwidPerfctr::AddHPMThread(int cpu) {
    if (HPMaddThread(cpu) != 0)
        CLogging::log("LIKWID", CLogging::error, "HPMaddThread failed for cpu " + cpu);
}

void CLikwidPerfctr::parseMetrics() {
    std::string metricStr;
    Helper::readFileToString("/usr/local/share/xbatd/metrics.json", metricStr);

    nlohmann::json metricInfo = nlohmann::json::parse(metricStr);

    for (auto &set : metricInfo.items()) {
        std::string setName = set.key();
        auto metricObj = set.value();
        std::map<std::string, metricMeta> metricMapping;
        for (auto &metric : metricObj.items()) {
            std::string metricNameRaw = metric.key();
            auto metricDetails = metric.value();

            std::string metricName = metricNameRaw;
            int scale = 1;
            std::string level = "";

            if (metricDetails.contains("name"))
                metricName = metricDetails["name"];

            if (metricDetails.contains("scale"))
                scale = metricDetails["scale"];

            if (metricDetails.contains("level"))
                level = metricDetails["level"];

            metricMeta meta = {
                "likwid_" + metricName,
                scale,
                level};
            metricMapping[metricNameRaw] = meta;
        }
        metrics[setName] = metricMapping;
    }
}

/**
 * @brief Retrieve available sets
 *
 * @param availableGroups Reference to vector to contain all groups upon returning
 * @return 0 Success
 * @return 1 Error
 */
int CLikwidPerfctr::getAvailableGroups(std::vector<std::string> &availableGroups) {
    char **groupList = NULL;
    char **shortInfoList = NULL;
    char **longInfoList = NULL;
    int groupCount;
    if ((groupCount = perfmon_getGroups(&groupList, &shortInfoList, &longInfoList)) < 0) {
        logger.log(CLogging::error, "Error collecting available LIKWID eventsets");
        return 1;
    }

    for (int i = 0; i < groupCount; i++) {
        if (groupList[i]) {
            availableGroups.push_back(groupList[i]);
        }
    }

    perfmon_returnGroups(groupCount, groupList, shortInfoList, longInfoList);

    return groupCount;
}

/**
 * @brief Carry out measurements via LIKWID-API
 *
 * Retrieves topology information to know which cpu/core/thread to monitor.
 * Registers eventsets after initialization and starts measurements by switching between
 * the different sets and sleeping while measuring.
 *
 * @return 0 Success
 * @return 1 Error
 */
int CLikwidPerfctr::measureSets() {
    logger.log(CLogging::debug, "expected overhead: " + std::to_string(cycleOverhead) + " | timeleft: " + std::to_string(timeLeft));

    /* cancel measurements as soon as they can no longer be conducted within the required timeframe */
    if (cycleOverhead > timeLeft)
        return 1;

    uint64_t predictedAvailableInterval = timeLeft - cycleOverhead;

    int64_t setTime = floor((predictedAvailableInterval / gids.size())); /* milliseconds */
    auto start = std::chrono::high_resolution_clock::now();
    if (!gids.size()) {
        logger.log(CLogging::warning, "No GroupIds available. Stopping measurements");
        perfmon_finalize();
        return 1;
    }

    /* Gather information about the overhead of each run to adjust available time for measurements */
    std::vector<uint64_t> currentCycleOverheads;
    uint64_t overhead;
    // TODO gather multiple times per interval for better distribution on higher sampling rates
    for (size_t i = 0; i < gids.size(); i++) {
        if (terminate) {
            perfmon_finalize();
            return 0;
        }

        start = std::chrono::high_resolution_clock::now();
        if (perfmon_setupCounters(gids[i]) != 0) {
            logger.log(CLogging::error, "Error setting up counter for gid " + gids[i]);
            perfmon_finalize();
            return 1;
        }
        if (perfmon_startCounters() != 0) {
            logger.log(CLogging::error, "Error starting counter for gid " + gids[i]);
            perfmon_finalize();
            return 1;
        }
        overhead = std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::high_resolution_clock::now() - start).count();
        currentCycleOverheads.push_back(overhead);

        sleepMillisecondsAndCheck(setTime);

        start = std::chrono::high_resolution_clock::now();
        if (perfmon_stopCounters() != 0) {
            logger.log(CLogging::error, "Error stopping counter for gid " + gids[i]);
            perfmon_finalize();
            return 1;
        }
        overhead = std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::high_resolution_clock::now() - start).count();
        currentCycleOverheads.push_back(overhead);
    }

    std::vector<int> channelBasedMemorySets = {};
    for (size_t i = 0; i < gids.size(); i++) {
        std::string setName = setList[i];
        if (std::regex_match(setName, std::regex("MEM\\d+")))
            channelBasedMemorySets.push_back(i);
    }

    start = std::chrono::high_resolution_clock::now();

    int metricCount;
    size_t cpusCount = cpus.size();
    std::vector<CQueue::ILP<double>> results;
    std::string collection_level = topology.smt ? "thread" : "core";
    for (size_t i = 0; i < gids.size(); i++) {
        metricCount = perfmon_getNumberOfMetrics(gids[i]);
        std::string setName = setList[i];

        // for zen3
        bool multiSetMemory = Helper::vectorContains(channelBasedMemorySets, static_cast<int>(i));

        // aggregate all channels on first set and skip others
        if (multiSetMemory) {
            if (setName != "MEM1")
                continue;
            setName = "MEM";
        }

        for (int k = 0; k < metricCount; k++) {
            std::string metricName = std::string(perfmon_getMetricName(gids[i], k));
            // remove unit
            if (metricName.find("[") != std::string::npos) {
                std::vector<std::string> split;
                Helper::splitStr(metricName, "[", split);
                metricName = split[0];
            }

            // remove additional info like "(channel 0-3)"
            if (metricName.find("(") != std::string::npos) {
                std::vector<std::string> split;
                Helper::splitStr(metricName, "(", split);
                metricName = split[0];
            }

            metricName = Helper::trimWhitespaces(metricName);

            if (!metrics.count(setName) || !metrics[setName].count(metricName))
                continue;

            auto metricMeta = metrics[setName][metricName];
            std::string level = metricMeta.level.length() ? metricMeta.level : collection_level;

            // socket level: first thread of first core of each socket contains values (WARNING: different ordering of hwthreads when SMT is enabled, consult likwid-topology)
            // node level: first hwThread contains value
            // std::cout << setName << "|" << metricName << "|" << level << " - " << std::endl;
            for (size_t l = 0; l < cpusCount; l++) {
                if (level == "socket" && (l % topology.coresPerSocket != 0 || topology.hwThreads[l].thread != "0"))
                    continue;
                if (level == "node" && l != 0)
                    break;
                std::map<std::string, std::string> tags = {{"level", level}};

                tags["thread"] = std::to_string(topology.hwThreads[l].hwThread);
                tags["core"] = topology.hwThreads[l].core;
                tags["socket"] = topology.hwThreads[l].socket;
                tags["numa"] = topology.hwThreads[l].numa;

                double value = 0.0;
                if (!multiSetMemory) {
                    value = perfmon_getLastMetric(gids[i], k, l);
                } else {
                    for (auto &m : channelBasedMemorySets) {
                        double tmp = perfmon_getLastMetric(gids[m], k, l);
                        if (!std::isnan(tmp))
                            value += tmp;
                    }
                }

                if (std::isnan(value)) value = 0.0;

                // std::cout << value << ",";

                CQueue::ILP<double>
                    ilp = {
                        metricMeta.label,
                        tags,
                        value * metricMeta.scale,
                        intervalEnd};
                results.push_back(ilp);
            }
            // std::cout << std::endl;
        }
    }

    dataQueue->pushMultiple<double>(results);

    overhead = std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::high_resolution_clock::now() - start).count();
    currentCycleOverheads.push_back(overhead);

    overhead = std::accumulate(currentCycleOverheads.begin(), currentCycleOverheads.end(), 0.0);
    logger.log(CLogging::debug, "Current Cycle: " + std::to_string(overhead / 1000) + " (ms)");
    /* account for old overhead when calculating next overhad - current overhead has more weight
     * overhead converted from microseconds to milliseconds
     */
    cycleOverhead = (cycleOverhead + 3 * (overhead / 1000)) / 4;
    logger.log(CLogging::debug, "Next Predicted Cycle (ms): " + std::to_string(cycleOverhead));
    return 0;
}

int CLikwidPerfctr::prepareMeasurements() {
    // perfmon_setVerbosity(3);
    auto start = std::chrono::high_resolution_clock::now();
    if (topology_init() != 0) {
        logger.log(CLogging::error, "Error initialising topology");
        return 1;
    }
    // TODO use topology module
    start = std::chrono::high_resolution_clock::now();
    CpuTopology_t topology = get_cpuTopology();
    for (uint32_t i = 0; i < topology->numHWThreads; i++) {
        if (topology->threadPool[i].inCpuSet) {
            cpus.push_back(topology->threadPool[i].apicId);
        }
    }
    start = std::chrono::high_resolution_clock::now();
    topology_finalize();

    // set direct access mode
    HPMmode(ACCESSMODE_DIRECT);
    if (HPMinit() != 0) {
        logger.log(CLogging::error, "Could not initialize HPM module");
        return 1;
    }

    /*
     * USE ONLY WITH ACCESSMODE_DAEMON
     * LIKWIDs overhead increases with large core counts as the single likwid-accessD must switch between all cores
     * to perform the required actions. Therefore cpus.size() likwid-accessDs are created.
     * Adding a new likwid-accessD requires that the calling threads TID is different than the previous ones,
     * therefore each HPMaddThread() must be called from a new thread.
     */
    // std::vector<std::thread> threadHandles;
    // start = std::chrono::high_resolution_clock::now();
    // for (size_t i = 0; i < cpus.size(); i++) {
    //     threadHandles.push_back(std::thread(AddHPMThread, cpus[i]));
    // }

    // for (size_t i = 0; i < threadHandles.size(); i++) {
    //     threadHandles[i].join();
    // }
    // std::cout << "[TIME] HPMaddThreads: " << std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::high_resolution_clock::now() - start).count() << std::endl;

    start = std::chrono::high_resolution_clock::now();
    if (perfmon_init(cpus.size(), &cpus[0]) != 0) {
        logger.log(CLogging::error, "Error - Failed to initialize performance monitoring.\nThis may happen due to missing access to MSR files.\nTry 'sudo modprobe msr'");
        return 1;
    }

    std::vector<std::string> availableGroups;
    start = std::chrono::high_resolution_clock::now();
    getAvailableGroups(availableGroups);

    setList = defaultSets;
    std::vector<std::string> tmpSets = defaultSets;
    for (auto set : tmpSets) {
        const auto posIt = std::find(availableGroups.begin(), availableGroups.end(), set);
        if (posIt == availableGroups.end()) {
            logger.log(CLogging::debug, "Set " + set + " is not available! Measurement will proceed without this set");
            setList.erase(std::remove(setList.begin(), setList.end(), set), setList.end());
        }
    }

    if (setList.size() < 1) {
        logger.log(CLogging::warning, "No event sets left to measure");
        perfmon_finalize();
        return 1;
    }

    int gid;
    for (size_t i = 0; i < setList.size(); i++) {
        start = std::chrono::high_resolution_clock::now();
        gid = perfmon_addEventSet(setList[i].c_str());
        if (gid < 0) {
            logger.log(CLogging::error, "Error adding '" + setList[i] + "' to eventset");
            perfmon_finalize();
            return 1;
        }
        gids.push_back(gid);
    }

    return 0;
}
