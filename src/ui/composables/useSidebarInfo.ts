import type { Benchmark } from "@/repository/modules/benchmarks";
import type { Job } from "@/repository/modules/jobs";
import type { SystemInfo } from "@/repository/modules/nodes";
import type { EnergyMeasurement } from "@/repository/modules/measurements";

import { deepClone } from "~/utils/misc";
import { replaceTrademark } from "~/utils/string";
import { humanSize } from "~/utils/conversion";
import { ObjectUtils } from "~/utils/object";

type SidebarEntry = {
    name: string;
    title: string;
    key?: string;
    editable?: boolean;
    hideCLI?: boolean;
};

const benchmarkEntries: SidebarEntry[] = [
    { name: "runNr", title: "Run Number" },
    { name: "name", title: "Benchmark Name", key: "name", editable: true },
    {
        name: "benchmarkConfiguration.configurationName",
        title: "Configuration",
        hideCLI: true
    }
];

const jobEntries: SidebarEntry[] = [
    { name: "jobInfo.jobId", title: "ID" },
    { name: "jobInfo.name", title: "Name" },
    {
        name: "configuration.jobscript.variantName",
        title: "Variant",
        key: "variantName",
        editable: true,
        hideCLI: true
    }
];

const hardwareEntries: SidebarEntry[] = [
    { name: "system.Manufacturer", title: "Manufacturer" },
    { name: "system.Product Name", title: "System" },
    { name: "cpu.Model name", title: "Processor" },
    { name: "cpu.Socket(s)", title: "Sockets" },
    { name: "cpu.Core(s) per socket", title: "Cores per Socket" },
    { name: "cpu.Thread(s) per core", title: "Threads per Core" },
    { name: "cpu.CPU max MHz", title: "Max Speed" },
    // currently not collected
    // { name: "PROCESSOR.0.TURBO_MODE", title: "Turbo Mode" },
    { name: "cpu.L1d cache", title: "Cache L1d" },
    { name: "cpu.L1i cache", title: "Cache L1i" },
    { name: "cpu.L2 cache", title: "Cache L2" },
    { name: "cpu.L3 cache", title: "Cache L3" },
    { name: "system-memory", title: "Memory" },
    { name: "system-gpu", title: "GPU" }
];

const softwareEntries: SidebarEntry[] = [
    // { name: "os.hostname", title: "Hostname" },
    { name: "os.distro", title: "Operating System" },
    { name: "os.kernel", title: "Kernel" },
    { name: "bios.Version", title: "BIOS Version" }
    // { name: "bios.Vendor", title: "BIOS Vendor" },
    // { name: "bios.BIOS Revision", title: "BIOS Revision" }
];

const EnergyLabels: Record<string, string> = {
    cpu: "CPU",
    core: "Core",
    dram: "DRAM",
    fpga: "FPGA",
    gpu: "GPU",
    system: "System"
};

export const useSidebarInfo = ({
    benchmark,
    job,
    nodeInfo,
    energy
}: {
    benchmark: Ref<Benchmark>;
    job: Ref<Job>;
    nodeInfo: Ref<SystemInfo>;
    energy: Ref<EnergyMeasurement | null>;
}) => {
    const benchmarkItems = computed(() => {
        const benchmarkInfo = {
            ...benchmark.value,
            benchmarkConfiguration:
                benchmark.value?.configuration?.configuration || {}
        };

        let entries = [
            ...benchmarkEntries
                .filter((x) => !benchmarkInfo.cli || !x.hideCLI)
                .map((x) =>
                    Object.assign({
                        title: x.title,
                        key: x.key || x.title,
                        // for unknown reasons these values are not displayed via ssr if they are not a string
                        value:
                            ObjectUtils.getByString(
                                benchmarkInfo,
                                x.name
                            )?.toString() || "",
                        editable: x.editable
                    })
                )
        ];

        if (!benchmarkInfo.cli) {
            entries = entries.concat([
                {
                    title: "Iterations",
                    value:
                        benchmarkInfo?.benchmarkConfiguration?.iterations.toString() ??
                        "",
                    key: "iterations"
                },
                {
                    title: "Capture Interval",
                    value: benchmarkInfo?.benchmarkConfiguration?.interval
                        ? `${benchmarkInfo?.benchmarkConfiguration?.interval}s`
                        : "unknown",
                    key: "captureInterval"
                }
            ]);
        }

        return entries;
    });

    const jobItems = computed(() => {
        const _job = unref(job);

        let items = [
            ...jobEntries
                .filter((x) => !_job.cli || !x.hideCLI)
                .map((x) =>
                    Object.assign({
                        title: x.title,
                        value:
                            ObjectUtils.getByString(_job, x.name)?.toString() ||
                            "",
                        key: x.key || x.title,
                        editable: x.editable
                    })
                ),
            {
                title: "Runtime",
                value: _job.runtimeSeconds
                    ? `${_job?.runtime || ""} (${_job?.runtimeSeconds || 0}s)`
                    : "unknown",
                key: "jobRuntime"
            }
        ];

        if (_job.captureStart && _job.captureEnd) {
            items.push({
                title: "Captured Runtime",
                value: `${_job.capturetime || ""} (${
                    _job.capturetimeSeconds
                }s)`,
                key: "capturedRuntime"
            });
        }

        if (energy.value) {
            Object.entries(energy.value)
                .filter(([_, value]) => value !== null)
                .forEach(([key, value]) => {
                    items.push({
                        title: `${EnergyLabels[key]} Energy`,
                        key: key,
                        value: `${value} kWh`
                    });
                });
        }

        return items;
    });

    const getInfo = (
        info: SystemInfo | {},
        entry: string,
        toHumanSize: boolean = false
    ) => {
        let value = ObjectUtils.getByString(info, entry);
        if (toHumanSize) value = humanSize(value);
        return toHumanSize ? `${value[0]} ${value[1]}` : value;
    };

    const formatSystemInfo = (info: SystemInfo) => {
        if (!Object.keys(info).length) return {};

        if (info.cpu) {
            let sockets = parseInt(info.cpu?.["Socket(s)"] || "1");
            info["system-cpu"] = `${sockets > 1 ? `${sockets}x ` : ""}${
                info.cpu?.["Model name"] || ""
            }`;

            info.cpu["CPU max MHz"] = `${parseInt(
                info.cpu?.["CPU max MHz"] || 0
            )} MHz`;
        }
        if (info.memory) {
            let installedDimms = parseInt(
                info.memory["Number Of Installed Devices"]
            );

            info["system-memory"] = `${
                installedDimms ? `${installedDimms}x ` : ""
            }${info.memory.Size} ${info.memory.Type} ${
                info.memory.Speed ? `(${info.memory.Speed})` : ""
            }`;
        }
        if (info.gpu) info["system-gpu"] = info.gpu.join("\n");

        return info;
    };

    const formatedNodeInfo = computed(() => {
        return formatSystemInfo(deepClone(nodeInfo.value || {}));
    });

    const hardwareItems = computed(() => {
        return hardwareEntries.map((x) =>
            Object.assign({
                title: x.title,
                value: replaceTrademark(
                    getInfo(formatedNodeInfo.value, x.name, !!x.humanSize)
                ),
                key: x.key || x.title
            })
        );
    });

    const softwareItems = computed(() => {
        return softwareEntries.map((x) =>
            Object.assign({
                title: x.title,
                value: getInfo(formatedNodeInfo.value, x.name),
                key: x.key || x.title
            })
        );
    });

    return { benchmarkItems, jobItems, hardwareItems, softwareItems };
};
