/**
 * @file CCpuStat.hpp
 * @brief Header for CCpuStat
 *
 ***********************************************/

#include "CDataCollectionBase.hpp"
#include "CQueue.hpp"
#include "topology.hpp"

/**
 * @class CCpuStat
 * @brief Retrieves data for computing cpu usage
 *
 */
class CCpuStat : public CDataCollectionBase {
   public:
    CCpuStat(CQueue *, std::chrono::time_point<std::chrono::system_clock> , uint64_t, Topology::cpuTopology &);
    virtual ~CCpuStat();
    int measure();

   private:
    int readProc(std::map<std::string, std::vector<uint64_t>> &);
    std::map<std::string, std::vector<uint64_t>> previous;
    void calculateUsage(std::map<std::string, std::vector<uint64_t>> &, std::map<std::string, std::vector<uint64_t>> &);
    Topology::cpuTopology topology;
};
