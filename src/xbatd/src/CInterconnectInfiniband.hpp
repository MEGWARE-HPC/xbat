/**
 * @file CInterconnectInfiniband.hpp
 * @brief Header for CInterconnectInfiniband
 *
 ***********************************************/

#include "CDataCollectionBase.hpp"

/**
 * @class CInterconnectInfiniband
 * @brief Retrieves infiniband usage data
 */
class CInterconnectInfiniband : public CDataCollectionBase {
   public:
    CInterconnectInfiniband(CQueue *, std::chrono::time_point<std::chrono::system_clock>, uint64_t);
    virtual ~CInterconnectInfiniband();
    int measure();

   private:
    const std::string prefix = "ib_";
    const std::vector<std::string> metricCounters = {
        "port_rcv_data",
        "port_rcv_packets",
        "port_xmit_data",
        "port_xmit_packets",
    };

    std::map<std::string, CDataCollectionBase::metricMeta> metricInfo = {
        {metricCounters[0], {prefix + "rcv_bw", 4}},
        {metricCounters[1], {prefix + "rcv_pkg", 1}},
        {metricCounters[2], {prefix + "xmit_bw", 4}},
        {metricCounters[3], {prefix + "xmit_pkg", 1}}};

    int readInfiniband(std::map<std::string, uint64_t> &);
    void calculateUsage(std::map<std::string, uint64_t> &, std::map<std::string, uint64_t> &);
};