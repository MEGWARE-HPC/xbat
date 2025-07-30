<script lang="ts" setup>
const { graphPreferences } = usePreferences();

const hideInactiveOptions = [
    {
        title: "disable traces",
        subtitle:
            "inactive traces are disabled but shown in the legend and statistics",
        value: "disabled"
    },
    {
        title: "hide traces",
        subtitle: "inactive traces are hidden completely",
        value: "hidden"
    }
];
</script>
<template>
    <v-dialog eager :max-width="600">
        <template v-slot:activator="{ props: activatorProps }">
            <div v-bind="activatorProps">
                <slot></slot>
            </div>
        </template>
        <template v-slot:default="{ isActive }">
            <v-card>
                <v-card-title>Settings</v-card-title>
                <v-card-text>
                    <div>
                        <v-switch
                            label="Rangeslider on Graph"
                            :model-value="graphPreferences.rangeslider"
                            @update:model-value="
                                graphPreferences.rangeslider = $event || false;
                                $graphStore.setPreference(
                                    'rangeslider',
                                    $event || false
                                );
                            "
                        ></v-switch>
                        <v-switch
                            label="Show X-Axis Title"
                            :model-value="graphPreferences.xTitle"
                            @update:model-value="
                                $graphStore.setPreference(
                                    'xTitle',
                                    $event || false
                                )
                            "
                        ></v-switch>
                        <div class="d-flex">
                            <v-switch
                                :model-value="
                                    graphPreferences.hideInactive !== 'none'
                                "
                                @update:model-value="
                                    $graphStore.setPreference(
                                        'hideInactive',
                                        $event ? 'disabled' : 'none'
                                    )
                                "
                            >
                                <template #label>
                                    Hide inactive
                                    <v-tooltip
                                        text="Activate this option to automatically hide traces exclusively reporting zero-values"
                                        location="right"
                                    >
                                        <template v-slot:activator="{ props }">
                                            <v-icon
                                                v-bind="props"
                                                icon="$information"
                                                class="ml-3"
                                            ></v-icon>
                                        </template>
                                    </v-tooltip>
                                </template>
                            </v-switch>
                            <v-select
                                class="ml-5"
                                :model-value="
                                    graphPreferences.hideInactive == 'none'
                                        ? 'disabled'
                                        : graphPreferences.hideInactive
                                "
                                @update:model-value="
                                    graphPreferences.hideInactive = $event;
                                    $graphStore.setPreference(
                                        'hideInactive',
                                        $event
                                    );
                                "
                                style="max-width: 200px"
                                :disabled="
                                    graphPreferences.hideInactive == 'none'
                                "
                                :items="hideInactiveOptions"
                                item-props
                                hide-details
                            ></v-select>
                        </div>
                    </div>
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn variant="text" @click="isActive.value = false"
                        >close</v-btn
                    >
                </v-card-actions>
            </v-card>
        </template>
    </v-dialog>
</template>
