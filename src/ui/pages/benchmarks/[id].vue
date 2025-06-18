<template>
    <div>
        <v-navigation-drawer
            permanent
            :rail="infoCollapsed"
            location="right"
            width="350"
            id="info-drawer"
        >
            <template v-slot:append>
                <div class="d-flex justify-center mt-2">
                    <v-btn
                        @click="setInfoDrawer(!infoCollapsed)"
                        variant="text"
                        size="small"
                        style="margin-top: 12px"
                    >
                        <v-icon
                            :icon="
                                infoCollapsed
                                    ? '$chevronDoubleLeft'
                                    : '$chevronDoubleRight'
                            "
                        ></v-icon>
                    </v-btn>
                </div>
            </template>
            <div class="system-info-wrapper" v-show="!infoCollapsed">
                <InfoColumn
                    title="benchmark"
                    :items="sidebarBenchmarkItems"
                    @update="updateInfo('benchmark', $event)"
                >
                    <v-chip
                        :color="stateColors[benchmark.state] || 'info'"
                        size="small"
                        >{{ benchmark.state }}</v-chip
                    >
                </InfoColumn>
                <InfoColumn
                    title="job"
                    :items="sidebarJobItems"
                    @update="updateInfo('job', $event)"
                >
                    <div>
                        <v-chip :color="jobState.color" size="small">
                            {{ jobState.value }}
                        </v-chip>
                        <v-tooltip location="top" v-if="jobRunning">
                            <template v-slot:activator="{ props }">
                                <v-chip
                                    :color="
                                        refreshPaused ? 'info' : 'secondary'
                                    "
                                    size="small"
                                    class="ml-1"
                                    v-bind="props"
                                    @click="
                                        jobRunning
                                            ? refreshPaused
                                                ? pausedRefresh.splice(
                                                      pausedRefresh.indexOf(
                                                          jobId
                                                      ),
                                                      1
                                                  )
                                                : pausedRefresh.push(jobId)
                                            : null
                                    "
                                >
                                    <v-icon icon="$refresh"></v-icon>
                                    <v-icon
                                        v-if="refreshPaused"
                                        icon="$play"
                                    ></v-icon>
                                    <v-icon v-else icon="$pause"></v-icon>
                                </v-chip>
                            </template>
                            <span v-if="refreshPaused"
                                >Automatic refresh is paused for this job. Click
                                to resume.</span
                            >
                            <span v-else
                                >Job is still running - output and values are
                                refreshed automatically every 30 seconds.<br />
                                Click to pause refresh for this job.
                            </span>
                        </v-tooltip>
                    </div>
                    <template
                        #append
                        v-if="Object.keys(currentJob.variables || {}).length"
                    >
                        <JobVariableOverview :variables="currentJob.variables">
                        </JobVariableOverview>
                    </template>
                </InfoColumn>
                <InfoColumn
                    title="hardware"
                    class="mt-3"
                    :items="sidebarHardwareItems"
                >
                    <v-select
                        style="width: 150px; margin-left: 10px"
                        :items="participatingNodes?.[jobId] || []"
                        label="Node"
                        v-model="nodeInfoSelectedNode"
                        hide-details
                        no-data-text="No nodes found for this job"
                    ></v-select>
                    <template #append>
                        <div
                            class="d-flex justify-center mt-3"
                            v-if="topologies?.[jobId]?.[nodeInfoSelectedNode]"
                        >
                            <v-btn
                                @click="state.showCpuTopologyDialog = true"
                                variant="text"
                                color="light"
                                prepend-icon="$memory"
                                >View CPU Topology</v-btn
                            >
                        </div>
                    </template>
                </InfoColumn>

                <InfoColumn
                    title="software"
                    :items="sidebarSoftwareItems"
                ></InfoColumn>
            </div>
        </v-navigation-drawer>
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

                    <v-btn
                        variant="text"
                        append-icon="$cog"
                        :disabled="invalidBenchmark"
                        @click="state.showSettingsDialog = true"
                        >Settings
                    </v-btn>
                </div>

                <div v-if="state.showOutput">
                    <v-tabs
                        v-model="state.outputTab"
                        style="margin-bottom: 20px"
                        color="primary-light"
                    >
                        <v-tab
                            v-for="v of [
                                ...outputTabs.map((x) => x.title),
                                'Job Script'
                            ]"
                            :key="v"
                        >
                            {{ v }}
                        </v-tab>
                    </v-tabs>
                    <v-tabs-window v-model="state.outputTab">
                        <template v-for="outputTab of outputTabs">
                            <v-tabs-window-item>
                                <div
                                    class="text-medium-emphasis text-caption mb-3 ml-6"
                                    v-if="currentJob.jobInfo?.[outputTab.value]"
                                >
                                    <div class="d-flex">
                                        <v-icon
                                            icon="$file"
                                            size="small"
                                        ></v-icon>
                                        File available at
                                        <span class="font-italic ml-1">{{
                                            currentJob.jobInfo[outputTab.value]
                                        }}</span>
                                    </div>
                                </div>
                                <Editor
                                    :model-value="
                                        outputs?.[jobId]?.[outputTab.value] !==
                                        null
                                            ? outputs?.[jobId]?.[
                                                  outputTab.value
                                              ]
                                            : '# No output available (yet)'
                                    "
                                    readonly
                                    height="750"
                                    :filename="`${jobId}_${outputTab.value}.txt`"
                                    :loading="outputLoading"
                                    language="plaintext"
                                ></Editor>
                            </v-tabs-window-item>
                        </template>
                        <v-tabs-window-item>
                            <Editor
                                :readonly="true"
                                :modelValue="
                                    currentJob?.userJobscriptFile ||
                                    '# Job script not available (yet)'
                                "
                                :filename="`${jobId}_jobscript.sh`"
                                height="750"
                            ></Editor>
                        </v-tabs-window-item>
                    </v-tabs-window>
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
        <v-dialog v-model="state.showCpuTopologyDialog" max-width="1000">
            <v-card>
                <v-card-title> CPU Topology (by LIKWID) </v-card-title>
                <v-card-text>
                    <Editor
                        :readonly="true"
                        :model-value="
                            topologies?.[jobId]?.[nodeInfoSelectedNode] || ''
                        "
                        :line-numbers="false"
                        no-wrap
                    ></Editor>
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn
                        variant="plain"
                        @click="state.showCpuTopologyDialog = false"
                        >close</v-btn
                    ></v-card-actions
                >
            </v-card>
        </v-dialog>
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
        <!-- TODO move to separate component -->
        <v-dialog v-model="state.showSettingsDialog" eager :max-width="600">
            <v-card>
                <v-card-title>Settings</v-card-title>
                <v-card-text>
                    <div>
                        <v-switch
                            label="Rangeslider on Graph"
                            :model-value="graphPreferences.rangeslider"
                            @update:model-value="
                                graphPreferences.rangeslider = $event;
                                $graphStore.setPreference(
                                    'rangeslider',
                                    $event
                                );
                            "
                        ></v-switch>
                        <v-switch
                            label="Show X-Axis Title"
                            :model-value="graphPreferences.xTitle"
                            @update:model-value="
                                $graphStore.setPreference('xTitle', $event)
                            "
                        ></v-switch>
                        <div class="d-flex">
                            <v-switch
                                :model-value="
                                    graphPreferences.hideInactive !== 'none'
                                "
                                @update:model-value="
                                    $graphStore.setPreference(
                                        'hideInactive',
                                        $event ? 'disabled' : 'none'
                                    )
                                "
                            >
                                <template #label>
                                    Hide inactive
                                    <v-tooltip
                                        text="Activate this option to automatically hide traces exclusively reporting zero-values"
                                        location="right"
                                    >
                                        <template v-slot:activator="{ props }">
                                            <v-icon
                                                v-bind="props"
                                                icon="$information"
                                                class="ml-3"
                                            ></v-icon>
                                        </template>
                                    </v-tooltip>
                                </template>
                            </v-switch>
                            <v-select
                                class="ml-5"
                                :model-value="
                                    graphPreferences.hideInactive == 'none'
                                        ? 'disabled'
                                        : graphPreferences.hideInactive
                                "
                                @update:model-value="
                                    graphPreferences.hideInactive = $event;
                                    $graphStore.setPreference(
                                        'hideInactive',
                                        $event
                                    );
                                "
                                style="max-width: 200px"
                                :disabled="
                                    graphPreferences.hideInactive == 'none'
                                "
                                :items="hideInactiveOptions"
                                item-props
                                hide-details
                            ></v-select>
                        </div>
                    </div>
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn
                        variant="text"
                        @click="state.showSettingsDialog = false"
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
import { stateColors } from "~/utils/colors";
const { $api, $store, $graphStore, $snackbar } = useNuxtApp();

definePageMeta({
    validate: async (route) => {
        // Check for id to be number only, otherwise redirected to error page
        return (
            typeof route.params.id === "string" && /^\d+$/.test(route.params.id)
        );
    }
});

const MAX_PLOTS_PER_PAGE = 4;

const hideInactiveOptions = [
    {
        title: "disable traces",
        subtitle:
            "inactive traces are disabled but shown in the legend and statistics",
        value: "disabled"
    },
    {
        title: "hide traces",
        subtitle: "inactive traces are hidden completely",
        value: "hidden"
    }
];

const state = reactive({
    runNr: 0,
    synchronizeGraphs: true,
    showOutput: false,
    nodesWithMeasurements: {},
    showCompareDialog: false,
    showCpuTopologyDialog: false,
    showRooflineDialog: false,
    showSettingsDialog: false,
    infoCollapsed: false,
    outputTab: "Slurm",
    selectedJob: null,
    loading: false,
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

const useJobOutputs = ({ jobId, outputShown }) => {
    const outputs = ref({});
    const pending = ref(false);
    const defaultTabs = [{ title: "StdOut & StdErr", value: "standardOutput" }];

    // determine tabs based on whether stdout and stderr are combined
    const outputTabs = computed(() => {
        if (!jobId.value || !outputs.value[jobId.value]) return defaultTabs;

        const output = outputs.value[jobId.value];

        if (output.standardOutput !== null)
            if (output.standardError !== null)
                return [
                    { title: "StdOut", value: "standardOutput" },
                    { title: "StdErr", value: "standardError" }
                ];

        return defaultTabs;
    });

    const refresh = async () => {
        if (!jobId.value) return;
        pending.value = true;
        const output = await $api.jobs.getOutput(jobId.value);
        outputs.value[jobId.value] = output || {};
        pending.value = false;
    };

    watch([jobId, outputShown], async ([id, shown]) => {
        if (!shown || id in outputs.value) return;
        await refresh();
    });

    return { outputs, pending, refresh, outputTabs };
};

const {
    outputs,
    pending: outputLoading,
    refresh: refreshOutput,
    outputTabs
} = useJobOutputs({
    jobId: toRef(() => state.selectedJob),
    outputShown: toRef(() => state.showOutput)
});

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

const {
    nodeInfo,
    participatingNodes,
    nodeInfoSelectedNode,
    topologies,
    nodeBenchmarks
} = useNodes({
    jobs,
    currentJob
});

const { powerConsumption, fetch: fetchPower } = usePower();

const {
    benchmarkItems: sidebarBenchmarkItems,
    jobItems: sidebarJobItems,
    hardwareItems: sidebarHardwareItems,
    softwareItems: sidebarSoftwareItems
} = useSidebarInfo({
    benchmark,
    job: currentJob,
    nodeInfo: toRef(
        () => nodeInfo.value?.[jobId.value]?.[nodeInfoSelectedNode.value]
    ),
    powerConsumption
});

const setInfoDrawer = (v) => {
    infoCollapsed.value = v;
    nextTick(() => {
        // delay resize event to wait for sidebar animation to finish
        // otherwise graph scales incorrectly
        setTimeout(() => window.dispatchEvent(new Event("resize")), 500);
    });
};

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

const updateInfo = async (type, { key, value, title }) => {
    if ($store.demo) {
        $snackbar.show($store.demoMessage);
        return;
    }

    if (type === "benchmark") {
        await $api.benchmarks.patch(runNr.value, { [key]: value });
    } else if (type === "job") {
        await $api.jobs.patch(state.selectedJob, {
            [key]: value
        });
    }

    await refreshData();

    $snackbar.show(`Updated ${title}`);
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
            fetchPower(v);
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

const refreshAll = async () => {
    let handlers = [refreshData(), refreshMetrics()];

    // only fetch output if visited before (and therefore available in outputs)
    // if not visitied it will be fetched automatically on visit
    if (jobId.value in outputs.value) handlers.push(refreshOutput());

    await Promise.all(handlers);

    nextTick(async () => {
        // bustCache event triggers reload of graphs, load power data afterwards to prevent busting data of power queries
        // bust cache only for currently viewed job as others may already have finished
        $graphStore.bustCache([jobId.value]);
        await fetchPower(jobId.value);
    });
};

const terminalStates = new Set([
    "done",
    "failed",
    "canceled",
    "cancelled",
    "timeout"
]);

watch(
    [() => jobState, () => benchmark.value?.state],
    ([newJobState, newBenchmarkState]) => {
        if (
            terminalStates.has(newJobState) ||
            terminalStates.has(newBenchmarkState)
        ) {
            clearInterval(state.refreshHandler);
            state.refreshHandler = null;
            jobRunning.value = false;
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

<style lang="scss" scoped>
.variables-tooltip {
    :deep(&.v-tooltip) {
        background: red !important;
    }
}

.system-info-wrapper {
    margin-top: 10px;
    padding: 0 20px;
}
</style>
