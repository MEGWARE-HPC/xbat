<template>
    <v-data-table
        :headers="tableHeaders"
        hide-default-footer
        :items-per-page="-1"
        :items="props.jobs"
    >
        <template v-slot:[`item.nodes`]="{ item }">
            {{ extractNodes(item.nodes) }}
        </template>
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

const tableHeaders = [
    { title: "Job ID", value: "jobId" },
    { title: "Variant", value: "configuration.jobscript.variantName" },
    { title: "Iteration", value: "iteration" },
    { title: "Runtime", value: "runtime" },
    { title: "Nodes", value: "nodes" },
    { title: "Variables", value: "variables" },
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
</script>
