<template>
    <div>
        <v-tooltip
            :location="props.location"
            :class="{ 'custom-tooltip': props.custom }"
        >
            <template v-slot:activator="{ props: tooltipProps }">
                <v-icon
                    :color="props.color"
                    v-bind="tooltipProps"
                    :icon="props.icon"
                    :size="props.size"
                >
                </v-icon>
            </template>
            <slot>{{ props.value || "" }}</slot>
        </v-tooltip>
    </div>
</template>

<script lang="ts" setup>
const props = withDefaults(
    defineProps<{
        value?: string;
        color?: string;
        size?: "x-small" | "small" | "default" | "large" | "x-large";
        icon?: string;
        location?: "top" | "bottom" | "left" | "right";
        custom?: boolean;
    }>(),
    {
        color: "primary-light",
        size: "default",
        icon: "$information",
        location: "top",
        custom: false
    }
);
</script>

<style lang="scss" scoped>
.custom-tooltip :deep(.v-overlay__content) {
    background-color: transparent;
}
</style>
