/**
 * @file CAMDGPU.cpp
 * @brief Class for AMD gpu performance data
 *
 ***********************************************/

#include "CAMDGPU.hpp"

/**
 * @brief Construct a new CAMDGPU::CAMDGPU object and initialize parameters
 *
 * @param dataQueue Pointer to queue for data
 * @param startTime Starting timestamp
 * @param interval Interval duration in seconds
 */
CAMDGPU::CAMDGPU(CQueue *dataQueue, std::chrono::time_point<std::chrono::system_clock> startTime, uint64_t interval) {
    this->dataQueue = dataQueue;
    this->interval = interval;
    intervalStart = startTime;
    moduleName = "amdGPU";
    launchMutex.unlock();
}

CAMDGPU::~CAMDGPU(void) {
    this->intervalEnd = std::chrono::system_clock::now();
    amdsmi_status_t ret = amdsmi_shut_down();
    if (ret != AMDSMI_STATUS_SUCCESS) {
        const char *err_str;
        amdsmi_status_code_to_string(ret, &err_str);
        logger.log(CLogging::error, "Failed to shut down AMD SMI. " + std::string(err_str));
    }
    cleanUpMutex.lock();
    cleanUpMutex.unlock();
}

int CAMDGPU::prepare() {
    amdsmi_status_t ret = amdsmi_init(AMDSMI_INIT_AMD_GPUS);
    if (ret != AMDSMI_STATUS_SUCCESS) {
        const char *err_str;
        amdsmi_status_code_to_string(ret, &err_str);
        logger.log(CLogging::error, "Failed to initialize AMD SMI. " + std::string(err_str));
        return 1;
    }
    uint32_t socket_count = 0;
    ret = amdsmi_get_socket_handles(&socket_count, nullptr);
    if (ret != AMDSMI_STATUS_SUCCESS) {
        const char *err_str;
        amdsmi_status_code_to_string(ret, &err_str);
        logger.log(CLogging::error, "Failed to get socket count. " + std::string(err_str));
        return 1;
    }
    std::vector<amdsmi_socket_handle> socket_list(socket_count);

    ret = amdsmi_get_socket_handles(&socket_count, &socket_list[0]);
    if (ret != AMDSMI_STATUS_SUCCESS) {
        const char *err_str;
        amdsmi_status_code_to_string(ret, &err_str);
        logger.log(CLogging::error, "Failed to get socket list. " + std::string(err_str));
        return 1;
    }
    this->sockets = socket_list;

    std::vector<std::vector<amdsmi_processor_handle>> processor_list(socket_count);
    for (uint32_t i = 0; i < socket_count; i++) {
        // Get the device count for the socket.
        uint32_t device_count = 0;
        ret = amdsmi_get_processor_handles(sockets[i], &device_count, nullptr);
        if (ret != AMDSMI_STATUS_SUCCESS) {
            const char *err_str;
            amdsmi_status_code_to_string(ret, &err_str);
            logger.log(CLogging::error, "Failed to get processor count for socket " + std::to_string(i) + " " + std::string(err_str));
        }
        // Allocate the memory for the device handlers on the socket
        std::vector<amdsmi_processor_handle> processor_handles(device_count);
        // Get all devices of the socket
        ret = amdsmi_get_processor_handles(sockets[i], &device_count, &processor_handles[0]);
        if (ret != AMDSMI_STATUS_SUCCESS) {
            const char *err_str;
            amdsmi_status_code_to_string(ret, &err_str);
            logger.log(CLogging::error, "Failed to get processors for socket " + std::to_string(i) + " " + std::string(err_str));
        }
        // Check if every processor is an AMD GPU
        for (auto it = processor_handles.begin(); it != processor_handles.end(); /* no increment here */) {
            processor_type_t processor_type;
            ret = amdsmi_get_processor_type(*it, &processor_type);
            if (ret == AMDSMI_STATUS_SUCCESS) {
                if (processor_type != AMDSMI_PROCESSOR_TYPE_AMD_GPU) {
                    logger.log(CLogging::error, "One of processor is not an AMD GPU. Socket: " + std::to_string(i) + "\n");
                    // Remove only that processor in case there is a hybrid GPU system
                    it = processor_handles.erase(it);
                } else {
                    ++it;
                }
            } else {
                const char *err_str;
                amdsmi_status_code_to_string(ret, &err_str);
                logger.log(CLogging::error, "Failed to get one of processor's type for Socket: " + std::to_string(i) + " " + std::string(err_str));
                ++it;
            }
        }
        processor_list[i] = processor_handles;
    }
    this->processors = processor_list;

    // Check for no AMD GPU case
    int total_gpus = 0;
    uint32_t socket_size = this->sockets.size();
    for (uint32_t i = 0; i < socket_size; i++) {
        total_gpus += this->processors[i].size();
    }
    if (total_gpus == 0) {
        logger.log(CLogging::error, "No AMD GPUs found.");
        return 1;
    }

    return 0;
}

int CAMDGPU::collect() {
    int socket_count = this->sockets.size();
    for (int i = 0; i < socket_count; i++) {
        int processor_count = this->processors[i].size();
        for (int j = 0; j < processor_count; j++) {
            std::string deviceId = std::to_string(i);

            // TODO: Decide later if board info will be used
            // amdsmi_board_info_t board_info;
            // amdsmi_status_t ret = amdsmi_get_gpu_board_info(this->processors[i][j], &board_info);
            // if (ret != AMDSMI_STATUS_SUCCESS) {
            //     const char *err_str;
            //     amdsmi_status_code_to_string(ret, &err_str);
            //     logger.log(CLogging::error, "Failed to get GPU board info for Socket: " + std::to_string(i) + " GPU: " + std::to_string(j) + " " + std::string(err_str));
            // }

            int64_t gpu_temp = 0;
            amdsmi_status_t ret = amdsmi_get_temp_metric(this->processors[i][j], AMDSMI_TEMPERATURE_TYPE_EDGE, AMDSMI_TEMP_CURRENT, &gpu_temp);
            if (ret != AMDSMI_STATUS_SUCCESS) {
                const char *err_str;
                amdsmi_status_code_to_string(ret, &err_str);
                logger.log(CLogging::error, "Failed to get temparature metrics for Socket: " + std::to_string(i) + " GPU: " + std::to_string(j) + " " + std::string(err_str));
            } else {
                dataQueue->push(CQueue::DeviceMeasurement<int64_t>{"gpu_temp", "device", deviceId, static_cast<int64_t>(gpu_temp), intervalEnd});
            }

            amdsmi_engine_usage_t usage_info;
            ret = amdsmi_get_gpu_activity(this->processors[i][j], &usage_info);
            if (ret != AMDSMI_STATUS_SUCCESS) {
                const char *err_str;
                amdsmi_status_code_to_string(ret, &err_str);
                logger.log(CLogging::error, "Failed to get GPU activity for Socket: " + std::to_string(i) + " GPU: " + std::to_string(j) + " " + std::string(err_str));
            } else {
                dataQueue->push(CQueue::DeviceMeasurement<double>{"gpu_util", "device", deviceId, static_cast<double>(usage_info.gfx_activity), intervalEnd});
                dataQueue->push(CQueue::DeviceMeasurement<double>{"gpu_mem_util", "device", deviceId, static_cast<double>(usage_info.umc_activity), intervalEnd});
                dataQueue->push(CQueue::DeviceMeasurement<double>{"gpu_mm_util", "device", deviceId, static_cast<double>(usage_info.mm_activity), intervalEnd});
            }

            amdsmi_power_info_t power_info;
            ret = amdsmi_get_power_info(this->processors[i][j], &power_info);
            if (ret != AMDSMI_STATUS_SUCCESS) {
                const char *err_str;
                amdsmi_status_code_to_string(ret, &err_str);
                logger.log(CLogging::error, "Failed to get power consumption for Socket: " + std::to_string(i) + " GPU: " + std::to_string(j) + " " + std::string(err_str));
            } else {
                dataQueue->push(CQueue::DeviceMeasurement<double>{"gpu_power", "device", deviceId, static_cast<double>(power_info.average_socket_power), intervalEnd});
            }

            for (auto const &[name, type] : clockTypes) {
                amdsmi_clk_type_t clk_type = type;
                amdsmi_clk_info_t clk_info;
                ret = amdsmi_get_clock_info(this->processors[i][j], clk_type, &clk_info);
                if (ret != AMDSMI_STATUS_SUCCESS) {
                    const char *err_str;
                    amdsmi_status_code_to_string(ret, &err_str);
                    logger.log(CLogging::error, "Failed to get clock info for Socket: " + std::to_string(i) + " GPU: " + std::to_string(j) + " " + std::string(err_str));
                } else {
                    dataQueue->push(CQueue::DeviceMeasurement<int64_t>{name, "device", deviceId, static_cast<int64_t>(clk_info.clk), intervalEnd});
                    // dataQueue->push(CQueue::DeviceMeasurement<int64_t>{name + "_max", "device", deviceId, static_cast<int64_t>(clk_info.max_clk), intervalEnd});
                }
            }

            amdsmi_vram_usage_t vram_info;
            ret = amdsmi_get_gpu_vram_usage(this->processors[i][j], &vram_info);
            if (ret != AMDSMI_STATUS_SUCCESS) {
                const char *err_str;
                amdsmi_status_code_to_string(ret, &err_str);
                logger.log(CLogging::error, "Failed to get VRAM usage for Socket: " + std::to_string(i) + " GPU: " + std::to_string(j) + " " + std::string(err_str));
            } else {
                dataQueue->push(CQueue::DeviceMeasurement<int64_t>{"gpu_mem_fb_free", "device", deviceId, static_cast<int64_t>(vram_info.vram_total), intervalEnd});
                dataQueue->push(CQueue::DeviceMeasurement<int64_t>{"gpu_mem_fb_used", "device", deviceId, static_cast<int64_t>(vram_info.vram_used), intervalEnd});
                dataQueue->push(CQueue::DeviceMeasurement<double>{"gpu_mem_fb_usage", "device", deviceId, (static_cast<double>(vram_info.vram_used) / vram_info.vram_total) * 100, intervalEnd});
            }
        }
    }
    return 0;
}

int CAMDGPU::measure() {
    logger.setModule(moduleName);

    if (prepare() != 0)
        return 1;

    while (!terminate) {
        synchronizeMeasurement();

        if (terminate)
            break;

        if (collect() != 0) {
            return 1;
        }

        sleepMillisecondsAndCheck(timeLeft);

        intervalCleanup();
    }

    return 0;
}
