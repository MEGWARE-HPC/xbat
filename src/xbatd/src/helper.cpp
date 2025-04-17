/**
 * @file helper.cpp
 * @brief Collection of helper functions
 *
 ***********************************************/

#include "helper.hpp"

#include <grp.h>
#include <openssl/evp.h>
#include <pwd.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/utsname.h>
#include <unistd.h>

#include <algorithm>
#include <boost/exception/diagnostic_information.hpp>
#include <cctype>
#include <chrono>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <regex>
#include <sstream>
#include <vector>

#include "CLogging.hpp"

#define RETMARKER "#RETVAL#" /**< Marker for return code retrieval */

namespace fs = std::filesystem;

CLogging logger;

/**
 * @brief Execute command, get output and return value
 *
 * @param cmd Command to be executed
 * @param output Reference to write output to
 * @return 0 Success
 * @return 1 Failure (non-zero exit code of cmd)
 */
int Helper::getCommandOutput(std::string cmd, std::string &output) {
    std::string data;
    FILE *stream;
    const int max_buffer = 256;
    char buffer[max_buffer];
    cmd.append(" 2>&1; echo ").append("\"#RETVAL#\"").append(" $?");
    stream = popen(cmd.c_str(), "r");
    if (stream) {
        while (!feof(stream))
            if (fgets(buffer, max_buffer, stream) != NULL)
                data.append(buffer);
        pclose(stream);
    }

    /* get exit code of executed command */
    const auto pos = data.find(RETMARKER);

    if (pos == std::string::npos) {
        output = data;
        // logger.log(CLogging::debug, data);
        return 1;
    }

    output = data.substr(0, pos);
    return stoi(data.substr(pos + std::string(RETMARKER).length()));
}

/**
 * @brief Read file and save to string reference
 *
 * @param path Path + filename of file
 * @param output Reference to write file to
 * @return 0 Success
 * @return 1 Error opening file
 */
int Helper::readFileToString(std::string path, std::string &output) {
    std::ifstream fileStream(path);
    if (!fileStream.is_open() || !fileStream.good()) {
        logger.log(CLogging::error, "Error reading file '" + path + "'");
        return 1;
    }
    std::stringstream buffer;
    buffer << fileStream.rdbuf();
    fileStream.close();
    output = buffer.str();
    return 0;
}

/**
 * @brief Write data to file
 *
 * @param path Path + filename of file
 * @param data Data to be written to file
 * @param append Append
 * @return 0 Success
 * @return 1 Error writing to file
 */
int Helper::writeToFile(std::string path, const std::string &data, bool append) {
    std::ofstream ofs;
    if (append)
        ofs.open(path, std::ofstream::app);
    else
        ofs.open(path, std::ofstream::trunc);

    if (!ofs) {
        logger.log(CLogging::error, "Error writing to file '" + path + "'");
        return 1;
    }
    ofs << data;
    ofs.close();
    return 0;
}

int Helper::deleteFile(std::string path) {
    if (!fs::exists(path))
        return 0;

    if (!fs::remove(path)) {
        logger.log(CLogging::error, "Error deleting file '" + path + "'");
        return 1;
    }

    return 0;
}

/**
 * @brief Remove the first <lineCout> lines from referenced string
 *
 * @param data String to be modified
 * @param lineCount Lines to be erased
 */
void Helper::eraseLinesFromStart(std::string &data, int lineCount) {
    for (int i = 0; i < lineCount; i++)
        data.erase(0, data.find("\n") + 1);
}

/* Use anonymous namespace to make this function only accessible via its wrappers */
namespace {
/**
 * @brief
 *
 * @param entryList
 * @param input
 * @param fromStart
 * @param addContaining
 */
void filterLines(std::vector<std::string> entryList,
                 std::string &input, bool fromStart, bool addContaining) {
    std::istringstream iss(input);
    input = "";
    // TODO improve time complexity
    for (std::string line; std::getline(iss, line);) {
        for (auto name : entryList) {
            auto pos = fromStart ? line.rfind(name, 0) : line.find(name, 0);
            // add only lines not containing name
            if (!addContaining && pos != std::string::npos) {
                input = input + line + "\n";
                break;
            } else if (addContaining && pos == std::string::npos) {
                // add only lines containing name
                input = input + line + "\n";
                break;
            }
        }
    }
}
} /* namespace */

/**
 * @brief Filter out lines not containing any entry in passed vector
 *
 * @param entryList Vector entries causing a line to be removed if not found
 * @param input Reference to string to be manipulated
 * @param fromStart Match from start of line or at any place within the line
 */
void Helper::filterLinesNotContaining(std::vector<std::string> entryList,
                                      std::string &input, bool fromStart) {
    filterLines(entryList, input, fromStart, false);
}

/**
 * @brief Filter out lines containing any entry in passed vector
 *
 * @param entryList Vector entries causing a line to be removed if found
 * @param input Reference to string to be manipulated
 * @param fromStart Match from start of line or at any place within the line
 */
void Helper::filterLinesContaining(std::vector<std::string> entryList,
                                   std::string &input, bool fromStart) {
    filterLines(entryList, input, fromStart, true);
}

/**
 * @brief Trim any prefixed or suffixed whitespaces of a line
 *
 * @param input Reference to string to be trimmed line by line
 * @param addNewLine Readd any trimmed newlines
 * @return String trimmed string
 */
std::string Helper::trimWhitespaces(std::string input, bool addNewLine) {
    std::istringstream iss(input);
    std::string output = "";
    for (std::string line; std::getline(iss, line);) {
        output += std::regex_replace(line, std::regex("^ +| +$|( ) +"), "$1");
        if (addNewLine)
            output += "\n";
    }
    return output;
}

/**
 * @brief Create string by joining elements of vector with a seperator
 *
 * @param inputVec Vector of elements to be joined
 * @param seperator Seperator
 * @param output Reference to write output to
 */
void Helper::joinVector(const std::vector<std::string> &inputVec, std::string seperator, std::string &output) {
    for (std::vector<std::string>::const_iterator it = inputVec.begin();
         it != inputVec.end(); ++it) {
        output += *it;
        if (it != inputVec.end() - 1)
            output += seperator;
    }
}

/**
 * @brief Get current Unix timestamp in seconds
 *
 * @return time_t Unix timestamp in seconds
 */
time_t Helper::getSecondsSinceEpoch() {
    return std::chrono::duration_cast<std::chrono::seconds>(std::chrono::system_clock::now().time_since_epoch()).count();
}

/**
 * @brief Get current Unix timestamp in milliseconds
 *
 * @return time_t Unix timestamp in milliseconds
 */
uint64_t Helper::getMillisecondsSinceEpoch() {
    return std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
}

/**
 * @brief Split string at delimiter
 *
 * @param input Input string
 * @param delimiter Delimiter
 * @param ret Output vector
 */
void Helper::splitStr(const std::string &input, const std::string delimiter, std::vector<std::string> &ret) {
    const size_t lengthDelimiter = delimiter.length();
    size_t posStartSearch = 0;
    size_t posDelimiter = input.find(delimiter, posStartSearch);

    if (ret.size() > 0)
        ret.clear();

    while (posDelimiter != std::string::npos) {
        std::string v = input.substr(posStartSearch, posDelimiter - posStartSearch);
        if (v.length())
            ret.push_back(v);
        posStartSearch = posDelimiter + lengthDelimiter;
        posDelimiter = input.find(delimiter, posStartSearch);
    }

    if (posStartSearch < input.length()) {
        std::string v = input.substr(posStartSearch);
        if (v.length())
            ret.push_back(v);
    }
}

/**
 * @brief Gather system information as json and return it as string
 *
 */
nlohmann::json Helper::gatherSystemInfo() {
    auto parseDmidecode = [&](std::string output, nlohmann::json &json, std::string name) {
        try {
            std::istringstream iss(output);
            for (std::string line; std::getline(iss, line);) {
                std::vector<std::string> v;
                Helper::splitStr(line, "=", v);
                if (json[name].contains(v[0]))
                    continue;
                json[name][v[0]] = v.size() == 2 ? v[1] : "";
            }
        } catch (const std::exception &exc) {
            logger.log(CLogging::warning, "Error parsing dmidecode output - \n" + output + " - \n" + boost::current_exception_diagnostic_information());
        }
    };

    std::vector<std::string> lscpuData = {
        "Architecture",
        "CPU(s)",
        "Vendor ID",
        "Model name",
        "CPU family",
        "Model",
        "Thread(s) per core",
        "Core(s) per socket",
        "Socket(s)",
        "Frequency boost",
        "CPU max MHz",
        "Caches (sum of all)",
        "L1d cache",
        "L1i cache",
        "L2 cache",
        "L3 cache",
    };

    auto parseLscpu = [&](nlohmann::json &data, nlohmann::json &values) {
        try {
            if (values.contains("field") && values.contains("data")) {
                std::string key = values["field"];
                if (Helper::endsWith(key, ":"))
                    key.pop_back();
                if (Helper::vectorContains(lscpuData, key) || Helper::startsWith(key, "NUMA "))
                    data[key] = values["data"];
            }
        } catch (const std::exception &exc) {
            logger.log(CLogging::warning, "Error parsing lscpu - " + boost::current_exception_diagnostic_information());
        }
    };

    std::string output;

    nlohmann::json data;

    /* OS */
    utsname uts;
    uname(&uts);
    data["os"] = {
        {"kernel", uts.release},
        {"version", uts.version},
        {"hostname", uts.nodename},
        {"sysname", uts.sysname},
        {"architecture", uts.machine},
    };

    /* uts does not provide the name of the exact distro, only "linux" -> extract from os-release */
    std::vector<std::string> v;
    if (Helper::getCommandOutput("cat /etc/os-release | grep '^PRETTY_NAME=' | sed 's/\"//g' | tr -d '\n'", output) == 0) {
        Helper::splitStr(output, "=", v);
        data["os"]["distro"] = v[1];
    }

    /* CPU */
    if (Helper::getCommandOutput("lscpu --json", output) == 0) {
        nlohmann::json lscpu = nlohmann::json::parse(output);
        for (auto &v : lscpu["lscpu"]) {
            parseLscpu(data["cpu"], v);
            if (!v.contains("children")) continue;
            for (auto &c : v["children"])
                parseLscpu(data["cpu"], c);
        }
    }

    if (Helper::getCommandOutput("LD_LIBRARY_PATH='/usr/local/share/xbatd/lib' /usr/local/share/xbatd/bin/likwid-topology", output) == 0)
        data["cpu"]["topology"] = output;

    /*  Get cpu features (most importantly TURBO_MODE) from likwid.
     *  Check only a single core and assume that the same setting applies to all other cores.
     */
    // cpuFeatures_init();

    // for (int i = CpuFeature::FEAT_HW_PREFETCHER; i != CpuFeature::FEAT_TM2; i++) {
    //     CpuFeature f = static_cast<CpuFeature>(i);
    //     rapidjson::Value key(cpuFeatures_name(f), allocator);
    //     rapidjson::Value value(static_cast<bool>(cpuFeatures_get(0, f)));
    //     cpu.AddMember(rapidjson::StringRef(cpuFeatures_name(f)), value, allocator);
    // }

    /* GPU */
    if (Helper::getCommandOutput("/usr/local/share/xbatd/pci_devices.sh", output) == 0) {
        std::istringstream iss(output);
        std::vector<std::string> gpu;
        for (std::string line; std::getline(iss, line);)
            gpu.push_back(line);

        data["gpu"] = gpu;
    }

    /* BIOS */
    if (Helper::getCommandOutput("dmidecode -t BIOS | grep 'Vendor\\|Version\\|Release Date\\|BIOS Revision\\|Firmware Revision' | awk '{$1=$1};1' | sed -r 's/:{1}\\s?/=/'", output) == 0)
        parseDmidecode(output, data, "bios");

    /* SYSTEM */
    if (Helper::getCommandOutput("dmidecode -t system | grep 'Manufacturer\\|Product Name\\|Version\\|Family' | awk '{$1=$1};1' | sed -r 's/:{1}\\s?/=/'", output) == 0)
        parseDmidecode(output, data, "system");

    /* MEMORY */
    if (Helper::getCommandOutput("dmidecode -t memory | grep 'Error Correction Type\\|Maximum Capacity\\|Number Of Devices\\|Size\\|Form Factor\\|Type\\|Speed\\|Configured Memory Speed\\|Configured Voltage\\|Manufacturer' | grep -Ev 'Unknown|None|No Module Installed|Module Manufacturer ID' | awk '{$1=$1};1' | sed -r 's/:{1}\\s?/=/'", output) == 0)
        parseDmidecode(output, data, "memory");

    /* Cant retrieve number of used slots directly from dmidecode */
    if (Helper::getCommandOutput("dmidecode -t memory | grep 'Memory Device' | wc -l", output) == 0) {
        try {
            int max = std::stoi(output);
            if (Helper::getCommandOutput("dmidecode -t memory | grep 'No Module Installed' | wc -l", output) == 0) {
                int installed = max - std::stoi(output);
                data["memory"]["Number Of Installed Devices"] = installed;
            }
        } catch (const std::exception &exc) {
            logger.log(CLogging::warning, "Error gathering number of installed devices - " + boost::current_exception_diagnostic_information());
        }
    }
    return data;
}

std::string Helper::sanitizeForILP(std::string s) {
    std::regex remove_braces("\\(.*\\)");
    std::regex escape("[\\s/]");
    s = std::regex_replace(s, remove_braces, "");
    s = std::regex_replace(s, escape, "_");

    return toLower(s);
}

double Helper::round(double v, int places) {
    double multiplicator = std::pow(10.0, places);
    return floor(v * multiplicator) / multiplicator;
}

std::string Helper::toLower(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return std::tolower(c); });
    return s;
}

// extract number from a string
std::string Helper::extractNumber(std::string s, bool allowFloat) {
    std::string numbers = "0123456789";
    if (allowFloat) numbers += ".,";
    std::size_t const n = s.find_first_of(numbers);
    if (n != std::string::npos) {
        std::size_t const m = s.find_first_not_of(numbers, n);
        return s.substr(n, m != std::string::npos ? m - n : m);
    }
    return "";
}

bool Helper::strToBool(std::string s) {
    bool b;
    std::istringstream(toLower(s)) >> std::boolalpha >> b;
    return b;
}

std::string Helper::boolToStr(bool b) {
    return b ? "true" : "false";
}

// TODO
// parses ISO8601
std::chrono::system_clock::time_point Helper::parseTime(std::string date) {
    std::tm t = {};
    std::istringstream ss(date);
    ss >> std::get_time(&t, "%Y-%m-%dT%H:%M:%S");

    // dst unknown
    t.tm_isdst = -1;
    if (ss.fail()) {
        logger.log(CLogging::error, "Parsing of date-time '" + date + "' failed! Falling back to current time");
        return std::chrono::system_clock::now();
    }

    return std::chrono::system_clock::from_time_t(mktime(&t));
}

std::string Helper::md5(const std::string &in) {
    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    std::string hashed = "";
    if (ctx != NULL) {
        if (EVP_DigestInit_ex(ctx, EVP_md5(), NULL)) {
            if (EVP_DigestUpdate(ctx, in.c_str(), in.length())) {
                unsigned char hash[EVP_MAX_MD_SIZE];
                unsigned int hashLen = 0;

                if (EVP_DigestFinal_ex(ctx, hash, &hashLen)) {
                    std::stringstream ss;
                    for (unsigned int i = 0; i < hashLen; ++i)
                        ss << std::hex << std::setw(2) << std::setfill('0') << (int)hash[i];

                    hashed = ss.str();
                }
            }
        }

        EVP_MD_CTX_free(ctx);
    }

    return hashed;
}

#include <boost/algorithm/string.hpp>
#include <boost/archive/iterators/base64_from_binary.hpp>
#include <boost/archive/iterators/binary_from_base64.hpp>
#include <boost/archive/iterators/transform_width.hpp>

std::string Helper::decode64(const std::string &val) {
    using namespace boost::archive::iterators;
    using It = transform_width<binary_from_base64<std::string::const_iterator>, 8, 6>;
    return boost::algorithm::trim_right_copy_if(std::string(It(std::begin(val)), It(std::end(val))), [](char c) {
        return c == '\0';
    });
}

std::string Helper::encode64(const std::string &val) {
    using namespace boost::archive::iterators;
    using It = base64_from_binary<transform_width<std::string::const_iterator, 6, 8>>;
    auto tmp = std::string(It(std::begin(val)), It(std::end(val)));
    return tmp.append((3 - val.size() % 3) % 3, '=');
}