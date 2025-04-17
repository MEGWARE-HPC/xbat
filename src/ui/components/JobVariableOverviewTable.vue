<template>
    <v-data-table
        style="margin-top: -10px"
        :items-per-page="-1"
        v-model:sortBy="variablesTableSortBy"
        :items="variableTableItems"
        :headers="variableTableHeaders"
        :hide-default-header="props.hideHeader"
        hide-default-footer
    >
    </v-data-table>
</template>
<script setup lang="ts">
const props = withDefaults(
    defineProps<{
        variables: Record<string, string>;
        hideHeader?: boolean;
    }>(),
    {
        hideHeader: false
    }
);

const variableTableHeaders = [
    { title: "Variable", value: "key", sortable: true },
    { title: "Value", value: "value", sortable: true }
];

const variablesTableSortBy = ref([{ key: "key", order: "asc" }]);

const variableTableItems = computed(() => {
    return Object.entries(props.variables || {}).map(([k, v]) => ({
        key: k,
        value: v
    }));
});
</script>
