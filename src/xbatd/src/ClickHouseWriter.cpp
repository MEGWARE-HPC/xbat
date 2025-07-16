/**
 * @file ClickHouseWriter.cpp
 * @brief ClickHouse database writer implementation
 *
 * Implementation of all ClickHouse operations including client setup, batching,
 * and inserting measurements from the schema-aware queue.
 ***********************************************/

#include "ClickHouseWriter.hpp"
#include "CLogging.hpp"
#include "definitions.hpp"

#include <chrono>
#include <atomic>
#include <thread>
#include <variant>
#include <sstream>
#include <type_traits>

#include "external/clickhouse-cpp/clickhouse/client.h"
#include "external/clickhouse-cpp/clickhouse/query.h"

// External variable from main.cpp
extern std::atomic<bool> canceled;

void ClickHouseWriter::executeQueryWithRetry(clickhouse::Client &client,
                                            const std::string &query,
                                            int maxRetries) {
    int attempts = 0;
    while (attempts < maxRetries) {
        try {
            clickhouse::Query q(query);
            client.Execute(q);
            return; // Success
        } catch (const std::exception &e) {
            attempts++;
            if (attempts >= maxRetries) {
                CLogging::log("DbWriter", CLogging::error, 
                             "Failed to execute query after " + 
                             std::to_string(maxRetries) + " attempts: " + e.what());
                throw; // Re-throw after max retries
            } else {
                CLogging::log("DbWriter", CLogging::warning, 
                             "Query execution attempt " + std::to_string(attempts) + 
                             " failed: " + e.what() + " (retrying...)");
                // Brief wait before retry
                std::this_thread::sleep_for(std::chrono::milliseconds(100 * attempts));
            }
        }
    }
}

void ClickHouseWriter::sendData(clickhouse::Client &client, 
                               const CQueue::SchemaEntries &data,
                               uint32_t jobId, 
                               const std::string &hostname) {
    try {
        // Send each measurement type using the templated function
        insertMeasurements(client, data.basic_int, jobId, hostname);
        insertMeasurements(client, data.basic_double, jobId, hostname);
        insertMeasurements(client, data.device_int, jobId, hostname);
        insertMeasurements(client, data.device_double, jobId, hostname);
        insertMeasurements(client, data.topology_int, jobId, hostname);
        insertMeasurements(client, data.topology_double, jobId, hostname);
    } catch (const std::exception &e) {
        CLogging::log("DbWriter", CLogging::error, 
                     "Error sending data: " + std::string(e.what()));
        throw;
    }
}

void ClickHouseWriter::writeToDb(CQueue &dataQueue, config_map &config) {
    try {
        // Configure ClickHouse client options
        clickhouse::ClientOptions clientOptions;
        clientOptions.SetHost(std::get<std::string>(config["clickhouse_host"]))
                    .SetPort(std::get<uint>(config["clickhouse_port"]))
                    .SetDefaultDatabase(std::get<std::string>(config["clickhouse_database"]))
                    .SetUser(std::get<std::string>(config["clickhouse_user"]))
                    .SetPassword(std::get<std::string>(config["clickhouse_password"]));

        clickhouse::Client client(clientOptions);

        uint32_t jobId = static_cast<uint32_t>(std::get<uint>(config["jobId"]));
        std::string hostname = std::get<std::string>(config["hostname"]);

        CLogging::log("DbWriter", CLogging::info, 
                     "Starting ClickHouse writer");

        while (!canceled) {
            // Sleep for 10 seconds first to ensure consistent polling interval
            std::this_thread::sleep_for(std::chrono::seconds(QUEUE_POLL_INTERVAL));
            
            // Check if we were cancelled during sleep
            if (canceled) break;
            
            CQueue::SchemaEntries data;
            // Get all available data from queue without waiting
            if (dataQueue.waitAndPopAll(data, 0) != 0)
                continue;

            // Send all data immediately if any measurements are available
            int totalMeasurements = data.basic_int.size() + data.basic_double.size() + 
                                   data.device_int.size() + data.device_double.size() +
                                   data.topology_int.size() + data.topology_double.size();

            if (totalMeasurements > 0) {
                CLogging::log("DbWriter", CLogging::debug, 
                             "Sending " + std::to_string(totalMeasurements) + " measurements to ClickHouse");
                sendData(client, data, jobId, hostname);
            }
        }

    } catch (const std::exception &e) {
        CLogging::log("DbWriter", CLogging::error, "Database Error - " + std::string(e.what()));
        canceled = true;
    }
}
