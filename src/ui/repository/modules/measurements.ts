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

    async exportStatistics(query: GraphQuery) {
        const jobIds = [...new Set(query.jobIds)];

        if (jobIds.length === 0) {
            return null;
        }

        const params = new URLSearchParams({
            group: query.group,
            metric: query.metric,
            level: query.level,
            node: query.node || ""
        });

        // Fetch statistics for all selected jobs
        const responses = await Promise.all(
            jobIds.map((jobId) =>
                this.call<Blob>(
                    "GET",
                    `${this.RESOURCE}/${jobId}/statistics/csv?${params.toString()}`,
                    undefined,
                    { responseType: "blob" }
                )
            )
        );

        const blobs: Blob[] = [];

        for (let index = 0; index < responses.length; index++) {
            const response = responses[index];

            if (!response || response.size === 0) {
                if (jobIds.length === 1) {
                    return null;
                }

                throw new Error(
                    `No statistics data available for job ${jobIds[index]}`
                );
            }

            blobs.push(response);
        }

        if (blobs.length === 1) {
            return blobs[0];
        }

        // Read CSV contents
        const contents = await Promise.all(blobs.map((blob) => blob.text()));

        const parts = contents.map((content, index) => {
            const headerEnd = content.indexOf("\n");

            if (headerEnd === -1) {
                throw new Error(
                    `Invalid statistics CSV for job ${jobIds[index]}`
                );
            }

            const header = content
                .slice(0, headerEnd)
                .replace(/^\uFEFF/, "")
                .replace(/\r$/, "");

            const body = content.slice(headerEnd + 1);

            if (!body.trim()) {
                throw new Error(
                    `No statistics rows available for job ${jobIds[index]}`
                );
            }

            return { header, body };
        });

        const header = parts[0].header;

        if (parts.some((part) => part.header !== header)) {
            throw new Error("Inconsistent statistics CSV headers");
        }

        return new Blob(
            [
                `${header}\r\n`,
                ...parts.map((part) =>
                    part.body.endsWith("\n") ? part.body : `${part.body}\r\n`
                )
            ],
            { type: "text/csv;charset=utf-8" }
        );
    }
}

export default MeasurementModule;
