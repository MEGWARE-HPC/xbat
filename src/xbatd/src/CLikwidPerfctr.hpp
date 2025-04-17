/**
 * @file CLikwidPerfctr.hpp
 * @brief Header for CLikwidPerfctr
 *
 ***********************************************/

#include <tuple>

#include "CDataCollectionBase.hpp"
#include "topology.hpp"

/**
 * @class CLikwidPerfctr
 * @brief Measurement via LIKWID
 */
class CLikwidPerfctr : public CDataCollectionBase {
   public:
    CLikwidPerfctr(CQueue *, std::chrono::time_point<std::chrono::system_clock>, uint64_t, const Topology::cpuTopology &);
    virtual ~CLikwidPerfctr();
    int measure();

   private:
    int measureSets();
    int getAvailableGroups(std::vector<std::string> &);
    int prepareMeasurements();
    static void AddHPMThread(int);
    void parseMetrics();
    std::vector<int> gids;
    std::vector<int> cpus;
    std::vector<std::string> setList;
    int64_t cycleOverhead = 1000;
    Topology::cpuTopology topology;

    const std::vector<std::string> defaultSets = {
    "BRANCH",
    "CYCLE_ACTIVITY",
    "CYCLE_STALLS",
    "DATA",
    "ENERGY",
    "FLOPS_SP",
    "FLOPS_DP",
    "HBM",
    "ICACHE",
    "L2CACHE",
    "L2",
    "L3CACHE",
    "L3",
    "MEM",
    "MEM1",
    "MEM2",
    "MEMREAD",
    "MEMWRITE",
    // "NUMA",
    "UPI"};

    std::map<std::string, std::map<std::string, metricMeta>> metrics;
};