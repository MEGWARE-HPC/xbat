/**
 * @file CEnergyIpmi.hpp
 * @brief Header for CEnergyIpmi
 *
 ***********************************************/

#include "CDataCollectionBase.hpp"

/**
 * @class CEnergyIpmi
 * @brief Retrieves energy usage data
 */
class CEnergyIpmi : public CDataCollectionBase {
   public:
    CEnergyIpmi(CQueue *, std::chrono::time_point<std::chrono::system_clock> , uint64_t);
    virtual ~CEnergyIpmi();
    int measure();

   private:
    int parse(std::string &);
};