import type { Job } from "@/repository/modules/jobs";
import type { Benchmark } from "@/repository/modules/benchmarks";
import { getJobState } from "~/utils/misc";

export const useJob = (job: Ref<Job>, benchmark: Ref<Benchmark>) => {
    const rawStates = computed(() => {
        return (
            job.value?.jobInfo?.jobState ||
            benchmark.value?.state || ["PENDING"]
        );
    });

    const jobState = computed((): { value: string; color: string } => {
        return getJobState(rawStates.value);
    });

    const jobRunning = computed(() => {
        return (
            rawStates.value.includes("PENDING") ||
            rawStates.value.includes("RUNNING")
        );
    });

    const jobId = computed(() => {
        return typeof job.value.jobId === "string"
            ? parseInt(job.value.jobId)
            : job.value.jobId || 0;
    });

    return {
        jobState,
        jobRunning,
        jobId
    };
};

export default useJob;
