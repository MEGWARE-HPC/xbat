import { operators } from "~/utils/misc";
import { decodeBraceNotation, isValidBrace } from "~/utils/braceNotation";
import { humanSizeFixed, CONVERSION_SIZES } from "~/utils/conversion";
import { colors } from "~/utils/colors";
import { ArrayUtils } from "~/utils/array";
import { extractNumber } from "~/utils/string";
import { useGraphBase } from "~/components/graphs/useGraphBase";
import type { Graph, Trace } from "~/types/graph";
import type { StoreGraphReturnDefault } from "~/store/graph";

const { allTitels: benchmarkTitles } = useNodeBenchmarks();

const parseGeneralUnit = (unit: string) => {
    const match = unit.match(/^([KMGTP]?)([a-zA-Z\/]+)$/);
    if (!match) return { prefix: "", base: unit, index: 0 };
    const [, prefix, base] = match;
    return {
        prefix,
        base,
        index: CONVERSION_SIZES.indexOf(prefix.toUpperCase())
    };
};

let __lastLevel: string | null = null;

export const useGraph = () => {
    const { createLayout, createTrace, calculateTimestamps } = useGraphBase();

    const generateGraph = (graphId: string): Graph => {
        const { $graphStore } = useNuxtApp();
        const storeGraph = $graphStore.useStoreGraph(graphId, "default");

        const query = storeGraph.query.value;
        const overrides = storeGraph.overrides.value;

        if (!Object.keys(query).length) {
            return {
                traces: [],
                layout: createLayout({ dataCount: 0, noData: true })
            };
        }

        const unitInfoList: {
            baseUnit: string;
            unitIndex: number;
            jobId: number;
            prefix: string;
        }[] = [];

        for (const jobId of query.jobIds) {
            let prefix = query.jobIds.length > 1 ? `${jobId} ` : "";
            if (
                prefix &&
                jobId in overrides.prefixes &&
                overrides.prefixes[jobId]?.length
            ) {
                prefix = `${overrides.prefixes[jobId]} `;
            }
            const measurements = $graphStore.getMeasurements({
                ...query,
                jobIds: [jobId]
            });

            if (!measurements?.traces?.length) continue;

            const unit = measurements.traces[0]?.unit;
            if (!unit) continue;

            const parsed = parseGeneralUnit(unit);
            unitInfoList.push({
                baseUnit: parsed.base,
                unitIndex: parsed.index,
                jobId,
                prefix
            });
        }

        if (!unitInfoList.length) {
            return {
                traces: [],
                layout: createLayout({ dataCount: 0, noData: true })
            };
        }

        const allBaseUnits = new Set(unitInfoList.map((u) => u.baseUnit));
        if (allBaseUnits.size > 1) {
            console.warn("Inconsistent base units across jobs:", [
                ...allBaseUnits
            ]);
        }

        const unifiedBaseUnit = unitInfoList[0].baseUnit;
        const unifiedUnitIndex = Math.max(
            ...unitInfoList.map((u) => u.unitIndex)
        );
        const unifiedUnit = `${CONVERSION_SIZES[unifiedUnitIndex]}${unifiedBaseUnit}`;

        let all: {
            traces: Partial<Trace>[];
            dataCount: number;
            unit: string;
            traceCount: number;
        } = {
            traces: [],
            dataCount: 0,
            unit: unifiedUnit,
            traceCount: 0
        };

        for (const { jobId, prefix } of unitInfoList) {
            const result = assembleGraph({
                storeGraph,
                jobId,
                prefix,
                traceCount: all.traceCount,
                unifiedBaseUnit,
                unifiedUnitIndex
            });

            if (!result?.traces.length) continue;

            all.traces.push(...result.traces);
            all.dataCount += result.dataCount;
            all.traceCount += result.traces.length;
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
        } else {
            const vis = new Set(storeGraph.settings.value.visible);
            all.traces.forEach((x: Partial<Trace>) => {
                x.visible = x.uid ? vis.has(x.uid) : true;
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
        traceCount = 0,
        unifiedBaseUnit,
        unifiedUnitIndex
    }: {
        storeGraph: StoreGraphReturnDefault;
        jobId: number;
        prefix?: string;
        traceCount?: number;
        unifiedBaseUnit: string;
        unifiedUnitIndex: number;
    }) => {
        const { $graphStore } = useNuxtApp();

        const query = storeGraph.query.value;

        const result = $graphStore.getMeasurements({
            ...query,
            jobIds: [jobId]
        });

        const preferences = storeGraph.preferences.value;

        if (!result?.traces?.length)
            return {
                traces: [],
                dataCount: 0,
                unit: "",
                baseUnit: "",
                unitIndex: 0
            };

        let measurements = result.traces;

        let traces = [];
        let dataCount = 0;
        let interval = 0;

        // assume same unit for all traces
        const unit = measurements[0]?.unit || "";
        const parsedUnit = parseGeneralUnit(unit);

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

            const conversionFactor = Math.pow(
                1000,
                parsedUnit.index - unifiedUnitIndex
            );
            const values = metric.values.map((v) => v * conversionFactor);
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
                x: calculateTimestamps(values.length, metric.interval),
                y: values,
                name: metricName,

                tableName: tableName,
                legendgroup: metric?.legend_group ?? id,
                visible: visible,
                rawName: metricRawName,
                table: metric.table,
                unit: `${CONVERSION_SIZES[unifiedUnitIndex]}${parsedUnit.base}`,
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

        {
            const { flopItems, dramItems, cacheItems } = useNodeBenchmarks();
            const supportedPeaks =
                query.metric === "FLOPS" ||
                (query.metric === "Bandwidth" &&
                    (query.group === "memory" || query.group === "cache"));

            const allowed = (() => {
                if (!supportedPeaks) return new Set<string>();
                const arr =
                    query.metric === "FLOPS"
                        ? Array.isArray(flopItems)
                            ? flopItems
                            : []
                        : query.group === "memory"
                        ? Array.isArray(dramItems)
                            ? dramItems
                            : []
                        : Array.isArray(cacheItems)
                        ? cacheItems
                        : [];
                return new Set<string>(arr.map((i: any) => i.value));
            })();

            const prevSel: string[] = Array.isArray(modifiers.systemBenchmarks)
                ? modifiers.systemBenchmarks
                : [];
            const nextSel = supportedPeaks
                ? prevSel.filter((b) => allowed.has(b))
                : [];

            if (nextSel.length !== prevSel.length) {
                modifiers.systemBenchmarks = nextSel;
            }

            const prevVis: string[] = Array.isArray(
                storeGraph.settings.value.visible
            )
                ? storeGraph.settings.value.visible
                : [];
            const prefix = `${query.node}-peak-`;

            const nextVis = prevVis.filter((uid) => {
                if (typeof uid !== "string" || !uid.startsWith(prefix))
                    return true;
                const bench = uid.slice(prefix.length);
                return supportedPeaks && allowed.has(bench);
            });

            if (nextVis.length !== prevVis.length) {
                storeGraph.settings.value.visible = nextVis;
            }
        }

        if (modifiers.systemBenchmarks?.length) {
            const existUids = new Set<string>(
                (storeGraph.graph.value?.traces ?? [])
                    .map((t: any) => t?.uid)
                    .filter((u: any): u is string => typeof u === "string")
            );

            const scaleRaw = modifiers.systemBenchmarksScalingFactor ?? 1;
            const formatScale = (v: number) => {
                const n = Number(v);
                if (!isFinite(n) || n <= 0) return "1";
                if (n >= 1) return String(n);
                if (n < 0.01) return n.toExponential(2);
                return n.toFixed(2);
            };
            // The display format of the scaling factor can be customized
            // The current format is 'peak* x factor'
            const formattedScale = formatScale(scaleRaw);
            const scaleSuffix =
                formattedScale !== "1" && formattedScale !== "1.0"
                    ? ` × ${formattedScale}`
                    : "";
            const stripScaleSuffix = (name: string) =>
                (name || "")
                    .replace(/\s*[\(\[]\s*×[^)\]]*[\)\]]\s*$/u, "")
                    .replace(/\s*×[0-9.+\-eE]+\s*$/u, "");

            modifiers.systemBenchmarks.forEach((benchmark) => {
                const nodeNames = Object.keys(nodes[query.jobIds[0]]);
                const node =
                    nodes[query.jobIds[0]]?.[
                        query.level == "job" ? nodeNames[0] : query.node
                    ];
                let peak = node?.benchmarks?.[benchmark];
                if (!node || !peak) return;

                peak *= modifiers.systemBenchmarksScalingFactor;

                if (query.level == "job") peak *= nodeNames.length;

                const isBandwidth = benchmark.includes("bandwidth");
                const baseUnit = unit.substring(
                    0,
                    unit.length - (isBandwidth ? "B/s".length : "FLOPS".length)
                );

                const uidNode =
                    query.level === "job" ? nodeNames[0] : query.node;
                const uid = `${uidNode}-peak-${benchmark}`;
                const paletteColor = palette[traceCount % palette.length];
                const overrideName = overrides.traces?.[uid]?.name || null;
                {
                    const prev = Array.isArray(
                        storeGraph.settings.value.visible
                    )
                        ? storeGraph.settings.value.visible
                        : [];
                    if (!prev.includes(uid) && !existUids.has(uid)) {
                        storeGraph.settings.value = {
                            ...storeGraph.settings.value,
                            visible: Array.from(new Set([...prev, uid]))
                        };
                    }
                }

                const baseName =
                    overrideName || `Peak ${benchmarkTitles.value[benchmark]}`;
                const nameWithScale = `${stripScaleSuffix(
                    baseName
                )}${scaleSuffix}`;
                const scaledPeak = humanSizeFixed(peak, baseUnit);
                traces.push(
                    createTrace({
                        name: nameWithScale,
                        y: new Array(xMax).fill(scaledPeak),
                        interval,
                        legendgroup: "benchmarks",
                        width: 3,
                        auxiliary: true,
                        color: paletteColor,
                        uid
                    })
                );
                traceCount += 1;
            });
        }

        {
            const curLevel = query.level;
            if (__lastLevel !== curLevel) {
                __lastLevel = curLevel;
                const allUids: string[] = (traces ?? [])
                    .map((t: any) => t?.uid)
                    .filter((u: any): u is string => typeof u === "string");
                const prev = storeGraph.settings.value ?? {};
                storeGraph.settings.value = {
                    ...prev,
                    visible: allUids
                };
            }
        }

        return {
            traces,
            dataCount,
            unit,
            baseUnit: parsedUnit.base,
            unitIndex: parsedUnit.index
        };
    };

    return { generateGraph };
};
