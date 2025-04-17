import { operators } from "~/utils/misc";
import { decodeBraceNotation, isValidBrace } from "~/utils/braceNotation";
import { humanSizeFixed } from "~/utils/conversion";
import { colors } from "~/utils/colors";
import { ArrayUtils } from "~/utils/array";
import { extractNumber } from "~/utils/string";
import { useGraphBase } from "~/components/graphs/useGraphBase";
import type { Graph, Trace } from "~/types/graph";
import type { StoreGraphReturnDefault } from "~/store/graph";

const { allTitels: benchmarkTitles } = useNodeBenchmarks();

export const useGraph = () => {
    const { createLayout, createTrace, calculateTimestamps } = useGraphBase();

    const generateGraph = (graphId: string): Graph => {
        const { $graphStore } = useNuxtApp();

        const storeGraph = $graphStore.useStoreGraph(graphId, "default");

        const query = storeGraph.query.value;

        if (!Object.keys(query).length)
            return {
                traces: [],
                layout: createLayout({ dataCount: 0, noData: true })
            };

        const overrides = storeGraph.overrides.value;

        let all: {
            traces: Partial<Trace>[];
            dataCount: number;
            unit: string;
            traceCount: number;
        } = {
            traces: [],
            dataCount: 0,
            unit: "",
            traceCount: 0
        };

        for (const jobId of query.jobIds) {
            let prefix = query.jobIds.length > 1 ? `${jobId} ` : "";
            if (
                prefix &&
                jobId in overrides.prefixes &&
                overrides.prefixes[jobId]?.length
            )
                prefix = `${overrides.prefixes[jobId]} `;

            let { traces, dataCount, unit } = assembleGraph({
                storeGraph,
                jobId: jobId,
                prefix,
                traceCount: all.traceCount
            });
            all.traces.push(...traces);
            all.dataCount += dataCount;
            all.unit = unit;
            all.traceCount += traces.length;
        }

        // visible traces resets on group/metric/level change -> set all traces to visible initially
        if (!storeGraph.settings.value.visible.length) {
            const prevVisibleTables =
                storeGraph.settings.value.prevVisibleTables;

            const visibleTraces = all.traces
                .map((x) => x.uid)
                .filter((uid): uid is string => uid !== undefined);

            // preserve toggled traces when switching between levels
            const filteredVisibleTraces = prevVisibleTables.length
                ? visibleTraces.filter((uid) =>
                      prevVisibleTables.includes(uid.split("-")[0])
                  )
                : visibleTraces;

            storeGraph.settings.value = {
                visible: filteredVisibleTraces,
                visibleStatistics: [],
                prevVisibleTables: []
            };
            all.traces.forEach((x: Partial<Trace>) => {
                x.visible = x.uid && filteredVisibleTraces.includes(x.uid);
            });
        }

        const layout = createLayout({
            dataCount: Math.max(all.dataCount),
            yTitle: `${query.metric}${all.unit ? ` [${all.unit}]` : ""}`,
            xTitle: storeGraph.preferences.value.xTitle
                ? "Runtime [HH:MM:SS]"
                : undefined,
            autorange: all.unit != "%",
            rangeslider: storeGraph.preferences.value.rangeslider,
            noData: storeGraph.noData.value || !all.traces.length
        });

        // TODO fix ts
        return {
            traces: all.traces,
            layout: layout
        };
    };

    const assembleGraph = ({
        storeGraph,
        jobId,
        prefix = "",
        traceCount = 0
    }: {
        storeGraph: StoreGraphReturnDefault;
        jobId: number;
        prefix?: string;
        traceCount?: number;
    }) => {
        const { $graphStore } = useNuxtApp();

        const query = storeGraph.query.value;

        const result = $graphStore.getMeasurements({
            ...query,
            jobIds: [jobId]
        });
        const preferences = storeGraph.preferences.value;

        if (!result || !result?.traces?.length)
            return {
                traces: [],
                dataCount: 0,
                unit: ""
            };

        let measurements = result.traces;

        let traces = [];
        let dataCount = 0;
        let interval = 0;

        // assume same unit for all traces
        const unit = measurements[0]?.unit || "";

        const modifiers = storeGraph.modifiers.value;
        const settings = storeGraph.settings.value;
        const styling = storeGraph.styling.value;

        let filter = modifiers.filterRange;
        const filterRangeAvailable =
            !["job", "node", "device"].includes(query.level) && !query.deciles;

        if (filterRangeAvailable && filter && isValidBrace(filter)) {
            filter = decodeBraceNotation(filter).map((x: string) =>
                parseInt(x)
            );
            measurements = measurements.filter((x) => {
                const id = extractNumber(x.id);
                return !isNaN(id) && filter?.includes(id.toString());
            });
        }

        const palette =
            colors[styling.colorPalette ? styling.colorPalette : "D3"];
        const overrides = storeGraph.overrides.value;

        let xMax = 0;
        for (let [idx, metric] of measurements.entries()) {
            dataCount = metric.values.length;
            interval = metric.interval;

            const overrideName = overrides.traces?.[metric.uid]?.name || null;

            const metricName = prefix + (overrideName || metric.name);
            const metricRawName = metric.rawName;
            const values = metric.values;
            xMax = Math.max(values.length, xMax);

            let visible: string | boolean = settings.visible.length
                ? settings.visible?.includes(metric.uid)
                : true;

            if (visible && !query.deciles) {
                let notMatchingFilters = false;
                if (modifiers.filterBy) {
                    for (const idx in ["0", "1"]) {
                        const f = `filter${idx}`;
                        const o = `operator${idx}`;
                        if (
                            (modifiers[f] || modifiers[f] == 0) &&
                            modifiers[o]
                        ) {
                            if (
                                !operators[modifiers[o]](
                                    metric.statistics[
                                        modifiers.filterBy.toLowerCase()
                                    ],
                                    modifiers[f]
                                )
                            ) {
                                notMatchingFilters = true;
                                break;
                            }
                        }
                    }
                }
                const isZero = ArrayUtils.sum(values) == 0;

                if (
                    (isZero && preferences.hideInactive == "disabled") ||
                    notMatchingFilters
                )
                    visible = "legendonly";
                else if (isZero && preferences.hideInactive == "hidden")
                    visible = "hidden";
            }

            const id = `${metric.group} ${idx}`;
            const stacked = metric.stacked;

            // name to be displayed in table for trace
            let tableName = "";
            // Prefix does only occur with comparison (which only allows for job-level)
            if (prefix)
                tableName = `${prefix} <span class="font-italic">${metric.variant} [${metric.iteration}]</span>`;
            else if (metric.level != "job" && metric.level != "node")
                tableName = metric.id;

            let trace: Trace = createTrace({
                x: calculateTimestamps(metric.values.length, metric.interval),
                y: values,
                name: metricName,

                tableName: tableName,
                legendgroup: metric?.legend_group ?? id,
                visible: visible,
                rawName: metricRawName,
                table: metric.table,
                unit: unit,
                color: palette[traceCount % palette.length],
                uid: metric.uid
            });

            if (stacked) {
                trace.fill = idx == 0 ? "tozeroy" : "tonexty";
                trace.stackgroup = "one";
            }

            trace.statistics = metric.statistics;
            traceCount += 1;
            traces.push(trace);
        }

        for (const [metric, statistics] of Object.entries(result.statistics)) {
            if (!settings.visibleStatistics?.includes(metric)) continue;

            const legendgroup = `stats_${metric}`;
            const baseUid = `${metric}-${jobId}`;
            traces.push(
                createTrace({
                    name: `${metric} avg`,
                    y: statistics.values.avg,
                    interval,
                    legendgroup: legendgroup,
                    width: 3,
                    auxiliary: true,
                    color: palette[traceCount % palette.length],
                    uid: `${baseUid}-avg`
                }),
                createTrace({
                    name: `${metric} max`,
                    y: statistics.values.max,
                    interval,
                    legendgroup: legendgroup,
                    // fill: "tonexty",
                    width: 3,
                    auxiliary: true,
                    color: palette[(traceCount + 1) % palette.length],
                    uid: `${baseUid}-max`
                }),
                createTrace({
                    name: `${metric} min`,
                    y: statistics.values.min,
                    interval,
                    legendgroup: legendgroup,
                    // fill: "tonexty",
                    width: 3,
                    auxiliary: true,
                    color: palette[(traceCount + 2) % palette.length],
                    uid: `${baseUid}-min`
                })
            );
            traceCount += 3;
        }

        const nodes = storeGraph.nodes.value;

        if (modifiers.systemBenchmarks?.length) {
            modifiers.systemBenchmarks.forEach((benchmark) => {
                const nodeNames = Object.keys(nodes[query.jobIds[0]]);
                const node =
                    nodes[query.jobIds[0]]?.[
                        query.level == "job" ? nodeNames[0] : query.node
                    ];
                let peak = node?.benchmarks?.[benchmark];
                if (!node || !peak) return;

                peak = peak * modifiers.systemBenchmarksScalingFactor;

                if (query.level == "job") peak = peak * nodeNames.length;

                const isBandwidth = benchmark.includes("bandwidth");
                const baseUnit = unit.substring(
                    0,
                    unit.length - (isBandwidth ? "B/s".length : "FLOPS".length)
                );

                const uid = `${query.node}-peak-${benchmark}`;
                const paletteColor = palette[traceCount % palette.length];

                const scaledPeak = humanSizeFixed(peak, baseUnit);
                traces.push(
                    createTrace({
                        name: `Peak ${benchmarkTitles.value[benchmark]}`,
                        y: new Array(xMax).fill(scaledPeak),
                        interval,
                        legendgroup: "benchmarks",
                        width: 3,
                        auxiliary: true,
                        color: paletteColor,
                        uid: uid
                    })
                );
                traceCount += 1;
            });
        }

        return {
            traces,
            dataCount,
            unit
        };
    };

    return { generateGraph };
};
