#ifndef CURLCLIENT_HPP
#define CURLCLIENT_HPP

#include <curl/curl.h>

#include <string>

#include "external/nlohmann-json/include/nlohmann/json.hpp"

class CurlClient {
   public:
    CurlClient(const std::string&, const std::string&, const std::string&);
    ~CurlClient();
    nlohmann::json post(const std::string&, const std::string& = "", const std::string& = "application/json");
    nlohmann::json get(const std::string&);
    bool login();
    bool logout();
    nlohmann::json registerJob(uint, std::string, std::string);
    nlohmann::json registerNode(std::string, const nlohmann::json&);

   private:
    static size_t writeCallback(void*, size_t, size_t, std::string*);
    CURL* curl;
    std::string base_url;
    std::string client_id;
    std::string client_secret;
    std::string token;

    std::string constructAuthHeader();
};

#endif  // CURLCLIENT_HPP