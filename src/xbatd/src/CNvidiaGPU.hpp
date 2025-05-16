/**
 * @file CNvidiaGPU.hpp
 * @brief Header for CNvidiaGPU
 *
 ***********************************************/

#include <nvml.h>

#include "CDataCollectionBase.hpp"

/**
 * @class CNvidiaGPU
 * @brief Retrieves NVIDIA gpu performance data
 */
class CNvidiaGPU : public CDataCollectionBase {
   public:
    CNvidiaGPU(CQueue *, std::chrono::time_point<std::chrono::system_clock>, uint64_t);
    virtual ~CNvidiaGPU();
    int measure();

   private:
    int prepare();
    int collect();
    std::vector<nvmlDevice_t> devices;
    std::vector<int> device_nvlinks;
    std::vector<std::vector<unsigned long long int>> former_nvlink_tx;
    std::vector<std::vector<unsigned long long int>> former_nvlink_rx;
    std::map<std::string, nvmlClockType_enum> clockTypes = {{"gpu_clk_graphics", NVML_CLOCK_GRAPHICS},
                                                            {"gpu_clk_sm", NVML_CLOCK_SM},
                                                            {"gpu_clk_mem", NVML_CLOCK_MEM},
                                                            {"gpu_clk_video", NVML_CLOCK_VIDEO}};
};