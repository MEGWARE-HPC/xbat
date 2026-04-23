import { ref, onUnmounted } from "vue";
import type { Ref } from "vue";
import type { EChartsType } from "echarts/core";
import { roundTo } from "~/utils/misc";

export interface HoverSeriesItem {
    name: string;
    color: string;
    unit: string;
    y: (number | null)[];
}

export interface HoverDisplayConfig {
    bgColor: string;
    fontColor: string;
    /** Right grid margin in px (e.g. LEGEND_WIDTH or 60) */
    gridRight: number;
    /** Bottom grid margin in px */
    gridBottom: number;
    /** Left grid margin in px (default 60) */
    gridLeft?: number;
    /** Top grid margin in px (default 20) */
    gridTop?: number;
}

const ROWS_PER_COL = 10;
const MAX_COLS = 4;
const MAX_TOTAL = ROWS_PER_COL * MAX_COLS;
/** Below this count, items are shown in original legend order (no sort) */
const SORT_THRESHOLD = ROWS_PER_COL;

export function useChartHover(options: {
    getChart: () => EChartsType | null;
    chartRef: Ref<HTMLElement | null>;
    currentXData: Ref<string[]>;
    getLegendItems: () => Array<{ name: string; selected: boolean }>;
}) {
    const crosshairVRef = ref<HTMLElement | null>(null);
    const crosshairHRef = ref<HTMLElement | null>(null);
    const customTooltipRef = ref<HTMLElement | null>(null);

    let seriesData: HoverSeriesItem[] = [];
    let displayConfig: HoverDisplayConfig = {
        bgColor: "transparent",
        fontColor: "",
        gridRight: 60,
        gridBottom: 40,
        gridLeft: 60,
        gridTop: 20
    };

    let rafId: number | null = null;
    let lastX = 0;
    let lastY = 0;

    const buildTooltipHTML = (xIdx: number): string & { colCount?: number } => {
        const label = options.currentXData.value[xIdx] ?? "";
        const unit = seriesData[0]?.unit ?? "";
        const header = `${label}${unit ? ` [${unit}]` : ""}`;

        const selectedNames = new Set(
            options
                .getLegendItems()
                .filter((li) => li.selected)
                .map((li) => li.name)
        );

        const items = seriesData
            .filter((s) => selectedNames.has(s.name))
            .map((s) => ({ name: s.name, color: s.color, value: s.y[xIdx] }))
            .filter((s) => s.value != null);

        // When there are more items than we can show, drop traces with value === 0
        // (they add no information density when the chart is crowded)
        const filtered =
            items.length > MAX_TOTAL
                ? items.filter((s) => (s.value as number) !== 0)
                : items;

        // Sort by highest value descending when crowded; preserve legend order when ≤ SORT_THRESHOLD
        const sorted =
            filtered.length > SORT_THRESHOLD
                ? [...filtered].sort(
                      (a, b) => (b.value as number) - (a.value as number)
                  )
                : filtered;

        const shown = sorted.slice(0, MAX_TOTAL);
        const hiddenCount = sorted.length - shown.length;

        // Distribute into columns: fill down, then across
        const colCount = Math.min(
            MAX_COLS,
            Math.max(1, Math.ceil(shown.length / ROWS_PER_COL))
        );
        const rowCount = Math.ceil(shown.length / colCount);

        let html = `<div data-cols="${colCount}" style="font-style:italic;margin-bottom:5px;">${header}</div>`;

        if (shown.length > 0) {
            html += `<div style="display:grid;grid-template-columns:repeat(${colCount},auto);grid-auto-flow:column;grid-template-rows:repeat(${rowCount},auto);gap:0 14px;">`;
            for (const p of shown) {
                const valStr = String(roundTo(p.value as number));
                html += `<div style="display:flex;align-items:center;gap:4px;white-space:nowrap;">`;
                html += `<span style="flex-shrink:0;width:10px;height:2px;background:${p.color};border-radius:2px;display:inline-block;"></span>`;
                html += `<span style="overflow:hidden;text-overflow:ellipsis;max-width:120px;">${p.name}</span>`;
                html += `<span style="padding-left:8px;font-weight:500;">${valStr}</span>`;
                html += `</div>`;
            }
            html += `</div>`;
        }

        if (hiddenCount > 0) {
            html += `<div style="font-style:italic;font-size:0.7rem;color:gray;margin-top:3px;">…and ${hiddenCount} more</div>`;
        }

        return html;
    };

    const hideHover = () => {
        if (crosshairVRef.value) crosshairVRef.value.style.display = "none";
        if (crosshairHRef.value) crosshairHRef.value.style.display = "none";
        if (customTooltipRef.value)
            customTooltipRef.value.style.display = "none";
    };

    const updateHover = (offsetX: number, offsetY: number) => {
        const chart = options.getChart();
        if (!chart || !options.chartRef.value) return;
        const len = options.currentXData.value.length;
        if (!len) return;

        const canvasW = options.chartRef.value.clientWidth;
        const canvasH = options.chartRef.value.clientHeight;
        const gridL = displayConfig.gridLeft ?? 60;
        const gridR = canvasW - displayConfig.gridRight;
        const gridT = displayConfig.gridTop ?? 20;
        const gridB = canvasH - displayConfig.gridBottom;

        if (
            offsetX < gridL ||
            offsetX > gridR ||
            offsetY < gridT ||
            offsetY > gridB
        ) {
            hideHover();
            return;
        }

        const rawIdx = chart.convertFromPixel({ xAxisIndex: 0 }, offsetX);
        if (rawIdx == null) {
            hideHover();
            return;
        }
        const xIdx = Math.max(
            0,
            Math.min(len - 1, Math.round(rawIdx as number))
        );
        const snappedX = chart.convertToPixel(
            { xAxisIndex: 0 },
            xIdx
        ) as number;

        if (crosshairVRef.value) {
            crosshairVRef.value.style.display = "block";
            crosshairVRef.value.style.left = `${snappedX}px`;
            crosshairVRef.value.style.top = `${gridT}px`;
            crosshairVRef.value.style.height = `${gridB - gridT}px`;
        }

        if (crosshairHRef.value) {
            crosshairHRef.value.style.display = "block";
            crosshairHRef.value.style.top = `${offsetY}px`;
            crosshairHRef.value.style.left = `${gridL}px`;
            crosshairHRef.value.style.width = `${gridR - gridL}px`;
        }

        if (customTooltipRef.value) {
            const html = buildTooltipHTML(xIdx);
            // Read colCount from the data attribute embedded in the first child
            customTooltipRef.value.innerHTML = html;
            const colCount = parseInt(
                (customTooltipRef.value.firstElementChild as HTMLElement | null)
                    ?.dataset?.cols ?? "1",
                10
            );
            // ~160px per column + 12px padding each side; avoids horizontal scroll
            const COL_WIDTH = 160;
            customTooltipRef.value.style.width = `${colCount * COL_WIDTH + 24}px`;
            customTooltipRef.value.style.background =
                displayConfig.bgColor || "#1e1e1e";
            customTooltipRef.value.style.color =
                displayConfig.fontColor || "#ccc";
            customTooltipRef.value.style.display = "block";

            const rect = options.chartRef.value.getBoundingClientRect();
            const cx = rect.left + offsetX;
            const cy = rect.top + offsetY;
            const tipW =
                customTooltipRef.value.offsetWidth || colCount * COL_WIDTH + 24;
            const tipH = customTooltipRef.value.offsetHeight || 200;
            const left =
                cx + tipW + 20 > window.innerWidth ? cx - tipW - 15 : cx + 15;
            const top = Math.min(cy - 10, window.innerHeight - tipH - 10);
            customTooltipRef.value.style.left = `${left}px`;
            customTooltipRef.value.style.top = `${Math.max(10, top)}px`;
        }
    };

    const scheduleHover = (x: number, y: number) => {
        lastX = x;
        lastY = y;
        if (rafId !== null) return;
        rafId = requestAnimationFrame(() => {
            rafId = null;
            updateHover(lastX, lastY);
        });
    };

    const cancelHover = () => {
        if (rafId !== null) {
            cancelAnimationFrame(rafId);
            rafId = null;
        }
        hideHover();
    };

    const setSeriesData = (data: HoverSeriesItem[]) => {
        seriesData = data;
    };

    const setDisplayConfig = (cfg: HoverDisplayConfig) => {
        displayConfig = cfg;
    };

    onUnmounted(() => {
        cancelHover();
    });

    return {
        crosshairVRef,
        crosshairHRef,
        customTooltipRef,
        setSeriesData,
        setDisplayConfig,
        scheduleHover,
        cancelHover,
        hideHover
    };
}
