/**
 * @file ClickHouseWriter.cpp
 * @brief ClickHouse database writer implementation
 *
 * Implementation of all ClickHouse operations including client setup, batching,
 * and inserting measurements from the schema-aware queue.
 ***********************************************/

#include "ClickHouseWriter.hpp"
#include "CLogging.hpp"

#include <chrono>
#include <atomic>

#include "external/clickhouse-cpp/clickhouse/client.h"
#include "external/clickhouse-cpp/clickhouse/block.h"
#include "external/clickhouse-cpp/clickhouse/columns/string.h"
#include "external/clickhouse-cpp/clickhouse/columns/numeric.h"
#include "external/clickhouse-cpp/clickhouse/columns/date.h"

// External variable from main.cpp
extern std::atomic<bool> canceled;

void ClickHouseWriter::insertBasicInt(clickhouse::Client &client, 
                                     const std::vector<CQueue::BasicMeasurement<int64_t>> &measurements,
                                     uint32_t jobId, 
                                     const std::string &hostname) {
    if (measurements.empty()) return;
    
    using namespace clickhouse;
    
    // Group by table name
    std::map<std::string, std::vector<CQueue::BasicMeasurement<int64_t>>> tables;
    for (const auto &m : measurements) {
        tables[m.measurement].push_back(m);
    }
    
    // Insert each table
    for (const auto &[tableName, rows] : tables) {
        auto block = std::make_shared<Block>();
        auto col_job_id = std::make_shared<ColumnUInt32>();
        auto col_node = std::make_shared<ColumnString>();
        auto col_level = std::make_shared<ColumnString>();
        auto col_value = std::make_shared<ColumnUInt64>();
        auto col_ts = std::make_shared<ColumnDateTime64>(3);

        for (const auto &row : rows) {
            col_job_id->Append(jobId);
            col_node->Append(hostname);
            col_level->Append(row.level);
            col_value->Append(static_cast<uint64_t>(row.value));
            
            auto duration = row.ts.time_since_epoch();
            auto millis = std::chrono::duration_cast<std::chrono::milliseconds>(duration).count();
            col_ts->Append(millis);
        }

        block->AppendColumn("job_id", col_job_id);
        block->AppendColumn("node", col_node);
        block->AppendColumn("level", col_level);
        block->AppendColumn("value", col_value);
        block->AppendColumn("ts", col_ts);

        client.Insert(tableName, *block);
    }
}

void ClickHouseWriter::insertBasicDouble(clickhouse::Client &client, 
                                        const std::vector<CQueue::BasicMeasurement<double>> &measurements,
                                        uint32_t jobId, 
                                        const std::string &hostname) {
    if (measurements.empty()) return;
    
    using namespace clickhouse;
    
    // Group by table name
    std::map<std::string, std::vector<CQueue::BasicMeasurement<double>>> tables;
    for (const auto &m : measurements) {
        tables[m.measurement].push_back(m);
    }
    
    // Insert each table
    for (const auto &[tableName, rows] : tables) {
        auto block = std::make_shared<Block>();
        auto col_job_id = std::make_shared<ColumnUInt32>();
        auto col_node = std::make_shared<ColumnString>();
        auto col_level = std::make_shared<ColumnString>();
        auto col_value = std::make_shared<ColumnFloat64>();
        auto col_ts = std::make_shared<ColumnDateTime64>(3);

        for (const auto &row : rows) {
            col_job_id->Append(jobId);
            col_node->Append(hostname);
            col_level->Append(row.level);
            col_value->Append(row.value);
            
            auto duration = row.ts.time_since_epoch();
            auto millis = std::chrono::duration_cast<std::chrono::milliseconds>(duration).count();
            col_ts->Append(millis);
        }

        block->AppendColumn("job_id", col_job_id);
        block->AppendColumn("node", col_node);
        block->AppendColumn("level", col_level);
        block->AppendColumn("value", col_value);
        block->AppendColumn("ts", col_ts);

        client.Insert(tableName, *block);
    }
}

void ClickHouseWriter::insertDeviceInt(clickhouse::Client &client, 
                                      const std::vector<CQueue::DeviceMeasurement<int64_t>> &measurements,
                                      uint32_t jobId, 
                                      const std::string &hostname) {
    if (measurements.empty()) return;
    
    using namespace clickhouse;
    
    // Group by table name
    std::map<std::string, std::vector<CQueue::DeviceMeasurement<int64_t>>> tables;
    for (const auto &m : measurements) {
        tables[m.measurement].push_back(m);
    }
    
    // Insert each table
    for (const auto &[tableName, rows] : tables) {
        auto block = std::make_shared<Block>();
        auto col_job_id = std::make_shared<ColumnUInt32>();
        auto col_node = std::make_shared<ColumnString>();
        auto col_level = std::make_shared<ColumnString>();
        auto col_device = std::make_shared<ColumnString>();
        auto col_value = std::make_shared<ColumnUInt64>();
        auto col_ts = std::make_shared<ColumnDateTime64>(3);

        for (const auto &row : rows) {
            col_job_id->Append(jobId);
            col_node->Append(hostname);
            col_level->Append(row.level);
            col_device->Append(row.device);
            col_value->Append(static_cast<uint64_t>(row.value));
            
            auto duration = row.ts.time_since_epoch();
            auto millis = std::chrono::duration_cast<std::chrono::milliseconds>(duration).count();
            col_ts->Append(millis);
        }

        block->AppendColumn("job_id", col_job_id);
        block->AppendColumn("node", col_node);
        block->AppendColumn("level", col_level);
        block->AppendColumn("device", col_device);
        block->AppendColumn("value", col_value);
        block->AppendColumn("ts", col_ts);

        client.Insert(tableName, *block);
    }
}

void ClickHouseWriter::insertDeviceDouble(clickhouse::Client &client, 
                                         const std::vector<CQueue::DeviceMeasurement<double>> &measurements,
                                         uint32_t jobId, 
                                         const std::string &hostname) {
    if (measurements.empty()) return;
    
    using namespace clickhouse;
    
    // Group by table name
    std::map<std::string, std::vector<CQueue::DeviceMeasurement<double>>> tables;
    for (const auto &m : measurements) {
        tables[m.measurement].push_back(m);
    }
    
    // Insert each table
    for (const auto &[tableName, rows] : tables) {
        auto block = std::make_shared<Block>();
        auto col_job_id = std::make_shared<ColumnUInt32>();
        auto col_node = std::make_shared<ColumnString>();
        auto col_level = std::make_shared<ColumnString>();
        auto col_device = std::make_shared<ColumnString>();
        auto col_value = std::make_shared<ColumnFloat64>();
        auto col_ts = std::make_shared<ColumnDateTime64>(3);

        for (const auto &row : rows) {
            col_job_id->Append(jobId);
            col_node->Append(hostname);
            col_level->Append(row.level);
            col_device->Append(row.device);
            col_value->Append(row.value);
            
            auto duration = row.ts.time_since_epoch();
            auto millis = std::chrono::duration_cast<std::chrono::milliseconds>(duration).count();
            col_ts->Append(millis);
        }

        block->AppendColumn("job_id", col_job_id);
        block->AppendColumn("node", col_node);
        block->AppendColumn("level", col_level);
        block->AppendColumn("device", col_device);
        block->AppendColumn("value", col_value);
        block->AppendColumn("ts", col_ts);

        client.Insert(tableName, *block);
    }
}

void ClickHouseWriter::insertTopologyInt(clickhouse::Client &client, 
                                        const std::vector<CQueue::TopologyMeasurement<int64_t>> &measurements,
                                        uint32_t jobId, 
                                        const std::string &hostname) {
    if (measurements.empty()) return;
    
    using namespace clickhouse;
    
    // Group by table name
    std::map<std::string, std::vector<CQueue::TopologyMeasurement<int64_t>>> tables;
    for (const auto &m : measurements) {
        tables[m.measurement].push_back(m);
    }
    
    // Insert each table
    for (const auto &[tableName, rows] : tables) {
        auto block = std::make_shared<Block>();
        auto col_job_id = std::make_shared<ColumnUInt32>();
        auto col_node = std::make_shared<ColumnString>();
        auto col_level = std::make_shared<ColumnString>();
        auto col_thread = std::make_shared<ColumnUInt16>();
        auto col_core = std::make_shared<ColumnUInt16>();
        auto col_numa = std::make_shared<ColumnUInt8>();
        auto col_socket = std::make_shared<ColumnUInt8>();
        auto col_value = std::make_shared<ColumnUInt64>();
        auto col_ts = std::make_shared<ColumnDateTime64>(3);

        for (const auto &row : rows) {
            col_job_id->Append(jobId);
            col_node->Append(hostname);
            col_level->Append(row.level);
            col_thread->Append(row.thread);
            col_core->Append(row.core);
            col_numa->Append(row.numa);
            col_socket->Append(row.socket);
            col_value->Append(static_cast<uint64_t>(row.value));
            
            auto duration = row.ts.time_since_epoch();
            auto millis = std::chrono::duration_cast<std::chrono::milliseconds>(duration).count();
            col_ts->Append(millis);
        }

        block->AppendColumn("job_id", col_job_id);
        block->AppendColumn("node", col_node);
        block->AppendColumn("level", col_level);
        block->AppendColumn("thread", col_thread);
        block->AppendColumn("core", col_core);
        block->AppendColumn("numa", col_numa);
        block->AppendColumn("socket", col_socket);
        block->AppendColumn("value", col_value);
        block->AppendColumn("ts", col_ts);

        client.Insert(tableName, *block);
    }
}

void ClickHouseWriter::insertTopologyDouble(clickhouse::Client &client, 
                                           const std::vector<CQueue::TopologyMeasurement<double>> &measurements,
                                           uint32_t jobId, 
                                           const std::string &hostname) {
    if (measurements.empty()) return;
    
    using namespace clickhouse;
    
    // Group by table name
    std::map<std::string, std::vector<CQueue::TopologyMeasurement<double>>> tables;
    for (const auto &m : measurements) {
        tables[m.measurement].push_back(m);
    }
    
    // Insert each table
    for (const auto &[tableName, rows] : tables) {
        auto block = std::make_shared<Block>();
        auto col_job_id = std::make_shared<ColumnUInt32>();
        auto col_node = std::make_shared<ColumnString>();
        auto col_level = std::make_shared<ColumnString>();
        auto col_thread = std::make_shared<ColumnUInt16>();
        auto col_core = std::make_shared<ColumnUInt16>();
        auto col_numa = std::make_shared<ColumnUInt8>();
        auto col_socket = std::make_shared<ColumnUInt8>();
        auto col_value = std::make_shared<ColumnFloat64>();
        auto col_ts = std::make_shared<ColumnDateTime64>(3);

        for (const auto &row : rows) {
            col_job_id->Append(jobId);
            col_node->Append(hostname);
            col_level->Append(row.level);
            col_thread->Append(row.thread);
            col_core->Append(row.core);
            col_numa->Append(row.numa);
            col_socket->Append(row.socket);
            col_value->Append(row.value);
            
            auto duration = row.ts.time_since_epoch();
            auto millis = std::chrono::duration_cast<std::chrono::milliseconds>(duration).count();
            col_ts->Append(millis);
        }

        block->AppendColumn("job_id", col_job_id);
        block->AppendColumn("node", col_node);
        block->AppendColumn("level", col_level);
        block->AppendColumn("thread", col_thread);
        block->AppendColumn("core", col_core);
        block->AppendColumn("numa", col_numa);
        block->AppendColumn("socket", col_socket);
        block->AppendColumn("value", col_value);
        block->AppendColumn("ts", col_ts);

        client.Insert(tableName, *block);
    }
}

void ClickHouseWriter::writeToDb(CQueue &dataQueue, config_map &config) {
    try {
        clickhouse::Client client(clickhouse::ClientOptions()
                          .SetHost(std::get<std::string>(config["clickhouse_host"]))
                          .SetPort(std::get<uint>(config["clickhouse_port"]))
                          .SetDefaultDatabase(std::get<std::string>(config["clickhouse_database"]))
                          .SetUser(std::get<std::string>(config["clickhouse_user"]))
                          .SetPassword(std::get<std::string>(config["clickhouse_password"])));

        uint32_t jobId = std::get<uint>(config["jobId"]);
        std::string hostname = std::get<std::string>(config["hostname"]);

        // Batch storage
        CQueue::SchemaEntries accumulated_data;
        int bufferSize = 0;

        while (!canceled) {
            CQueue::SchemaEntries data;
            // wait with timeout in case no new data is coming in and measurements are canceled
            if (dataQueue.waitAndPopAll(data, QUEUE_TIMEOUT) != 0)
                continue;

            // Accumulate data
            accumulated_data.basic_int.insert(accumulated_data.basic_int.end(), 
                                            data.basic_int.begin(), data.basic_int.end());
            accumulated_data.basic_double.insert(accumulated_data.basic_double.end(), 
                                                data.basic_double.begin(), data.basic_double.end());
            accumulated_data.device_int.insert(accumulated_data.device_int.end(), 
                                              data.device_int.begin(), data.device_int.end());
            accumulated_data.device_double.insert(accumulated_data.device_double.end(), 
                                                 data.device_double.begin(), data.device_double.end());
            accumulated_data.topology_int.insert(accumulated_data.topology_int.end(), 
                                                data.topology_int.begin(), data.topology_int.end());
            accumulated_data.topology_double.insert(accumulated_data.topology_double.end(), 
                                                   data.topology_double.begin(), data.topology_double.end());

            bufferSize += data.basic_int.size() + data.basic_double.size() + 
                         data.device_int.size() + data.device_double.size() +
                         data.topology_int.size() + data.topology_double.size();

            // Flush batches when buffer size is reached
            if (bufferSize >= BUFFER_SIZE) {
                insertBasicInt(client, accumulated_data.basic_int, jobId, hostname);
                insertBasicDouble(client, accumulated_data.basic_double, jobId, hostname);
                insertDeviceInt(client, accumulated_data.device_int, jobId, hostname);
                insertDeviceDouble(client, accumulated_data.device_double, jobId, hostname);
                insertTopologyInt(client, accumulated_data.topology_int, jobId, hostname);
                insertTopologyDouble(client, accumulated_data.topology_double, jobId, hostname);

                // Clear accumulated data
                accumulated_data = CQueue::SchemaEntries{};
                bufferSize = 0;
            }
        }

        // Final flush for remaining data
        if (bufferSize > 0) {
            insertBasicInt(client, accumulated_data.basic_int, jobId, hostname);
            insertBasicDouble(client, accumulated_data.basic_double, jobId, hostname);
            insertDeviceInt(client, accumulated_data.device_int, jobId, hostname);
            insertDeviceDouble(client, accumulated_data.device_double, jobId, hostname);
            insertTopologyInt(client, accumulated_data.topology_int, jobId, hostname);
            insertTopologyDouble(client, accumulated_data.topology_double, jobId, hostname);
        }

    } catch (const std::exception &e) {
        CLogging::log("DbWriter", CLogging::error, "Database Error - " + std::string(e.what()));
        canceled = true;
    }
}
