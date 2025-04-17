import FetchFactory from "../factory";

export interface Metrics {
    metrics?: JobMetrics;
    nodes?: string[];
    jobId?: number;
    missing?: number[];
}

export interface JobMetrics {
    [key: string]: {
        [key: string]: {
            metrics: {
                [key: string]:
                    | {
                          name: string;
                          description?: string;
                      }
                    | string;
            };
            unit?: string;
            description?: string;
            level_min?: string;
            aggregation?: string;
        };
    };
}

class MetricModule extends FetchFactory {
    private RESOURCE = "/metrics";

    async get(ids: number[] = [], intersect = false) {
        if (!Array.isArray(ids)) ids = [ids];
        return this.call<Metrics>(
            "GET",
            `${this.RESOURCE}${
                ids.length
                    ? `?jobIds=${ids}${intersect ? "&intersect=true" : ""}`
                    : ""
            }`,
            undefined // body
        );
    }
}

export default MetricModule;
