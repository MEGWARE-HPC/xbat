/**
 * @file main.cpp
 * @brief xbatd measurement daemon
 *
 ***********************************************/

#include "main.hpp"

#include <limits.h>
#include <signal.h>
#include <unistd.h>

#include <boost/exception/diagnostic_information.hpp>
#include <boost/property_tree/ini_parser.hpp>
#include <boost/property_tree/ptree.hpp>
#include <cstdlib>
#include <iostream>
#include <list>
#include <map>
#include <thread>
#include <variant>
#include <algorithm>

#include "CLikwidPerfctr.hpp"
#include "ClickHouseWriter.hpp"
#include "CLogging.hpp"
#include "CQueue.hpp"
#include "CurlClient.hpp"
#include "clipp.h"
#include "helper.hpp"
#include "nlohmann/json.hpp"
#include "threadhelper.hpp"

#define WATCHDOGSLEEP 3
#define JOB_INFO_PATH "/run/xbatd/job"
#define BENCHMARK_STATUS_FILE_PATH "/run/xbatd/benchmarkInProgress"

using namespace std::literals::string_view_literals;

bool daemonMode = false;
std::string outputPath = "";
std::atomic<bool> canceled(false); /**< Daemon receives SIGINT from CTRL+C or SIGTERM from systemctl stop */

std::condition_variable measurementsCanceledCV;
std::mutex measurementsCanceledMutex;

/**
 * @brief Handle caught signal
 *
 * This function is called when either SIGINT or SIGTERM are caught.
 * It will initialize the shutdown of all threads on the first call.
 * The second call forcefully terminates the whole application.
 *
 * @param signal Number of signal
 */
void sigHandler(int signal) {
    CLogging::log("SignalHandler", CLogging::debug, "Caught signal " + std::to_string(signal));
    if (canceled)
        exit(EXIT_FAILURE);
    canceled = true;
}

statusInfo::~statusInfo() {
    for (auto i = classList.begin(); i != classList.end(); ++i)
        if (*i != nullptr)
            delete *i;
}

/**
 * @brief Periodically checks and manages all measurement threads.
 *
 * @param statusList List of statusInfo
 */
void watchdog(std::unique_ptr<statusInfo> &statusList) {
    do {
        time_t currentTime = Helper::getSecondsSinceEpoch();
        for (const auto &entry : statusList->classList) {
            /* Check whether thread is hung and forcefully terminate it if this is the case.
             * Restart thread on next watchdog execution.
             */
            bool timedOut = (currentTime - entry->getLastHeartbeat() > 2 * entry->getInterval());
            int threadStatus = entry->getThreadStatus();
            // /* Assume that thread is hung if it does not return after grace period of two intervals*/
            if (timedOut && threadStatus == THREAD_RUNNING) {
                entry->forceStop();
            } else if (threadStatus == THREAD_FORCEFULLY_TERMINATED) {
                /* Thread is not running but job has not yet ended.
                 * Only revive forcefully killed threads since it is an accepted behaviour
                 * for a thread to terminate if measurements could not be executed (e.g. certain tool missing on system).
                 */
                entry->startMeasurement();
            }
        }
        sleep(WATCHDOGSLEEP);

    } while (!canceled);
}

int measure(config_map &config, Topology::cpuTopology &topology) {
    std::unique_ptr<statusInfo> statusList(new statusInfo);

    CQueue dataQueue = CQueue();

    std::thread watchdogThread(&watchdog, std::ref(statusList));
    std::thread writeThread(&ClickHouseWriter::writeToDb, std::ref(dataQueue), std::ref(config));

    ThreadHelper::init(statusList, &dataQueue, config, topology);

    writeThread.join();

    ThreadHelper::stop(statusList);
    watchdogThread.join();

    while (!ThreadHelper::terminated(statusList)) {
        sleep(1);
    }

    return 0;
}

std::map<std::string, double> benchmarkSystem(Topology::cpuTopology &topology) {
    std::map<std::string, double> values;
    if (Helper::writeToFile(BENCHMARK_STATUS_FILE_PATH, "") != 0)
        return values;

    auto generateBenchmarkCommand = [](std::string benchmark, int threads, int sizeInByte) {
        std::string path = "/usr/local/share/xbatd/bin/likwid-bench";
        std::string workgroup = "-W N:" + std::to_string(sizeInByte / 1024) + "KB:" + std::to_string(threads);
        return path + " -t " + benchmark + " " + workgroup;
    };

    auto benchmarkAvailable = [](std::string &available, std::string benchmark) {
        // available benchmarks are suffixed with " -"
        return available.find(benchmark + " -") != std::string::npos;
    };

    auto getValue = [](std::string output, std::string filter) {
        Helper::filterLinesNotContaining(std::vector<std::string>{filter}, output, true);
        std::vector<std::string> split;
        Helper::splitStr(output, "\n", split);
        return std::stod(Helper::extractNumber(split[0], true));
    };

    std::string available;
    if (Helper::getCommandOutput("/usr/local/share/xbatd/bin/likwid-bench -a", available) != 0) {
        Helper::deleteFile(BENCHMARK_STATUS_FILE_PATH);
        return values;
    }

    int threads = topology.coresPerSocket * topology.threadsPerCore * topology.sockets;

    std::string output;
    for (auto &benchmark : flopBenchmarks) {
        if (!benchmarkAvailable(available, benchmark)) continue;
        if (Helper::getCommandOutput(generateBenchmarkCommand(benchmark, threads, topology.l1CacheTotal), output) != 0)
            continue;
        /* store as flops to stay consistent with other metrics */
        values[benchmark] = getValue(output, "MFlops/s:") * 1000 * 1000;
    }

    std::vector<std::string> stream = {"l1", "l2", "l3", "mem"};

    for (auto &variant : stream) {
        std::string benchmark = "load";
        if (!benchmarkAvailable(available, benchmark)) continue;
        int cacheSize = 0;

        if (variant == "l1")
            cacheSize = topology.l1CacheTotal;
        else if (variant == "l2")
            cacheSize = topology.l2CacheTotal;
        else if (variant == "l3")
            cacheSize = topology.l3CacheTotal;
        else if (variant == "mem")
            /* To prevent measuring cache bandwidth workgroup size must be greater than sum of all caches per socket.
             * Using sum * 4 as recommended by stream */
            cacheSize = topology.cacheTotal * 4;

        if (Helper::getCommandOutput(generateBenchmarkCommand(benchmark, threads, cacheSize), output) != 0)
            continue;
        /* store as bytes/s to stay consistent with other metrics */
        std::string key = "bandwidth_" + variant;
        values[key] = getValue(output, "MByte/s:") * 1024 * 1024;
    }

    Helper::deleteFile(BENCHMARK_STATUS_FILE_PATH);

    return values;
}

/**
 * @brief xbat daemon.
 *
 * Collects system information and conducts measurements during runtime.
 *
 * @param argc Number of arguments
 * @param argv arguments
 * @return int Exit status
 */
int main(int argc, char *argv[]) {
    bool help = false;
    std::string confPath = "/etc/xbatd/xbatd.conf";
    uint jobId = 0;
    auto cli_help = clipp::option("-h", "--help").set(help) % "Shows this help message";
    auto cli_conf = (clipp::option("-c", "--config") & clipp::value("path", confPath)) % ("Path to configuration file (default " + confPath + ")");
    auto cli_jobId = (clipp::option("-j", "--job") & clipp::value("jobId", jobId)) % ("ID of current job (overwrites /run/xbatd/job for local testing)");
    auto cli = (cli_help, cli_conf, cli_jobId);

    if (!clipp::parse(argc, argv, cli) || help) {
        std::cout << "USAGE:\n"
                  << clipp::usage_lines(cli, argv[0]) << "\n\n\n"
                  << "PARAMETERS:\n\n"
                  << clipp::documentation(cli) << std::endl;
        return EXIT_FAILURE;
    }

    struct sigaction sigIntHandler;

    sigIntHandler.sa_handler = sigHandler;
    sigemptyset(&sigIntHandler.sa_mask);
    sigIntHandler.sa_flags = 0;

    sigaction(SIGINT, &sigIntHandler, NULL);  /* for CTRL+C */
    sigaction(SIGTERM, &sigIntHandler, NULL); /* for SIGTERM via systemctl stop */

    std::string configString;
    if (Helper::readFileToString(confPath, configString) != 0) {
        std::cerr << "Failed to read configuration file" << std::endl;
        return EXIT_FAILURE;
    }

    std::cout << "Using configuration file: " << configString << std::endl;

    config_map config;
    try {
        std::istringstream isConfig(configString);
        boost::property_tree::ptree pt;
        boost::property_tree::ini_parser::read_ini(isConfig, pt);
        config = {
            {"log_level", pt.get<std::string>("general.log_level")},
            {"log_level_file", pt.get<std::string>("general.log_level_file")},
            {"restapi_host", pt.get<std::string>("restapi.host")},
            {"restapi_port", pt.get<uint>("restapi.port")},
            {"restapi_client_id", pt.get<std::string>("restapi.client_id")},
            {"restapi_client_secret", pt.get<std::string>("restapi.client_secret")},
            {"clickhouse_host", pt.get<std::string>("clickhouse.host")},
            {"clickhouse_port", pt.get<uint>("clickhouse.port")},
            {"clickhouse_database", pt.get<std::string>("clickhouse.database")},
            {"clickhouse_user", pt.get<std::string>("clickhouse.user")},
            {"clickhouse_password", pt.get<std::string>("clickhouse.password")}};

    } catch (boost::property_tree::ptree_bad_path const &) {
        std::cerr << "Invalid configuration at " << confPath << "\n"
                  << boost::current_exception_diagnostic_information();
        return EXIT_FAILURE;
    }

    CLogging::initLogging(config);

    /* read jobId from JOB_INFO_PATH if not provided by cli */
    if (jobId == 0) {
        std::string jobIdStr;
        if (Helper::readFileToString(JOB_INFO_PATH, jobIdStr) != 0) {
            std::cerr << "Failed to read job ID from file" << std::endl;
            return EXIT_FAILURE;
        }
        jobId = static_cast<uint>(std::stoi(Helper::trimWhitespaces(jobIdStr)));
    }
    config["jobId"] = jobId;

    CLogging logger;

    logger.log(CLogging::debug, "Monitoring for JobID " + std::to_string(jobId));

    /* use short hostname (if available) instead of FQDN as the latter is normally not known to slurm */
    std::string hostname;
    if (Helper::getCommandOutput("hostname -s", hostname) != 0) {
        logger.log(CLogging::error, "Failed to get hostname");
        return EXIT_FAILURE;
    }

    hostname = Helper::trimWhitespaces(hostname);
    config["hostname"] = hostname;

    /* gather system info of this node to check whether a identical system was already benchmarked*/
    nlohmann::json systemInfo = Helper::gatherSystemInfo();
    systemInfo["os"]["hostname"] = hostname;

    /* create copy of systeminfo and remove topology/hostname as it contains volatile information like free memory which
     * interferes with the hash calculation */
    nlohmann::json hashableSystemInfo = systemInfo;
    if (hashableSystemInfo["cpu"].contains("topology"))
        hashableSystemInfo["cpu"].erase("topology");

    if (hashableSystemInfo["os"].contains("hostname"))
        hashableSystemInfo["os"].erase("hostname");

    std::string systeminfoHash = Helper::md5(hashableSystemInfo.dump());
    logger.log(CLogging::debug, "Hash: " + systeminfoHash);

    CurlClient curlClient("https://" + std::get<std::string>(config["restapi_host"]) + ":" +
                              std::to_string(std::get<uint>(config["restapi_port"])),
                          std::get<std::string>(config["restapi_client_id"]), std::get<std::string>(config["restapi_client_secret"]));

    curlClient.login();
    nlohmann::json jobConfig = curlClient.registerJob(jobId, hostname, systeminfoHash);

    logger.log(CLogging::debug, "Job settings: " + jobConfig.dump(4));

    config["interval"] = jobConfig["interval"].get<uint>();
    config["enableMonitoring"] = jobConfig["enableMonitoring"].get<bool>();
    config["enableLikwid"] = jobConfig["enableLikwid"].get<bool>();

    Topology::cpuTopology topology;
    if (Topology::getCpuTopology(topology) != 0) {
        curlClient.logout();
        return EXIT_FAILURE;
    }

    if (jobConfig["benchmarkRequired"].get<bool>()) {
        logger.log(CLogging::info, "Benchmarking system...");

        std::map<std::string, double> benchmarkValues = benchmarkSystem(topology);

        if (benchmarkValues.empty())
            logger.log(CLogging::error, "Failed to benchmark system");

        for (auto &v : benchmarkValues) {
            systemInfo["benchmarks"][v.first] = v.second;
        }
        curlClient.registerNode(systeminfoHash, systemInfo);
        logger.log(CLogging::info, "Benchmarking completed - node successfully registered");
    }

    curlClient.logout();

    if (!std::get<bool>(config["enableMonitoring"])) {
        logger.log(CLogging::info, "Monitoring is disabled for this job - returning");
        return EXIT_SUCCESS;
    }

    std::thread measurementThread = std::thread(&measure, std::ref(config), std::ref(topology));
    measurementThread.join();

    return EXIT_SUCCESS;
}
