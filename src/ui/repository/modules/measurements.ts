import FetchFactory from "../factory";
import type { GraphQuery, GraphRawData } from "~/types/graph";

export type EnergyMeasurement = {
    cpu: number | null;
    core: number | null;
    dram: number | null;
    fpga: number | null;
    gpu: number | null;
    system: number | null;
};

class MeasurementModule extends FetchFactory {
    private RESOURCE = "/measurements";

    async get(query: GraphQuery) {
        return this.call<GraphRawData>(
            "GET",
            `${this.RESOURCE}/${query.jobIds[0]}?group=${query.group}&metric=${query.metric}&level=${query.level}&node=${query.node}&deciles=${query.deciles}`,
            undefined // body
        );
    }

    async getEnergy(jobId: number) {
        return this.call<EnergyMeasurement>(
            "GET",
            `${this.RESOURCE}/${jobId}/energy`,
            undefined // body
        );
    }
}

export default MeasurementModule;
