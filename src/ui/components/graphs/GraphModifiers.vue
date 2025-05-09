<template>
    <div>
        <div class="d-flex flex-column">
            <div class="d-flex align-center modifier-header mb-2">
                System Benchmarks
                <Tooltip class="ml-1" value="">
                    Display peak performance values (synthetic benchmarks) of
                    the hardware for reference.<br />
                    <span class="font-italic"
                        >(only for FLOPS and cache/memory bandwidth)</span
                    >
                </Tooltip>
            </div>
            <div class="d-flex gap-20 justify-space-between mb-4">
                <v-autocomplete
                    :label="`Peak ${
                        query.metric == 'Bandwidth' ? 'Bandwidth' : 'FLOPS'
                    }`"
                    v-model="state.modifiers.systemBenchmarks"
                    multiple
                    chips
                    clearable
                    :items="
                        query.metric == 'FLOPS'
                            ? flopItems
                            : query.group == 'memory'
                            ? dramItems
                            : cacheItems
                    "
                    hide-details
                    :list-props="{ maxWidth: '500px' }"
                    :disabled="!systemBenchmarksAvailable"
                >
                </v-autocomplete>
                <v-number-input
                    label="Scaling Factor"
                    v-model="state.modifiers.systemBenchmarksScalingFactor"
                    :min="0"
                    :max="1"
                    :step="0.05"
                    hide-details
                    :disabled="!systemBenchmarksAvailable"
                    v-if="query.level == 'job' || query.level == 'node'"
                >
                </v-number-input>
            </div>
            <div class="d-flex align-center modifier-header mb-2">
                Range Filter
                <Tooltip class="ml-1">
                    Specify range of threads/cores/numa-domains/sockets to be
                    accounted for.<br />
                    <span class="font-italic"
                        >(not available for device/node/job level)</span
                    >
                </Tooltip>
            </div>
            <div class="mb-4">
                <v-text-field
                    :label="`Filter ${
                        filterRangeAvailable ? `${query.level}s` : 'Range'
                    }`"
                    clearable
                    placeholder="e.g. 0-16,32-48"
                    prepend-inner-icon="$filter"
                    :disabled="!filterRangeAvailable"
                    hide-details
                    v-model="state.modifiers.filterRange"
                ></v-text-field>
            </div>
            <div class="d-flex align-center modifier-header mb-4">
                Statistics Filter
                <Tooltip
                    class="ml-1"
                    value="Filter traces based on statistic values"
                >
                    Filter traces based on statistic values.<br />
                    <span class="font-italic"
                        >(not available for device/node/job level)</span
                    >
                </Tooltip>
            </div>
            <div class="d-flex gap-20 justify-space-between mb-4">
                <v-select
                    prepend-inner-icon="$filterMultiple"
                    :min-width="200"
                    label="Filter By"
                    hide-details
                    :items="[
                        'Min',
                        'Max',
                        'Avg',
                        'Median',
                        'StdDev',
                        'Variance'
                    ]"
                    clearable
                    v-model="state.modifiers.filterBy"
                    :disabled="!filterByAvailable"
                ></v-select>
                <CompareTextField
                    placeholder="10"
                    defaultOperator="gt"
                    hide-details
                    v-model="state.modifiers.filter0"
                    @update:operator="state.modifiers.operator0 = $event"
                    :disabled="!state.modifiers.filterBy || !filterByAvailable"
                ></CompareTextField>
                <CompareTextField
                    v-model="state.modifiers.filter1"
                    hide-details
                    placeholder="20"
                    defaultOperator="lt"
                    @update:operator="state.modifiers.operator1 = $event"
                    :disabled="!state.modifiers.filterBy || !filterByAvailable"
                ></CompareTextField>
            </div>

            <div class="d-flex align-center modifier-header mb-2">
                Deciles
                <Tooltip class="ml-1">
                    Summarize data into ten equal parts, each representing 10%
                    of the total, to provide insight into the distribution of
                    values.<br />
                    <span class="font-italic"
                        >(only for thread/core level)</span
                    >
                </Tooltip>
            </div>
            <v-switch
                v-model="deciles"
                :disabled="!decilesAvailable"
                label="Use Deciles"
                class="ml-2"
            >
            </v-switch>
        </div>
    </div>
</template>
<script setup lang="ts">
import { useDebounceFn } from "@vueuse/core";
import type { GraphModifiers } from "~/types/graph";
import type { SystemInfo } from "~/repository/modules/nodes";

const props = defineProps<{
    graphId: string;
}>();

const { $graphStore } = useNuxtApp();

const storeGraph = $graphStore.useStoreGraph(props.graphId, "default");

const { flopItems, dramItems, cacheItems } = useNodeBenchmarks();

const state = reactive<{
    filterMatchingNone: boolean;
    modifiers: GraphModifiers;
    activeModifiers: string[];
}>({
    filterMatchingNone: false,
    modifiers: {
        filterRange: null,
        filterBy: null,
        filter0: undefined,
        operator0: null,
        filter1: undefined,
        operator1: null,
        systemBenchmarks: [],
        systemBenchmarksScalingFactor: 1
    },
    activeModifiers: []
});

const deciles = ref(false);
const query = computed(() => storeGraph.query.value);
const decilesAvailable = computed(
    () => query.value.level == "thread" || query.value.level == "core"
);

watchEffect(() => {
    if (!decilesAvailable.value) deciles.value = false;

    storeGraph.query.value = {
        ...storeGraph.query.value,
        deciles: decilesAvailable.value ? deciles.value : false
    };
});

const enableBenchmarks = computed(() => {
    return (
        query.value.level != "job" &&
        query.value.level != "device" &&
        (query.value.metric == "FLOPS" || query.value.metric == "Bandwidth")
    );
});

const modifiers = computed(() => [
    {
        title: "System Benchmarks",
        subtitle:
            "Display peak performance values (synthetic benchmarks) of the hardware for reference",
        hint: "node level or below",
        value: "peaks",
        disabled: query.value.level == "job" || !enableBenchmarks.value
    },
    {
        title: "Statistic Filters",
        subtitle: "Filter values based on statistic values",
        hint: "thread & core level only",
        value: "statistics",
        disabled: query.value.level != "thread" && query.value.level != "core"
    },
    {
        title: "Range Filter",
        subtitle: "Specify range of threads or cores to be accounted for",
        hint: "thread & core level only",
        value: "range",
        disabled: query.value.level != "thread" && query.value.level != "core"
    },
    {
        title: "Use Deciles",
        subtitle:
            "Summarize data into ten equal parts, each representing 10% of the total, to provide insight into the distribution of values",
        hint: "thread & core level only",
        value: "deciles",
        disabled: query.value.level != "thread" && query.value.level != "core"
    }
]);

const debounceModifiers = useDebounceFn(() => {
    storeGraph.modifiers.value = { ...state.modifiers };
}, 1000);

watch(
    Object.keys(state.modifiers).map(
        (key) => () => state.modifiers[key as keyof GraphModifiers]
    ),
    () => {
        debounceModifiers();
    },
    { deep: true }
);

const filterRangeAvailable = computed(() => {
    return (
        !["job", "node", "device"].includes(query.value.level) && !deciles.value
    );
});

const systemBenchmarksAvailable = computed(() => {
    return (
        query.value.metric == "FLOPS" ||
        (query.value.metric == "Bandwidth" &&
            (query.value.group == "memory" || query.value.group == "cache"))
    );
});

const filterByAvailable = computed(() => {
    return (
        query.value.level != "job" &&
        query.value.level != "node" &&
        query.value.level != "device"
    );
});

const currentNodeInfo = computed(() => {
    if (query.value.level === "job" || !query.value.node) return {};
    return (
        storeGraph.nodes.value?.[query.value.jobIds[0]]?.[query.value.node] ||
        {}
    );
});

const nodeLevelSettings = computed(() => {
    if (!Object.keys(currentNodeInfo.value).length) return {};
    const n = currentNodeInfo.value as SystemInfo;

    const sockets = parseInt(n.cpu["Socket(s)"]);
    const coresPerSocket = parseInt(n.cpu["Core(s) per socket"]);
    const threadsPerCore = parseInt(n.cpu["Thread(s) per core"]);
    return {
        thread: sockets * coresPerSocket * threadsPerCore,
        core: coresPerSocket * sockets,
        numa: parseInt(n.cpu["NUMA node(s)"]),
        socket: sockets
    };
});

watch(
    () => query.value.level,
    (v) => {
        if (v == "job" || v == "node") {
            state.modifiers.systemBenchmarksScalingFactor = 1;
            return;
        }

        const levelKey = v as keyof typeof nodeLevelSettings.value;

        if (nodeLevelSettings.value[levelKey] !== undefined) {
            state.modifiers.systemBenchmarksScalingFactor =
                1 / nodeLevelSettings.value[levelKey]!;
        } else {
            state.modifiers.systemBenchmarksScalingFactor = 1;
        }
    },
    {
        immediate: true
    }
);
</script>
<style lang="scss" scoped>
@use "~/assets/css/colors.scss" as *;

.modifier-hint {
    font-style: italic;
    font-size: 0.875rem;
    color: $font-disabled;
    margin-left: 5px;
}

.modifier-header {
    font-size: 0.925rem;
    color: $font-light;
}

.modifier-subheader {
    font-size: 0.825rem;
    color: $font-disabled;
}
</style>
