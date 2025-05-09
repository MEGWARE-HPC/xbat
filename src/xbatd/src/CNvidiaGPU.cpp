/**
 * @file CNvidiaGPU.cpp
 * @brief Class for NVIDIA gpu performance data
 *
 ***********************************************/

#include "CNvidiaGPU.hpp"

#include <iostream>

/**
 * @brief Construct a new CNvidiaGPU::CNvidiaGPU object and initialize parameters
 *
 * @param dataQueue Pointer to queue for data
 * @param timestamp Starting timestamp
 * @param interval Interval duration in seconds
 */
CNvidiaGPU::CNvidiaGPU(CQueue *dataQueue, std::chrono::time_point<std::chrono::system_clock> startTime, uint64_t interval) {
    this->dataQueue = dataQueue;
    this->interval = interval;
    intervalStart = startTime;
    moduleName = "nvidiaGPU";
    launchMutex.unlock();
}

/**
 * @brief Destroy the CNvidiaGPU::CNvidiaGPU object but only after measurement is completed
 *
 */
CNvidiaGPU::~CNvidiaGPU(void) {
    /* Destruct only if measure() already returned */
    cleanUpMutex.lock();
    cleanUpMutex.unlock();
}

int CNvidiaGPU::prepare() {
    nvmlReturn_t ret = nvmlInit_v2();
    if (ret != NVML_SUCCESS) {
        logger.log(CLogging::error, "Failed to initialize NVML - " + std::string(nvmlErrorString(ret)));
        return 1;
    }

    unsigned int deviceCount;
    if (nvmlDeviceGetCount_v2(&deviceCount) != NVML_SUCCESS) {
        logger.log(CLogging::error, "Failed to get device count");
        return 1;
    }

    if (!deviceCount) {
        logger.log(CLogging::info, "No devices found");
        return 1;
    }

    for (unsigned int i = 0; i < deviceCount; i++) {
        nvmlDevice_t device;
        if (nvmlDeviceGetHandleByIndex_v2(i, &device) != NVML_SUCCESS) {
            logger.log(CLogging::error, "Failed to get device handle");
            return 1;
        }
        devices.push_back(device);
    }

    return 0;
}

int CNvidiaGPU::collect() {
    std::vector<CQueue::ILP<int64_t>> int_data;
    std::vector<CQueue::ILP<double>> double_data;
    for (size_t i = 0; i < devices.size(); i++) {
        nvmlDevice_t device = devices[i];
        std::map<std::string, std::string> tags = {{"level", "device"}, {"device", std::to_string(i)}};

        nvmlDevice_t migDevice;
        bool migEnabled = nvmlDeviceGetMigDeviceHandleByIndex(device, 0, &migDevice) == NVML_SUCCESS;

        nvmlMemory_t fb;
        if (nvmlDeviceGetMemoryInfo(device, &fb) == NVML_SUCCESS) {
            int_data.insert(int_data.end(), {CQueue::ILP<int64_t>{"gpu_mem_fb_free", tags, static_cast<int64_t>(fb.free), intervalEnd},
                                             CQueue::ILP<int64_t>{"gpu_mem_fb_used", tags, static_cast<int64_t>(fb.used), intervalEnd}});
            double_data.push_back(CQueue::ILP<double>{"gpu_mem_fb_usage", tags, (static_cast<double>(fb.used) / fb.total) * 100, intervalEnd});
        }

        nvmlBAR1Memory_t bar1;
        if (nvmlDeviceGetBAR1MemoryInfo(device, &bar1) == NVML_SUCCESS) {
            int_data.insert(int_data.end(), {CQueue::ILP<int64_t>{"gpu_mem_bar1_free", tags, static_cast<int64_t>(bar1.bar1Free), intervalEnd},
                                             CQueue::ILP<int64_t>{"gpu_mem_bar1_used", tags, static_cast<int64_t>(bar1.bar1Used), intervalEnd}});
            double_data.push_back(CQueue::ILP<double>{"gpu_mem_bar1_usage", tags, (static_cast<double>(bar1.bar1Used) / bar1.bar1Total) * 100, intervalEnd});
        }

        nvmlUtilization_t util;
        if (!migEnabled && nvmlDeviceGetUtilizationRates(device, &util) == NVML_SUCCESS) {
            double_data.insert(double_data.end(), {CQueue::ILP<double>{"gpu_util", tags, static_cast<double>(util.gpu), intervalEnd},
                                                   CQueue::ILP<double>{"gpu_mem_util", tags, static_cast<double>(util.memory), intervalEnd}});
        }

        nvmlPstates_t pstate;
        if (nvmlDeviceGetPerformanceState(device, &pstate) == NVML_SUCCESS)
            int_data.push_back(CQueue::ILP<int64_t>{"gpu_pstate", tags, static_cast<int64_t>(pstate), intervalEnd});

        nvmlEnableState_t mode;
        if (nvmlDeviceGetPowerManagementMode(device, &mode) == NVML_SUCCESS && mode == NVML_FEATURE_ENABLED) {
            unsigned int power;
            if (nvmlDeviceGetPowerUsage(device, &power) == NVML_SUCCESS)
                double_data.push_back(CQueue::ILP<double>{"gpu_power", tags, static_cast<double>(power) / 1000, intervalEnd});

            /* TODO remove if it doesnt change during execution */
            unsigned int limit;
            if (nvmlDeviceGetPowerManagementLimit(device, &limit) == NVML_SUCCESS)
                int_data.push_back(CQueue::ILP<int64_t>{"gpu_power_limit", tags, static_cast<int64_t>(limit) / 1000, intervalEnd});
        }

        unsigned int clock;

        for (auto const &[name, type] : clockTypes) {
            if (nvmlDeviceGetClockInfo(device, type, &clock) == NVML_SUCCESS)
                int_data.push_back(CQueue::ILP<int64_t>{name, tags, static_cast<int64_t>(clock), intervalEnd});

            /* TODO test if max clock is static or can change during runtime (e.g. when chaning P-states) */
            // if (nvmlDeviceGetMaxClockInfo(device, type, &clock) == NVML_SUCCESS)
            //     int_data.push_back(CQueue::ILP<int64_t>{name + "_max", tags, static_cast<int64_t>(clock), intervalEnd});
        }

        // not supported on MIG-enabled devices
        if (!migEnabled) {
            unsigned int utilization;
            unsigned int _;
            if (nvmlDeviceGetEncoderUtilization(device, &utilization, &_) == NVML_SUCCESS)
                double_data.push_back(CQueue::ILP<double>{"gpu_enc_util", tags, static_cast<double>(utilization), intervalEnd});

            if (nvmlDeviceGetDecoderUtilization(device, &utilization, &_) == NVML_SUCCESS)
                double_data.push_back(CQueue::ILP<double>{"gpu_dec_util", tags, static_cast<double>(utilization), intervalEnd});
        }

        nvmlFieldValue_t fields[2];
        // scopeId with UINT_MAX returns sum of total nvlink bandwidth
        fields[0].fieldId = NVML_FI_DEV_NVLINK_THROUGHPUT_DATA_RX;
        fields[0].scopeId = UINT_MAX;
        fields[1].fieldId = NVML_FI_DEV_NVLINK_THROUGHPUT_DATA_TX;
        fields[1].scopeId = UINT_MAX;

        auto result = nvmlDeviceGetFieldValues(device, 2, fields);
        if (result == NVML_SUCCESS) {
            logger.log(CLogging::info, "RX: " + std::to_string(fields[0].value.ullVal) + " KiB/sec");
            logger.log(CLogging::info, "TX: " + std::to_string(fields[1].value.ullVal) + " KiB/sec");
        } else {
            logger.log(CLogging::error, "Failed to get throughput: - " + std::string(nvmlErrorString(result)));
        }
    }

    if ((int_data.size() + double_data.size()) == 0)
        return 1;

    dataQueue->pushMultiple<int64_t>(int_data);
    dataQueue->pushMultiple<double>(double_data);

    return 0;
}

int CNvidiaGPU::measure() {
    logger.setModule(moduleName);
    if (prepare() != 0)
        return 1;

    while (!terminate) {
        synchronizeMeasurement();

        if (terminate)
            break;

        if (collect() != 0)
            return 1;

        sleepMillisecondsAndCheck(timeLeft);

        intervalCleanup();
    }
    nvmlShutdown();
    return 0;
}
