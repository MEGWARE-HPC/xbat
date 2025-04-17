<template>
    <v-card class="mt-5 mb-5 codeblock" variant="tonal">
        <v-card-text style="overflow-y: auto; position: relative">
            <v-btn
                size="small"
                variant="plain"
                @click="copyToClipboard(content)"
                class="copy"
                title="Copy to Clipboard"
                ><v-icon icon="$copy"></v-icon
            ></v-btn>
            <ContentSlot :use="$slots.default" />
        </v-card-text>
    </v-card>
</template>
<script setup lang="ts">
import { copyToClipboard } from "@/helper";
import { useSlots } from "vue";
const slots = useSlots();

const content = computed(() => {
    if (!slots?.default) return "";
    return slots?.default()?.[0]?.ctx?.vnode?.el?.innerText || "";
});
</script>
<style lang="scss">
code {
    font-family: "Source Code Pro", monospace;
    white-space: pre-wrap !important;
}

.copy {
    position: absolute;
    top: 0px;
    right: 0;
}
</style>
