<template>
    <div>
        <v-dialog
            :model-value="fullscreen"
            @update:model-value="fullscreen = false"
            transition="dialog-bottom-transition"
            fullscreen
            style="height: 100vh"
            scrollable
        >
            <v-card>
                <v-toolbar>
                    <v-btn icon="$arrowLeft" @click="fullscreen = false" />

                    <v-toolbar-title>{{ props.title }}</v-toolbar-title>
                </v-toolbar>
                <v-card-title>
                    <v-tabs v-model="tab" color="primary-light">
                        <v-tab value="graph">Graph</v-tab>
                        <v-tab value="statistics">Statistics</v-tab>
                        <v-tab value="export">Export</v-tab>
                    </v-tabs>
                </v-card-title>
                <v-card-text>
                    <v-tabs-window v-model="tab">
                        <v-tabs-window-item value="graph">
                            <v-row>
                                <v-col sm="12" md="8">
                                    <component
                                        :is="
                                            props.roofline
                                                ? RooflineGraph
                                                : Graph
                                        "
                                        v-bind="$attrs"
                                        :graph-id="graphId"
                                        v-model:fullscreen="fullscreen"
                                        :height="600"
                                        :nodes="props.nodes"
                                        flat
                                    />
                                </v-col>
                                <v-divider vertical style="height: 85vh" />
                                <v-col sm="12" md="4">
                                    <v-expansion-panels
                                        variant="accordion"
                                        elevation="0"
                                        v-model="panel"
                                    >
                                        <v-expansion-panel
                                            title="Traces"
                                            value="traces"
                                        >
                                            <v-expansion-panel-text>
                                                <GraphTraces
                                                    :graph-id="graphId"
                                                ></GraphTraces
                                            ></v-expansion-panel-text>
                                        </v-expansion-panel>
                                        <v-expansion-panel
                                            title="Styling"
                                            value="styling"
                                        >
                                            <v-expansion-panel-text>
                                                <GraphStyling
                                                    :graph-id="graphId"
                                                ></GraphStyling>
                                            </v-expansion-panel-text>
                                        </v-expansion-panel>
                                        <v-expansion-panel
                                            title="Modifiers"
                                            value="modifiers"
                                        >
                                            <v-expansion-panel-text>
                                                <GraphModifiers
                                                    :graph-id="graphId"
                                                ></GraphModifiers>
                                            </v-expansion-panel-text>
                                        </v-expansion-panel>
                                    </v-expansion-panels>
                                </v-col>
                            </v-row>
                        </v-tabs-window-item>
                        <v-window-item value="statistics">
                            <GraphStatistics
                                :graph-id="graphId"
                            ></GraphStatistics>
                        </v-window-item>
                        <v-window-item value="export">
                            <GraphExport
                                :graph-id="graphId"
                                :type="props.roofline ? 'roofline' : 'default'"
                            ></GraphExport>
                        </v-window-item>
                    </v-tabs-window>
                </v-card-text>
            </v-card>
        </v-dialog>
        <component
            :is="props.roofline ? RooflineGraph : Graph"
            v-bind="$attrs"
            v-model:fullscreen="fullscreen"
            :graph-id="graphId"
            :nodes="props.nodes"
        ></component>
    </div>
</template>
<script setup lang="ts">
import { nanoid } from "nanoid";
import type { Metrics } from "~/types/graph";
import type { NodeMap } from "~/repository/modules/nodes";
import RooflineGraph from "./RooflineGraph.vue";
import Graph from "./Graph.vue";

interface Props {
    title?: string;
    fullscreen?: boolean;
    metrics?: Metrics;
    nodes?: Record<string, NodeMap>;
    roofline?: boolean;
}

const { $graphStore } = useNuxtApp();

const graphId = nanoid(6);

const props = withDefaults(defineProps<Props>(), {
    title: "Modify Graph",
    nodes: () => ({}),
    roofline: false
});

const storeGraph = props.roofline
    ? $graphStore.useStoreGraph(graphId, "roofline")
    : $graphStore.useStoreGraph(graphId, "default");

const tab = ref("graph");
const fullscreen = ref(false);
const panel = ref("traces");

watch(
    () => props.fullscreen,
    (v) => {
        fullscreen.value = v;
    },
    {
        immediate: true
    }
);

watch(
    () => props.metrics,
    (v) => {
        if (v) storeGraph.metrics.value = v;
    },
    {
        immediate: true,
        deep: true
    }
);

onUnmounted(() => {
    $graphStore.unregisterGraph(graphId);
});
</script>
<style scoped lang="scss"></style>
