<template>
    <div class="d-flex justify-center">
        <v-btn
            :color="props.color"
            class="btn"
            :append-icon="props.icon"
            :href="props.href"
            :target="props.target"
            rel="noopener noreferrer"
            ><ContentSlot :use="$slots.default"
        /></v-btn>
    </div>
</template>
<script setup lang="ts">
const props = withDefaults(
    defineProps<{
        color?: string;
        icon?: string;
        href: string;
        target?: string;
    }>(),
    {
        color: "primary",
        href: "#",
        target: "_self"
    }
);
</script>
<style scoped lang="scss">
.btn {
    // since ContentSlot is passed as a <p>
    :deep(p) {
        margin: 0 !important;
    }
}
</style>
