<template>
    <div>
        <BenchmarkSidebar
            :benchmark="benchmark"
            :jobs="jobs"
            :jobId="jobId"
            :energy="energy"
            @update:refreshPaused="
                jobRunning
                    ? refreshPaused
                        ? pausedRefresh.splice(pausedRefresh.indexOf(jobId), 1)
                        : pausedRefresh.push(jobId)
                    : null
            "
            :refreshPaused="refreshPaused"
            @refresh="refreshBenchmark()"
        ></BenchmarkSidebar>
        <v-container fluid>
            <!-- TODO using v-main here causes hydration mismatch -->
            <div :style="{ 'margin-right': infoCollapsed ? '56px' : '350px' }">
                <div
                    class="d-flex flex-wrap justify-end align-center mb-1"
                    style="gap: 10px; margin-top: -20px"
                >
                    <div>
                        <v-btn
                            variant="text"
                            title="Row Arrangement"
                            @click="setArrangement(false)"
                            :color="displayColumns ? 'font-light' : 'primary'"
                            :disabled="state.showOutput"
                            ><v-icon
                                size="small"
                                icon="$viewSequential"
                            ></v-icon
                        ></v-btn>
                        <v-btn
                            variant="text"
                            title="Column Arrangement"
                            @click="setArrangement(true)"
                            :color="!displayColumns ? 'font-light' : 'primary'"
                            :disabled="state.showOutput"
                            ><v-icon size="small" icon="$viewColumn"></v-icon
                        ></v-btn>
                    </div>
                    <ClientOnly>
                        <v-autocomplete
                            :items="jobItems"
                            v-model="state.selectedJob"
                            auto-select-first
                            :disabled="invalidBenchmark || jobs.length < 2"
                            hide-details
                        >
                            <template v-slot:item="{ props, item }">
                                <v-list-item
                                    v-bind="props"
                                    :title="item.raw.title"
                                >
                                    <v-list-item-subtitle
                                        v-html="item.raw.subtitle"
                                    >
                                    </v-list-item-subtitle>
                                    <template #append>
                                        <div class="d-flex align-center gap-10">
                                            <v-chip
                                                class="ml-2"
                                                size="small"
                                                variant="tonal"
                                                :color="item.raw.stateColor"
                                                >{{ item.raw.state }}
                                            </v-chip>
                                            <JobVariableOverview
                                                :variables="item.raw.variables"
                                                v-if="
                                                    Object.keys(
                                                        item.raw.variables
                                                    ).length
                                                "
                                            >
                                                <v-btn
                                                    icon="$currency"
                                                    size="x-small"
                                                    variant="text"
                                                ></v-btn>
                                            </JobVariableOverview>
                                        </div>
                                    </template>
                                </v-list-item>
                            </template>
                        </v-autocomplete>
                    </ClientOnly>
                    <v-spacer></v-spacer>
                    <v-switch
                        label="Synchronize Graphs"
                        v-model="state.synchronizeGraphs"
                        title="Synchronize X-Axis of Graphs"
                        :disabled="invalidBenchmark || state.showOutput"
                    ></v-switch>
                    <v-btn
                        @click="state.showOutput = !state.showOutput"
                        variant="text"
                        :append-icon="
                            state.showOutput ? '$chartLine' : '$textBox'
                        "
                    >
                        {{ state.showOutput ? "Graphs" : "Output" }}
                    </v-btn>
                    <v-btn
                        variant="text"
                        @click="state.showCompareDialog = true"
                        append-icon="$compareHorizontal"
                        :disabled="invalidBenchmark"
                        >Compare
                    </v-btn>
                    <v-btn
                        variant="text"
                        @click="showRoofline"
                        append-icon="$chartSankey"
                        :disabled="invalidBenchmark"
                        >Roofline
                    </v-btn>
                    <BenchmarkSettings>
                        <v-btn
                            variant="text"
                            append-icon="$cog"
                            :disabled="invalidBenchmark"
                            @click="state.showSettingsDialog = true"
                            >Settings
                        </v-btn>
                    </BenchmarkSettings>
                </div>

                <div v-if="state.showOutput">
                    <BenchmarkOutput
                        ref="benchmarkOutputRef"
                        :job="currentJob"
                        :detailsRevision="selectedDetailsRevision"
                        :visible="state.showOutput"
                    ></BenchmarkOutput>
                </div>
                <div v-show="!state.showOutput">
                    <div v-if="invalidBenchmark">
                        <div
                            class="text-medium-emphasis text-caption mx-auto font-italic font-bold"
                            style="
                                width: fit-content;
                                font-size: 1rem;
                                margin-top: 150px;
                            "
                        >
                            <div
                                class="d-flex flex-column align-center justify-center"
                            >
                                <div>
                                    benchmark
                                    {{
                                        benchmark.status == "failed"
                                            ? "failed"
                                            : "was cancelled"
                                    }}
                                </div>
                                <div>
                                    <v-btn
                                        variant="text"
                                        @click="state.showOutput = true"
                                        >view output</v-btn
                                    >
                                </div>
                            </div>
                        </div>
                    </div>
                    <GraphGroup
                        :synchronize="state.synchronizeGraphs"
                        v-if="!invalidBenchmark"
                    >
                        <template v-slot:default="{ relayout, relayoutData }">
                            <v-row dense>
                                <v-col
                                    :md="displayColumns ? '6' : '12'"
                                    sm="12"
                                    v-for="id of range(0, MAX_PLOTS_PER_PAGE)"
                                    :key="id"
                                >
                                    <GraphWrapper
                                        :jobIds="[jobId]"
                                        :metrics="currentMetrics"
                                        :nodes="nodeInfo"
                                        :defaultGroup="
                                            defaultGraphs?.[id]?.['group']
                                        "
                                        :defaultMetric="
                                            defaultGraphs?.[id]?.['metric']
                                        "
                                        :defaultLevel="
                                            defaultGraphs?.[id]?.['level']
                                        "
                                        @relayout="relayout"
                                        :relayoutData="relayoutData"
                                    ></GraphWrapper>
                                </v-col>
                            </v-row>
                        </template>
                    </GraphGroup>
                </div>
            </div>
        </v-container>
        <v-dialog v-model="state.showRooflineDialog" id="dialog-roofline">
            <v-card>
                <v-card-title>Roofline Model</v-card-title>
                <GraphWrapper
                    roofline
                    :benchmarks="generalData.benchmarks"
                    :runNr="runNr"
                    :jobs="generalData.jobs"
                    :nodes="nodeInfo"
                    flat
                ></GraphWrapper>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn @click="state.showRooflineDialog = false"
                        >close</v-btn
                    >
                </v-card-actions>
            </v-card>
        </v-dialog>
        <ClientOnly>
            <BenchmarkComparison
                :modelValue="state.showCompareDialog"
                @update:modelValue="state.showCompareDialog = false"
                :selected="jobIds"
                :benchmarks="generalData.benchmarks"
                :hide-inactive="
                    graphPreferences.hideInactive
                        ? graphPreferences.hideInactiveOption
                        : false
                "
                :jobs="generalData.jobs"
            ></BenchmarkComparison>
        </ClientOnly>
    </div>
</template>
<script setup>
import { getJobState, range } from "~/utils/misc";
const { $api, $store, $graphStore } = useNuxtApp();

definePageMeta({
    validate: async (route) => {
        // Check for id to be number only, otherwise redirected to error page
        return (
            typeof route.params.id === "string" && /^\d+$/.test(route.params.id)
        );
    }
});

const MAX_PLOTS_PER_PAGE = 4;

const state = reactive({
    runNr: 0,
    synchronizeGraphs: true,
    showOutput: false,
    showCompareDialog: false,
    showRooflineDialog: false,
    selectedJob: null,
    refreshHandler: null
});

const pausedRefresh = useCookie("xbat_paused-refresh", { default: () => [] });

const refreshPaused = computed(
    () => jobId.value && pausedRefresh.value.includes(jobId.value)
);

const route = useRoute();
const { graphPreferences, displayColumns, infoCollapsed } = usePreferences();

useSeoMeta({
    title: `Benchmark - ${route.params.id}`,
    description: "xbat benchmark results"
});

const runNr = ref(Number.parseInt(route.params.id, 10) || 0);
let disposed = false;
const defaultGraphs = ref([]);

const setDefaultGraphs = (_metrics) => {
    if (defaultGraphs.value.length) return;
    const desired = [
        ["cpu", "FLOPS"],
        ["memory", "Bandwidth"],
        ["cache", "Bandwidth"],
        ["energy", "System Power"]
    ];
    for (const entry of desired) {
        let values = entry;
        if (!(entry[0] in _metrics)) continue;
        // use first of group as default
        if (
            !(entry[1] in _metrics[entry[0]]) &&
            Object.keys(_metrics[entry[0]]).length
        )
            values[1] = Object.keys(_metrics[entry[0]])[0];
        defaultGraphs.value.push({
            group: values[0],
            metric: values[1],
            level: "job"
        });
    }
};

const {
    data,
    error: refreshDataError,
    refresh: refreshData
} = await useAsyncData(`benchmark-data:${runNr.value}`, async () => {
    const [benchmarkResult, jobsResult] = await Promise.allSettled([
        $api.benchmarks.get(runNr.value),
        $api.jobs.get(runNr.value)
    ]);

    if (benchmarkResult.status === "rejected") throw benchmarkResult.reason;
    if (jobsResult.status === "rejected") throw jobsResult.reason;

    return {
        benchmark: benchmarkResult.value?.data,
        jobs: jobsResult.value?.data ?? []
    };
});

if (
    !data.value?.benchmark ||
    Object.keys(data.value?.benchmark || {}).length === 0
) {
    throw createError({
        statusCode: 404,
        statusMessage: `Benchmark #${runNr.value} Not Found`,
        fatal: true
    });
}

const benchmark = computed((previous) => data.value?.benchmark ?? previous);
const jobs = computed((previous) => data.value?.jobs ?? previous ?? []);
const terminalStates = new Set([
    "done",
    "failed",
    "canceled",
    "cancelled",
    "timeout",
    "deadline"
]);
const jobLifecycles = shallowReactive({});

const getJobPhase = (job) => {
    const states = job.jobInfo?.jobState ?? [];
    if (states.includes("PENDING") || states.includes("RUNNING"))
        return "active";
    if (terminalStates.has(getJobState(states).value)) return "terminal";
    return null;
};

watch(
    jobs,
    (items) => {
        for (const job of items) {
            const id = Number(job.jobId);
            const phase = getJobPhase(job);
            if (!id || !phase) continue;

            const previous = jobLifecycles[id];
            if (previous?.phase === phase) continue;

            // Change the cache revision on completion or requeue.
            const revision = previous
                ? previous.revision + 1
                : Number(phase === "terminal");
            jobLifecycles[id] = { phase, revision };
        }
    },
    { immediate: true, flush: "sync" }
);

const getDetailsRevision = (id) => jobLifecycles[id]?.revision ?? 0;
const selectedDetailsRevision = computed(() =>
    getDetailsRevision(Number(state.selectedJob))
);

if (jobs.value.length) {
    const availableJobIds = jobs.value
        .map((job) => Number(job.jobId))
        .filter(Number.isFinite)
        .sort((a, b) => a - b);

    state.selectedJob = availableJobIds[0] ?? null;
}

const metricsCache = useJobResourceCache(
    (id) => $api.metrics.get(id),
    (id, revision) => {
        if (!disposed && getDetailsRevision(id) === revision) {
            $graphStore.bustCache([id]);
        }
    }
);

const currentMetrics = computed(
    () => metricsCache.entries[Number(state.selectedJob)]?.value?.metrics ?? {}
);
watch(currentMetrics, setDefaultGraphs, { immediate: true });

const initialJobId = Number(state.selectedJob);
if (initialJobId) {
    await metricsCache
        .load(initialJobId, selectedDetailsRevision.value)
        .catch((error) =>
            console.error("Failed to load initial job metrics:", error)
        );
}

// TODO maybe load at later stage and cut down on data
// lazy currently does not work as benchmark data is needed right away
const { data: generalData } = await useAsyncData("general-data", async () => {
    const [b, j] = await Promise.all([
        $api.benchmarks.get(),
        $api.jobs.get(null, true)
    ]);

    return {
        benchmarks: b.data,
        jobs: j.data
    };
});

const currentJob = computed(() => {
    return jobsById.value[state.selectedJob] || {};
});

const { invalidBenchmark } = useBenchmarks({
    runNr,
    benchmarks: generalData.value.benchmarks
});

const { jobItems, jobsById, jobIds } = useJobs({
    benchmarks: benchmark,
    jobs,
    itemOrder: "asc"
});

const { jobId, jobRunning } = useJob(currentJob, benchmark);

const { nodeInfo } = useNodes({
    jobs,
    currentJob
});

const setArrangement = (columns) => {
    displayColumns.value = columns;
    nextTick(() => {
        window.dispatchEvent(new Event("resize"));
    });
};

const showRoofline = () => {
    state.showRooflineDialog = true;
    nextTick(() => {
        window.dispatchEvent(new Event("resize"));
    });
};

const energyCache = useJobResourceCache((id) =>
    $api.measurements.getEnergy(id)
);
const energy = computed(() => {
    const value = energyCache.entries[jobId.value]?.value;
    return value ? { [jobId.value]: value } : {};
});

watch(
    jobItems,
    (items) => {
        if (!items.length) return;

        const selected = items.find(
            ({ value }) => Number(value) === Number(state.selectedJob)
        );
        state.selectedJob = selected?.value ?? items[0].value;
    },
    { immediate: true }
);

const benchmarkOutputRef = ref(null);

const loadJobDetails = (id, revision, force = false) => {
    const reportError = (resource) => (error) =>
        console.error(`Failed to load ${resource} for job ${id}:`, error);

    void metricsCache.load(id, revision, force).catch(reportError("metrics"));
    void energyCache.load(id, revision, force).catch(reportError("energy"));

    if (force && benchmarkOutputRef.value) {
        void benchmarkOutputRef.value
            .refresh(id, revision)
            .catch(reportError("output"));
    }
};

watch(
    [jobId, selectedDetailsRevision],
    ([id, revision]) => {
        if (id) loadJobDetails(id, revision);
    },
    { immediate: true }
);

const REFRESH_INTERVAL = 30_000;
const shouldPollJob = computed(() =>
    Boolean(jobId.value && jobRunning.value && !refreshPaused.value)
);
const shouldPoll = computed(
    () =>
        ["pending", "running"].includes(benchmark.value?.state) ||
        shouldPollJob.value
);

let metadataRefresh = null;

const refreshBenchmark = async (poll = false) => {
    if (poll && metadataRefresh) return;

    // A sidebar edit needs a fresh read after any older request.
    while (metadataRefresh) await metadataRefresh;
    if (disposed) return;

    metadataRefresh = (async () => {
        try {
            await refreshData();
            if (refreshDataError.value) throw refreshDataError.value;
            await nextTick();

            if (!disposed && poll && shouldPollJob.value) {
                loadJobDetails(
                    jobId.value,
                    selectedDetailsRevision.value,
                    true
                );
            }
        } catch (error) {
            console.error("Failed to refresh benchmark:", error);
        }
    })();

    try {
        await metadataRefresh;
    } finally {
        metadataRefresh = null;
    }
};

const stopPolling = () => {
    if (state.refreshHandler === null) return;
    clearInterval(state.refreshHandler);
    state.refreshHandler = null;
};

watch(
    shouldPoll,
    (enabled) => {
        if (import.meta.server) return;

        if (!enabled) {
            stopPolling();
        } else if (state.refreshHandler === null) {
            state.refreshHandler = setInterval(
                () => void refreshBenchmark(true),
                REFRESH_INTERVAL
            );
        }
    },
    { immediate: true }
);

onMounted(() => {
    $store.benchmarkNr = runNr.value;
});

onBeforeUnmount(() => {
    disposed = true;
    stopPolling();
    if ($store.benchmarkNr === runNr.value) $store.benchmarkNr = null;
});
</script>
