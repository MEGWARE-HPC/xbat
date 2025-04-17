#include "CurlClient.hpp"

#include <iostream>

#include "helper.hpp"

CurlClient::CurlClient(const std::string& base_url, const std::string& client_id, const std::string& client_secret)
    : base_url(base_url), client_id(client_id), client_secret(client_secret) {
    curl_global_init(CURL_GLOBAL_DEFAULT);
    curl = curl_easy_init();
    if (!curl) {
        std::cerr << "Failed to initialize cURL" << std::endl;
        throw std::runtime_error("Failed to initialize cURL");
    }
}

CurlClient::~CurlClient() {
    if (curl) {
        curl_easy_cleanup(curl);
    }
    curl_global_cleanup();
}

size_t CurlClient::writeCallback(void* contents, size_t size, size_t nmemb, std::string* s) {
    size_t newLength = size * nmemb;
    try {
        s->append((char*)contents, newLength);
    } catch (std::bad_alloc& e) {
        // Handle memory problem
        return 0;
    }
    return newLength;
}

std::string CurlClient::constructAuthHeader() {
    if (!token.empty()) {
        return "Authorization: Bearer " + token;
    } else {
        std::string credentials = client_id + ":" + client_secret;
        std::string encodedCredentials = Helper::encode64(credentials);
        return "Authorization: Basic " + encodedCredentials;
    }
}

nlohmann::json CurlClient::post(const std::string& resource_path, const std::string& data, const std::string& content_type) {
    std::string readBuffer;
    nlohmann::json jsonResponse;

    // Construct the full URL
    std::string url = base_url + resource_path;

    // Construct the headers
    struct curl_slist* headers = NULL;
    std::string authHeader = constructAuthHeader();
    headers = curl_slist_append(headers, authHeader.c_str());
    headers = curl_slist_append(headers, ("Content-Type: " + content_type).c_str());

    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_POST, 1L);
    if (!data.empty())
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, data.c_str());
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, writeCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);
    curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);  // --insecure equivalent
    curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0L);  // Disable host verification

    CURLcode res = curl_easy_perform(curl);
    if (res != CURLE_OK) {
        std::cerr << "curl_easy_perform() failed: " << curl_easy_strerror(res) << std::endl;
    } else {
        jsonResponse = nlohmann::json::parse(readBuffer);
    }

    curl_slist_free_all(headers);

    return jsonResponse;
}

nlohmann::json CurlClient::get(const std::string& resource_path) {
    std::string readBuffer;
    nlohmann::json jsonResponse;

    // Construct the full URL
    std::string url = base_url + resource_path;

    // Construct the headers
    struct curl_slist* headers = NULL;
    std::string authHeader = constructAuthHeader();
    headers = curl_slist_append(headers, authHeader.c_str());
    headers = curl_slist_append(headers, "Content-Type: application/json");

    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_HTTPGET, 1L);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, writeCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);
    curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);  // --insecure equivalent
    curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0L);  // Disable host verification

    CURLcode res = curl_easy_perform(curl);
    if (res != CURLE_OK) {
        std::cerr << "curl_easy_perform() failed: " << curl_easy_strerror(res) << std::endl;
    } else {
        jsonResponse = nlohmann::json::parse(readBuffer);
    }

    curl_slist_free_all(headers);

    return jsonResponse;
}

bool CurlClient::login() {
    nlohmann::json response = post("/oauth/token", "grant_type=client_credentials", "application/x-www-form-urlencoded");
    if (response.contains("access_token")) {
        token = response["access_token"].get<std::string>();
        return true;
    }

    std::cerr << "Failed to obtain access token" << std::endl;
    return false;
}

bool CurlClient::logout() {
    std::string payload = "client_id=" + client_id + "&token=" + token + "&token_type_hint=access_token";
    nlohmann::json response = post("/oauth/revoke", payload, "application/x-www-form-urlencoded");

    // always clear token as it will expire anyway after 15 minutes
    token.clear();

    if (response.contains("error")) {
        std::cerr << "Failed to revoke access token - " << response["error"].get<std::string>() << std::endl;
        return false;
    }

    return true;
}

nlohmann::json CurlClient::registerJob(uint jobId, std::string hostname, std::string hash) {
    nlohmann::json payload = {{"hostname", hostname}, {"hash", hash}};
    return post("/api/v1/jobs/" + std::to_string(jobId) + "/register", payload.dump());
}

nlohmann::json CurlClient::registerNode(std::string hash, const nlohmann::json& node) {
    return post("/api/v1/nodes/" + hash + "/register", node.dump());
}