<template>
    <v-dialog
        :modelValue="props.modelValue"
        @update:modelValue="emit('update:modelValue', false)"
        width="80%"
    >
        <v-card>
            <v-card-title>Compare</v-card-title>
            <v-card-text>
                <v-autocomplete
                    v-model="state.selected"
                    label="Jobs"
                    chips
                    closable-chips
                    multiple
                    clearable
                    :items="jobItems"
                    item-value="value"
                    persistent-hint
                    class="mb-2"
                    :hint="
                        state.missing.length
                            ? `Could not account for the following job(s): ${state.missing.join(
                                  ','
                              )}`
                            : ''
                    "
                >
                    <template v-slot:item="{ props, item }">
                        <v-list-item v-bind="props" :title="item.raw.title">
                            <template #prepend>
                                <v-icon
                                    :color="
                                        props.isSelected ? 'primary' : 'grey'
                                    "
                                    class="mr-2"
                                    size="small"
                                >
                                    {{
                                        props.isSelected
                                            ? "$checkboxMark"
                                            : "$checkboxBlank"
                                    }}
                                </v-icon>
                            </template>
                            <v-list-item-subtitle v-html="item.raw.subtitle" />
                            <template #append>
                                <div class="d-flex align-center gap-10">
                                    <JobVariableOverview
                                        :variables="item.raw.variables"
                                        v-if="
                                            Object.keys(item.raw.variables)
                                                .length
                                        "
                                    >
                                        <v-btn
                                            icon="$currency"
                                            size="x-small"
                                            variant="text"
                                        />
                                    </JobVariableOverview>
                                    <v-chip
                                        class="ml-2"
                                        size="small"
                                        variant="tonal"
                                        :color="item.raw.stateColor"
                                        >{{ item.raw.state }}
                                    </v-chip>
                                </div>
                            </template>
                        </v-list-item>
                    </template>
                </v-autocomplete>
                <div v-if="state.selected.length">
                    <v-switch
                        label="Synchronize Graphs"
                        v-model="state.synchronizeGraphs"
                        title="Synchronize X-Axis of Graphs"
                        density="compact"
                        v-if="state.graphCount > 1"
                    />
                    <GraphGroup :synchronize="state.synchronizeGraphs">
                        <template v-slot:default="{ relayout, relayoutData }">
                            <GraphWrapper
                                title="Comparison - Modify Graph"
                                :job-ids="state.selected"
                                :metrics="metrics"
                                default-level="job"
                                default-group="cpu"
                                default-metric="FLOPS"
                                @relayout="relayout"
                                :relayout-data="relayoutData"
                                comparison-mode
                                flat
                            />
                        </template>
                    </GraphGroup>
                    <div class="d-flex justify-center">
                        <v-btn
                            prepend-icon="$plus"
                            variant="text"
                            class="mt-3"
                            @click="state.graphCount += 1"
                            v-show="state.graphCount < 2"
                            >Add Graph</v-btn
                        >
                    </div>
                </div>
            </v-card-text>
            <v-card-actions>
                <v-spacer />
                <v-btn variant="text" @click="emit('update:modelValue', false)"
                    >Close</v-btn
                >
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>
<script setup>
const emit = defineEmits(["update:modelValue"]);
const { $api } = useNuxtApp();

const state = reactive({
    selected: [],
    noData: false,
    nodesWithMeasurements: {},
    graphCount: 1,
    synchronizeGraphs: true,
    missing: [] // selected jobs that could not be accounted for during metric intersection
});

const metrics = ref({});
const benchmarks = ref([]);
const jobs = ref([]);
const { jobItems } = useJobs({ benchmarks, jobs, hideUnfinished: true });

const props = defineProps({
    modelValue: {
        type: Boolean,
        default: false
    },
    benchmarks: {
        type: Array,
        default: () => []
    },
    jobs: {
        type: Object,
        default: () => []
    },
    selected: {
        type: Array,
        default: () => []
    }
});

watch(
    [() => props.benchmarks, () => props.jobs],
    ([b, j]) => {
        if (b.length) benchmarks.value = b;
        if (j.length) jobs.value = j;
    },
    { immediate: true, deep: true }
);

watch(
    () => props.modelValue,
    async (visible) => {
        if (!visible) return;
        if (!props.benchmarks.length)
            benchmarks.value = (await $api.benchmarks.get())?.data || [];

        if (!props.jobs?.length)
            jobs.value = (await $api.jobs.get())?.data || [];
    }
);

watch(
    () => props.selected,
    (v) => {
        state.selected = v;
    },
    { immediate: true }
);

watch(
    [() => state.selected, () => props.modelValue],

    async ([v, m]) => {
        if (!v.length || !m) return;

        const res = await $api.metrics.get(v, true);
        metrics.value = res.metrics;
        state.noData = !Object.keys(res.metrics).length;
        state.missing = res.missing || [];
    },
    {
        immediate: true
    }
);
</script>
