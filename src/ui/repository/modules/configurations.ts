import FetchFactory from "../factory";

export type ConfigurationResponse = {
    data: ConfigurationDoc[];
};

export interface ConfigurationDoc {
    _id: string;
    configuration: Configuration;
    misc: {
        created: string;
        owner: string;
        edited: string;
    };
}

export interface WrappedConfiguration {
    configuration: Configuration;
}

export type Configuration = {
    jobscript: Jobscript[];
    variables: JobVariable[];
    iterations: number;
    enableLikwid: boolean;
    enableMonitoring: boolean;
    interval: number;
    configurationName: string;
    sharedProjects: string[];
};

export type JobVariable = {
    key: string;
    values: string[];
    selected: string[];
    input?: string;
};

export type Jobscript = {
    script: string;
    variantName: string;
    nodes: number;
    nodelist: string;
    "job-name": string;
    time: string;
    ntasks: number;
    partition: string;
    output: string;
    error: string;
};

class ConfigurationModule extends FetchFactory {
    private RESOURCE = "/configurations";

    async get() {
        return this.call<ConfigurationResponse>(
            "GET",
            `${this.RESOURCE}`,
            undefined // body
        );
    }

    async delete(id: number) {
        return this.call("DELETE", `${this.RESOURCE}/${id}`, undefined);
    }

    async put(id: number, payload: ConfigurationDoc) {
        return this.call<ConfigurationDoc>(
            "PUT",
            `${this.RESOURCE}/${id}`,
            payload
        );
    }

    async post(payload: WrappedConfiguration) {
        return this.call<ConfigurationDoc>("POST", `${this.RESOURCE}`, payload);
    }
}

export default ConfigurationModule;
