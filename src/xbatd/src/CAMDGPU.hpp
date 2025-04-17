/**
 * @file CAMDGPU.hpp
 * @brief Header for CAMDGPU
 *
 ***********************************************/

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wpedantic"
// Silence Wpedantic warning from inside of amdsmi.h
#include <amd_smi/amdsmi.h>
#pragma GCC diagnostic pop

#include "CDataCollectionBase.hpp"

/**
 * @class CAMDGPU
 * @brief Retrieves AMD gpu performance data
 */
class CAMDGPU : public CDataCollectionBase {
   public:
    CAMDGPU(CQueue *, std::chrono::time_point<std::chrono::system_clock> timestamp = std::chrono::system_clock::now(),
            uint64_t interval = 5000);
    virtual ~CAMDGPU();
    int measure();

   private:
    int prepare();
    int collect();
    std::vector<amdsmi_socket_handle> sockets;
    std::vector<std::vector<amdsmi_processor_handle>> processors;
    // TODO AMD_CLK_TYPE_SOC is not supported in all devices.
    //  AMDSMI_CLK_TYPE_VCLK0 and AMDSMI_CLK_TYPE_VCLK1 represent the video-related clock domains
    std::map<std::string, amdsmi_clk_type_t> clockTypes = {{"gpu_clk_graphics", AMDSMI_CLK_TYPE_GFX},
                                                           {"gpu_clk_mem", AMDSMI_CLK_TYPE_MEM}};
};