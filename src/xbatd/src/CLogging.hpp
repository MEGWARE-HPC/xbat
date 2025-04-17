#ifndef CLOGGING_HPP
#define CLOGGING_HPP

#include <boost/date_time/posix_time/posix_time.hpp>
#include <boost/log/attributes.hpp>
#include <boost/log/attributes/timer.hpp>
#include <boost/log/common.hpp>
#include <boost/log/core.hpp>
#include <boost/log/expressions.hpp>
#include <boost/log/sources/severity_logger.hpp>
#include <boost/log/support/date_time.hpp>
#include <boost/log/utility/setup/common_attributes.hpp>
#include <boost/log/utility/setup/console.hpp>
#include <boost/log/utility/setup/file.hpp>
#include <map>
#include <string>
#include <variant>

#include "definitions.hpp"

namespace logging = boost::log;
namespace sinks = boost::log::sinks;
namespace attrs = boost::log::attributes;
namespace src = boost::log::sources;
namespace expr = boost::log::expressions;
namespace keywords = boost::log::keywords;

class CLogging {
   public:
    CLogging();
    ~CLogging();
    static void initLogging(config_map&);
    enum severity_level {
        debug,
        info,
        warning,
        error
    };
    void log(severity_level, std::string);
    static void log(std::string, severity_level, std::string);
    void setModule(std::string);
};

#endif /* CLOGGING_HPP */