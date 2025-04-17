import type { Benchmark } from "~/repository/modules/benchmarks";
import type { JobShort } from "~/repository/modules/jobs";
import type { GraphQueryRoofline } from "~/store/graph";

export const useGraphRooflineForm = ({
    runNr,
    benchmarks,
    jobs,
    nodeBenchmarks
}: {
    runNr: Ref<number>;
    benchmarks: Ref<Benchmark[]>;
    jobs: Ref<JobShort[]>;
    nodeBenchmarks: Ref<any>;
}) => {
    const { flopItems, memItems } = useNodeBenchmarks();

    const form = reactive<GraphQueryRoofline>({
        node: undefined,
        plotFlops: ["peakflops"],
        jobIds: [],
        plotSP: true,
        plotDP: true,
        crossCompare: false,
        plotBy: "peak"
    });

    const { jobItems, jobsById, jobNodes } = useJobs({
        benchmarks,
        jobs,
        hideUnfinished: false
    });

    const filteredJobs = computed(() => {
        return jobItems.value
            .filter((x) =>
                runNr.value && !form.crossCompare
                    ? x.runNr == runNr.value
                    : true
            )
            .sort((a, b) => b.runNr - a.runNr);
    });

    const nodeWarning = computed(() => {
        return (
            form.jobIds.length > 1 &&
            [
                ...new Set(
                    Object.keys(jobNodes.value)
                        .filter((x) => form.jobIds.includes(parseInt(x)))
                        .map((x) => jobNodes.value[x])
                        .flat()
                )
            ].length > 1
        );
    });

    const filteredFlopItems = computed(() => {
        if (!form.node || !nodeBenchmarks.value?.[form.node]) return [];

        return flopItems.filter(
            (x) => form.node && x.value in nodeBenchmarks.value[form.node]
        );
    });

    // const filteredMemitems = computed(() => {
    //     if (!form.node || !nodeBenchmarks.value?.[form.node]) return [];

    //     return memItems.filter(
    //         (x) => form.node && x.value in nodeBenchmarks.value[form.node]
    //     );
    // });

    const nodeNames = computed(() => {
        const jobIds = filteredJobs.value.map((x) => x.value);

        const participatingNodes = Array.from(
            new Set(
                ...jobIds.map((x) =>
                    Object.keys(jobsById.value?.[x]?.nodes || {})
                )
            )
        );

        return participatingNodes;
    });

    // reset and set defaults
    watch(
        [filteredFlopItems, jobs, nodeBenchmarks],
        () => {
            form.plotFlops = [];

            if (!form.jobIds.length && !form.crossCompare)
                form.jobIds = filteredJobs.value.map((x) => x.value);

            if (
                // !filteredMemitems.value.length &&
                !filteredFlopItems.value.length
            )
                return;

            // const memKeys = filteredMemitems.value.map((x) => x.value);

            // if (memKeys.includes("bandwidth_mem")) form.mem = ["bandwidth_mem"];
            // else if (memKeys.length) rooflineForm.mem = [memKeys[0]];

            const flopKeys = filteredFlopItems.value.map((x) => x.value);
            // "peakflops_avx", "peakflops_avx512"
            ["peakflops"].forEach((x) => {
                if (flopKeys.includes(x)) form.plotFlops.push(x);
            });

            if (!form.plotFlops.length && flopKeys.length)
                form.plotFlops = [flopKeys[0]];
        },
        {
            deep: true,
            immediate: true
        }
    );

    // reset selection when turning off cross compare
    watch(
        () => form.crossCompare,
        (v) => {
            if (!v) {
                form.jobIds = form.jobIds.filter(
                    (x) => jobsById.value[x].runNr == runNr.value
                );
            }
        }
    );

    watch(
        nodeNames,
        (v) => {
            if (v.length) form.node = v[0];
        },
        { immediate: true }
    );

    return {
        form,
        filteredJobs,
        nodeWarning,
        filteredFlopItems,
        // filteredMemitems,
        nodeNames,
        jobItems
    };
};
