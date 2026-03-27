
#include "topology.hpp"

#include <iostream>
#include <map>

#include "CLogging.hpp"
#include "likwid.h"

int Topology::getCpuTopology(cpuTopology &topo) {
    if (topology_init() != 0 or numa_init() != 0) {
        CLogging::log("Topology", CLogging::error, "Error initialising topology");
        return 1;
    }

    CpuInfo_t cpuInfo = get_cpuInfo();

    topo.name = cpuInfo->name;
    topo.short_name = cpuInfo->short_name;
    topo.osname = cpuInfo->osname;

    CpuTopology_t topology = get_cpuTopology();
    NumaTopology_t numa = get_numaTopology();

    std::map<int, uint32_t> numaMapping;

    for (uint32_t i = 0; i < numa->numberOfNodes; i++) {
        auto processors = numa->nodes[i].processors;
        for (uint32_t j = 0; j < numa->nodes[i].numberOfProcessors; j++) {
            numaMapping[processors[j]] = i;
        }
    }

    topo.smt = topology->numThreadsPerCore != 1;
    topo.threadsPerCore = topology->numThreadsPerCore;
    topo.coresPerSocket = topology->numCoresPerSocket;
    topo.sockets = topology->numSockets;
    int level = 0;
    for (uint32_t i = 0; i < topology->numCacheLevels; i++) {
        auto cacheLevel = topology->cacheLevels[i];

        uint32_t size = cacheLevel.size;
        int instances = (topo.coresPerSocket * topo.threadsPerCore) / cacheLevel.threads;
        int levelSize = size * instances;
        topo.cachePerSocket += levelSize;

        // ignore L1i
        if (cacheLevel.type == INSTRUCTIONCACHE) continue;

        switch (level) {
            case 0:
                topo.l1Cache = size;
                topo.l1CachePerSocket = levelSize;
                topo.l1CacheTotal = levelSize * topo.sockets;
                break;
            case 1:
                topo.l2Cache = size;
                topo.l2CachePerSocket = levelSize;
                topo.l2CacheTotal = levelSize * topo.sockets;
                break;
            case 2:
                topo.l3Cache = size;
                topo.l3CachePerSocket = levelSize;
                topo.l3CacheTotal = levelSize * topo.sockets;
                break;
            default:
                break;
        }
        level++;
    }

    topo.cacheTotal = topo.cachePerSocket * topo.sockets;

    std::map<uint32_t, hwThread> mapping;

    for (uint32_t i = 0; i < topology->numHWThreads; i++) {
        auto threadInfo = topology->threadPool[i];

        uint32_t apicId = topology->threadPool[i].apicId;

        hwThread thread = {
            apicId,
            threadInfo.threadId,
            threadInfo.coreId,
            threadInfo.packageId,
            numaMapping[apicId]};

        mapping[apicId] = thread;
    }

    topo.hwThreads = mapping;
    topology_finalize();
    numa_finalize();

    return 0;
}