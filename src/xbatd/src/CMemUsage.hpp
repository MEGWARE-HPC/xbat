/**
 * @file CMemUsage.hpp
 * @brief Header for CMemUsage
 *
 ***********************************************/

#include "CDataCollectionBase.hpp"

/**
 * @class CMemUsage
 * @brief Retrieves memory usage data
 */
class CMemUsage : public CDataCollectionBase {
   public:
    CMemUsage(CQueue *, std::chrono::time_point<std::chrono::system_clock>, uint64_t);
    virtual ~CMemUsage();
    int measure();

   private:
    int readProc();
};