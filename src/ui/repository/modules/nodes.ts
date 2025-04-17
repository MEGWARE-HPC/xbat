import FetchFactory from "../factory";

export interface NodeMap {
    [key: string]: SystemInfo;
}

export interface SystemInfo {
    bios: BIOS;
    cpu: CPU;
    gpu: string[];
    hash: string;
    memory: Memory;
    os: OS;
    system: System;
    benchmarks: Record<string, number>;
}

export interface BIOS {
    "BIOS Revision": string;
    "Firmware Revision": string;
    "Release Date": string;
    Vendor: string;
    Version: string;
}

export interface CPU {
    Architecture: string;
    "CPU family": string;
    "CPU max MHz": string;
    "CPU(s)": string;
    "Core(s) per socket": string;
    "L1d cache": string;
    "L1i cache": string;
    "L2 cache": string;
    "L3 cache": string;
    Model: string;
    "Model name": string;
    "NUMA node(s)": string;
    "NUMA node0 CPU(s)": string;
    "NUMA node1 CPU(s)": string;
    "Socket(s)": string;
    "Thread(s) per core": string;
    "Vendor ID": string;
    topology: string;
}

export interface Memory {
    "Configured Memory Speed": string;
    "Configured Voltage": string;
    "Error Correction Type": string;
    "Form Factor": string;
    Manufacturer: string;
    "Maximum Capacity": string;
    "Number Of Devices": string;
    "Number Of Installed Devices": number;
    Size: string;
    Speed: string;
    Type: string;
    "Type Detail": string;
}

export interface OS {
    architecture: string;
    distro: string;
    hostname: string;
    kernel: string;
    sysname: string;
    version: string;
}

export interface System {
    Manufacturer: string;
    "Product Name": string;
    Version: string;
}

class NodeModule extends FetchFactory {
    private RESOURCE = "/nodes";

    async get(hashes: string[]) {
        return this.call<NodeMap>(
            "GET",
            `${this.RESOURCE}${hashes.length ? `?node_hashes=${hashes}` : ""}`,
            undefined // body
        );
    }
}

export default NodeModule;
