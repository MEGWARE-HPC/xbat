/**
 * @file ClickHouseWriter.hpp
 * @brief ClickHouse database writer for schema-aware measurement data
 *
 * Handles all ClickHouse operations including client setup, batching,
 * and inserting measurements from the schema-aware queue.
 ***********************************************/

#pragma once

#include <string>
#include <vector>
#include <map>
#include <variant>

#include "CQueue.hpp"
#include "external/clickhouse-cpp/clickhouse/client.h"

/**
 * @brief ClickHouse database writer class
 * 
 * Provides functionality to write measurement data from schema-aware queues
 * to ClickHouse database with proper batching and error handling.
 */
class ClickHouseWriter {
public:
    /**
     * @brief Configuration map type for database connection
     */
    using config_map = std::map<std::string, std::variant<std::string, uint, bool>>;

    /**
     * @brief Insert basic measurements (int64_t) into ClickHouse
     * 
     * @param client ClickHouse client connection
     * @param measurements Vector of basic int measurements
     * @param jobId Job identifier
     * @param hostname Node hostname
     */
    static void insertBasicInt(clickhouse::Client &client, 
                              const std::vector<CQueue::BasicMeasurement<int64_t>> &measurements,
                              uint32_t jobId, 
                              const std::string &hostname);

    /**
     * @brief Insert basic measurements (double) into ClickHouse
     * 
     * @param client ClickHouse client connection
     * @param measurements Vector of basic double measurements
     * @param jobId Job identifier
     * @param hostname Node hostname
     */
    static void insertBasicDouble(clickhouse::Client &client, 
                                 const std::vector<CQueue::BasicMeasurement<double>> &measurements,
                                 uint32_t jobId, 
                                 const std::string &hostname);

    /**
     * @brief Insert device measurements (int64_t) into ClickHouse
     * 
     * @param client ClickHouse client connection
     * @param measurements Vector of device int measurements
     * @param jobId Job identifier
     * @param hostname Node hostname
     */
    static void insertDeviceInt(clickhouse::Client &client, 
                               const std::vector<CQueue::DeviceMeasurement<int64_t>> &measurements,
                               uint32_t jobId, 
                               const std::string &hostname);

    /**
     * @brief Insert device measurements (double) into ClickHouse
     * 
     * @param client ClickHouse client connection
     * @param measurements Vector of device double measurements
     * @param jobId Job identifier
     * @param hostname Node hostname
     */
    static void insertDeviceDouble(clickhouse::Client &client, 
                                  const std::vector<CQueue::DeviceMeasurement<double>> &measurements,
                                  uint32_t jobId, 
                                  const std::string &hostname);

    /**
     * @brief Insert topology measurements (int64_t) into ClickHouse
     * 
     * @param client ClickHouse client connection
     * @param measurements Vector of topology int measurements
     * @param jobId Job identifier
     * @param hostname Node hostname
     */
    static void insertTopologyInt(clickhouse::Client &client, 
                                 const std::vector<CQueue::TopologyMeasurement<int64_t>> &measurements,
                                 uint32_t jobId, 
                                 const std::string &hostname);

    /**
     * @brief Insert topology measurements (double) into ClickHouse
     * 
     * @param client ClickHouse client connection
     * @param measurements Vector of topology double measurements
     * @param jobId Job identifier
     * @param hostname Node hostname
     */
    static void insertTopologyDouble(clickhouse::Client &client, 
                                    const std::vector<CQueue::TopologyMeasurement<double>> &measurements,
                                    uint32_t jobId, 
                                    const std::string &hostname);

    /**
     * @brief Main database writer function
     * 
     * Continuously reads measurement data from the schema queue and inserts it into ClickHouse tables.
     * Uses batch inserts for performance optimization.
     * 
     * @param dataQueue Schema-aware queue with results
     * @param config Configuration map containing database connection parameters
     */
    static void writeToDb(CQueue &dataQueue, config_map &config);

private:
    static constexpr int BUFFER_SIZE = 1000;  ///< Batch size for database operations
    static constexpr int QUEUE_TIMEOUT = 3;  ///< Timeout for queue operations in seconds
};
