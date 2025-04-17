<template>
    <div>
        <v-card :elevation="props.flat ? 0 : undefined">
            <v-card-title>
                <v-row
                    density="compact"
                    class="mt-1 mb-1"
                    style="max-width: calc(100% - 30px)"
                >
                    <v-col md="6" sm="6">
                        <v-autocomplete
                            label="Jobs"
                            :items="filteredJobs"
                            v-model="form.jobIds"
                            chips
                            closable-chips
                            multiple
                            persistent-hint
                            :hint="
                                nodeWarning
                                    ? 'Warning - jobs may not be comparable as they were executed on different nodes'
                                    : ''
                            "
                        >
                            <template #append-inner
                                ><v-btn
                                    size=""
                                    variant="plain"
                                    title="Enable comparison across benchmarks"
                                    :color="
                                        form.crossCompare ? 'primary-light' : ''
                                    "
                                    @click="
                                        form.crossCompare = !form.crossCompare
                                    "
                                    ><v-icon icon="$abtesting"></v-icon></v-btn
                            ></template>
                            <template v-slot:item="{ props, item }">
                                <v-list-item
                                    v-bind="props"
                                    :title="item.raw.title"
                                >
                                    <v-list-item-subtitle
                                        v-html="item.raw.subtitle"
                                    >
                                    </v-list-item-subtitle>
                                    <template #prepend
                                        ><v-checkbox-btn
                                            v-model="form.jobIds"
                                            :value="item.raw.value"
                                            class="mr-2"
                                        ></v-checkbox-btn> </template
                                ></v-list-item>
                            </template>
                        </v-autocomplete>
                    </v-col>
                    <v-col md="3" sm="6">
                        <v-autocomplete
                            label="Peak FLOPS"
                            hide-details
                            v-model="form.plotFlops"
                            :items="filteredFlopItems"
                            multiple
                            closable-chips
                            chips
                            class="mb-5"
                        ></v-autocomplete>
                    </v-col>
                    <v-col md="3" sm="12">
                        <v-autocomplete
                            label="Reference Node"
                            :items="nodeNames"
                            v-model="form.node"
                        ></v-autocomplete>
                    </v-col>
                </v-row>
                <!-- <v-btn
                    class="fullscreen"
                    icon="$fullscreen"
                    variant="text"
                    @click="emit('update:fullscreen', true)"
                    v-show="!props.fullscreen"
                ></v-btn> -->
                <div class="d-flex justify-start">
                    <div>
                        <v-checkbox
                            label="Job SP"
                            hide-details
                            v-model="form.plotSP"
                            class="mr-5"
                        ></v-checkbox>
                    </div>
                    <div>
                        <v-checkbox
                            label="Job DP"
                            hide-details
                            v-model="form.plotDP"
                        ></v-checkbox>
                    </div>
                    <div style="width: 200px" class="ml-5">
                        <v-select
                            label="Plot Jobs by"
                            v-model="form.plotBy"
                            :items="['peak', 'median', 'average']"
                            hide-details
                        ></v-select>
                    </div>
                </div>
            </v-card-title>
            <v-card-text>
                <ReactiveGraph
                    :style="`height: ${props.height}px;`"
                    :graphId="props.graphId"
                    ref="graphRef"
                    :graph="storeGraph.graph"
                    type="default"
                    @rendered="storeGraph.loading.value = false"
                    :loading="storeGraph.loading.value"
                    v-if="!storeGraph.noData.value"
                ></ReactiveGraph>
                <!-- graph already displays annotation stating the same issues but graph is never rendered when there are no metics - use this as fallback -->
                <div
                    v-else
                    class="d-flex justify-center no-data"
                    :style="`height: ${props.height}px;`"
                >
                    <div style="margin-top: 160px">no data available</div>
                </div>
            </v-card-text>
        </v-card>
    </div>
</template>
<script setup lang="ts">
import { useGraphRooflineForm } from "~/components/graphs/useGraphRooflineForm";
import type { Benchmark } from "~/repository/modules/benchmarks";
import type { JobShort } from "~/repository/modules/jobs";
import type { NodeMap } from "~/repository/modules/nodes";
import type { NodeBenchmarks } from "~/store/graph";

interface Props {
    graphId: string;
    jobIds?: number[];
    runNr: number;
    benchmarks: Benchmark[];
    jobs: JobShort[];
    fullscreen?: boolean;
    flat?: boolean;
    nodes?: Record<string, NodeMap>;
    height?: number;
}

const props = withDefaults(defineProps<Props>(), {
    benchmarks: () => [],
    jobIds: () => [],
    jobs: () => [],
    height: 400
});

const emit = defineEmits(["update:fullscreen"]);

const { $graphStore } = useNuxtApp();
const storeGraph = $graphStore.useStoreGraph(props.graphId, "roofline");

watch(
    () => props.nodes,
    (v) => {
        if (v) storeGraph.nodes.value = { ...v };
    },
    { immediate: true, deep: true }
);

const { nodeBenchmarks } = useNodes({
    jobs: toRef(() => props.jobs),
    currentJob: toRef(() => undefined)
});

watch(nodeBenchmarks, (v) => {
    storeGraph.benchmarks.value = v as NodeBenchmarks;
});

const {
    form,
    filteredJobs,
    nodeWarning,
    filteredFlopItems,
    // filteredMemitems,
    nodeNames,
    jobItems
} = useGraphRooflineForm({
    runNr: toRef(() => props.runNr),
    benchmarks: toRef(() => props.benchmarks),
    jobs: toRef(() => props.jobs),
    nodeBenchmarks: nodeBenchmarks
});

// TODO refactor as this will also trigger when changing crossCompare
watch(
    form,
    () => {
        storeGraph.query.value = deepClone(toRaw(form));
    },
    {
        deep: true,
        immediate: true
    }
);
</script>
<style lang="scss" scoped>
.fullscreen {
    position: absolute;
    right: 10px;
    top: 20px;
}
</style>
