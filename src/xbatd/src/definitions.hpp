#ifndef DEFINITIONS_HPP
#define DEFINITIONS_HPP

#include <map>
#include <string>
#include <variant>

using config_map = std::map<std::string, std::variant<std::string, uint, bool>>;

#endif /* DEFINITIONS_HPP */