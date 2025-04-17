/**
 * @file CInterconnectEthernet.hpp
 * @brief Header for CInterconnectEthernet
 *
 ***********************************************/

#include "CDataCollectionBase.hpp"

/**
 * @class CInterconnectEthernet
 * @brief Retrieves ethernet usage data
 */
class CInterconnectEthernet : public CDataCollectionBase {
   public:
    CInterconnectEthernet(CQueue *, std::chrono::time_point<std::chrono::system_clock>, uint64_t);
    virtual ~CInterconnectEthernet();
    int measure();

   private:
    int readProc(std::map<std::string, uint64_t> &);
    void calculateUsage(std::map<std::string, uint64_t> &, std::map<std::string, uint64_t> &);
    const std::string prefix = "eth_";
    std::map<std::string, CDataCollectionBase::metricMeta> metricInfo = {
        {"rcv_bytes", {prefix + "rcv_bw"}},
        {"rcv_packets", {prefix + "rcv_pkg"}},
        {"xmit_bytes", {prefix + "xmit_bw"}},
        {"xmit_packets", {prefix + "xmit_pkg"}}};
};