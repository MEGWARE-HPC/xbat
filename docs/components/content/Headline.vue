<template>
    <span class="headline-wrapper d-flex align-center">
        <div>
            <a
                v-if="anchorId"
                class="headline-link"
                :class="{ visible: hovered }"
                :href="`#${anchorId}`"
                aria-label="Copy link to this section"
            >
                <v-icon icon="$link" size="small" />
            </a>
            <v-icon
                v-else
                class="headline-link"
                :class="{ visible: hovered }"
                icon="$link"
                size="small"
            />
        </div>

        <div ref="contentRef">
            <slot mdc-unwrap="p" />
        </div>
    </span>
</template>
<script setup lang="ts">
import { useElementHover } from "@vueuse/core";

const contentRef = ref<HTMLElement | null>(null);
const hovered = useElementHover(contentRef);
const anchorId = ref<string | null>(null);

onMounted(() => {
    const host = contentRef.value;
    if (!host) return;
    const heading = host.closest("h1,h2,h3,h4,h5,h6") as HTMLElement | null;
    anchorId.value = heading?.id || null;
});
</script>
<style scoped lang="scss">
@use "~/assets/css/colors.scss" as *;

.headline-wrapper {
    display: inline-flex;
    align-items: center;
    position: relative;
    margin: 20px 0;

    .headline-link {
        color: $font-light;
        opacity: 0;
        position: absolute;
        left: -25px;
        top: 8px;
        text-decoration: none;
        &.visible {
            opacity: 1;
        }
    }
}
</style>
