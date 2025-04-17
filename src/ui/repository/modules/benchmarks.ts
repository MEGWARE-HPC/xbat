import FetchFactory from "../factory";
import type { ConfigurationDoc } from "./configurations";

export type Benchmark = {
    name: string;
    issuer: string;
    startTime: Date;
    state: string;
    sharedProjects: string[];
    variables: { [key: string]: string };
    configuration: ConfigurationDoc;
    runNr: number;
    failureReason: null | string;
    endTime: Date;
    jobIds: number[];
    cli?: boolean;
};

type BenchmarkPayload = {
    name: string;
    configId: string;
    variables: object;
    sharedProjects: string[];
};

type BenchmarkPatchPayload = {
    sharedProjects?: string[];
    name?: string;
};

type BenchmarkExportPayload = {
    runNrs: number[];
    anonymise: boolean;
};

type BenchmarkImportPayload = {
    file: File;
    reassignRunNr: boolean;
    updateColl: boolean;
};

class BenchmarkModule extends FetchFactory {
    private RESOURCE = "/benchmarks";

    async get(id: null | number = null) {
        let queryParam = "";
        if (Array.isArray(id)) queryParam += `?runNrs=${id}`;
        else if (id !== null) queryParam += `/${id}`;
        return this.call<Benchmark[] | Benchmark>(
            "GET",
            `${this.RESOURCE}${queryParam}`,
            undefined // body
        );
    }

    async delete(id: number) {
        return this.call<void>("DELETE", `${this.RESOURCE}/${id}`, undefined);
    }

    async cancel(id: number) {
        return this.call<void>(
            "POST",
            `${this.RESOURCE}/${id}/cancel`,
            undefined
        );
    }

    async patch(id: number, payload: BenchmarkPatchPayload) {
        return this.call<Benchmark>("PATCH", `${this.RESOURCE}/${id}`, payload);
    }

    async submit(payload: BenchmarkPayload) {
        return this.call<Benchmark>("POST", `${this.RESOURCE}`, payload);
    }

    async export(payload: BenchmarkExportPayload) {
        const response = await this.call<Blob>(
            "POST",
            `${this.RESOURCE}/export`,
            payload,
            {
                responseType: "blob"
            }
        );
        if (response && response.size === 0) {
            return null;
        }
        return response;
    }

    async import(payload: BenchmarkImportPayload) {
        const formData = new FormData();
        formData.append("file", payload.file);
        formData.append("reassignRunNr", String(payload.reassignRunNr));
        formData.append("updateColl", String(payload.updateColl));
        return this.call<void>("POST", `${this.RESOURCE}/import`, formData);
    }

    async purge() {
        return this.call<void>("POST", `${this.RESOURCE}/purge`, undefined);
    }
}

export default BenchmarkModule;
