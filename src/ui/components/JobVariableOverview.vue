<template>
    <HoverMenu>
        <template #activator
            ><v-btn size="small" variant="text" prepend-icon="$currency"
                >Variables ({{
                    Object.keys(props.variables || {}).length
                }})</v-btn
            ></template
        >
        <JobVariableOverviewTable
            :variables="props.variables"
        ></JobVariableOverviewTable>
    </HoverMenu>
</template>
<script setup lang="ts">
const props = defineProps<{
    variables: Record<string, string>;
}>();
</script>
