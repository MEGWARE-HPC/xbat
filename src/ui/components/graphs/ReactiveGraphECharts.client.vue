<template>
    <div :style="props.style" class="graph-wrapper" ref="wrapperRef">
        <v-overlay
            :model-value="true"
            v-if="props.loading"
            contained
            class="align-center justify-center"
        >
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
            ref="chartRef"
            style="height: 100%; width: 100%"
        ></div>
        <!-- Crosshair vertical line (custom, avoids ECharts axis-trigger overhead) -->
        <div ref="crosshairVRef" class="crosshair-v"></div>
        <!-- Crosshair horizontal line -->
        <div ref="crosshairHRef" class="crosshair-h"></div>
        <!-- Teleport tooltip to body so it escapes any parent stacking context -->
        <Teleport v-if="mounted" to="body">
            <div ref="customTooltipRef" class="custom-tooltip-box"></div>
        </Teleport>
        <div class="legend-scroll" v-if="legendItems.length">
            <div
                v-for="item in legendItems"
                :key="item.name"
                class="legend-item"
                :class="{ 'legend-item--hidden': !item.selected }"
                :title="item.name"
                @click="toggleLegendItem(item)"
            >
                <span
                    class="legend-swatch"
                    :style="{ backgroundColor: item.color }"
                ></span>
                <span class="legend-label">{{ item.name }}</span>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { Mutex } from "async-mutex";
import type { LineSeriesOption } from "echarts/charts";
import { LineChart } from "echarts/charts";
import type {
    DataZoomComponentOption,
    GridComponentOption,
    LegendComponentOption,
    TooltipComponentOption
} from "echarts/components";
import {
    DataZoomComponent,
    GraphicComponent,
    GridComponent,
    LegendComponent,
    ToolboxComponent,
    TooltipComponent
} from "echarts/components";
import type { ComposeOption, EChartsType } from "echarts/core";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { deepEqual, download } from "~/utils/misc";

echarts.use([
    LineChart,
    GridComponent,
    TooltipComponent,
    LegendComponent,
    DataZoomComponent,
    GraphicComponent,
    ToolboxComponent,
    CanvasRenderer
]);

type ECOption = ComposeOption<
    | LineSeriesOption
    | GridComponentOption
    | TooltipComponentOption
    | LegendComponentOption
    | DataZoomComponentOption
>;

import { LEGEND_WIDTH } from "@/components/graphs/useGraphBase";
import type { HoverSeriesItem } from "~/composables/useChartHover";
import { useChartHover } from "~/composables/useChartHover";
import type { Graph } from "~/types/graph";

const { $graphStore } = useNuxtApp();
const wrapperRef = ref<HTMLElement | null>(null);
const chartRef = ref<HTMLElement | null>(null);
const mounted = ref(false);
let chart: EChartsType | null = null;

const emit = defineEmits(["rendered", "relayout"]);

const props = defineProps<{
    graphId: string;
    type: "default" | "roofline";
    relayoutData?: Record<string, number | boolean | string>;
    style?: string;
    loading?: boolean;
}>();

const storeGraph =
    props.type === "roofline"
        ? $graphStore.useStoreGraph(props.graphId, "roofline")
        : $graphStore.useStoreGraph(props.graphId, "default");

// Track current x-axis data for zoom conversion
const currentXData = ref<string[]>([]);
// Track current zoom state to avoid relayout emit loops
const currentZoomStart = ref(0);
const currentZoomEnd = ref(100);
const mutex = new Mutex();
const currentGraph = ref<Graph | null>(null);

const {
    crosshairVRef,
    crosshairHRef,
    customTooltipRef,
    setSeriesData,
    setDisplayConfig,
    scheduleHover,
    cancelHover,
    hideHover
} = useChartHover({
    getChart: () => chart,
    chartRef,
    currentXData,
    getLegendItems: () => legendItems.value
});

interface LegendItem {
    name: string;
    color: string;
    selected: boolean;
    /** ECharts series id for targeted single-series updates */
    uid: string;
    /** Raw y data — stored so toggle-on can restore without a full setOption */
    yData: (number | null)[];
}
const legendItems = ref<LegendItem[]>([]);

const toggleLegendItem = (item: LegendItem) => {
    item.selected = !item.selected;
    // Targeted update by id: avoids re-processing all series on every legend click.
    chart?.setOption({
        series: [{ id: item.uid, data: item.selected ? item.yData : [] }]
    });
};

const graphMounted = computed(() => !!chartRef.value && !!chart);

const getImageBase64 = async (properties?: {
    type?: string;
    width?: number;
    height?: number;
    devicePixelRatio?: number;
}): Promise<string> => {
    if (!chart) return "";
    return chart.getDataURL({
        type: (properties?.type as "png" | "jpeg" | "svg") || "png",
        pixelRatio: properties?.devicePixelRatio || 2,
        excludeComponents: []
    });
};

const exportImg = async (
    name: string,
    properties?: { type?: string; width?: number; height?: number }
) => {
    download(name, await getImageBase64(properties), "base64");
};

// Convert graph data to ECharts option
const buildOption = (g: Graph): ECOption => {
    const t0 = performance.now();
    const layout = g.layout;
    const traces = g.traces.filter((t) => t.visible !== "hidden");

    const hasRangeslider = !!layout?.xaxis?.rangeslider;
    const showLegend = layout?.showlegend !== false;
    const yType = layout?.yaxis?.type === "log" ? "log" : "value";
    const xTitle = layout?.xaxis?.title?.text ?? "";
    const yTitle = layout?.yaxis?.title?.text ?? "";
    const bgColor = layout?.paper_bgcolor ?? "transparent";
    const fontColor = layout?.font?.color ?? "";
    const fontFamily = layout?.font?.family ?? "Source Code Pro";
    const noDataAnnotation = (layout?.annotations?.length ?? 0) > 0;

    // x-axis values from first trace with data
    const xData: string[] =
        (traces.find((t: any) => t.x?.length) as any)?.x ?? [];
    currentXData.value = xData;

    // Target ~7 visible tick labels (matching original nticks: 7).
    // interval=0 means show every label; interval=N skips N labels between each shown one.
    const TARGET_TICKS = 7;
    const labelInterval =
        xData.length > TARGET_TICKS
            ? Math.ceil(xData.length / TARGET_TICKS) - 1
            : 0;

    const right = showLegend ? LEGEND_WIDTH : 60;
    const bottom = hasRangeslider ? 60 : xTitle ? 60 : 40;

    // Store for custom hover handler
    setDisplayConfig({
        bgColor,
        fontColor,
        gridRight: right,
        gridBottom: bottom
    });
    const hoverSeriesData: HoverSeriesItem[] = traces.map((trace) => ({
        name: trace.displayName ?? trace.name,
        color: trace.line?.color || trace.marker?.color || "#aaa",
        unit: trace.unit ?? "",
        y: trace.y ?? []
    }));
    setSeriesData(hoverSeriesData);
    const series: LineSeriesOption[] = traces.map((trace) => ({
        // id lets ECharts match series by identity across setOption calls,
        // and enables toggleLegendItem to do a single-series update instead of a full rebuild.
        id: trace.uid ?? trace.displayName ?? trace.name,
        name: trace.displayName ?? trace.name,
        type: "line",
        // Skip rendering of legendonly data
        data: trace.visible === "legendonly" ? [] : trace.y,
        lineStyle: {
            color: trace.line?.color || undefined,
            width: trace.line?.width ?? 1
        },
        itemStyle: { color: trace.line?.color || undefined },
        // Disable emphasis so colors never change on hover
        emphasis: { disabled: true },
        symbol: "none",
        // Skip per-series event listener registration — hover is handled via ZRender
        silent: true,
        sampling: "lttb",
        areaStyle:
            trace.fill && trace.fill !== ""
                ? { opacity: 0.3, color: trace.line?.color || undefined }
                : undefined
    }));

    // Initial legend selections: hide traces that are "legendonly"
    const legendSelected: Record<string, boolean> = {};
    traces.forEach((trace) => {
        if (trace.visible === "legendonly") {
            legendSelected[trace.displayName ?? trace.name] = false;
        }
    });

    // Populate custom scrollable legend as a side-effect
    if (showLegend) {
        legendItems.value = traces.map((trace) => ({
            name: trace.displayName ?? trace.name,
            color: trace.line?.color || trace.marker?.color || "#aaa",
            selected: trace.visible !== "legendonly",
            uid: trace.uid ?? trace.displayName ?? trace.name ?? "",
            yData: (trace.y ?? []) as (number | null)[]
        }));
    } else {
        legendItems.value = [];
    }

    const noDataGraphic = noDataAnnotation
        ? [
              {
                  type: "text",
                  left: "center",
                  top: "middle",
                  style: {
                      text: "no data available or matching filters",
                      fontSize: 12,
                      fill: fontColor
                  }
              }
          ]
        : [];

    const option: ECOption = {
        // Disable animations — eliminates ECharts animation setup cost across all 336+ series
        animation: false,
        backgroundColor: bgColor,
        textStyle: { color: fontColor, fontFamily, fontSize: 12 },
        graphic: noDataGraphic,
        grid: {
            left: 60,
            right,
            bottom,
            top: 20,
            containLabel: false
        },
        xAxis: {
            type: "category",
            data: xData,
            name: xTitle || undefined,
            nameLocation: "middle",
            nameGap: 35,
            nameTextStyle: { color: fontColor, fontFamily },
            axisLine: { lineStyle: { color: fontColor } },
            axisTick: { show: false },
            axisLabel: {
                color: fontColor,
                fontFamily,
                hideOverlap: true,
                interval: labelInterval
            },
            splitLine: {
                show: true,
                lineStyle: { color: "rgba(128,128,128,0.15)" }
            }
        },
        yAxis: {
            type: yType,
            name: yTitle || undefined,
            nameLocation: "middle",
            nameGap: 40,
            nameRotate: 90,
            nameTextStyle: { color: fontColor, fontFamily },
            axisLabel: { color: fontColor, fontFamily },
            splitLine: {
                show: true,
                lineStyle: { color: "rgba(128,128,128,0.15)" }
            },
            minorSplitLine: { show: false }
        },
        // Legend is rendered as a custom HTML overlay for real scroll support.
        // Passing selected here so ECharts series visibility stays in sync.
        legend: { show: false, selected: legendSelected },
        toolbox: {
            // Must be show:true for the dataZoom feature to register.
            // Positioned off-canvas (CanvasRenderer clips at canvas bounds) so it's invisible.
            show: true,
            left: -9999,
            feature: {
                dataZoom: { show: true, yAxisIndex: false },
                restore: { show: false },
                saveAsImage: { show: false }
            }
        },
        // ECharts tooltip disabled — custom hover handler in registerHandlers does this instead
        tooltip: { show: false },
        dataZoom: hasRangeslider
            ? [
                  {
                      type: "slider",
                      xAxisIndex: 0,
                      bottom: 5,
                      height: 20,
                      start: currentZoomStart.value,
                      end: currentZoomEnd.value,
                      textStyle: { color: fontColor },
                      borderColor: "rgba(128,128,128,0.3)",
                      fillerColor: "rgba(128,128,128,0.15)"
                  },
                  {
                      type: "inside",
                      xAxisIndex: 0,
                      start: currentZoomStart.value,
                      end: currentZoomEnd.value
                  }
              ]
            : [
                  {
                      type: "inside",
                      xAxisIndex: 0,
                      start: currentZoomStart.value,
                      end: currentZoomEnd.value
                  }
              ],
        series
    };

    console.debug(
        `[xbat:perf] buildOption — ${g.traces.length} traces, ${(performance.now() - t0).toFixed(2)}ms`
    );
    return option;
};

const activateBoxZoom = () => {
    chart?.dispatchAction({
        type: "takeGlobalCursor",
        key: "dataZoomSelect",
        dataZoomSelectActive: true
    });
};

const registerHandlers = () => {
    if (!chart) return;

    // Re-activate box zoom after each zoom interaction (ECharts deactivates it automatically)
    chart.on("dataZoom", () => {
        if (!chart) return;
        const option = chart.getOption() as any;
        const zoom = option?.dataZoom?.[0];
        if (!zoom) return;
        const start: number = zoom.start ?? 0;
        const end: number = zoom.end ?? 100;

        // Avoid emitting if nothing changed
        if (start === currentZoomStart.value && end === currentZoomEnd.value)
            return;

        currentZoomStart.value = start;
        currentZoomEnd.value = end;

        const len = currentXData.value.length;
        if (!len) return;

        const startIdx = Math.round((start / 100) * (len - 1));
        const endIdx = Math.round((end / 100) * (len - 1));

        emit("relayout", {
            "xaxis.range[0]": startIdx,
            "xaxis.range[1]": endIdx
        });

        activateBoxZoom();
    });

    // Double-click resets zoom to full range
    chart.getZr().on("dblclick", () => {
        currentZoomStart.value = 0;
        currentZoomEnd.value = 100;
        chart?.dispatchAction({
            type: "dataZoom",
            dataZoomIndex: 0,
            start: 0,
            end: 100
        });
        emit("relayout", { "xaxis.autorange": true });
        activateBoxZoom();
    });

    // Custom hover: rAF-throttled ZRender mousemove → composable handles all logic
    chart.getZr().on("mousemove", (e: any) => {
        scheduleHover(e.offsetX, e.offsetY);
    });
    chart.getZr().on("globalout", () => {
        cancelHover();
    });
};

watch(
    storeGraph.graph,
    async (g) => {
        await mutex.runExclusive(async () => {
            await nextTick(async () => {
                if (!g || !Object.keys(g).length || !chartRef.value) return;

                if (deepEqual(g, currentGraph.value)) {
                    emit("rendered");
                    return;
                }

                const tWatch = performance.now();

                if (!chart) {
                    chart = echarts.init(chartRef.value);
                    registerHandlers();
                }

                const tBuild = performance.now();
                const option = buildOption(g as unknown as Graph);
                console.debug(
                    `[xbat:perf] buildOption (watcher): ${(performance.now() - tBuild).toFixed(2)}ms`
                );

                const tSet = performance.now();
                // Use replaceMerge for series so removed traces are cleaned up
                chart.setOption(option, { replaceMerge: ["series"] });
                console.debug(
                    `[xbat:perf] setOption: ${(performance.now() - tSet).toFixed(2)}ms`
                );

                // Activate box zoom after the next render frame so ECharts has fully processed setOption
                requestAnimationFrame(() => activateBoxZoom());

                currentGraph.value = g as unknown as Graph;
                console.debug(
                    `[xbat:perf] total render cycle: ${(performance.now() - tWatch).toFixed(2)}ms`
                );
                emit("rendered");
            });
        });
    },
    { immediate: true, deep: true }
);

// Sync zoom from sibling graphs via relayoutData prop
watch(
    () => props.relayoutData,
    (newLayout) => {
        if (!chart || !newLayout) return;

        if ("dragmode" in newLayout || "autosize" in newLayout) return;

        const len = currentXData.value.length;
        if (!len) return;

        if ("xaxis.autorange" in newLayout && newLayout["xaxis.autorange"]) {
            currentZoomStart.value = 0;
            currentZoomEnd.value = 100;
            chart.dispatchAction({
                type: "dataZoom",
                dataZoomIndex: 0,
                start: 0,
                end: 100
            });
            emit("rendered");
            return;
        }

        if ("xaxis.range[0]" in newLayout && "xaxis.range[1]" in newLayout) {
            const r0 = newLayout["xaxis.range[0]"] as number;
            const r1 = newLayout["xaxis.range[1]"] as number;
            const start = (r0 / (len - 1)) * 100;
            const end = (r1 / (len - 1)) * 100;

            if (
                start === currentZoomStart.value &&
                end === currentZoomEnd.value
            )
                return;

            currentZoomStart.value = start;
            currentZoomEnd.value = end;
            chart.dispatchAction({
                type: "dataZoom",
                dataZoomIndex: 0,
                start,
                end
            });
            emit("rendered");
        }
    },
    { deep: true }
);

const resizeObserver = ref<ResizeObserver | null>(null);

const handleResize = () => {
    chart?.resize();
};

onMounted(() => {
    mounted.value = true;
    // Window resize for overall layout changes
    window.addEventListener("resize", handleResize);
    // ResizeObserver on the wrapper for container-level resizes (dialogs, panels, etc.)
    if (wrapperRef.value) {
        resizeObserver.value = new ResizeObserver(handleResize);
        resizeObserver.value.observe(wrapperRef.value);
    }
});

onUnmounted(() => {
    window.removeEventListener("resize", handleResize);
    resizeObserver.value?.disconnect();
    // cancelHover + hideHover are handled by the composable's onUnmounted
    chart?.dispose();
    chart = null;
});

defineExpose({ exportImg, getImageBase64, graphMounted });
</script>

<style lang="scss" scoped>
.graph-wrapper {
    position: relative;

    .graph {
        width: 100%;
    }

    .crosshair-v {
        position: absolute;
        width: 0;
        border-left: 1px dashed rgba(150, 150, 150, 0.6);
        pointer-events: none;
        display: none;
    }

    .crosshair-h {
        position: absolute;
        height: 0;
        border-top: 1px dashed rgba(150, 150, 150, 0.6);
        pointer-events: none;
        display: none;
    }

    // Teleported to body — use :global so scoped attribute is not required
    :global(.custom-tooltip-box) {
        position: fixed;
        pointer-events: none;
        z-index: 9999;
        display: none;
        border: 1px solid rgba(128, 128, 128, 0.3);
        border-radius: 4px;
        font-family: "Source Code Pro", monospace;
        font-size: 0.775rem;
        padding: 4px 6px;
        overflow: hidden;
        // width is set dynamically by useChartHover based on column count
        scrollbar-width: thin;
        scrollbar-color: rgba(128, 128, 128, 0.35) transparent;
    }

    .legend-scroll {
        position: absolute;
        right: 0;
        top: 20px;
        bottom: 20px;
        width: 170px; // LEGEND_WIDTH - 10
        overflow-y: auto;
        overflow-x: hidden;
        font-family: "Source Code Pro", monospace;
        font-size: 11px;

        // thin scrollbar
        &::-webkit-scrollbar {
            width: 4px;
        }
        &::-webkit-scrollbar-track {
            background: transparent;
        }
        &::-webkit-scrollbar-thumb {
            background: rgba(128, 128, 128, 0.35);
            border-radius: 2px;
        }
        scrollbar-width: thin;
        scrollbar-color: rgba(128, 128, 128, 0.35) transparent;

        .legend-item {
            display: flex;
            align-items: center;
            gap: 5px;
            padding: 2px 2px 2px 0;
            cursor: pointer;
            user-select: none;
            opacity: 1;
            transition: opacity 0.15s;

            &:hover {
                opacity: 0.75;
            }

            &--hidden {
                opacity: 0.35;
            }

            .legend-swatch {
                flex-shrink: 0;
                width: 15px;
                height: 2px;
                border-radius: 2px;
            }

            .legend-label {
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                min-width: 0;
            }
        }
    }
}
</style>
