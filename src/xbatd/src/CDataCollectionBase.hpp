/**
 * @file CDataCollectionBase.hpp
 * @brief Header for CDataCollectionBase
 *
 ***********************************************/

#ifndef CDATACOLLECTIONBASE_HPP
#define CDATACOLLECTIONBASE_HPP

#include <atomic>
#include <chrono>
#include <cstdint>
#include <ctime>
#include <functional>
#include <sstream>
#include <string>
#include <thread>

#include "CLogging.hpp"
#include "CQueue.hpp"
#include "helper.hpp"

#define SLEEPINTERVALSECONDS 1
#define SLEEPINTERVALMILLISECONDS 1000 * SLEEPINTERVALSECONDS

class CDataCollectionBase {
   public:
    CDataCollectionBase();
    virtual ~CDataCollectionBase();
    void startMeasurement();
    void stopMeasurement();
    void forceStop();
    int getThreadStatus();
    time_t getInterval();
    time_t getLastHeartbeat();

   protected:
    virtual int measure();
    void sleepUntilIntervalEnd();
    void synchronizeMeasurement();
    void sleepMillisecondsAndCheck(int64_t sleepLeft);
    void sleepForMicroseconds(time_t);
    void intervalCleanup(bool = true);

    std::mutex launchMutex;
    std::mutex cleanUpMutex;

    CLogging logger;

    std::string moduleName;
    CQueue* dataQueue;
    int64_t interval;                                                 /**< Interval duration in milliseconds */
    std::chrono::time_point<std::chrono::system_clock> intervalStart; /**< Starting time_point of current interval */
    std::chrono::time_point<std::chrono::system_clock> intervalEnd;   /**< Ending time_point of current interval */
    int64_t timeLeft;                                                 /**< Time left for measurements when starting new measurement iteration */
    time_t lastHeartbeat;                                             /**< Unix timestamp of last heartbeat */
    bool hasTerminated = false;                                       /**< Thread terminated due to termination signal */
    bool wasForcefullyTerminated = false;                             /**< Thread forcefully terminated by watchdog */
    bool selfTerminated = false;                                      /**< Thread is not able to proceed measurements and thus terminated itself -> restart not reasonable */
    std::atomic_bool terminate;                                       /**< Unix timestamp of last heartbeat */
    std::stringstream output;                                         /**< Holds measurement data*/

    struct metricMeta {
        std::string label;
        int scale = 1;
        std::string level = "";
    };

   private:
    void createThreadAndMeasure(void*);
    std::thread measurementThread; /**< std::thread Handle for measurement thread*/
};

#endif