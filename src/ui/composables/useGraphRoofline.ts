import { range } from "~/utils/misc";
import { colors } from "~/utils/colors";
import { ArrayUtils } from "~/utils/array";
import { useGraphBase } from "~/components/graphs/useGraphBase";
import type { Graph, Trace } from "~/types/graph";
import type { StoreGraphReturnRoofline } from "~/store/graph";

export const useGraphRoofline = () => {
    const { createLayout, createTrace } = useGraphBase();

    const generateRooflineTraces = (
        storeGraph: StoreGraphReturnRoofline,
        maxOI: number,
        traceCount: number
    ): { traces: Trace[]; dataCount: number } => {
        const benchmarks = storeGraph.benchmarks.value;

        const query = storeGraph.query.value;

        if (!query.node || !(query.node in benchmarks))
            return { traces: [], dataCount: 0 };

        let nodeBenchmarks: Record<string, number> = {};
        // convert to GLOPS and GBytes/s
        Object.entries(benchmarks[query.node]).forEach(([benchmark, value]) => {
            nodeBenchmarks[benchmark] = benchmark.startsWith("bandwidth")
                ? value / 1024 / 1024 / 1024
                : value / 1000 / 1000 / 1000;
        });

        // // sort for consistent coloring
        const visibleFlops = query.plotFlops.sort();
        const visibleMemory = ["bandwidth_mem"];

        // // ceiling across all flop-types
        const maxCeiling = Math.max(
            ...Object.keys(nodeBenchmarks)
                .filter(
                    (x) => x.startsWith("peakflops") && visibleFlops.includes(x)
                )
                .map((x) => nodeBenchmarks[x])
        );

        const maxBandwidth = Math.max(
            ...Object.keys(nodeBenchmarks)
                .filter(
                    (x) =>
                        x.startsWith("bandwidth") && visibleMemory.includes(x)
                )
                .map((x) => nodeBenchmarks[x])
        );

        // calculate all intersection points of left-most (highest) bandwidth with all flop ceilings
        // required to draw ceiling only after first intersection
        const intersections = visibleFlops.map(
            (x) => nodeBenchmarks[x] / maxBandwidth
        );

        const xRange = [
            ...range(0, 1, 0.1),
            ...range(
                1,
                Math.max(
                    20,
                    Math.pow(10, Math.round(maxOI).toString().length) + 1
                )
            ),
            ...intersections
        ].sort((a, b) => a - b);

        const styling = storeGraph.styling.value;

        const palette =
            colors[styling.colorPalette ? styling.colorPalette : "D3"];
        let traces: Trace[] = [];

        for (let mem of visibleMemory) {
            const y = xRange.map((x) =>
                Math.min(nodeBenchmarks[mem] * x, maxCeiling)
            );

            const color = palette[traceCount % palette.length];

            // TODO fix ts
            traces.push(
                createTrace({
                    name: mem,
                    y,
                    x: xRange,
                    width: 2,
                    color: color,
                    uid: mem
                })
            );
            traceCount += 1;
        }

        for (let flop of visibleFlops) {
            const intersection = nodeBenchmarks[flop] / maxBandwidth;
            const xRangeIntercepted = xRange.filter((x) => x >= intersection);
            const y = xRangeIntercepted.map((_) => nodeBenchmarks[flop]);

            const color = palette[traceCount % palette.length];

            // TODO fix ts
            traces.push(
                createTrace({
                    name: flop,
                    y,
                    x: xRangeIntercepted,
                    width: 2,
                    uid: flop,
                    color: color
                })
            );
            traceCount += 1;
        }

        return { traces, dataCount: xRange.length };
    };

    const generateJobMarkers = (storeGraph: StoreGraphReturnRoofline) => {
        const { $graphStore } = useNuxtApp();
        const queries = storeGraph.generateQueries();

        let measurements: Record<string, Record<string, number[]>> = {};
        for (const query of queries) {
            const data = $graphStore.getMeasurements(query);
            if (!data || !data.traces) continue;
            for (const entry of data.traces) {
                if (!(entry.jobId in measurements))
                    measurements[entry.jobId] = {};

                if (
                    (entry.metric == "FLOPS" &&
                        ["SP", "DP"].includes(entry.name)) ||
                    (entry.metric == "Data Volume" && entry.name == "total")
                )
                    measurements[entry.jobId][entry.name] =
                        entry?.rawValues || entry.values;
            }
        }

        let traces: Trace[] = [];

        const query = storeGraph.query.value;

        let precisions = [];
        if (query.plotSP) precisions.push("SP");
        if (query.plotDP) precisions.push("DP");

        const styling = storeGraph.styling.value;
        const palette =
            colors[styling.colorPalette ? styling.colorPalette : "D3"];

        let traceCount = 0,
            maxOI = 0;

        for (const [jobId, values] of Object.entries(measurements)) {
            for (const precision of precisions) {
                if (!(precision in values && "total" in values)) continue;

                let avgFlops = 0;
                let avgDataVolumes = 0;
                switch (query.plotBy) {
                    case "peak":
                        avgFlops = Math.max(...values[precision]);
                        avgDataVolumes = Math.max(...values.total);
                        break;
                    case "average":
                        avgFlops = ArrayUtils.average(values[precision]);
                        avgDataVolumes = ArrayUtils.average(values.total);
                        break;
                    case "median":
                        avgFlops = ArrayUtils.median(values[precision]);
                        avgDataVolumes = ArrayUtils.median(values.total);
                        break;
                    default:
                        break;
                }

                if (!avgFlops || !avgDataVolumes) continue;

                // GFLOPS
                avgFlops = avgFlops / 1000 / 1000 / 1000;
                // GByte
                avgDataVolumes = avgDataVolumes / 1024 / 1024 / 1024;

                const operationIntensity = avgFlops / avgDataVolumes;
                if (operationIntensity > maxOI) maxOI = operationIntensity;

                const uid = `${jobId}-${precision}`;

                const overrides = storeGraph.overrides.value;
                const overrideName = overrides.traces?.[uid]?.name || null;

                const metricName = overrideName || `${jobId} ${precision}`;

                const paletteColor = palette[traceCount % palette.length];

                traces.push(
                    createTrace({
                        name: metricName,
                        y: [avgFlops],
                        x: [operationIntensity],
                        mode: "markers",
                        uid: uid,
                        color: paletteColor
                    })
                );
                traceCount += 1;
            }
        }

        return { traces, maxOI, traceCount };
    };

    const generateRooflineGraph = (graphId: string): Graph => {
        const { $graphStore } = useNuxtApp();
        const storeGraph = $graphStore.useStoreGraph(graphId, "roofline");

        const query = storeGraph.query.value;

        const defaultLayout = createLayout({
            dataCount: 0,
            yTitle: "FLOPS [GFLOPS/s]",
            xTitle: "Operational Intensity [FLOPS/byte]",
            rangeslider: false,
            autorange: true,
            xAutotick: true
        });

        if (
            !query.jobIds.length ||
            !query.node ||
            !query.plotFlops.length ||
            !(query.plotSP || query.plotDP)
        ) {
            return {
                traces: [],
                layout: defaultLayout
            };
        }

        const queries = storeGraph.generateQueries();

        const {
            traces: markers,
            maxOI,
            traceCount
        } = generateJobMarkers(storeGraph);

        const { traces = [] } = generateRooflineTraces(
            storeGraph,
            maxOI,
            traceCount
        );

        return {
            traces: [...markers, ...traces],
            layout: defaultLayout
        };
    };

    return { generateRooflineGraph };
};
