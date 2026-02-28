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
    for (size_t i = 0; i < devices.size(); i++) {
        nvmlDevice_t device = devices[i];
        std::string deviceId = std::to_string(i);

        nvmlDevice_t migDevice;
        bool migEnabled = nvmlDeviceGetMigDeviceHandleByIndex(device, 0, &migDevice) == NVML_SUCCESS;

        nvmlMemory_t fb;
        if (nvmlDeviceGetMemoryInfo(device, &fb) == NVML_SUCCESS) {
            dataQueue->push(CQueue::DeviceMeasurement<int64_t>{"gpu_mem_fb_free", "device", deviceId, static_cast<int64_t>(fb.free), intervalEnd});
            dataQueue->push(CQueue::DeviceMeasurement<int64_t>{"gpu_mem_fb_used", "device", deviceId, static_cast<int64_t>(fb.used), intervalEnd});
            dataQueue->push(CQueue::DeviceMeasurement<double>{"gpu_mem_fb_usage", "device", deviceId, (static_cast<double>(fb.used) / fb.total) * 100, intervalEnd});
        }

        nvmlBAR1Memory_t bar1;
        if (nvmlDeviceGetBAR1MemoryInfo(device, &bar1) == NVML_SUCCESS) {
            dataQueue->push(CQueue::DeviceMeasurement<int64_t>{"gpu_mem_bar1_free", "device", deviceId, static_cast<int64_t>(bar1.bar1Free), intervalEnd});
            dataQueue->push(CQueue::DeviceMeasurement<int64_t>{"gpu_mem_bar1_used", "device", deviceId, static_cast<int64_t>(bar1.bar1Used), intervalEnd});
            dataQueue->push(CQueue::DeviceMeasurement<double>{"gpu_mem_bar1_usage", "device", deviceId, (static_cast<double>(bar1.bar1Used) / bar1.bar1Total) * 100, intervalEnd});
        }

        nvmlUtilization_t util;
        if (!migEnabled && nvmlDeviceGetUtilizationRates(device, &util) == NVML_SUCCESS) {
            dataQueue->push(CQueue::DeviceMeasurement<double>{"gpu_util", "device", deviceId, static_cast<double>(util.gpu), intervalEnd});
            dataQueue->push(CQueue::DeviceMeasurement<double>{"gpu_mem_util", "device", deviceId, static_cast<double>(util.memory), intervalEnd});
        }

        nvmlPstates_t pstate;
        if (nvmlDeviceGetPerformanceState(device, &pstate) == NVML_SUCCESS)
            dataQueue->push(CQueue::DeviceMeasurement<int64_t>{"gpu_pstate", "device", deviceId, static_cast<int64_t>(pstate), intervalEnd});

        nvmlEnableState_t mode;
        if (nvmlDeviceGetPowerManagementMode(device, &mode) == NVML_SUCCESS && mode == NVML_FEATURE_ENABLED) {
            unsigned int power;
            if (nvmlDeviceGetPowerUsage(device, &power) == NVML_SUCCESS)
                dataQueue->push(CQueue::DeviceMeasurement<double>{"gpu_power", "device", deviceId, static_cast<double>(power) / 1000, intervalEnd});

            /* TODO remove if it doesnt change during execution */
            unsigned int limit;
            if (nvmlDeviceGetPowerManagementLimit(device, &limit) == NVML_SUCCESS)
                dataQueue->push(CQueue::DeviceMeasurement<int64_t>{"gpu_power_limit", "device", deviceId, static_cast<int64_t>(limit) / 1000, intervalEnd});
        }

        unsigned int clock;

        for (auto const &[name, type] : clockTypes) {
            if (nvmlDeviceGetClockInfo(device, type, &clock) == NVML_SUCCESS)
                dataQueue->push(CQueue::DeviceMeasurement<int64_t>{name, "device", deviceId, static_cast<int64_t>(clock), intervalEnd});

            /* TODO test if max clock is static or can change during runtime (e.g. when chaning P-states) */
            // if (nvmlDeviceGetMaxClockInfo(device, type, &clock) == NVML_SUCCESS)
            //     dataQueue->push(CQueue::DeviceMeasurement<int64_t>{name + "_max", "device", deviceId, static_cast<int64_t>(clock), intervalEnd});
        }

        // not supported on MIG-enabled devices
        if (!migEnabled) {
            unsigned int utilization;
            unsigned int _;
            if (nvmlDeviceGetEncoderUtilization(device, &utilization, &_) == NVML_SUCCESS)
                dataQueue->push(CQueue::DeviceMeasurement<double>{"gpu_enc_util", "device", deviceId, static_cast<double>(utilization), intervalEnd});

            if (nvmlDeviceGetDecoderUtilization(device, &utilization, &_) == NVML_SUCCESS)
                dataQueue->push(CQueue::DeviceMeasurement<double>{"gpu_dec_util", "device", deviceId, static_cast<double>(utilization), intervalEnd});
        }

        /* TODO nvlink */
        // for (unsigned int j = 0; j < NVML_NVLINK_MAX_LINKS; j++) {
        //     nvmlEnableState_t nvlink;
        //     if (nvmlDeviceGetNvLinkState(device, j, &nvlink) == NVML_SUCCESS) {
        //         if (nvlink != NVML_FEATURE_ENABLED)
        //             continue;
        //     }
        // }
    }

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