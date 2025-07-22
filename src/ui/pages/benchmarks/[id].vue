<template>
    <div>
        <BenchmarkSidebar
            :benchmark="benchmark"
            :jobs="jobs"
            :jobId="jobId"
            @update:refreshPaused="
                jobRunning
                    ? refreshPaused
                        ? pausedRefresh.splice(pausedRefresh.indexOf(jobId), 1)
                        : pausedRefresh.push(jobId)
                    : null
            "
            :refreshPaused="refreshPaused"
            @refresh="refreshData"
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
                                        :metrics="metrics?.[jobId] || {}"
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
import { range } from "~/utils/misc";
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
    noData: false,
    visitedJobs: [],
    refreshHandler: null
});

const pausedRefresh = useCookie("xbat_paused-refresh", { default: () => [] });

const refreshPaused = computed(
    () => jobId.value && pausedRefresh.value.includes(jobId.value)
);

const route = useRoute();
const { graphPreferences, displayColumns, infoCollapsed } = usePreferences();

const metrics = ref({});
const metricsCache = ref({}); // cache raw api responses for metrics call
const runNr = computed(() => parseInt(route.params.id) || 0);
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

const { data, refresh: refreshData } = await useAsyncData(
    async () => {
        const [b, j] = await Promise.all([
            $api.benchmarks.get(runNr.value),
            $api.jobs.get(runNr.value)
        ]);
        return {
            benchmark: b.data,
            jobs: j.data
        };
    },

    { watch: [runNr] }
);

if (data.value.jobs.length && !state.refreshHandler)
    state.selectedJob = data.value.jobs[0].jobId;

const { data: jobMetrics, refresh: refreshMetrics } = await useAsyncData(
    async () => {
        if (!state.selectedJob) return {};

        // if already loaded and not in refresh mode return cached data
        if (
            state.selectedJob in metricsCache.value &&
            Object.keys(metricsCache.value[state.selectedJob]).length &&
            !state.refreshHandler
        ) {
            return metricsCache.value[state.selectedJob];
        }

        return await $api.metrics.get(state.selectedJob);
    },
    { watch: [() => state.selectedJob] }
);

watch(
    jobMetrics,
    (v) => {
        if (!Object.keys(v).length) {
            state.noData = true;
            return;
        }

        metricsCache.value[state.selectedJob] = v;
        metrics.value[state.selectedJob] = v.metrics;
        state.nodesWithMeasurements[state.selectedJob] = v.nodes;
        state.noData = !Object.keys(v.metrics).length || !v.nodes.length;

        // set default graphs if not in refresh mode
        if (!state.refreshHandler || !defaultGraphs.value.length)
            setDefaultGraphs(v.metrics);

        // nextTick(() => {
        //     fetchPower(state.selectedJob, job);
        // });
    },
    { immediate: true, deep: true }
);

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

const benchmark = computed(() => data.value.benchmark);
const jobs = computed(() => data.value.jobs);

const { invalidBenchmark } = useBenchmarks({
    runNr,
    benchmarks: generalData.value.benchmarks
});

const { jobItems, jobsById, jobIds } = useJobs({
    benchmarks: benchmark,
    jobs,
    itemOrder: "asc"
});

const { jobState, jobId, jobRunning } = useJob(currentJob, benchmark);

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

// reset selection and visited jobs
watch(
    jobItems,
    (v) => {
        if (!v.length || state.refreshHandler) return;
        state.visitedJobs = [];
        state.selectedJob = v[0].value;
    },
    {
        immediate: true
    }
);

watch(
    () => state.selectedJob,
    (v) => {
        if (!state.visitedJobs.includes(v) && v) {
            console.log("TODO add power back in");
            state.visitedJobs.push(v);
        }
    },
    {
        immediate: true
    }
);

watch(
    runNr,
    () => {
        $store.benchmarkNr = runNr.value;
    },
    { immediate: true }
);

const benchmarkOutputRef = ref(null);

const refreshAll = async () => {
    let handlers = [refreshData(), refreshMetrics()];

    if (benchmarkOutputRef.value)
        handlers.push(benchmarkOutputRef.value.refresh());

    await Promise.all(handlers);

    nextTick(async () => {
        // bustCache event triggers reload of graphs, load power data afterwards to prevent busting data of power queries
        // bust cache only for currently viewed job as others may already have finished
        $graphStore.bustCache([jobId.value]);
    });
};

const terminalStates = ["done", "failed", "canceled", "cancelled", "timeout"];

watch(
    [() => jobState.value?.value, () => benchmark.value?.state],
    ([newJobState, newBenchmarkState]) => {
        if (
            terminalStates.includes(newJobState) &&
            terminalStates.includes(newBenchmarkState)
        ) {
            clearInterval(state.refreshHandler);
            clearInterval(state.refreshHandler);
            state.refreshHandler = null;
            if (newJobState == "done") refreshAll();

            return;
        }
    },
    { immediate: true }
);

watch(
    [jobId, refreshPaused],
    async () => {
        if (process.server) return;

        if (!jobRunning.value || refreshPaused.value) {
            if (state.refreshHandler) {
                clearInterval(state.refreshHandler);
                state.refreshHandler = null;
            }
            return;
        }
        if (!state.refreshHandler) {
            state.refreshHandler = setInterval(async () => {
                await refreshAll();
            }, 30000);
        }
    },
    { immediate: true }
);

onBeforeRouteLeave((to, from, next) => {
    $store.benchmarkNr = null;
    // $graphStore.cacheClearEvent.reset();
    if (state.refreshHandler) clearInterval(state.refreshHandler);
    next();
});
</script>

<style lang="scss" scoped></style>
