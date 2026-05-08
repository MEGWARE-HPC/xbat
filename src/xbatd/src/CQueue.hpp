/**
 * @file CQueue.hpp
 * @brief Header for Schema-Aware Queue for ClickHouse data
 *
 ***********************************************/

#ifndef CQUEUE_HPP
#define CQUEUE_HPP

#include <condition_variable>
#include <map>
#include <mutex>
#include <queue>
#include <vector>
#include <chrono>

/**
 * @class CQueue
 * @brief Thread-safe queue class for schema-aware ClickHouse data entries
 *
 * Supports storing and retrieving measurement data with explicit schema information.
 */
class CQueue {
   public:
    /**
     * @brief Construct a new CQueue object
     */
    CQueue() {}

    /**
     * @brief Destroy the CQueue object
     */
    ~CQueue() {}

    /**
     * @brief Basic measurement data (job_id, node, level, value, ts)
     */
    template <typename T>
    struct BasicMeasurement {
        std::string measurement;
        std::string level;
        T value;
        std::chrono::time_point<std::chrono::system_clock> ts;
    };

    /**
     * @brief Device measurement data (job_id, node, level, device, value, ts)
     */
    template <typename T>
    struct DeviceMeasurement {
        std::string measurement;
        std::string level;
        std::string device;
        T value;
        std::chrono::time_point<std::chrono::system_clock> ts;
    };

    /**
     * @brief Topology measurement data (job_id, node, level, thread, core, numa, socket, value, ts)
     */
    template <typename T>
    struct TopologyMeasurement {
        std::string measurement;
        std::string level;
        uint32_t thread;
        uint32_t core;
        uint32_t numa;
        uint32_t socket;
        T value;
        std::chrono::time_point<std::chrono::system_clock> ts;
    };

    /**
     * @brief Container for all schema-separated measurement entries
     */
    struct SchemaEntries {
        std::vector<BasicMeasurement<int64_t>> basic_int;
        std::vector<BasicMeasurement<double>> basic_double;
        std::vector<DeviceMeasurement<int64_t>> device_int;
        std::vector<DeviceMeasurement<double>> device_double;
        std::vector<TopologyMeasurement<int64_t>> topology_int;
        std::vector<TopologyMeasurement<double>> topology_double;
    };

    /**
     * @brief Generic push function that handles all measurement types
     * 
     * This function automatically determines the correct queue based on the measurement type
     * and value type, providing a unified interface for all insertions.
     */
    template <typename MeasurementType>
    void push(const MeasurementType &item) {
        std::vector<MeasurementType> items = {item};
        pushMultiple(items);
    }

    /**
     * @brief Generic push function for multiple measurements
     * 
     * This function automatically determines the correct queue based on the measurement type
     * and value type, providing a unified interface for batch insertions.
     */
    template <typename MeasurementType>
    void pushMultiple(const std::vector<MeasurementType> &items) {
        if (items.empty()) return;
        
        std::unique_lock<std::mutex> lock(queue_mutex);
        bool was_empty = isEmpty();

        // Use if constexpr to determine measurement and value type at compile time
        if constexpr (std::is_same_v<MeasurementType, BasicMeasurement<int64_t>>) {
            data_queue.basic_int.insert(data_queue.basic_int.end(), items.begin(), items.end());
        } else if constexpr (std::is_same_v<MeasurementType, BasicMeasurement<double>>) {
            data_queue.basic_double.insert(data_queue.basic_double.end(), items.begin(), items.end());
        } else if constexpr (std::is_same_v<MeasurementType, DeviceMeasurement<int64_t>>) {
            data_queue.device_int.insert(data_queue.device_int.end(), items.begin(), items.end());
        } else if constexpr (std::is_same_v<MeasurementType, DeviceMeasurement<double>>) {
            data_queue.device_double.insert(data_queue.device_double.end(), items.begin(), items.end());
        } else if constexpr (std::is_same_v<MeasurementType, TopologyMeasurement<int64_t>>) {
            data_queue.topology_int.insert(data_queue.topology_int.end(), items.begin(), items.end());
        } else if constexpr (std::is_same_v<MeasurementType, TopologyMeasurement<double>>) {
            data_queue.topology_double.insert(data_queue.topology_double.end(), items.begin(), items.end());
        } else {
            static_assert(std::is_same_v<MeasurementType, void>, "Unsupported measurement type");
        }

        lock.unlock();
        if (was_empty)
            data_available.notify_one();
    }

    /**
     * @brief Pop all items from the queue. Waits if the queue is empty.
     *
     * @param data Reference to SchemaEntries structure to hold all popped items
     * @param timeout Timeout in seconds to wait if the queue is empty (0 = wait indefinitely)
     * @return int 0 if successful, -1 if timeout occurred
     */
    int waitAndPopAll(SchemaEntries &data, int timeout = 0) {
        std::unique_lock<std::mutex> lock(queue_mutex);
        if (isEmpty()) {
            if (wait(lock, timeout) != 0) {
                lock.unlock();
                return -1;
            }
        }

        // Move all data to output structure
        data.basic_int = std::move(data_queue.basic_int);
        data.basic_double = std::move(data_queue.basic_double);
        data.device_int = std::move(data_queue.device_int);
        data.device_double = std::move(data_queue.device_double);
        data.topology_int = std::move(data_queue.topology_int);
        data.topology_double = std::move(data_queue.topology_double);

        // Clear the internal queue
        data_queue = SchemaEntries{};

        lock.unlock();
        return 0;
    }

    /**
     * @brief Clear all data from the queue
     */
    void dropData() {
        std::unique_lock<std::mutex> lock(queue_mutex);
        data_queue = SchemaEntries{};
        lock.unlock();
    }

    /**
     * @brief Check whether the queue has data
     *
     * @return true if the queue contains data
     * @return false if the queue is empty
     */
    bool hasData() {
        std::unique_lock<std::mutex> lock(queue_mutex);
        bool has_data = !isEmpty();
        lock.unlock();
        return has_data;
    }

   private:
    std::condition_variable data_available;
    std::mutex queue_mutex;
    SchemaEntries data_queue;

    /**
     * @brief Check if all queues are empty (internal, assumes lock is held)
     */
    bool isEmpty() const {
        return data_queue.basic_int.empty() && data_queue.basic_double.empty() &&
               data_queue.device_int.empty() && data_queue.device_double.empty() &&
               data_queue.topology_int.empty() && data_queue.topology_double.empty();
    }

    /**
     * @brief Internal wait helper function for condition variable
     */
    int wait(std::unique_lock<std::mutex> &lock, int timeout = 0) {
        if (timeout > 0) {
            auto endTime = std::chrono::system_clock::now() + std::chrono::seconds(timeout);
            auto res = data_available.wait_until(lock, endTime);
            if (res == std::cv_status::timeout)
                return -1;
        } else {
            data_available.wait(lock);
        }
        return 0;
    }
};

#endif /* CQUEUE_HPP */