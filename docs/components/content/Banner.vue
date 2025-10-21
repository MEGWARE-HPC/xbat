<template>
    <v-card
        variant="tonal"
        :color="settings.color"
        class="mt-5 mb-5 banner"
        :class="[props.type]"
    >
        <v-card-text>
            <div class="d-flex align-center">
                <div class="font-weight-bold mr-3">
                    <v-icon size="large" :icon="settings.icon" />
                </div>
                <div class="banner-content">
                    <slot mdc-unwrap="p" />
                </div>
            </div>
        </v-card-text>
    </v-card>
</template>
<script setup lang="ts">
const props = defineProps({
    type: {
        type: String,
        default: "hint",
        validator: (v: string) => ["hint", "warning", "info"].includes(v)
    }
});

const types: Record<string, { icon: string; color: string }> = {
    hint: {
        icon: "$lightbulb",
        color: "primary-light"
    },
    warning: {
        icon: "$alert",
        color: "danger"
    },
    info: {
        icon: "$info",
        color: "info"
    }
};

const settings = computed(() => types[props.type]);
</script>
<style scoped lang="scss">
@use "~/assets/css/colors.scss" as *;

.banner {
    border-style: solid;
    border-left-width: 3px;
    &.hint {
        border-color: $primary-light;
    }
    &.warning {
        border-color: $danger;
    }
    &.info {
        border-color: $info;
    }
}
</style>
