<template>
    <div class="d-flex justify-center">
        <v-btn
            :color="props.color"
            class="btn"
            :append-icon="props.icon"
            :href="props.href"
            ><ContentSlot :use="$slots.default"
        /></v-btn>
    </div>
</template>
<script setup lang="ts">
const props = withDefaults(
    defineProps<{ color: string; icon: string | undefined; href: string }>(),
    {
        color: "primary",
        href: "#"
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
