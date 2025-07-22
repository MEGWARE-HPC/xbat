<template>
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
                        <template v-slot:activator="{ props: slotProps }">
                            <v-chip
                                :color="
                                    props.refreshPaused ? 'info' : 'secondary'
                                "
                                size="small"
                                class="ml-1"
                                v-bind="slotProps"
                                @click="emit('update:refreshPaused')"
                            >
                                <v-icon icon="$refresh"></v-icon>
                                <v-icon
                                    v-if="props.refreshPaused"
                                    icon="$play"
                                ></v-icon>
                                <v-icon v-else icon="$pause"></v-icon>
                            </v-chip>
                        </template>
                        <span v-if="props.refreshPaused"
                            >Automatic refresh is paused for this job. Click to
                            resume.</span
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
                        <v-dialog max-width="1000">
                            <template
                                v-slot:activator="{ props: activatorProps }"
                            >
                                <v-btn
                                    variant="text"
                                    color="light"
                                    v-bind="activatorProps"
                                    prepend-icon="$memory"
                                    >View CPU Topology</v-btn
                                >
                            </template>
                            <template v-slot:default="{ isActive }">
                                <v-card>
                                    <v-card-title>
                                        CPU Topology (by LIKWID)
                                    </v-card-title>
                                    <v-card-text>
                                        <Editor
                                            :readonly="true"
                                            :model-value="
                                                topologies?.[jobId]?.[
                                                    nodeInfoSelectedNode
                                                ] || ''
                                            "
                                            :line-numbers="false"
                                            no-wrap
                                        ></Editor>
                                    </v-card-text>
                                    <v-card-actions>
                                        <v-spacer></v-spacer>
                                        <v-btn
                                            variant="plain"
                                            @click="isActive.value = false"
                                            >close</v-btn
                                        ></v-card-actions
                                    >
                                </v-card>
                            </template>
                        </v-dialog>
                    </div>
                </template>
            </InfoColumn>

            <InfoColumn
                title="software"
                :items="sidebarSoftwareItems"
            ></InfoColumn>
        </div>
    </v-navigation-drawer>
</template>
<script lang="ts" setup>
import type { Benchmark } from "@/repository/modules/benchmarks";
import type { Job } from "@/repository/modules/jobs";

const props = defineProps<{
    benchmark: Benchmark;
    jobs: Job[];
    jobId: number;
    refreshPaused: boolean;
}>();

const { infoCollapsed } = usePreferences();

const setInfoDrawer = (v: boolean) => {
    infoCollapsed.value = v;
    nextTick(() => {
        // delay resize event to wait for sidebar animation to finish
        // otherwise graph scales incorrectly
        setTimeout(() => window.dispatchEvent(new Event("resize")), 500);
    });
};

const currentJob = computed(() => {
    return props.jobs.find((job) => job.jobId === props.jobId) || ({} as Job);
});

const {
    nodeInfo,
    participatingNodes,
    nodeInfoSelectedNode,
    topologies,
} = useNodes({
    jobs: toRef(() => props.jobs),
    currentJob
});

const currentNodeInfo = computed(() => {
    return nodeInfo.value?.[jobId.value]?.[nodeInfoSelectedNode.value] || {};
});

const {
    benchmarkItems: sidebarBenchmarkItems,
    jobItems: sidebarJobItems,
    hardwareItems: sidebarHardwareItems,
    softwareItems: sidebarSoftwareItems
} = useSidebarInfo({
    benchmark: toRef(() => props.benchmark),
    job: currentJob,
    nodeInfo: currentNodeInfo,
    powerConsumption: toRef(() => {})
});

const { $api, $store, $snackbar } = useNuxtApp();

const emit = defineEmits<{
    (e: "refresh", jobId: number): void;
    (e: "update:refreshPaused"): void;
}>();

const { jobState, jobId, jobRunning } = useJob(
    currentJob,
    toRef(() => props.benchmark)
);

const updateInfo = async (
    type: "benchmark" | "job",
    { key, value, title }: { key: string; value: any; title: string }
) => {
    if ($store.demo) {
        $snackbar.show($store.demoMessage);
        return;
    }

    if (type === "benchmark") {
        await $api.benchmarks.patch(props.benchmark.runNr, { [key]: value });
    } else if (type === "job") {
        await $api.jobs.patch(jobId.value, {
            variantName: value
        });
    }

    emit("refresh", jobId.value);

    $snackbar.show(`Updated ${title}`);
};
</script>
<style lang="scss" scoped>
.system-info-wrapper {
    margin-top: 10px;
    padding: 0 20px;
}
</style>
