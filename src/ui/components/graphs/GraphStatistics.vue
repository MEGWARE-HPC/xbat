<template>
    <v-data-table
        height="75vh"
        fixed-header
        :headers="headers"
        :items="tableItems"
        :items-per-page="-1"
        :no-data-text="
            state.filterMatchingNone
                ? 'No entries matching filters'
                : 'No entries'
        "
        hide-default-footer
        :groupBy="[
            {
                key: 'rawName',
                order: 'desc'
            }
        ]"
    >
        <template v-slot:top>
            <div class="d-flex justify-end pa-2">
                <v-btn
                    icon="$download"
                    size="small"
                    density="comfortable"
                    variant="outlined"
                    rounded="sm"
                    :disabled="!canExport"
                />
            </div>
        </template>
        <template v-slot:header.data-table-group>
            {{ `Metric (${storeGraph.graph.value?.traces?.[0]?.unit || ""})` }}
        </template>
        <template v-slot:item.tableName="{ item }">
            <span v-html="item.tableName"></span>
        </template>
    </v-data-table>
</template>
<script setup lang="ts">
const defaultHeaders = [
    { title: "Min", key: "statistics.min" },
    { title: "Max", key: "statistics.max" },
    { title: "Avg", key: "statistics.avg" },
    { title: "Sum", key: "statistics.sum" },
    { title: "Median", key: "statistics.median" },
    { title: "StdDev", key: "statistics.std" },
    { title: "Variance", key: "statistics.var" }
];

const { $graphStore } = useNuxtApp();

const props = defineProps<{
    graphId: string;
}>();

const state = reactive({
    filterMatchingNone: false
});

const storeGraph = $graphStore.useStoreGraph(props.graphId, "default");

const headers = computed(() => {
    const level = storeGraph.query.value?.level;

    return [
        ...((level != "job" && level != "node") ||
        storeGraph.query.value.jobIds.length > 1
            ? [{ title: "Trace", key: "tableName" }]
            : []),
        ...defaultHeaders
    ];
});

const tableItems = computed(() => {
    // TODO filterMatchingNone
    if (!storeGraph.graph.value || !storeGraph.graph.value?.traces?.length)
        return [];

    // keep visible and invisible traces to preserve metrics/groups in table
    const visibleTraces = storeGraph.graph.value.traces.filter(
        (x) => !x.auxiliary && x.visible !== "legendonly"
    );

    if (!visibleTraces.length) {
        state.filterMatchingNone = true;
        return [];
    }

    state.filterMatchingNone = false;
    return visibleTraces;
});

const canExport = computed(() => {
    return !!storeGraph.graph.value?.traces?.length;
});
</script>
