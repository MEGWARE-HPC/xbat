/**
 * @file ClickHouseWriter.hpp
 * @brief ClickHouse database writer for schema-aware measurement data
 *
 * Handles all ClickHouse operations using SQL text format for async inserts.
 * Async insert settings are configured at user level in users.xml.
 ***********************************************/

#pragma once

#include <string>
#include <vector>
#include <map>
#include <variant>
#include <sstream>
#include <type_traits>
#include <chrono>

#include "CQueue.hpp"
#include "definitions.hpp"
#include "external/clickhouse-cpp/clickhouse/client.h"

/**
 * @brief ClickHouse database writer class
 * 
 * Provides functionality to write measurement data from schema-aware queues
 * to ClickHouse database using SQL text format for async inserts.
 */
class ClickHouseWriter {
public:
    /**
     * @brief Main database writer function
     * 
     * Continuously reads measurement data from the schema queue every 10 seconds 
     * and inserts it immediately into ClickHouse tables using SQL text format.
     * 
     * @param dataQueue Schema-aware queue with results
     * @param config Configuration map containing database connection parameters
     */
    static void writeToDb(CQueue &dataQueue, config_map &config);

private:
    /**
     * @brief Templated function to insert any measurement type using SQL text format.
     * 
     * Async insertion require SQL text format and are not compatible with ClickHouse's block/column approach.
     * 
     * @param client ClickHouse client connection
     * @param measurements Vector of measurements of any type
     * @param jobId Job identifier
     * @param hostname Node hostname
     */
    template<typename T>
    static void insertMeasurements(clickhouse::Client &client,
                                  const std::vector<T> &measurements,
                                  uint32_t jobId,
                                  const std::string &hostname) {
        if (measurements.empty()) return;
        
        // Group by table name
        std::map<std::string, std::vector<std::string>> table_values;
        
        for (const auto &m : measurements) {
            auto duration = m.ts.time_since_epoch();
            auto millis = std::chrono::duration_cast<std::chrono::milliseconds>(duration).count();
            
            std::ostringstream value;
            value << "(";
            
            // Common fields for all measurement types
            value << jobId << ",'" << hostname << "','" << m.level << "'";
            
            // Type-specific fields
            if constexpr (std::is_same_v<T, CQueue::BasicMeasurement<int64_t>> || 
                          std::is_same_v<T, CQueue::BasicMeasurement<double>>) {
                // Basic measurements: (job_id, node, level, value, ts)
                value << "," << m.value << "," << millis;
            } else if constexpr (std::is_same_v<T, CQueue::DeviceMeasurement<int64_t>> || 
                                 std::is_same_v<T, CQueue::DeviceMeasurement<double>>) {
                // Device measurements: (job_id, node, level, device, value, ts)
                value << ",'" << m.device << "'," << m.value << "," << millis;
            } else if constexpr (std::is_same_v<T, CQueue::TopologyMeasurement<int64_t>> || 
                                 std::is_same_v<T, CQueue::TopologyMeasurement<double>>) {
                // Topology measurements: (job_id, node, level, thread, core, numa, socket, value, ts)
                value << "," << m.thread << "," << m.core << "," << m.numa << "," << m.socket 
                      << "," << m.value << "," << millis;
            }
            
            value << ")";
            table_values[m.measurement].push_back(value.str());
        }
        
        // Execute inserts for each table
        for (const auto &[tableName, values] : table_values) {
            std::ostringstream query;
            query << "INSERT INTO " << tableName << " VALUES ";
            for (size_t i = 0; i < values.size(); ++i) {
                if (i > 0) query << ",";
                query << values[i];
            }
            
            executeQuery(client, query.str());
        }
    }
    /**
     * @brief Execute SQL query without retry (non-blocking)
     * 
     * @param client ClickHouse client connection
     * @param query SQL query to execute
     */
    static void executeQuery(clickhouse::Client &client,
                            const std::string &query);

    /**
     * @brief Send all measurement data to ClickHouse using templated insert
     * 
     * @param client ClickHouse client connection
     * @param data Schema entries with all measurement types
     * @param jobId Job identifier
     * @param hostname Node hostname
     */
    static void sendData(clickhouse::Client &client, 
                        const CQueue::SchemaEntries &data,
                        uint32_t jobId, 
                        const std::string &hostname);

    static constexpr int QUEUE_POLL_INTERVAL = 10;  ///< Poll queue every 10 seconds
};
