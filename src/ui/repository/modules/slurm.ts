import FetchFactory from "../factory";

type SlurmJobs = {};

class SlurmModule extends FetchFactory {
    private RESOURCE = "/slurm";

    async getJobs() {
        return this.call<SlurmJobs>(
            "GET",
            `${this.RESOURCE}/jobs`,
            undefined // body
        );
    }

    async getPartitions() {
        return this.call<SlurmJobs>(
            "GET",
            `${this.RESOURCE}/partitions`,
            undefined
        );
    }

    async getNodes() {
        return this.call<SlurmJobs>("GET", `${this.RESOURCE}/nodes`, undefined);
    }

    async cancelJob(id: number) {
        return this.call(
            "POST",
            `${this.RESOURCE}/jobs/${id}/cancel`,
            undefined
        );
    }
}

export default SlurmModule;
