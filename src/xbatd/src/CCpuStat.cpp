/**
 * @file CCpuStat.cpp
 * @brief Class for measuring CPU usage
 *
 ***********************************************/

#include "CCpuStat.hpp"

#include <boost/date_time/posix_time/posix_time.hpp>
#include <boost/log/attributes.hpp>
#include <boost/log/attributes/scoped_attribute.hpp>
#include <boost/log/core.hpp>
#include <boost/log/expressions.hpp>
#include <boost/log/sinks/sync_frontend.hpp>
#include <boost/log/sinks/text_ostream_backend.hpp>
#include <boost/log/sources/basic_logger.hpp>
#include <boost/log/sources/record_ostream.hpp>
#include <boost/log/sources/severity_logger.hpp>
#include <boost/log/utility/setup/common_attributes.hpp>
#include <boost/smart_ptr/make_shared_object.hpp>
#include <boost/smart_ptr/shared_ptr.hpp>
#include <iostream>
#include <regex>

namespace logging = boost::log;
namespace src = boost::log::sources;
namespace expr = boost::log::expressions;
namespace sinks = boost::log::sinks;
namespace attrs = boost::log::attributes;
namespace keywords = boost::log::keywords;

enum severity_level {
    normal,
    notification,
    warning,
    error,
    critical
};

#define DATAPATH "/proc/stat" /**< Path to cpu usage data*/

/**
 * @brief Construct a new CCpuStat::CCpuStat object and initialize parameters
 *
 * @param dataQueue Pointer to queue for data
 * @param timestamp Starting timestamp
 * @param interval Interval duration in seconds
 */
CCpuStat::CCpuStat(CQueue *dataQueue, std::chrono::time_point<std::chrono::system_clock> startTime, uint64_t interval, Topology::cpuTopology &topology) {
    this->dataQueue = dataQueue;
    this->interval = interval;
    this->topology = topology;
    intervalStart = startTime;
    moduleName = "CPU";
    launchMutex.unlock();
}

/**
 * @brief Destroy the CCpuStat::CCpuStat object but only after measurement is completed
 *
 */
CCpuStat::~CCpuStat() {
    /* Destruct only if measure() already returned */
    cleanUpMutex.lock();
    cleanUpMutex.unlock();
}

/**
 * @brief Measure CPU usage
 *
 * Overwrite measure() of the base class, collect the cpu usage data during the interval
 * and push it to the data queue.
 *
 */
int CCpuStat::measure() {
    logger.setModule(moduleName);

    while (!terminate) {
        synchronizeMeasurement();
        std::map<std::string, std::vector<uint64_t>> previous, current;

        if (terminate)
            return 0;

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

/**
 * @brief Read data from proc
 *
 * @return 0 Success
 * @return 1 Error
 */
int CCpuStat::readProc(std::map<std::string, std::vector<uint64_t>> &results) {
    std::string content;
    if (Helper::readFileToString(DATAPATH, content) != 0)
        return 1;

    std::istringstream iss(content);
    std::string line;
    while (std::getline(iss, line)) {
        if (line.rfind("cpu", 0) != std::string::npos) {
            line = Helper::trimWhitespaces(line);
            std::vector<std::string> fields;
            Helper::splitStr(line, " ", fields);
            std::string cpu = fields[0];
            fields.erase(fields.begin());
            std::vector<uint64_t> values;
            for (auto &field : fields)
                values.push_back(std::stoull(field));
            results[cpu] = values;
        }
    }

    return 0;
}

void CCpuStat::calculateUsage(std::map<std::string, std::vector<uint64_t>> &previous, std::map<std::string, std::vector<uint64_t>> &current) {
    std::map<std::string, std::vector<uint64_t>> difference;
    for (auto &entry : current) {
        std::string key = entry.first;
        std::vector<uint64_t> values = entry.second;
        std::transform(values.begin(), values.end(), previous[entry.first].begin(), values.begin(), std::minus<uint64_t>());

        /* calculations according to htop implementation beginning on line #945
         * https://github.com/hishamhm/htop/blob/e0209da88faf3b390d71ff174065abd407abfdfd/ProcessList.c
         */
        uint64_t user = values[0] - values[8];
        uint64_t nice = values[1] - values[9];
        uint64_t idle = values[3] + values[4];
        uint64_t iowait = values[4];
        uint64_t sys = values[2] + values[5] + values[6];
        uint64_t virt = values[8] + values[9];
        double total = user + nice + idle + sys + virt + values[7];

        // prevent division by zero
        if (total == 0.0) total = 1.0;

        uint32_t hwThreadId = UINT32_MAX;  // Use max value as sentinel instead of -1
        std::regex reg("cpu(\\d+)");
        std::smatch match;

        std::string level = "thread";
        if (key == "cpu") {
            level = "node";
        } else {
            hwThreadId = static_cast<uint32_t>(std::stoi(std::regex_replace(key, reg, "$1")));
            if (!topology.smt)
                level = "core";
        }

        if (hwThreadId == UINT32_MAX)
            continue;

        const auto hwThreadInfo = topology.hwThreads[hwThreadId];
        // Use topology measurements for per-thread/core data
        dataQueue->push(CQueue::TopologyMeasurement<double>{"cpu_usage", level,
                                                            hwThreadId,
                                                            hwThreadInfo.core,
                                                            hwThreadInfo.numa,
                                                            hwThreadInfo.socket,
                                                            ((total - idle) / total) * 100,
                                                            intervalEnd});
        dataQueue->push(CQueue::TopologyMeasurement<double>{"cpu_user", level,
                                                            hwThreadId,
                                                            hwThreadInfo.core,
                                                            hwThreadInfo.numa,
                                                            hwThreadInfo.socket,
                                                            (user / total) * 100,
                                                            intervalEnd});
        dataQueue->push(CQueue::TopologyMeasurement<double>{"cpu_system", level,
                                                            hwThreadId,
                                                            hwThreadInfo.core,
                                                            hwThreadInfo.numa,
                                                            hwThreadInfo.socket,
                                                            (sys / total) * 100,
                                                            intervalEnd});
        dataQueue->push(CQueue::TopologyMeasurement<double>{"cpu_iowait", level,
                                                            hwThreadId,
                                                            hwThreadInfo.core,
                                                            hwThreadInfo.numa,
                                                            hwThreadInfo.socket,
                                                            (iowait / total) * 100,
                                                            intervalEnd});
        dataQueue->push(CQueue::TopologyMeasurement<double>{"cpu_virtual", level,
                                                            hwThreadId,
                                                            hwThreadInfo.core,
                                                            hwThreadInfo.numa,
                                                            hwThreadInfo.socket,
                                                            (virt / total) * 100,
                                                            intervalEnd});
        dataQueue->push(CQueue::TopologyMeasurement<double>{"cpu_nice", level,
                                                            hwThreadId,
                                                            hwThreadInfo.core,
                                                            hwThreadInfo.numa,
                                                            hwThreadInfo.socket,
                                                            (nice / total) * 100,
                                                            intervalEnd});
    }
}