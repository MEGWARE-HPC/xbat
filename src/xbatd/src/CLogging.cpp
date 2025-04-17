#include "CLogging.hpp"

src::severity_logger_mt<CLogging::severity_level> slg;

BOOST_LOG_ATTRIBUTE_KEYWORD(mod, "Module", std::string)
BOOST_LOG_ATTRIBUTE_KEYWORD(severity, "Severity", CLogging::severity_level)

std::map<std::string, CLogging::severity_level> severityMapping = {
    {"debug", CLogging::debug},
    {"info", CLogging::info},
    {"warning", CLogging::warning},
    {"error", CLogging::error},
};

CLogging::CLogging() {
    BOOST_LOG_FUNCTION();
}

CLogging::~CLogging() {
}

void CLogging::setModule(std::string mod) {
    boost::log::core::get()->add_thread_attribute("Module",
                                                  boost::log::attributes::constant<std::string>(mod));
}

// The formatting logic for the severity level
template <typename CharT, typename TraitsT>
inline std::basic_ostream<CharT, TraitsT>& operator<<(
    std::basic_ostream<CharT, TraitsT>& strm, CLogging::severity_level lvl) {
    static const char* const str[] =
        {
            "debug",
            "info",
            "warning",
            "error"};
    if (static_cast<std::size_t>(lvl) < (sizeof(str) / sizeof(*str)))
        strm << str[lvl];
    else
        strm << static_cast<int>(lvl);
    return strm;
}

void CLogging::initLogging(config_map& config) {
    auto format = expr::stream << "[" << expr::format_date_time<boost::posix_time::ptime>("TimeStamp", "%Y-%m-%d, %H:%M:%S.%f") << "]"
                               << "[" << expr::attr<severity_level>("Severity") << "]"
                               << expr::if_(expr::has_attr(mod))[expr::stream << "[" << mod << "]"]
                               //<< "[" << logging::expressions::attr<logging::attributes::current_thread_id::value_type>("ThreadID") << "]"
                               << ": "
                               << expr::message;

    logging::add_file_log(keywords::file_name = "/var/log/xbatd/xbatd.log",
                          keywords::rotation_size = 1 * 1024 * 1024,
                          keywords::format = format,
                          keywords::auto_flush = true,
                          keywords::max_size = 10 * 1024 * 1024,
                          keywords::open_mode = std::ios_base::app,
                          keywords::filter = (severity >= severityMapping[std::get<std::string>(config["log_level_file"])]));
    logging::add_console_log(std::cout,
                             keywords::format = format,
                             keywords::auto_flush = true,
                             keywords::filter = (severity >= severityMapping[std::get<std::string>(config["log_level"])]));
    logging::add_common_attributes();
}

void CLogging::log(std::string name, severity_level level, std::string message) {
    // TODO find better approach
    // alternative boost::log::core::get()->add_thread_attribute
    auto moduleAttribute = slg.add_attribute("Module",
                                             boost::log::attributes::constant<std::string>(name));
    BOOST_LOG_SEV(slg, level) << message;
    slg.remove_attribute(moduleAttribute.first);
};

void CLogging::log(severity_level level, std::string message) {
    BOOST_LOG_SEV(slg, level) << message;
};