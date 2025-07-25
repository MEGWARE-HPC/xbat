import FetchFactory from "../factory";
import type { Configuration } from "./configurations";

export interface JobList {
    data: Job[];
}

export interface JobListShort {
    data: JobShort[];
}

export interface Job {
    configuration: Configuration;
    identificator: string;
    iteration: number;
    jobId: number;
    jobscriptFile: string;
    userJobscriptFile: string;
    permutationNr: number;
    runNr: number;
    slurmOutput?: string;
    variables: Record<string, string>;
    nodes: Record<string, JobNode>;
    runtime: string;
    runtimeSeconds: number;
    capturetime: string;
    capturetimeSeconds: number;
    captureStart: Date;
    captureEnd: Date;
    jobInfo: JobInfo;
    cli?: boolean;
}

export interface JobInfo {
    batchHost: string;
    cluster: string;
    command: string;
    endTime: Date;
    jobId: number;
    jobState: string[];
    name: string;
    nodes: string;
    partition: string;
    startTime: Date;
    standardError: string;
    standardOutput: string;
    submitTime: Date;
    userName: string;
    currentWorkingDirectory: string;
}

export interface JobOutput {
    runNr: number;
    jobId: number;
    lastUpdate: Date;
    standardOutput: string | null;
    standardError: string | null;
}

export interface JobPatchPayload {
    variantName: string;
}

export interface JobShort {
    configuration: {
        jobscript: {
            variantName: string;
        };
    };
    iteration: number;
    jobId: number;
    runNr: number;
    variables: Record<string, string>;
    nodes: Record<string, JobNode>;
    runtime: string;
    capturetime: string;
    jobInfo: {
        jobState: string[];
    };
}

export interface JobNode {
    hash: string;
    hostname: string;
}

class JobModule extends FetchFactory {
    private RESOURCE = "/jobs";

    async get(runNrs: number | null, short: true): Promise<JobListShort>;
    async get(runNrs: number | null, short: false): Promise<JobList>;
    async get(
        runNrs: number | null = null,
        short = false
    ): Promise<JobList | JobListShort> {
        let queryParameters = `${
            runNrs !== null
                ? `?runNrs=${Array.isArray(runNrs) ? runNrs : [runNrs]}`
                : ""
        }`;

        if (short) {
            queryParameters += `${
                queryParameters.includes("?") ? "&" : "?"
            }short=true`;
        }

        return this.call<JobListShort | JobList>(
            "GET",
            `${this.RESOURCE}${queryParameters}`,
            undefined
        ) as Promise<JobListShort | JobList>;
    }

    async patch(jobId: number, payload: JobPatchPayload) {
        return this.call<Job>("PATCH", `${this.RESOURCE}/${jobId}`, payload);
    }

    async getOutput(jobId: number) {
        return this.call<JobOutput>(
            "GET",
            `${this.RESOURCE}/${jobId}/output`,
            undefined // body
        );
    }
}

export default JobModule;
