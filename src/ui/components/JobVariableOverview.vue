<template>
    <div class="d-flex align-center justify-center mt-1">
        <v-menu location="start" open-on-hover :close-on-content-click="false">
            <template v-slot:activator="{ props: slotProps }">
                <div v-bind="slotProps">
                    <slot>
                        <v-btn
                            size="small"
                            variant="text"
                            prepend-icon="$currency"
                            >Variables ({{
                                Object.keys(props.variables || {}).length
                            }})</v-btn
                        >
                    </slot>
                </div>
            </template>
            <v-card>
                <v-card-text>
                    <JobVariableOverviewTable
                        :variables="props.variables"
                    ></JobVariableOverviewTable>
                </v-card-text>
            </v-card>
        </v-menu>
    </div>
</template>
<script setup lang="ts">
const props = defineProps<{
    variables: Record<string, string>;
}>();
</script>
