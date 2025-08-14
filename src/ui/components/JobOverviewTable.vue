<template>
    <v-data-table
        ref="tableRef"
        :headers="tableHeaders"
        hide-default-footer
        :items-per-page="-1"
        :items="tableItems"
    >
        <template v-slot:[`item.jobInfo.jobState`]="{ item }">
            <v-chip
                v-if="item.jobInfo && getJobState(item.jobInfo.jobState)"
                :color="getJobState(item.jobInfo.jobState).color"
                size="small"
            >
                {{ getJobState(item.jobInfo.jobState).value }}
            </v-chip>
            <v-chip v-else :color="getJobState(['unknown']).color" size="small"
                >unknown</v-chip
            >
        </template>
        <template v-slot:[`item.energy.cpu`]="{ item }">
            {{ item?.energy?.cpu ?? 0 }} kWh
        </template>
        <template v-slot:[`item.energy.gpu`]="{ item }">
            {{ item?.energy?.gpu ?? 0 }} kWh
        </template>
        <template v-slot:[`item.variables`]="{ item }">
            <JobVariableOverviewTable
                class="mt-1"
                v-bind="$attrs"
                v-if="Object.keys(item.variables).length"
                :variables="item.variables"
                hide-header
            ></JobVariableOverviewTable>
            <div v-else class="font-italic">None</div>
        </template>
    </v-data-table>
</template>
<script lang="ts" setup>
import { encodeBraceNotation } from "~/utils/braceNotation";
import { getJobState } from "~/utils/misc";
import type { JobShort, JobNode } from "~/repository/modules/jobs";
import type { EnergyMeasurement } from "~/repository/modules/measurements";
import { useIntersectionObserver } from "@vueuse/core";

const tableHeaders = [
    { title: "Job ID", value: "jobId" },
    { title: "Variant", value: "configuration.jobscript.variantName" },
    { title: "Runtime", value: "runtime" },
    { title: "Nodes", value: "nodes" },
    { title: "CPU Energy", value: "energy.cpu" },
    { title: "GPU Energy", value: "energy.gpu" },
    { title: "Variables", value: "variables" },
    { title: "Iteration", value: "iteration" },
    { title: "State", value: "jobInfo.jobState" }
];

const props = defineProps<{
    jobs: JobShort[];
}>();

const extractNodes = (nodes: Record<string, JobNode>) => {
    return Object.keys(nodes).length > 3
        ? encodeBraceNotation(Object.keys(nodes)).join(", ")
        : Object.keys(nodes).join(", ");
};

const jobIds = computed(() => {
    return props.jobs.map((job) => job.jobId);
});

const tableItems = computed(() => {
    return props.jobs.map((job) => ({
        ...job,
        nodes: extractNodes(job.nodes),
        energy: energyCache.value[job.jobId] || null
    }));
});

const energyCache: Ref<Record<number, EnergyMeasurement | null>> = ref({});
const tableRef = ref<HTMLElement | null>(null);
const hasBeenVisible = ref(false);

const { $api } = useNuxtApp();

// Use intersection observer to detect when component becomes visible
const { stop } = useIntersectionObserver(
    tableRef,
    ([{ isIntersecting }]: IntersectionObserverEntry[]) => {
        if (isIntersecting && !hasBeenVisible.value) {
            hasBeenVisible.value = true;
            // Fetch energy data for current jobs when first visible
            fetchEnergyData(jobIds.value);
            stop(); // Stop observing after first visibility
        }
    },
    {
        threshold: 0.1 // Trigger when 10% of component is visible
    }
);

const fetchEnergyData = async (jobIdsToFetch: number[]) => {
    const jobsToFetch = jobIdsToFetch.filter(
        (jobId) => !energyCache.value[jobId]
    );
    if (jobsToFetch.length === 0) return;

    const res = await Promise.all(
        jobsToFetch.map((jobId) => $api.measurements.getEnergy(jobId))
    );

    // Cache results
    jobsToFetch.forEach((jobId, index) => {
        energyCache.value[jobId] = res[index] || null;
    });
};

watch(jobIds, async (v) => {
    // Only fetch if component has been visible at least once and jobIds have changed
    if (hasBeenVisible.value) {
        await fetchEnergyData(v);
    }
});
</script>
