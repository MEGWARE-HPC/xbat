<template>
    <div class="relative">
        <v-card
            class="card"
            :class="{ rendered: !storeGraph.loading.value }"
            :elevation="props.flat ? 0 : undefined"
        >
            <v-card-title style="position: relative">
                <v-row
                    density="compact"
                    class="mt-1"
                    style="max-width: calc(100% - 30px)"
                >
                    <v-col md="3" sm="6">
                        <v-autocomplete
                            v-model="form.group"
                            label="Type"
                            no-data-text="No types available"
                            :items="metricGroups"
                            hide-details
                            :disabled="
                                storeGraph.loading.value || !metricGroups.length
                            "
                        >
                        </v-autocomplete>
                    </v-col>
                    <v-col md="4" sm="6">
                        <v-autocomplete
                            v-model="form.metric"
                            label="Metric"
                            no-data-text="No metrics available"
                            :items="metricItems"
                            hide-details
                            :disabled="
                                storeGraph.loading.value || !metricItems.length
                            "
                        >
                            <template v-slot:item="{ props, item }">
                                <v-list-item
                                    v-bind="props"
                                    :title="item.raw.title"
                                    :subtitle="item.raw.description || ''"
                                >
                                    <template #append>
                                        <v-btn
                                            v-if="item.raw.url"
                                            :href="item.raw.url"
                                            target="_blank"
                                            title="Visit documentation for this metric"
                                            icon="$openInNew"
                                            size="x-small"
                                            variant="plain"
                                            class="ml-2 hover-only"
                                        >
                                        </v-btn>
                                    </template>
                                </v-list-item>
                            </template>
                        </v-autocomplete>
                    </v-col>
                    <v-col md="2" sm="6">
                        <v-autocomplete
                            v-model="form.level"
                            label="Level"
                            :disabled="
                                !form.metric ||
                                storeGraph.loading.value ||
                                !metricLevels.length ||
                                props.comparisonMode
                            "
                            :items="metricLevels"
                            hide-details
                        >
                        </v-autocomplete>
                    </v-col>
                    <v-col md="3" sm="6">
                        <v-autocomplete
                            v-show="form.level !== 'job'"
                            v-model="form.node"
                            label="Node"
                            no-data-text="No nodes available"
                            :items="nodeNames"
                            auto-select-first
                            hide-details
                            :disabled="
                                storeGraph.loading.value ||
                                !nodeNames?.length ||
                                !multiNode
                            "
                        >
                        </v-autocomplete>
                    </v-col>
                </v-row>
                <v-btn
                    class="fullscreen"
                    icon="$fullscreen"
                    variant="text"
                    @click="emit('update:fullscreen', true)"
                    v-show="!props.fullscreen"
                ></v-btn>
            </v-card-title>
            <v-card-text>
                <ReactiveGraph
                    :style="`height: ${props.height}px;`"
                    :graphId="props.graphId"
                    ref="graphRef"
                    :graph="storeGraph.graph"
                    @relayout="emit('relayout', $event)"
                    type="default"
                    :relayoutData="props.relayoutData"
                    @rendered="storeGraph.loading.value = false"
                    :loading="storeGraph.loading.value"
                    v-if="
                        Object.keys(metrics.value || {}).length || !props.noData
                    "
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
import { useGraphForm } from "~/components/graphs/useGraphForm";
import type { NodeMap } from "~/repository/modules/nodes";
import type { GraphLevel } from "~/types/graph";

const { $graphStore } = useNuxtApp();
const graphRef = ref(null);

type RelayoutData = {
    [key: string]: number;
};

interface Props {
    graphId: string;
    jobIds?: number[];
    nodes?: Record<string, NodeMap>;
    relayoutData?: RelayoutData;
    height?: number;
    noData?: boolean;
    defaultGroup?: string;
    defaultMetric?: string;
    defaultLevel?: string;
    flat?: boolean;
    fullscreen?: boolean;
    comparisonMode?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
    jobIds: () => [] as number[],
    nodes: () => ({}),
    relayoutData: () => ({}),
    height: 360,
    noData: false,
    defaultGroup: "",
    defaultMetric: "",
    defaultLevel: "",
    flat: false,
    fullscreen: false,
    comparisonMode: false
});

const emit = defineEmits(["update:fullscreen", "relayout"]);

const storeGraph = $graphStore.useStoreGraph(props.graphId, "default");
const metrics = computed(() => storeGraph.metrics.value);
const theme = useCookie("xbat_theme");

const { form, metricGroups, metricLevels, metricItems } = useGraphForm(metrics);

watch(
    [
        () => props.defaultGroup,
        () => props.defaultMetric,
        () => props.defaultLevel
    ],
    () => {
        // do not set defaults if fullscreen or group/metric/level is already set to prevent overwrite
        if (props.fullscreen || form.group || form.metric || form.level) return;

        form.group = props.defaultGroup;
        form.metric = props.defaultMetric;
        form.level = props.defaultLevel;
    },
    { immediate: true }
);

const nodeNames = computed(() =>
    props.jobIds.length ? Object.keys(props.nodes[props.jobIds[0]] || {}) : []
);

watch(
    [() => props.jobIds, ...Object.keys(form).map((x) => () => form[x])],
    () => {
        if (!props.graphId || !form.group || !form.metric || !form.level)
            return;

        if (
            metrics.value?.[form.group] &&
            !(form.metric in metrics.value[form.group])
        )
            return;

        const q = $graphStore.createQuery(
            props.jobIds,
            form.group,
            form.metric,
            form.level as GraphLevel,
            form.node || ""
        );

        if (Object.keys(q).length) storeGraph.query.value = q;
    },
    { immediate: true }
);

watchEffect(() => {
    form.group = storeGraph.query.value.group || null;
    form.metric = storeGraph.query.value.metric || null;
    form.level = storeGraph.query.value.level || null;
    form.node = storeGraph.query.value.node || null;
});

const multiNode = computed(
    () => nodeNames.value.length > 1 && form.level != "job"
);

watchEffect(() => {
    if (nodeNames.value.length && !form.node) form.node = nodeNames.value[0];
});

watch(
    () => props.nodes,
    (v) => {
        if (v) storeGraph.nodes.value = { ...v };
    },
    { immediate: true, deep: true }
);

watchEffect(() => {
    if (props.comparisonMode) form.level = "job";
});

// use delay for updating graph colors as useGraph:getColors may otherwise still return old colors
watch(
    theme,
    () => {
        setTimeout(() => {
            storeGraph.updateGraph();
        }, 500);
    },
    { deep: true }
);

const unsubscribe = ref<(() => void) | null>(null);

onMounted(() => {
    unsubscribe.value = $graphStore.cacheClearEvent.on(
        async () => await storeGraph.updateData(true)
    );
});

onUnmounted(() => {
    if (unsubscribe.value !== null) unsubscribe.value();
});
</script>

<style lang="scss" scoped>
@use "~/assets/css/colors.scss" as *;

.statistic-toggle {
    margin-top: 4px !important;
}

.metric-description {
    font-size: 0.75rem;
    color: $font-light;
}

.hint {
    width: 100%;
    white-space: normal;
    color: $font-light;
}

.no-data {
    font-size: 12px;
    color: $font-light;
    font-family: "Source Code Pro";
}

.card {
    // padding is provided by graph
    :deep(.v-card-text) {
        padding: 0 0 10px 0 !important;
    }
    :deep(.v-card-title) {
        padding-top: 0px !important;
    }

    &.rendered {
        overflow: visible;
    }
}

.fullscreen {
    position: absolute;
    right: 10px;
    top: 10px;
}
</style>
