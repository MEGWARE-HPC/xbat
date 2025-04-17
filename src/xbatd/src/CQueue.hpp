/**
 * @file CQueue.hpp
 * @brief Header for CQueue
 *
 ***********************************************/

#ifndef CQUEUE_HPP
#define CQUEUE_HPP

#include <condition_variable>
#include <map>
#include <mutex>
#include <queue>
#include <variant>
#include <vector>

/**
 * @class CQueue
 * @brief Thread-safe queue class for Influx Line Protocol (ILP) entries
 *
 * Supports storing and retrieving ILP entries containing either `int64_t` or `double` values.
 */
class CQueue {
   public:
    /**
     * @brief Construct a new CQueue object
     *
     */
    CQueue() {}

    /**
     * @brief Destroy the CQueue object
     *
     */
    ~CQueue() {}

    /**
     * @struct ILP
     * @brief Represents a single Influx Line Protocol (ILP) data point
     *
     * @tparam T Type of the value stored (e.g., int64_t or double)
     */
    template <typename T>
    struct ILP {
        std::string measurement;
        std::map<std::string, std::string> tags;
        T value;
        std::chrono::time_point<std::chrono::system_clock> ts;
    };

    /**
     * @struct ILPEntries
     * @brief Container for multiple ILP entries of different types
     */
    struct ILPEntries {
        std::vector<ILP<int64_t>> ilp_int64_t;
        std::vector<ILP<double>> ilp_double;
    };

    /**
     * @brief Add multiple items to the queue at once
     *
     * @tparam T Type of ILP value
     * @param items Vector of ILP items to add to the queue
     */
    template <typename T>
    void pushMultiple(std::vector<CQueue::ILP<T>> items) {
        std::unique_lock<std::mutex> lock(queue_mutex);
        bool was_empty = data_queue.empty();

        for (auto &item : items)
            data_queue.push(item);

        lock.unlock();

        if (was_empty)
            data_available.notify_one();
    }

    /**
     * @brief Adds a single ILP item to the queue
     *
     * @tparam T Type of ILP value
     * @param item ILP item to add to the queue
     */
    template <typename T>
    void pushSingle(ILP<T> item) {
        std::vector<ILP<T>> items = {item};
        pushMultiple<T>(items);
    }

    /**
     * @brief Pop a single item from the queue. Waits if the queue is empty.
     *
     * @param data Reference to a variant where the popped item will be stored
     * @param timeout Timeout in seconds to wait if the queue is empty (0 = wait indefinitely)
     * @return int 0 if successful, -1 if timeout occurred
     */
    int waitAndPop(std::variant<ILP<int64_t>, ILP<double>> &data, int timeout = 0) {
        std::unique_lock<std::mutex> lock(queue_mutex);
        if (data_queue.empty()) {
            if (wait(lock, timeout) != 0) {
                lock.unlock();
                return -1;
            }
        }

        data = data_queue.front();
        data_queue.pop();
        lock.unlock();
        return 0;
    }

    /**
     * @brief Pop all items from the queue. Waits if the queue is empty.
     *
     * @param data Reference to ILPEntries structure to hold all popped items
     * @param timeout Timeout in seconds to wait if the queue is empty (0 = wait indefinitely)
     * @return int 0 if successful, -1 if timeout occurred
     */
    int waitAndPopAll(ILPEntries &data, int timeout = 0) {
        std::unique_lock<std::mutex> lock(queue_mutex);
        if (data_queue.empty()) {
            if (wait(lock, timeout) != 0) {
                lock.unlock();
                return -1;
            }
        }

        while (!data_queue.empty()) {
            auto entry = data_queue.front();
            data_queue.pop();

            switch (entry.index()) {
                case 0:
                    data.ilp_int64_t.push_back(std::get<CQueue::ILP<int64_t>>(entry));
                    break;
                case 1:
                    data.ilp_double.push_back(std::get<CQueue::ILP<double>>(entry));
                    break;
                default:
                    break;
            }
        }

        lock.unlock();
        return 0;
    }

    /**
     * @brief Clear all data from the queue
     */
    void dropData() {
        std::unique_lock<std::mutex> lock(queue_mutex);
        std::queue<std::variant<ILP<int64_t>, ILP<double>>> empty;
        std::swap(data_queue, empty);
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
        bool b = !data_queue.empty();
        lock.unlock();
        return b;
    }

   private:
    std::condition_variable data_available;
    std::mutex queue_mutex;
    std::queue<std::variant<ILP<int64_t>, ILP<double>>> data_queue;

    /**
     * @brief Internal wait helper function for condition variable
     *
     * @param lock Unique lock on the mutex
     * @param timeout Timeout in seconds (0 = wait indefinitely)
     * @return int 0 if notified, -1 if timeout occurred
     */
    int wait(std::unique_lock<std::mutex> &lock, int timeout = 0) {
        if (timeout > 0) {
            auto endTime = std::chrono::system_clock::now() + std::chrono::seconds(timeout);
            auto res = data_available.wait_until(lock, endTime);
            if (res == std::cv_status::timeout)
                return -1;

        } else
            data_available.wait(lock);

        return 0;
    };
};

#endif /* CQUEUE_HPP */