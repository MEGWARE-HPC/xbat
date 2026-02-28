/**
 * @file ClickHouseWriter.cpp
 * @brief ClickHouse database writer implementation
 *
 * Implementation of all ClickHouse operations including client setup, batching,
 * and inserting measurements from the schema-aware queue.
 ***********************************************/

#include "ClickHouseWriter.hpp"

#include <atomic>
#include <chrono>
#include <sstream>
#include <thread>
#include <type_traits>
#include <variant>

#include "CLogging.hpp"
#include "definitions.hpp"
#include "external/clickhouse-cpp/clickhouse/client.h"
#include "external/clickhouse-cpp/clickhouse/query.h"

// External variable from main.cpp
extern std::atomic<bool> canceled;

void ClickHouseWriter::executeQuery(clickhouse::Client& client,
                                    const std::string& query) {
    try {
        CLogging::log("DbWriter", CLogging::debug,
                      "Executing query: " + query);
        clickhouse::Query q(query);
        client.Execute(q);
    } catch (const std::exception& e) {
        std::string error_msg = e.what();

        // Check if this is a "table does not exist" error
        if (error_msg.find("Table") != std::string::npos &&
            error_msg.find("does not exist") != std::string::npos) {
            // Extract table name from error message for logging
            std::string table_name = "unknown";
            size_t table_pos = error_msg.find("Table ");
            if (table_pos != std::string::npos) {
                size_t start = table_pos + 6;  // Skip "Table "
                size_t end = error_msg.find(" does not exist", start);
                if (end != std::string::npos) {
                    table_name = error_msg.substr(start, end - start);
                }
            }

            CLogging::log("DbWriter", CLogging::warning,
                          "Skipping insert to non-existent table: " + table_name);
            return;
        }

        CLogging::log("DbWriter", CLogging::error,
                      "Failed to execute query: " + error_msg);
    }
}

void ClickHouseWriter::sendData(clickhouse::Client& client,
                                const CQueue::SchemaEntries& data,
                                uint32_t jobId,
                                const std::string& hostname) {
    try {
        // Send each measurement type using the templated function
        insertMeasurements(client, data.basic_int, jobId, hostname);
        insertMeasurements(client, data.basic_double, jobId, hostname);
        insertMeasurements(client, data.device_int, jobId, hostname);
        insertMeasurements(client, data.device_double, jobId, hostname);
        insertMeasurements(client, data.topology_int, jobId, hostname);
        insertMeasurements(client, data.topology_double, jobId, hostname);
    } catch (const std::exception& e) {
        std::string error_msg = e.what();

        // Check if this is a "table does not exist" error - these are recoverable
        if (error_msg.find("Table") != std::string::npos &&
            error_msg.find("does not exist") != std::string::npos) {
            CLogging::log("DbWriter", CLogging::warning,
                          "Skipping measurements for non-existent table: " + error_msg);
            return;  // Continue running despite missing table
        }

        // For other errors (connection issues, authentication, etc.), log and re-throw
        CLogging::log("DbWriter", CLogging::error,
                      "Error sending data: " + error_msg);
        throw;
    }
}

void ClickHouseWriter::writeToDb(CQueue& dataQueue, config_map& config) {
    try {
        // Configure ClickHouse client options
        clickhouse::ClientOptions clientOptions;
        clientOptions.SetHost(std::get<std::string>(config["clickhouse_host"]))
            .SetPort(std::get<uint>(config["clickhouse_port"]))
            .SetDefaultDatabase(std::get<std::string>(config["clickhouse_database"]))
            .SetUser(std::get<std::string>(config["clickhouse_user"]))
            .SetPassword(std::get<std::string>(config["clickhouse_password"]))
            .SetSSLOptions(clickhouse::ClientOptions::SSLOptions()
                .SetSkipVerification(true));

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
                try {
                    sendData(client, data, jobId, hostname);
                } catch (const std::exception& e) {
                    // Critical error (connection, authentication, etc.) - stop the daemon
                    CLogging::log("DbWriter", CLogging::error,
                                  "Critical database error - stopping daemon: " + std::string(e.what()));
                    canceled = true;
                    break;
                }
            }
        }

    } catch (const std::exception& e) {
        CLogging::log("DbWriter", CLogging::error,
                      "Failed to initialize ClickHouse client: " + std::string(e.what()));
        canceled = true;
    }
}
