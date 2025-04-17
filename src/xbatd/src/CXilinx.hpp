/**
 * @file CXilinx.hpp
 * @brief Header for CXilinx
 *
 ***********************************************/

#include "CDataCollectionBase.hpp"
#include "CQueue.hpp"

/**
 * @class CXilinx
 * @brief Class for measuring Xilinx FPGA power usage
 *
 */
class CXilinx : public CDataCollectionBase {
   public:
    CXilinx(CQueue *, std::chrono::time_point<std::chrono::system_clock>, uint64_t);
    virtual ~CXilinx();
    int measure();

   private:
    int prepare();
    int readUsage();
    std::vector<std::string> bdfs;
};
