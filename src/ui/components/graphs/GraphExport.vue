<template>
    <div>
        <v-tabs v-model="state.tab" fixed-tabs>
            <v-tab v-for="tab in tabs" :value="tab">{{ tab }}</v-tab>
        </v-tabs>
        <div style="height: 75vh; overflow: auto">
            <v-window v-model="state.tab">
                <v-window-item value="json" class="mt-2"
                    ><Editor
                        readonly
                        :modelValue="exportJSON"
                        height="700"
                        language="json"
                    ></Editor
                ></v-window-item>
                <v-window-item value="csv" class="mt-2">
                    <div class="d-flex align-center justify-space-between">
                        <div class="font-italic">
                            {{ exportCSV.unit }}
                        </div>
                        <div>
                            <v-switch
                                v-show="exportCSV.isScaled"
                                v-model="state.exportUnscaled"
                                label="Remove Scaling"
                                hide-details
                            ></v-switch>
                        </div>
                    </div>
                    <Editor
                        readonly
                        :modelValue="exportCSV.value"
                        height="700"
                        no-wrap
                        language="csv"
                    ></Editor>
                </v-window-item>
                <v-window-item value="image" class="mt-2">
                    <v-row class="mt-5">
                        <v-col sm="12" md="3">
                            <v-number-input
                                v-model="state.imgHeight"
                                label="Height (px)"
                            ></v-number-input>
                        </v-col>
                        <v-col sm="12" md="3">
                            <v-number-input
                                v-model="state.imgWidth"
                                label="Width (px)"
                            ></v-number-input>
                        </v-col>
                        <v-col sm="12" md="3">
                            <v-select
                                :items="['PNG', 'SVG']"
                                v-model="state.imgFormat"
                                label="Format"
                            ></v-select>
                        </v-col>
                        <v-col sm="12" md="3">
                            <v-btn color="primary-light" @click="exportGraph"
                                >export</v-btn
                            >
                        </v-col>
                    </v-row>
                    <v-divider class="mt-1 mb-1"></v-divider>
                    <div>
                        <v-row>
                            <v-col sm="12" md="4"
                                ><v-row class="mt-5">
                                    <v-col sm="12" md="12">
                                        <v-text-field
                                            label="Title"
                                            v-model="state.title"
                                            hide-details
                                        ></v-text-field>
                                    </v-col>
                                    <template v-if="state.title">
                                        <v-col sm="12" md="12">
                                            <div class="d-flex">
                                                <v-slider
                                                    label="Title X-Pos."
                                                    v-model="state.titleX"
                                                    :max="1"
                                                    :min="0"
                                                    :step="0.05"
                                                    thumb-label
                                                    hide-details
                                                ></v-slider>
                                                <v-slider
                                                    label="Title Y-Pos."
                                                    v-model="state.titleY"
                                                    :max="1"
                                                    :min="0"
                                                    :step="0.05"
                                                    thumb-label
                                                    hide-details
                                                ></v-slider>
                                            </div>
                                        </v-col>
                                        <v-col sm="12" md="12" class="mb-5">
                                            <v-number-input
                                                label="Font Size Title"
                                                v-model="state.fontsizeTitle"
                                                hide-details
                                                :min="1"
                                                :max="100"
                                            ></v-number-input>
                                        </v-col>
                                    </template>
                                    <v-col sm="12" md="6">
                                        <v-text-field
                                            label="X-Title"
                                            v-model="state.xTitle"
                                            hide-details
                                        ></v-text-field>
                                    </v-col>
                                    <v-col sm="12" md="6" class="mb-5">
                                        <v-text-field
                                            label="Y-Title"
                                            v-model="state.yTitle"
                                            hide-details
                                        ></v-text-field>
                                    </v-col>
                                    <v-col sm="12" md="6">
                                        <v-number-input
                                            label="Font Size"
                                            v-model="state.fontsize"
                                            hide-details
                                            :min="1"
                                            :max="100"
                                        ></v-number-input>
                                    </v-col>
                                    <v-col sm="12" md="6">
                                        <v-number-input
                                            label="Trace Width"
                                            :min="1"
                                            :max="10"
                                            v-model="state.traceWidth"
                                            hide-details
                                        >
                                        </v-number-input>
                                    </v-col>
                                    <v-col sm="12" md="12">
                                        <v-select
                                            label="Legend Location"
                                            :items="[
                                                'right',
                                                'bottom',
                                                'inside'
                                            ]"
                                            v-model="state.legendLocation"
                                            hide-details
                                        >
                                        </v-select>
                                    </v-col>
                                    <v-col
                                        sm="12"
                                        md="6"
                                        v-if="state.legendLocation == 'inside'"
                                    >
                                        <v-slider
                                            label="Label X-Pos."
                                            v-model="state.legendLocationX"
                                            :max="1"
                                            :min="0"
                                            :step="0.05"
                                            thumb-label
                                            hide-details
                                        ></v-slider>
                                    </v-col>
                                    <v-col
                                        sm="12"
                                        md="6"
                                        v-if="state.legendLocation == 'inside'"
                                    >
                                        <v-slider
                                            label="Label Y-Pos."
                                            v-model="state.legendLocationY"
                                            :max="1"
                                            :min="0"
                                            :step="0.05"
                                            thumb-label
                                            hide-details
                                        ></v-slider>
                                    </v-col>
                                    <v-col sm="12" md="12">
                                        <v-switch
                                            class="ml-3"
                                            label="Disallow Line Breaks In Legend"
                                            hide-details
                                            v-model="state.disallowLineBreaks"
                                        ></v-switch>
                                    </v-col>
                                    <v-col
                                        sm="12"
                                        md="6"
                                        v-for="margin of margins"
                                    >
                                        <v-number-input
                                            :label="`Margin ${margin}`"
                                            :min="0"
                                            :max="500"
                                            :step="5"
                                            v-model="
                                                state.margin[
                                                    margin[0].toLowerCase()
                                                ]
                                            "
                                            hide-details
                                        ></v-number-input>
                                    </v-col>

                                    <v-col sm="12">
                                        <v-btn
                                            prepend-icon="$reset"
                                            variant="text"
                                            @click="resetGraphSettings"
                                            >reset settings</v-btn
                                        >
                                    </v-col>
                                </v-row></v-col
                            >
                            <v-col sm="12" md="8"
                                ><div class="preview">
                                    <img :src="graphImg" /></div
                            ></v-col>
                        </v-row>
                    </div>
                    <ReactiveGraph
                        :graphId="exportGraphId"
                        ref="exportGraphRef"
                        :graph="modifiedGraph"
                        :style="'display: none'"
                    ></ReactiveGraph>
                </v-window-item>
            </v-window>
        </div>
    </div>
</template>
<script setup>
import { download, range } from "~/utils/misc";
import { reactive, computed, ref, watch } from "vue";
import { useDebounceFn } from "@vueuse/core";
import { deepClone } from "~/utils/misc";
import { nanoid } from "nanoid";

const margins = ["Top", "Bottom", "Left", "Right"];

const { $graphStore } = useNuxtApp();

const props = defineProps({
    modelValue: { type: Boolean, default: false },
    graphId: {
        type: String,
        required: true
    },
    noJson: {
        type: Boolean,
        default: false
    },
    noCsv: {
        type: Boolean,
        default: false
    }
});

const exportGraphId = nanoid(6);

const storeGraph = $graphStore.useStoreGraph(props.graphId);
const exportStoreGraph = $graphStore.useStoreGraph(exportGraphId);

const state = reactive({
    tab: "image",
    unscaled: false,
    imgWidth: 1600,
    imgHeight: 800,
    imgFormat: "PNG",
    legendLocation: "right",
    legendLocationX: 0.9,
    legendLocationY: 0.9,
    traceWidth: 1,
    yTitle: "",
    xTitle: "Runtime [HH:MM:SS]",
    fontsize: 12,
    fontsizeTitle: 24,
    titleX: 0.5,
    titleY: 1,
    title: "",
    margin: {
        l: 0,
        r: 0,
        b: 0,
        t: 0,
        pad: 0
    },
    disallowLineBreaks: false
});

const emit = defineEmits(["update:modelValue", "export-image"]);
const exportGraphRef = ref(null);

const mounted = ref(false);

// TODO refactor (?)
const resetGraphSettings = () => {
    state.legendLocation = "right";
    state.legendLocationX = 0.9;
    state.legendLocationY = 0.9;
    state.traceWidth = 1;
    state.xTitle = "Runtime [HH:MM:SS]";
    state.fontsize = 12;
    state.fontsizeTitle = 24;
    state.titleX = 0.5;
    state.titleY = 1;
    state.title = "";
    state.disallowLineBreaks = false;

    if (storeGraph.graph.value) setByGraph(storeGraph.graph.value);
};

const tabs = computed(() => {
    let t = ["image"];

    if (!props.noCsv) t.push("csv");
    if (!props.noJson) t.push("json");

    return t;
});

const modifiedGraph = computed(() => {
    if (
        !storeGraph.graph.value ||
        !storeGraph.graph.value?.layout ||
        !storeGraph.graph.value.traces?.length ||
        // workaround as eager is not used for dialog and thus ReactiveGraph might not be mounted yet
        // and plotting of graph is triggered on invalid graph
        !exportGraphRef.value?.graphMounted
    ) {
        return {};
    }

    let g = deepClone(storeGraph.graph.value);

    if (state.legendLocation == "bottom") {
        g.layout.legend.orientation = "h";
    } else if (state.legendLocation == "inside") {
        g.layout.legend.x = state.legendLocationX;
        g.layout.legend.y = state.legendLocationY;
    }

    g.layout.font.size = state.fontsize;

    g.layout.xaxis.title = state.xTitle;
    g.layout.yaxis.title = state.yTitle;
    g.layout.title = {
        text: state.title,
        font: {
            family: "Source Code Pro",
            size: state.fontsizeTitle
        },
        x: state.titleX,
        y: state.titleY
    };

    g.layout.margin = state.margin;

    g.traces = g.traces.filter(
        (x) => x.visible != "legendonly" && x.visible != false
    );

    g.traces.forEach((t) => {
        t.line.width = t.line.width * state.traceWidth;
        t.line.color = t.line.color;
        if (state.disallowLineBreaks) t.name = t.displayName;
    });
    return g;
});

watch(modifiedGraph, (v) => {
    exportStoreGraph.graph.value = v;
});

const debounceGraphRender = useDebounceFn(async () => {
    if (!exportGraphRef.value || !mounted.value) return;
    graphImg.value = await exportGraphRef.value.getImageBase64(
        imgExportSettings.value
    );
}, 500);

const setByGraph = (v) => {
    if (v.layout?.yaxis?.title)
        state.yTitle =
            v.layout.yaxis?.title?.text || v.layout.yaxis?.title || "";

    if (v.layout?.margin)
        Object.keys(v.layout.margin).forEach((x) => {
            if (x in state.margin) state.margin[x] = v.layout.margin[x];
        });
    debounceGraphRender();
};

watch(
    storeGraph.graph,
    (v) => {
        if (!v) return;
        setByGraph(v);
    },
    {
        deep: true,
        immediate: true
    }
);

watch(
    [
        ...Object.keys(state).map((x) => () => state[x]),
        ...Object.keys(state.margin).map((x) => () => state.margin[x]),
        mounted
    ],
    () => {
        if (mounted.value) debounceGraphRender();
    }
);

const exportJSON = computed(() =>
    JSON.stringify(storeGraph.raw.value, null, 2)
);

const exportCSV = computed(() => {
    let headers = "jobId,metric,";
    let csv = "";
    let unit = null;
    let rawUnit = null;
    let maxEntries = 0;
    for (const [jobId, values] of Object.entries(storeGraph.raw.value)) {
        for (const trace of values.traces) {
            const lineEntries = [
                jobId,
                trace.name,
                ...trace[state.exportUnscaled ? "rawValues" : "values"]
            ];
            csv += lineEntries.join(",") + "\n";
            maxEntries = Math.max(maxEntries, lineEntries.length);
            if (!unit) {
                unit = trace.unit;
                rawUnit = trace.rawUnit;
            }
        }
    }
    return {
        value:
            headers +
            range(0, maxEntries)
                .map((x) => `interval ${x}`)
                .join(",") +
            "\n" +
            csv,
        unit: state.exportUnscaled ? rawUnit : unit,
        isScaled: rawUnit !== unit
    };
});

const graphImg = ref("");

const imgExportSettings = computed(() => {
    return {
        height: state.imgHeight,
        width: state.imgWidth,
        format: state.imgFormat.toLowerCase()
    };
});

const exportGraph = async () => {
    const query = $graphStore.getQuery(props.graphId);
    const name = `${Object.keys(storeGraph.raw.value).join("_")}_${
        query.group
    }_${query.metric}_${query.level}${
        query.level != "job" ? `_${query.node}` : ""
    }`;
    if (state.tab == "json") download(name + ".json", exportJSON.value);
    else if (state.tab == "csv") download(name + ".csv", exportCSV.value.value);
    else {
        graphImg.value = await exportGraphRef.value.getImageBase64(
            imgExportSettings.value
        );

        download(
            `${name}.${imgExportSettings.value.format}`,
            graphImg.value,
            "base64"
        );
    }
    emit("update:modelValue", false);
};

onMounted(() => {
    mounted.value = true;
});
</script>
<style lang="scss" scoped>
@use "~/assets/css/colors.scss" as *;

.preview {
    img {
        border: 1px solid $font-disabled;
        width: 90%;
        margin-left: 20px;
        object-fit: contain;
        margin-top: 30px;
    }
}
</style>
