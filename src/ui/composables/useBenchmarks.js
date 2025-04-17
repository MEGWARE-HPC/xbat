import { stateColors } from "~/utils/colors";
import { ArrayUtils } from "~/utils/array";

export const useBenchmarks = ({ slurmJobs, runNr, benchmarks }) => {
    const benchmarksByRunNr = computed(() => {
        if (!benchmarks?.value) return {};
        return Object.fromEntries(benchmarks.map((x) => [x.runNr, x]));
    });

    const currentBenchmark = computed(() => {
        if (!(runNr.value in benchmarksByRunNr.value)) return {};

        return benchmarksByRunNr.value[runNr.value];
    });

    const benchmarkStates = computed(() => {
        if (!benchmarks.value.length || !slurmJobs.value) return {};

        let s = {};
        for (const benchmark of benchmarks.value) {
            // for backwards compatibility
            if (benchmark.state == "canceled") benchmark.state = "cancelled";

            s[benchmark.runNr] = {
                title: benchmark.state,

                color:
                    stateColors[
                        benchmark.state
                            ? benchmark.state.toLowerCase()
                            : "pending"
                    ] || "grey",
                label: benchmark.state || "pending",
                info:
                    benchmark.state == "failed"
                        ? `${benchmark.failureReason || "reason unknown"}`
                        : null
            };

            if (benchmark.state != "running") continue;

            let stateCounter = {
                failed: 0,
                running: 0,
                queued: 0,
                cancelled: 0,
                completed: 0
            };

            for (const jobId of benchmark.jobIds) {
                if (!(jobId in slurmJobs.value)) continue;
                // jobState may be an array as jobs can have multiple concurrent states
                const jobStates = slurmJobs.value[jobId].jobState;
                switch (true) {
                    case jobStates.includes("FAILED"):
                        stateCounter.failed += 1;
                        break;
                    case jobStates.includes("CANCELLED"):
                        stateCounter.cancelled += 1;
                        break;
                    case jobStates.includes("RUNNING"):
                        stateCounter.running += 1;
                        break;
                    case jobStates.includes("COMPLETING"):
                    case jobStates.includes("COMPLETED"):
                        stateCounter.completed += 1;
                        break;
                    default:
                        stateCounter.queued += 1;
                }
            }

            if (ArrayUtils.sum(Object.values(stateCounter)) == 0) continue;

            s[benchmark.runNr].info = Object.keys(stateCounter)
                .filter((x) => stateCounter[x] != 0)
                .sort()
                .map((x) => `${stateCounter[x]} ${x}`)
                .join(" - ");
        }

        return s;
    });

    const invalidBenchmark = computed(() => {
        return (
            currentBenchmark.value?.state == "failed" ||
            currentBenchmark.value?.state == "cancelled" ||
            // for backwards compatibility
            currentBenchmark.value?.state == "canceled"
        );
    });

    return {
        currentBenchmark,
        benchmarkStates,
        invalidBenchmark
    };
};

export default useBenchmarks;
