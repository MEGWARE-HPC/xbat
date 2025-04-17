<template>
    <span class="headline-wrapper d-flex aligin-center">
        <div>
            <v-icon
                class="headline-link"
                :class="{ visible: hovered }"
                icon="$link"
                size="small"
            ></v-icon>
        </div>
        <div ref="contentRef">
            <ContentSlot :use="$slots.default" />
        </div>
    </span>
</template>
<script setup lang="ts">
import { useElementHover } from "@vueuse/core";

const contentRef = ref<HTMLElement | null>(null);
const hovered = useElementHover(contentRef);
</script>
<style scoped lang="scss">
@use "~/assets/css/colors.scss" as *;

.headline-wrapper {
    display: inline-block;
    position: relative;
    margin: 20px 0;

    .headline-link {
        color: $font-light;
        opacity: 0;
        position: absolute;
        left: -25px;
        top: 8px;
        &.visible {
            opacity: 1;
        }
    }
}
</style>
