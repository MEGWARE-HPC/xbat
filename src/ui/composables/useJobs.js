import { getJobState } from "~/utils/misc";

export const useJobs = ({
    benchmarks,
    jobs,
    hideUnfinished = false,
    itemOrder = "desc"
}) => {
    const filteredJobs = computed(() => {
        if (!hideUnfinished || !jobs.value) return jobs.value;
        return jobs.value.filter(
            (x) =>
                !x?.jobInfo?.jobState ||
                x.jobInfo.jobState?.includes("COMPLETED") ||
                x.jobInfo.jobState?.includes("COMPLETING") ||
                x.jobInfo.jobState?.includes("CANCELLED") ||
                x.jobInfo.jobState?.includes("TIMEOUT")
        );
    });

    const jobsById = computed(() => {
        return Object.fromEntries(filteredJobs.value.map((x) => [x.jobId, x]));
    });

    const jobIds = computed(() => filteredJobs.value.map((x) => x.jobId));

    const jobNodes = computed(() =>
        Object.fromEntries(
            filteredJobs.value.map((x) => [x.jobId, Object.keys(x.nodes)])
        )
    );

    const jobItems = computed(() => {
        const _benchmarks = Array.isArray(benchmarks.value)
            ? benchmarks.value
            : [benchmarks.value];

        if (!_benchmarks.length || !filteredJobs.value.length) return [];

        let items = [];
        _benchmarks.forEach((b) => {
            if (!b.jobIds) return;

            b.jobIds.forEach((jobId) => {
                const job = jobsById.value?.[jobId] || {};
                const jobState = getJobState(job.jobInfo?.jobState || []);

                items.push({
                    title: `Job ID ${jobId}`,
                    value: jobId,
                    subtitle: `#${b.runNr} ${
                        b.name
                    } - <span class='font-italic'>${
                        job.configuration?.jobscript?.variantName || "default"
                    }</span> [iteration ${job.iteration ?? 0}]`,
                    runNr: b.runNr,
                    state: jobState.value,
                    stateColor: jobState.color,
                    variables: job.variables || {}
                });
            });
        });

        const sortFn =
            itemOrder === "asc"
                ? (a, b) => a.value - b.value
                : (a, b) => b.value - a.value;

        return items.toSorted(sortFn);
    });

    return {
        jobsById,
        jobItems,
        jobIds,
        jobNodes
    };
};

export default useJobs;
