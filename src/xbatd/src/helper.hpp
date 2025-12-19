/**
 * @file helper.hpp
 * @brief Header for helper.cpp
 *
 ***********************************************/

#ifndef HELPER_HPP
#define HELPER_HPP

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <list>
#include <regex>
#include <string>
#include <vector>

#include "external/nlohmann-json/include/nlohmann/json.hpp"

#define THREAD_RUNNING 0
#define THREAD_TERMINATED 1
#define THREAD_FORCEFULLY_TERMINATED 2
#define THREAD_SELF_TERMINATED 3

namespace Helper {
int getCommandOutput(std::string, std::string &);
int readFileToString(std::string, std::string &);
int writeToFile(std::string, const std::string &, bool = false);
int deleteFile(std::string);
void eraseLinesFromStart(std::string &, int);
void filterLinesNotContaining(std::vector<std::string>, std::string &, bool = false);
void filterLinesContaining(std::vector<std::string>, std::string &, bool = false);
std::string trimWhitespaces(std::string, bool = false);
void joinVector(const std::vector<std::string> &, std::string, std::string &);
time_t getSecondsSinceEpoch();
uint64_t getMillisecondsSinceEpoch();
void splitStr(const std::string &, const std::string, std::vector<std::string> &);
nlohmann::json gatherSystemInfo();
std::string sanitizeForILP(std::string);
double round(double v, int = 2);
int getCpuTopology();
std::string toLower(std::string);
std::string extractNumber(std::string, bool = false);
bool strToBool(std::string);
std::string boolToStr(bool);
std::chrono::system_clock::time_point parseTime(std::string);
std::string md5(const std::string &);
std::string decode64(const std::string &);
std::string encode64(const std::string &);
template <typename T>
bool vectorContains(const std::vector<T> &vec, T entry) {
    return std::find(vec.begin(), vec.end(), entry) != vec.end();
}

/**
 * @brief Checks whether a string starts with the specified prefix
 *
 * @param str String to be examined
 * @param prefix Prefix to be checked for
 */
inline bool startsWith(const std::string &str, const std::string &prefix) {
    return str.size() >= prefix.size() && 0 == str.compare(0, prefix.size(), prefix);
}

/**
 * @brief Checks whether a string ends with the specified suffix
 *
 * @param str String to be examined
 * @param suffix Suffix to be checked for
 */
inline bool endsWith(const std::string &str, const std::string &suffix) {
    return str.size() >= suffix.size() && 0 == str.compare(str.size() - suffix.size(), suffix.size(), suffix);
}

/**
 * @brief Checks whether a string is a number
 *
 * @param str String to be examined
 */
inline bool isNumber(const std::string &str) {
    return std::regex_match(str, std::regex(("((\\+|-)?[[:digit:]]+)(\\.(([[:digit:]]+)?))?")));
}

} /* namespace Helper */

#endif /* HELPER_HPP */