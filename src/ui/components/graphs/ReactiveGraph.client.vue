<template>
    <div :style="props.style" class="graph-wrapper">
        <v-overlay
            :model-value="true"
            v-if="props.loading"
            contained
            class="align-center justify-center"
        >
            <!-- use v-show on progress as overlay does not correctly hide its slot under on rapid loading state changes -->
            <v-progress-circular
                color="primary"
                v-if="props.loading"
                indeterminate
                size="32"
            ></v-progress-circular>
        </v-overlay>
        <div
            class="graph"
            :id="props.graphId"
            ref="graphRef"
            style="height: 100%"
        ></div>
        <Teleport v-if="mounted" to="body">
            <v-card
                ref="graphCardRef"
                class="hover-info"
                :class="{ visible: hoverVisible }"
                position="absolute"
                :style="`left: ${cursorX + hoverText.leftOffset}px; top: ${
                    cursorY + hoverText.topOffset + pageScrollOffset
                }px;`"
            >
                <div class="header font-italic">{{ hoverText.header }}</div>
                <div class="d-flex gap-20 mb-3">
                    <div
                        v-for="[idx, traces] of hoverText.traces.entries()"
                        class="d-flex justify-space-between"
                    >
                        <div>
                            <div
                                v-for="trace of traces"
                                class="d-flex align-center trace"
                            >
                                <div
                                    :class="
                                        trace?.fullData?.line
                                            ? 'trace-color'
                                            : 'trace-color-marker'
                                    "
                                    :style="`background-color: ${
                                        trace?.fullData?.line?.color ||
                                        trace?.fullData?.marker?.color ||
                                        '#fff'
                                    }`"
                                ></div>
                                <div
                                    class="trace-name flex-grow-1"
                                    :class="{
                                        'font-weight-bold':
                                            trace.curveNumber ===
                                            hoverText.highlight
                                    }"
                                >
                                    {{ trace.data.displayName }}
                                </div>
                                <div
                                    class="trace-value"
                                    :class="{
                                        'font-weight-bold':
                                            trace.curveNumber ===
                                            hoverText.highlight
                                    }"
                                >
                                    {{ roundTo(trace.y) }}
                                </div>
                            </div>
                        </div>
                        <v-divider
                            vertical
                            v-if="
                                hoverText.traces.length > 1 &&
                                idx != hoverText.traces.length - 1
                            "
                        ></v-divider>
                    </div>
                </div>
                <div
                    v-show="hoverText.truncated"
                    class="text-medium-emphasis text-caption font-italic"
                >
                    too many traces - legend is truncated
                </div>
            </v-card>
        </Teleport>
    </div>
</template>
<script setup lang="ts">
import { download, roundTo, deepEqual } from "~/utils/misc";
import { ArrayUtils } from "~/utils/array";
import { useMouse, useElementHover, useScroll } from "@vueuse/core";
import { LEGEND_WIDTH } from "@/components/graphs/useGraphBase";
import Plotly from "plotly.js-basic-dist-min";
import { Mutex } from "async-mutex";

const plotlySettings = {
    scrollZoom: true,
    displaylogo: false,
    responsive: true,
    doubleClick: "autosize",
    // disable resetScale2d as this resets layout to default settings,
    // select2d and lasso2d are not useful for our graphs and using them makes the current tab crash
    modeBarButtonsToRemove: ["resetScale2d", "select2d", "lasso2d"],
    hovermode: "closest"
};

const { $graphStore } = useNuxtApp();
const graphRef = ref<Plotly.PlotlyHTMLElement | null>(null);
const graphCardRef = ref<HTMLElement | null>(null);

const { y: pageScrollOffset } = useScroll(window);

const emit = defineEmits(["rendered", "relayout"]);

const props = defineProps<{
    graphId: string;
    type: "default" | "roofline";
    relayoutData?: Plotly.PlotRelayoutEvent;
    style?: string;
    loading?: boolean;
}>();

const storeGraph = $graphStore.useStoreGraph(props.graphId, props.type);

const extractor = (event: MouseEvent) =>
    event instanceof Touch ? null : [event.offsetX, event.offsetY];
const { x: cursorX, y: cursorY } = useMouse({
    target: graphRef,
    type: extractor
});

const CHUNK_SIZE = 16;
const CHUNKS = 4;

const mounted = ref(false);
const hoverVisible = ref(false);
const hoverText = reactive<{
    header: string;
    traces: Plotly.PlotData[];
    highlight: number | null;
    leftOffset: number;
    topOffset: number;
    truncated: boolean;
}>({
    header: "",
    traces: [],
    highlight: null,
    leftOffset: 0,
    topOffset: 0,
    truncated: false
});

const handlersRegistered = ref(false);

const currentGraph = ref({});

const getImageBase64 = async (properties: Plotly.ToImgopts) => {
    if (!graphRef.value) return "";
    return await Plotly.toImage(graphRef.value, properties);
};

const exportImg = async (name: string, properties: Plotly.ToImgopts) => {
    download(name, await getImageBase64(properties), "base64");
};

const graphHovered = useElementHover(graphRef);

watch(graphHovered, (v) => {
    if (v) return;
    hoverVisible.value = false;
});

const graphSize = ref<DOMRect | null>(null);

watch(cursorX, (x) => {
    if (!graphSize.value) return;
    if (x >= graphSize.value.width - LEGEND_WIDTH + 5) {
        hoverVisible.value = false;
    }
});

const registerHandlers = () => {
    if (!graphRef.value) return;

    graphRef.value.on(
        "plotly_relayout",
        (eventdata: Plotly.PlotRelayoutEvent) => {
            emit("relayout", eventdata);
        }
    );

    graphRef.value.on("plotly_hover", (data: Plotly.PlotHoverEvent) => {
        let traces = data.points.sort((a, b) => a.curveNumber - b.curveNumber);

        if (!graphCardRef.value || !graphRef.value || !traces.length) {
            hoverVisible.value = false;
            return;
        }

        // TODO updating graph size on each hover is a workaround for graphs within a dialog
        // as they would otherwise have incorrect position/size data
        // if (!graphSize.value) {
        updateGraphSize();
        //     if (!graphSize.value) return;
        // }

        const time = data.points.length ? data.points[0].x : "";
        const unit = traces[0].data.unit || "";

        hoverText.header = `${time} ${unit ? `[${unit}]` : ""}`;

        if (traces.length > CHUNKS * CHUNK_SIZE) {
            traces = traces.slice(0, CHUNKS * CHUNK_SIZE);
            hoverText.truncated = true;
        } else {
            hoverText.truncated = false;
        }

        hoverText.traces = [
            ...ArrayUtils.chunks(
                traces,
                traces.length > CHUNK_SIZE
                    ? Math.floor(traces.length / CHUNKS)
                    : CHUNK_SIZE
            )
        ];
        const hoverSize = graphCardRef.value.$el.getBoundingClientRect();

        if (!graphSize.value) return;

        const leftMargin = graphSize.value.left + 10;

        const clipsRight =
            cursorX.value + hoverSize.width + 10 >= window.innerWidth;
        // rather clip on right side than left side
        // check if hover would clip left if placed on right side
        const clipsLeftOnRightClip =
            cursorX.value - hoverSize.width + graphSize.value.left <= 0;

        hoverText.leftOffset =
            clipsRight && !clipsLeftOnRightClip ? -hoverSize.width : leftMargin;

        const clipsBottom =
            cursorY.value + graphSize.value.top + hoverSize.height >=
            window.innerHeight;

        hoverText.topOffset = graphSize.value.top + 10;

        if (clipsBottom) hoverText.topOffset -= hoverSize.height + 30;

        const y = data.yvals[0];
        let smallestDeviation = null;
        const accountableTraces = hoverText.traces.flat();
        if (accountableTraces.length > 1) {
            for (const p of hoverText.traces.flat()) {
                const deviation = Math.abs(p.y - y);
                if (
                    smallestDeviation === null ||
                    deviation < smallestDeviation
                ) {
                    smallestDeviation = deviation;
                    hoverText.highlight = p.curveNumber;
                }
            }
        } else hoverText.highlight = null;
        hoverVisible.value = true;
    });
};

const graphMounted = computed(() => !!graphRef.value);

const mutex = new Mutex();
watch(
    storeGraph.graph,
    async (g) => {
        // run in mutex as watcher may be triggered multiple times
        await mutex.runExclusive(async () => {
            // nextTick in case graphId is not yet registered as ref
            await nextTick(async () => {
                if (!g || !Object.keys(g).length || !graphRef.value) return;

                // prevent rerender of same graph
                if (deepEqual(g, currentGraph.value)) {
                    emit("rendered");
                    return;
                }

                await Plotly.react(
                    graphRef.value,
                    g.traces.filter((t) => t.visible != "hidden"),
                    g.layout as Partial<Plotly.Layout>,
                    plotlySettings as Partial<Plotly.Config>
                );

                // refrain from using any kind of hooks to register handlers due to differences in CSR/SSR on when the graph div is available
                if (!handlersRegistered.value) {
                    registerHandlers();
                    handlersRegistered.value = true;
                }

                currentGraph.value = deepClone(g);

                emit("rendered");
            });
        });
    },
    { immediate: true, deep: true }
);

watch(
    () => props.relayoutData,
    async (newLayout) => {
        if (!graphRef.value || !newLayout) return;

        // activating Plotlys pan/zoom triggers relayout
        if ("dragmode" in newLayout || "autosize" in newLayout) return;

        const xaxis = graphRef.value.layout.xaxis;

        // graph already using autorange
        if (xaxis.autorange && newLayout["xaxis.autorange"] && xaxis.autorange)
            return;

        // no change in x range
        if (
            "xaxis.range[0]" in newLayout &&
            "xaxis.range[1]" in newLayout &&
            xaxis.range?.[0] == newLayout["xaxis.range[0]"] &&
            xaxis.range?.[1] == newLayout["xaxis.range[1]"]
        )
            return;

        await Plotly.relayout(graphRef.value, newLayout);
        emit("rendered");
    },
    { deep: true }
);

const updateGraphSize = () => {
    if (!graphRef.value) return;
    graphSize.value = graphRef.value.getBoundingClientRect();
};

onMounted(() => {
    updateGraphSize();
    window.addEventListener("resize", updateGraphSize);
    mounted.value = true;
});

onUnmounted(() => {
    window.removeEventListener("resize", updateGraphSize);
});

defineExpose({ exportImg, getImageBase64, graphMounted });
</script>
<style lang="scss" scoped>
.hover-info {
    width: fixed;
    padding: 5px;
    position: absolute !important;
    pointer-events: none;
    opacity: 0;
    visibility: hidden;
    font-family: "Source Code Pro";
    font-size: 0.775rem;
    z-index: 9999;

    &.visible {
        opacity: 1;
        visibility: visible;
    }

    .trace {
        .trace-name {
            width: max-content;
        }
        .trace-value {
            margin-left: 30px;
            min-width: 60px;
        }
        .trace-color {
            margin-right: 5px;
            width: 15px;
            height: 2px;
            border-radius: 2px;
        }
        .trace-color-marker {
            margin-right: 10px;
            // margin-left: 5px;
            width: 5px;
            height: 5px;
            border-radius: 50%;
        }
    }
}
</style>
