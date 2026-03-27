#ifndef TOPOLOGY_HPP
#define TOPOLOGY_HPP

#include <cstdint>
#include <map>
#include <string>

namespace Topology {

struct hwThread {
    uint32_t hwThread;
    uint32_t thread;
    uint32_t core;
    uint32_t socket;
    uint32_t numa;
};

struct cpuTopology {
    std::string name;
    std::string short_name;
    std::string osname;
    bool smt;
    uint32_t threadsPerCore;
    uint32_t coresPerSocket;
    uint32_t sockets;
    // per instance in byte
    uint32_t l1Cache;
    uint32_t l2Cache;
    uint32_t l3Cache;
    // total accross respective instances in byte per socket
    uint32_t l1CachePerSocket;
    uint32_t l2CachePerSocket;
    uint32_t l3CachePerSocket;
    uint32_t cachePerSocket;
    // total accross respective instances in byte across all sockets
    uint32_t l1CacheTotal;
    uint32_t l2CacheTotal;
    uint32_t l3CacheTotal;
    uint32_t cacheTotal;
    std::map<uint32_t, hwThread> hwThreads;
};

int getCpuTopology(cpuTopology &);

} /* namespace Topology */

#endif /* TOPOLOGY_HPP */
