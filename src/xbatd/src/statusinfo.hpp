
/**
 * @file statusinfo.hpp
 * @brief Header containing statusInfo definition
 *
 ***********************************************/

#ifndef STATUSINFO_HPP
#define STATUSINFO_HPP

#include "CDataCollectionBase.hpp"
#include "CQueue.hpp"

/**
 * @brief Structure holding all information required to carry out measurements for a job.
 */
struct statusInfo {
    std::vector<CDataCollectionBase*> classList; /**< Vector of all classes initialized for measurements */
    CQueue dataQueue;                            /**< Queue holding data to be sent to master */
    /**
     * @brief Construct a new statusInfo object and initialize
     *
     */
    statusInfo() {}
    ~statusInfo();
};

#endif /* STATUSINFO_HPP */