/**
 * @file CIOStat.hpp
 * @brief Header for CIOStat
 *
 ***********************************************/

#include "CDataCollectionBase.hpp"

/**
 * @class CIOStat
 * @brief Retrieves I/O usage data
 */
class CIOStat : public CDataCollectionBase {
   public:
    CIOStat(CQueue *, std::chrono::time_point<std::chrono::system_clock>, uint64_t);
    virtual ~CIOStat();
    int measure();

   private:
    std::string readIOStat();
    int parseIOStat();
    const std::string prefix = "disk_";
    std::map<std::string, CDataCollectionBase::metricMeta> metricInfo = {
        {"r/s", {prefix + "r_req_s"}},
        {"w/s", {prefix + "w_req_s"}},
        {"d/s", {prefix + "d_req_s"}},
        {"f/s", {prefix + "f_req_s"}},
        {"rkB/s", {prefix + "r_bw", 1024}},
        {"rmB/s", {prefix + "r_bw", 1024 * 1024}},
        {"wkB/s", {prefix + "w_bw", 1024}},
        {"wmB/s", {prefix + "w_bw", 1024 * 1024}},
        {"areq_sz", {prefix + "areq_sz", 1024}},
        {"rareq_sz", {prefix + "rareq_sz", 1024}},
        {"wareq_sz", {prefix + "wareq_sz", 1024}},
        {"dareq_sz", {prefix + "dareq_sz", 1024}},
        {"await", {prefix + "await"}},
        {"r_await", {prefix + "r_await"}},
        {"w_await", {prefix + "w_await"}},
        {"rqm,", {prefix + "rqm"}},
        {"rrqm,", {prefix + "rrqm"}},
        {"wrqm", {prefix + "wrqm"}},
        {"drqm", {prefix + "drqm"}},
        {"util", {prefix + "util"}}

    };
};