/**
 * @file CDataCollectionBase.cpp
 * @brief Base class for all data collection classes.
 *
 * Lock launchMutex for derived class' constructor to unlock. This way it is ensured that
 * the constructor of the derived class has finished before the base class is abled to call
 * the measure().
 *
 * Lock cleanUpMutex to unlock it after the measure() thread returned. This prevents the calling
 * of the destructor while the measurement is still in progress.
 ***********************************************/

#include "CDataCollectionBase.hpp"

#include <pthread.h>
#include <signal.h>

#include <chrono>
#include <iostream>  //TODO REMOVE
#include <string>

/**
 * @brief Construct a new CDataCollectionBase::CDataCollectionBase object
 *
 * Set up all data and lock mutexes.
 */
CDataCollectionBase::CDataCollectionBase() {
    launchMutex.lock();
    cleanUpMutex.lock();
    terminate = false;
    lastHeartbeat = Helper::getSecondsSinceEpoch();
}

/**
 * @brief Destroy the CDataCollectionBase::CDataCollectionBase object
 *
 */
CDataCollectionBase::~CDataCollectionBase() {
    if (!wasForcefullyTerminated)
        measurementThread.join();
}

/**
 * @brief Returns the termination status of the measurement thread
 *
 * @return thread status
 */
int CDataCollectionBase::getThreadStatus() {
    if (hasTerminated) return THREAD_TERMINATED;
    if (wasForcefullyTerminated) return THREAD_FORCEFULLY_TERMINATED;
    if (selfTerminated) return THREAD_SELF_TERMINATED;
    return THREAD_RUNNING;
}

/**
 * @brief Creates a new thread for measurement and starts measurements
 *
 */
void CDataCollectionBase::startMeasurement() {
    /* when using a member function as the first thread argument the second argument is supposed to be a pointer to
     * object. the second this is the parameter for the member function.
     */
    measurementThread = std::thread(&CDataCollectionBase::createThreadAndMeasure, this, this);
    wasForcefullyTerminated = false; /**< required in case a thread was terminated and restarted again */
}

/**
 * @brief Calls the measure() function of derived class within the thread
 *
 * @param selfPtr Pointer to this
 */
void CDataCollectionBase::createThreadAndMeasure(void* selfPtr) {
    launchMutex.lock();
    launchMutex.unlock();
    /* Call childs measure function */
    if (((CDataCollectionBase*)selfPtr)->measure() != 0)
        selfTerminated = true;
    else
        hasTerminated = true;
    /* Measurements of thread stopped either due to error or terminate being set */
    cleanUpMutex.unlock();
}

/**
 * @brief Signal thread to stop measurements
 *
 */
void CDataCollectionBase::stopMeasurement() {
    terminate = true;
}

/**
 * @brief Forcefully stop/kill a thread
 *
 */
void CDataCollectionBase::forceStop() {
    /* Detach thread before killing.
     * Refrain from calling ~thread(), it would call std::terminate on a joinable
     * thread which would terminate the whole application. Calling it on a non joinable
     * thread will do nothing.
     * Use pthread_kill over native handle instead.
     */
    CLogging::log(moduleName, CLogging::error, "Forcefully stopping thread");
    // auto handle = measurementThread.native_handle();
    measurementThread.detach();
    return;
    /* TODO TODO TODO
     * Find different solution since SIGKILL kills entire process.
     * Other signals like SIGTERM might work but would require the thread to have a different
     * signalhandler than the one inherited from main.
     * TODO TODO TODO
     */

    /*if (pthread_kill(handle, SIGKILL) != 0)
     *   std::cerr << "Error killing timed out thread." << std::endl;
     */
    wasForcefullyTerminated = true;
}

/**
 * @brief Start measurements.
 *
 * This function will be overwritten by derived classed
 *
 * @return int
 */
int CDataCollectionBase::measure() {
    return 0;
}

/**
 * @brief Returns the interval in seconds
 *
 * @return time_t Duration in seconds
 */
time_t CDataCollectionBase::getInterval() {
    return interval;
}

/**
 * @brief Returns the last heartbeat as a unix timestamp
 *
 * @return time_t Unix timestamp
 */
time_t CDataCollectionBase::getLastHeartbeat() {
    return lastHeartbeat;
}

/**
 * @brief Sleeps until the end of the current interval or termination
 *
 */
void CDataCollectionBase::sleepUntilIntervalEnd() {
    int64_t remaining = std::chrono::duration_cast<std::chrono::milliseconds>(intervalEnd - std::chrono::system_clock::now()).count();
    if (remaining <= 0) return;
    sleepMillisecondsAndCheck(remaining);
}

/**
 * @brief Sleep in slices of size SLEEPINTERVALSECONDS milliseconds and check if terminated
 *
 * @param sleepLeft Intended sleep duration in milliseconds
 */
void CDataCollectionBase::sleepMillisecondsAndCheck(int64_t sleepLeft) {
    while (sleepLeft > 0 && !terminate) {
        if (sleepLeft < SLEEPINTERVALMILLISECONDS) {
            std::this_thread::sleep_for(std::chrono::milliseconds(sleepLeft));
            return;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(SLEEPINTERVALMILLISECONDS));
        sleepLeft -= SLEEPINTERVALMILLISECONDS;
    }
}

/**
 * @brief Adjust current interval of the measurement to the intended interval
 *
 */
void CDataCollectionBase::synchronizeMeasurement() {
    int64_t minimumTime = interval / 4;
    intervalEnd = intervalStart + std::chrono::milliseconds(interval);
    auto currentTime = std::chrono::system_clock::now();
    int64_t remaining = std::chrono::duration_cast<std::chrono::milliseconds>(intervalEnd - currentTime).count();
    timeLeft = remaining;

    if (remaining < minimumTime) {
        int64_t catchup = abs(remaining);
        int64_t remainder = catchup % interval;
        intervalEnd = intervalEnd + std::chrono::milliseconds(catchup - remainder + interval);
        timeLeft = std::chrono::duration_cast<std::chrono::milliseconds>(intervalEnd - currentTime).count();
        // CLogging::log(moduleName, CLogging::debug,
        //               "remaining: " + std::to_string(remaining) + " | minimumTime: " + std::to_string(minimumTime) +
        //                   " | catchup: " + std::to_string(catchup) + " | remainder: " + std::to_string(remainder) +
        //                   " | timeleft: " + std::to_string(timeLeft));
    }

    if (timeLeft > interval) {
        int64_t sleepLeft = timeLeft - interval;
        timeLeft = interval;
        sleepMillisecondsAndCheck(sleepLeft);
    }

    intervalStart = intervalEnd + std::chrono::milliseconds(interval);
}

/**
 * @brief Clean up data, push to queue and set heartbeat
 *
 */
void CDataCollectionBase::intervalCleanup(bool setintervalEnd) {
    if (setintervalEnd)
        intervalStart = intervalEnd;

    /* set new heartbeat timestamp to signal watchdog that this thread is not hung. */
    lastHeartbeat = Helper::getSecondsSinceEpoch();
};