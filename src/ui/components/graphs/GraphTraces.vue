<template>
    <div>
        <v-data-table
            :headers="headers"
            :items="traces"
            class="trace-table"
            :groupBy="groupBy"
            item-value="name"
            fixed-header
            :items-per-page="-1"
            hide-default-footer
            style="max-height: 60vh; overflow: auto"
        >
            <template v-slot:header.data-table-group>
                <div>
                    Metric
                    {{ unit ? `[${unit}]` : "" }}
                </div>
            </template>
            <template v-slot:item.visible="{ item }">
                <v-checkbox-btn
                    v-model="settings.visible"
                    :value="item.uid"
                    :disabled="
                        settings.visible.length < 2 &&
                        settings.visible.includes(item.uid)
                    "
                    false-icon="$hide"
                    true-icon="$show"
                    title="Toggle Visibility"
                    :color="
                        settings.visible.includes(item.uid)
                            ? 'primary-light'
                            : ''
                    "
                ></v-checkbox-btn>
            </template>
            <template
                v-slot:group-header="{
                    item,
                    columns,
                    toggleGroup,
                    isGroupOpen
                }"
            >
                <tr>
                    <td :colspan="columns.length">
                        <div class="d-flex align-center gap-10 justfiy-start">
                            <div>
                                <v-checkbox-btn
                                    :model-value="
                                        metricGroupSelection[item.value].value
                                    "
                                    title="Hide/Show metric"
                                    color="primary-light"
                                    @update:model-value="
                                        updateGroup(item.value, $event)
                                    "
                                    :indeterminate="
                                        metricGroupSelection[item.value]
                                            .indeterminate
                                    "
                                ></v-checkbox-btn>
                            </div>
                            {{ item.value }}
                            <Tooltip
                                size="small"
                                v-if="traceDescriptions[item.value]"
                                >{{ traceDescriptions[item.value] }}</Tooltip
                            >
                            <VBtn
                                :icon="isGroupOpen(item) ? '$expand' : '$next'"
                                size="small"
                                variant="text"
                                @click="toggleGroup(item)"
                            ></VBtn>
                            <div
                                class="d-flex align-center gap-10"
                                style="margin-left: auto; margin-right: 40px"
                                v-if="statisticsEnabled"
                            >
                                <v-checkbox-btn
                                    v-model="settings.visibleStatistics"
                                    :value="item.value"
                                    title="Toggle Min/Max/Avg for this trace"
                                ></v-checkbox-btn>
                            </div>
                        </div>
                    </td>
                </tr>
            </template>
            <template v-slot:item.displayName="{ item }">
                <div class="d-flex align-center gap-10">
                    {{ item.displayName }}
                    <div class="name-edit">
                        <InlineEdit
                            title="Rename Trace"
                            hover-title="Rename Trace"
                            :placeholder="item.displayName"
                            :model-value="
                                overrides.traces[item.uid]?.name || ''
                            "
                            clearable
                            @update:model-value="setTraceName(item.uid, $event)"
                        >
                            <template #activator>
                                <v-btn
                                    size="x-small"
                                    title="Rename Variant"
                                    icon="$edit"
                                    variant="plain"
                                >
                                </v-btn>
                            </template>
                        </InlineEdit>
                    </div>

                    <Tooltip
                        size="small"
                        style="margin-left: auto"
                        v-if="
                            traceDescriptions[item.rawName] && !groupBy.length
                        "
                        >{{ traceDescriptions[item.rawName] }}</Tooltip
                    >
                </div>
            </template>
        </v-data-table>
        <div
            style="font-size: 0.875rem"
            v-if="storeGraph.query.value.jobIds.length > 1"
        >
            <div class="ml-4 mt-4 font-weight-bold">Rename Job Prefix</div>
            <v-list>
                <v-list-item v-for="jobId of storeGraph.query.value.jobIds">
                    <div class="d-flex gap-20 align-end">
                        {{ jobId }}
                        <v-icon icon="$arrowRight"></v-icon>
                        <v-text-field
                            class="prefix-input"
                            :placeholder="jobId.toString()"
                            variant="underlined"
                            hide-details
                            clearable
                            v-model="overrides.prefixes[jobId]"
                        ></v-text-field>
                    </div>
                </v-list-item>
            </v-list>
        </div>
    </div>
</template>
<script setup lang="ts">
import { useDebounceFn } from "@vueuse/core";
import type { GraphSettings, GraphOverrides } from "~/types/graph";
import { deepEqual } from "~/utils/misc";
import { extractNumber } from "~/utils/string";

const baseHeaders = [
    { title: "Visible", key: "visible", align: "start", sortable: false },
    { title: "Trace", key: "displayName", align: "start", sortable: false }
];

const props = defineProps<{
    graphId: string;
}>();

const { $graphStore } = useNuxtApp();
const storeGraph = $graphStore.useStoreGraph(props.graphId, "default");

const settings: Ref<GraphSettings> = ref({
    visible: [],
    visibleStatistics: [],
    prevVisibleTables: []
});

const statisticsEnabled = computed(() => {
    const level = storeGraph.query.value?.level;
    return level != "job" && level != "node" && level != "device";
});

const headers = computed(() => {
    return [
        ...baseHeaders,
        ...(statisticsEnabled.value
            ? [
                  {
                      title: "Min/Max/Avg",
                      key: "statisticsVisible",
                      align: "center",
                      sortable: false
                  }
              ]
            : [])
    ];
});

const debounceSettings = useDebounceFn(() => {
    storeGraph.settings.value = { ...settings.value };
    storeGraph.updateGraph();
}, 500);

const unit = computed(() => storeGraph.graph.value?.traces?.[0]?.unit || "");

const groupBy = computed(() => {
    const level = storeGraph.query.value?.level;
    if (
        storeGraph.query.value.jobIds.length > 1 ||
        (level !== "job" && level !== "node" && level !== "device")
    )
        return [
            {
                key: "rawName",
                order: "desc"
            }
        ];
    return [];
});

watchEffect(() => {
    if (deepEqual(settings.value, storeGraph.settings.value)) return;
    settings.value = { ...storeGraph.settings.value };
});

watch(
    () => settings.value,
    () => {
        debounceSettings();
    },
    { deep: true }
);

const traces = computed(() => {
    if (!storeGraph.graph.value || !storeGraph.graph.value?.traces?.length)
        return [];

    return storeGraph.graph.value.traces
        // .filter((t) => !t.auxiliary)
        .sort((a, b) => {
            if (
                ["job", "node", "device"].includes(storeGraph.query.value.level)
            )
                return 0;
            const aNr = extractNumber(a.tableName || "");
            const bNr = extractNumber(b.tableName || "");

            if (Number.isNaN(aNr) || Number.isNaN(bNr)) return 0;

            return aNr - bNr;
        });
});

const currentMetrics = computed(() => {
    return (
        storeGraph.metrics.value?.[storeGraph.query.value.group]?.[
            storeGraph.query.value.metric
        ]?.metrics || []
    );
});

const traceDescriptions = computed(() => {
    let descriptions: { [key: string]: string } = {};
    storeGraph.graph.value?.traces.forEach((trace) => {
        if (trace.table && trace.table in currentMetrics.value) {
            const metric = currentMetrics.value[trace.table];
            descriptions[trace.rawName] =
                typeof metric === "string" ? "" : metric.description || "";
        }
    });
    return descriptions;
});

const metricGroups = computed(() => {
    let groups: { [key: string]: string[] } = {};
    traces.value.forEach((trace) => {
        if (!(trace.rawName in groups)) groups[trace.rawName] = [];
        groups[trace.rawName].push(trace.uid);
    });
    return groups;
});

const metricGroupSelection = computed(() => {
    let groupValue: {
        [key: string]: { value: boolean; indeterminate: boolean };
    } = {};
    Object.keys(metricGroups.value).forEach((key) => {
        let visibleCnt = 0;
        metricGroups.value[key].forEach((trace) => {
            if (settings.value.visible.includes(trace)) visibleCnt++;
            groupValue[key] = {
                value: visibleCnt > 0,
                indeterminate:
                    visibleCnt > 0 &&
                    visibleCnt < metricGroups.value[key].length
            };
        });
    });
    return groupValue;
});

const updateGroup = (group: string, value: boolean) => {
    let visible = settings.value.visible;
    let visibleStatistics = settings.value.visibleStatistics;
    metricGroups.value[group].forEach((trace) => {
        if (value && !visible.includes(trace)) visible.push(trace);
        if (!value && visible.includes(trace))
            visible.splice(visible.indexOf(trace), 1);
        if (!value && visibleStatistics.includes(trace))
            visibleStatistics.splice(visibleStatistics.indexOf(trace), 1);
    });
    settings.value = { ...settings.value, visible };
};

const overrides: Ref<GraphOverrides> = ref({
    prefixes: {},
    traces: {}
});

const debounceOverride = useDebounceFn(() => {
    storeGraph.overrides.value = { ...overrides.value };
    storeGraph.updateGraph();
}, 500);

watchEffect(() => {
    if (deepEqual(overrides.value, storeGraph.overrides.value)) return;
    overrides.value = { ...storeGraph.overrides.value };
});

const setTraceName = (uid: string, value: string) => {
    if (!(uid in overrides.value.traces))
        overrides.value.traces[uid] = { name: "", color: "" };
    overrides.value.traces[uid].name = value;
};

watch(
    () => overrides.value,
    () => {
        debounceOverride();
    },
    { deep: true }
);
</script>
<style lang="scss" scoped>
.prefix-input {
    :deep(input) {
        font-size: 0.875rem;
    }
}

.trace-table {
    .name-edit {
        opacity: 0;
        visibility: hidden;
        display: inline-block;
    }
    :deep(tr) {
        &:hover {
            .name-edit {
                opacity: 1;
                visibility: visible;
            }
        }
    }
}
</style>
