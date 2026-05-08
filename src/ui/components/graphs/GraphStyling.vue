<template>
    <div>
        <div class="d-flex align-center gap-10">
            <v-select
                v-model="colorPalette"
                :items="colorItems"
                label="Color palette"
                hide-details
            >
                <template v-slot:item="{ props, item }">
                    <v-list-item v-bind="props" :title="item.raw.title">
                        <v-list-item-subtitle>
                            <span
                                v-for="color of item.raw.colors"
                                :style="`background-color: ${color}`"
                                class="color-tile"
                            ></span>
                        </v-list-item-subtitle>
                    </v-list-item>
                </template>
            </v-select>
            <v-btn
                icon="$saveMove"
                variant="text"
                size="small"
                title="Apply this color palette permanently to all graphs"
                @click="$graphStore.syncColorPalette(colorPalette)"
            />
        </div>
        <div class="d-flex align-center gap-10 mt-3">
            <v-switch
                v-model="showLegend"
                label="Show Legend"
                hide-details
            />
        </div>
    </div>
</template>
<script setup lang="ts">
import { colors } from "~/utils/colors";

const props = defineProps<{ graphId: string }>();

const { $graphStore } = useNuxtApp();

const storeGraph = $graphStore.useStoreGraph(props.graphId, "default");

const colorPalette = ref("");
const showLegend = ref(true);

watch(
    [colorPalette, showLegend],
    ([palette, legend]) => {
        storeGraph.styling.value = {
            ...storeGraph.styling.value,
            colorPalette: palette,
            showLegend: legend
        };
    },
    { immediate: false }
);

watchEffect(() => {
    const styling = storeGraph.styling.value || {};
    colorPalette.value = styling.colorPalette || "";
    showLegend.value = styling.showLegend ?? true;
});

const colorItems = computed(() =>
    Object.keys(colors).map((x) =>
        Object.assign({
            title: `${x} (${colors[x].length})`,
            value: x,
            colors: colors[x]
        })
    )
);
</script>
<style lang="scss" scoped>
@use "~/assets/css/colors.scss" as *;

.color-tile {
    display: inline-block;
    width: 10px;
    height: 10px;
}
</style>
