import { defineStore } from "pinia";
import type {
    GraphQuery,
    GraphRawData,
    GraphOverrides,
    Graph,
    Metrics,
    GraphSettings,
    GraphStyling,
    GraphModifiers,
    GraphLevel
} from "~/types/graph";
import { deepEqual } from "~/utils/misc";
import type { NodeMap } from "~/repository/modules/nodes";
import { Mutex } from "async-mutex";

const createAccessString = (p: GraphQuery) => {
    return `${p.jobIds[0]}.${p.node || "job"}.${p.group}.${p.metric}.${
        p.level
    }.${p?.deciles ? "deciles" : "default"}`;
};

export interface StoreBaseGraph {
    graph: Graph | null;
    nodes: { [key: string]: NodeMap }; // by jobId
    styling: GraphStyling;
    noData: boolean;
    loading: boolean;
}

export interface StoreGraph extends StoreBaseGraph {
    type: "default";
    query: GraphQuery;
    prevQuery: GraphQuery;
    metrics: Metrics;
    modifiers: GraphModifiers;
    raw: { [key: string]: GraphRawData }; // save by jobId due to multi-job graphs
    settings: GraphSettings;
    dataError: boolean;
}

export type GraphQueryRoofline = {
    jobIds: number[];
    node: string | undefined;
    // queries: GraphQuery[];
    plotSP: boolean;
    plotDP: boolean;
    plotBy: "peak" | "median" | "average";
    plotFlops: string[];
    crossCompare: boolean;
};

export type NodeBenchmarks = {
    [key: string]: Record<string, number>;
};

export interface StoreGraphRoofline extends StoreBaseGraph {
    type: "roofline";
    query: GraphQueryRoofline;
    benchmarks: NodeBenchmarks;
}

const defaultSettings = {
    visible: [],
    visibleStatistics: [],
    prevVisibleTables: []
};

const defaultQuery: GraphQuery = {
    jobIds: [],
    node: "",
    group: "",
    metric: "",
    level: "job",
    deciles: false
};

const defaultGraphQueryRoofline: GraphQueryRoofline = {
    jobIds: [],
    node: undefined,
    plotFlops: [],
    plotSP: true,
    plotDP: true,
    crossCompare: false,
    plotBy: "peak"
};

const defaultModifiers: GraphModifiers = {
    filterRange: null,
    filterBy: null,
    filter0: undefined,
    operator0: null,
    filter1: undefined,
    operator1: null,
    systemBenchmarks: [],
    systemBenchmarksScalingFactor: 1
};

interface StoreGraphReturnBase {
    graph: Ref<Graph | null>;
    updateGraph: () => void;
    updateData: (refresh?: boolean) => void;
    loading: Ref<boolean>;
    noData: Ref<boolean>;
    styling: Ref<GraphStyling>;
    nodes: Ref<Record<string, NodeMap>>;
    preferences: Ref<GeneralGraphSettings>;
    overrides: Ref<GraphOverrides>;
    id: string;
}

export interface StoreGraphReturnDefault extends StoreGraphReturnBase {
    query: Ref<GraphQuery>;
    raw: Ref<Record<string, GraphRawData>>;
    metrics: Ref<Metrics>;
    modifiers: Ref<GraphModifiers>;
    settings: Ref<GraphSettings>;
    dataError: Ref<boolean>;
}

export interface StoreGraphReturnRoofline extends StoreGraphReturnBase {
    query: Ref<GraphQueryRoofline>;
    generateQueries: () => GraphQuery[];
    benchmarks: Ref<NodeBenchmarks>;
}

export const useGraphStore = defineStore("graph", () => {
    const measurements = new Map<string, GraphRawData>();

    const graphs = ref<Record<string, StoreGraph | StoreGraphRoofline>>({});

    const { graphPreferences: preferences, graphOverrides: overrides } =
        usePreferences();

    const { generateGraph } = useGraph();
    const { generateRooflineGraph } = useGraphRoofline();

    const pendingMeasurements = new Map<string, Promise<GraphRawData | null>>();
    const defaultRequests = new WeakMap<StoreGraph, symbol>();

    const loadMeasurements = (
        query: GraphQuery,
        refresh = false
    ): Promise<GraphRawData | null> => {
        if (process.server || !query.metric || !query.level)
            return Promise.resolve(null);

        const key = createAccessString(query);

        const pending = pendingMeasurements.get(key);
        if (pending) return pending;

        const cached = measurements.get(key);
        if (!refresh && cached) return Promise.resolve(cached);

        const { $api } = useNuxtApp();
        const request = Promise.resolve()
            .then(() => $api.measurements.get(query))
            .then((result) => {
                if (pendingMeasurements.get(key) !== request || !result)
                    return null;

                measurements.set(key, result);
                return result;
            })
            .finally(() => {
                if (pendingMeasurements.get(key) === request)
                    pendingMeasurements.delete(key);
            });

        pendingMeasurements.set(key, request);
        return request;
    };

    const fetchMeasurements = async (
        query: GraphQuery,
        refresh = false
    ): Promise<boolean> => {
        if (process.server || !query.metric || !query.level) return false;
        if (!refresh && measurements.has(createAccessString(query)))
            return true;
        return !!(await loadMeasurements(query, refresh))?.traces?.length;
    };

    const bustCache = (jobIds: number[]) => {
        const matches = (key: string) =>
            jobIds.some((jobId) => key.startsWith(`${jobId}.`));

        for (const key of measurements.keys()) {
            if (matches(key)) measurements.delete(key);
        }

        for (const key of pendingMeasurements.keys()) {
            if (matches(key)) pendingMeasurements.delete(key);
        }

        // Let the accepted metrics update reach the graph query first.
        void nextTick(() => {
            for (const [id, graph] of Object.entries(graphs.value)) {
                if (
                    graph.type === "default" &&
                    graph.query.jobIds.some((jobId) => jobIds.includes(jobId))
                ) {
                    void updateDefaultData(id, graph);
                }
            }
        });
    };

    const getMeasurements = (query: GraphQuery): GraphRawData | null => {
        return measurements.get(createAccessString(query)) || null;
    };

    const createQuery = (
        jobIds: number[] | number = [],
        group: string = "",
        metric: string = "",
        level: GraphLevel = "job",
        node: string = "",
        deciles: boolean = false
    ): GraphQuery => {
        let query = {
            jobIds: Array.isArray(jobIds) ? jobIds : [jobIds],
            group: group,
            metric: metric,
            level: level,
            node: level != "job" ? node : "",
            deciles: deciles
        };
        return query;
    };

    const registerGraph = (id: string, type: string): void => {
        if (!preferences.value.colorPalette)
            preferences.value.colorPalette = "D3";

        if (type === "default")
            graphs.value[id] = {
                type: "default",
                graph: null,
                query: { ...defaultQuery },
                raw: {},
                settings: { ...defaultSettings },
                modifiers: { ...defaultModifiers },
                metrics: {},
                styling: {
                    colorPalette: preferences.value.colorPalette,
                    showLegend: true
                },
                nodes: {},
                noData: false,
                loading: false,
                dataError: false
            };
        else {
            graphs.value[id] = {
                graph: null,
                type: "roofline",
                nodes: {},
                styling: {
                    colorPalette: preferences.value.colorPalette,
                    showLegend: true
                },
                noData: false,
                loading: false,
                query: { ...defaultGraphQueryRoofline },
                benchmarks: {}
            };
        }
    };

    const unregisterGraph = (id: string): void => {
        delete graphs.value[id];
    };

    const getQuery = (id: string): GraphQuery | {} => {
        return graphs.value[id].query || {};
    };

    const syncColorPalette = (palette: string) => {
        Object.entries(graphs.value).forEach(([key, graph]) => {
            if (graph.type === "default") {
                const store = useStoreGraph(key, "default");
                store.styling.value = {
                    ...store.styling.value,
                    colorPalette: palette
                };
            } else if (graph.type === "roofline") {
                const store = useStoreGraph(key, "roofline");
                store.styling.value = {
                    ...store.styling.value,
                    colorPalette: palette
                };
            }
        });
        preferences.value.colorPalette = palette;
    };

    const updateAllGraphs = () => {
        Object.entries(graphs.value).forEach(([key, graph]) => {
            if (graph.type === "default") {
                useStoreGraph(key, "default").updateGraph();
            } else if (graph.type === "roofline") {
                useStoreGraph(key, "roofline").updateGraph();
            }
        });
    };

    const setPreference = <K extends keyof GeneralGraphSettings>(
        key: K,
        value: GeneralGraphSettings[K]
    ) => {
        preferences.value[key] = value;
        updateAllGraphs();
    };

    const updateDefaultData = async (
        id: string,
        graph: StoreGraph,
        refresh = false
    ) => {
        if (process.server || !graph?.query.jobIds.length) return;

        const query = { ...graph.query, jobIds: [...graph.query.jobIds] };
        const request = Symbol();

        defaultRequests.set(graph, request);

        const isCurrent = () =>
            graphs.value[id] === graph &&
            defaultRequests.get(graph) === request;

        graph.loading = true;
        graph.dataError = false;

        try {
            const payloads = await Promise.all(
                query.jobIds.map(async (jobId) => {
                    const payload = await loadMeasurements(
                        { ...query, jobIds: [jobId] },
                        refresh
                    );
                    if (!payload) throw new Error("Measurements unavailable");
                    return [jobId, payload] as const;
                })
            );

            if (!isCurrent()) return;

            graph.raw = Object.fromEntries(payloads);
            graph.graph = payloads.some(([, payload]) => payload.traces?.length)
                ? generateGraph(id)
                : null;
        } catch (error) {
            if (!isCurrent()) return;

            console.error("Failed to load graph measurements:", error);
            graph.raw = {};
            graph.graph = null;
            graph.dataError = true;
        } finally {
            if (isCurrent()) graph.loading = false;
        }
    };

    function useStoreGraph(
        id: string,
        type: "default"
    ): StoreGraphReturnDefault;
    function useStoreGraph(
        id: string,
        type: "roofline"
    ): StoreGraphReturnRoofline;

    function useStoreGraph(
        id: string,
        type: "default" | "roofline" = "default"
    ) {
        if (!graphs.value[id]) registerGraph(id, type);

        const mutex = new Mutex();

        const graphRef = computed(() => graphs.value[id]);

        const updateGraph = () => {
            const graph = graphRef.value;
            if (!graph) return;

            if (graph.type === "default") {
                if (graph.graph) graph.graph = generateGraph(id);
                return;
            }

            graph.loading = true;
            graph.graph = generateRooflineGraph(id);
            // Roofline loading state is reset when its graph is rendered.
        };

        watch(
            () => graphRef.value?.noData,
            (v) => {
                if (v && id in graphs.value) graphRef.value.loading = false;
            }
        );

        const useDefaultStoreGraph = (
            id: string,
            graphRef: Ref<StoreGraph>
        ) => {
            const updateData = (refresh = false) =>
                updateDefaultData(id, graphRef.value, refresh);

            return {
                query: computed({
                    get: () => graphRef.value?.query || {},
                    set: (value: GraphQuery) => {
                        const graph = graphRef.value;
                        if (!graph || deepEqual(graph.query, value)) return;

                        const previous = graph.query;
                        const onlyLevelChange =
                            value.jobIds.length > 0 &&
                            deepEqual(previous.jobIds, value.jobIds) &&
                            previous.group === value.group &&
                            previous.metric === value.metric &&
                            previous.level !== value.level &&
                            previous.deciles === value.deciles &&
                            (previous.node === value.node ||
                                previous.level === "job" ||
                                value.level === "job");

                        const visibleTables = onlyLevelChange
                            ? (graph.graph?.traces ?? [])
                                  .filter((trace) =>
                                      graph.settings.visible.includes(trace.uid)
                                  )
                                  .map((trace) => trace.table)
                            : [];

                        defaultRequests.delete(graph);

                        graph.query = { ...value, jobIds: [...value.jobIds] };
                        graph.graph = null;
                        graph.raw = {};
                        graph.loading = false;
                        graph.dataError = false;
                        graph.settings = {
                            ...defaultSettings,
                            prevVisibleTables: [...new Set(visibleTables)]
                        };

                        if (value.jobIds.length) void updateData();
                    }
                }),
                dataError: computed(() => graphRef.value?.dataError ?? false),
                raw: computed({
                    get: () => graphRef.value?.raw || {},
                    set: (value: { [key: string]: GraphRawData }) => {
                        graphRef.value.raw = value;
                    }
                }),
                settings: computed({
                    get: () => graphRef.value?.settings || {},
                    set: (value: GraphSettings) => {
                        // use manual trigger of updateGraph to prevent infinite loops and other compilications
                        graphRef.value.settings = value;
                    }
                }),
                modifiers: computed({
                    get: () => graphRef.value?.modifiers || {},
                    set: (value: GraphModifiers) => {
                        if (deepEqual(graphRef.value.modifiers, value)) return;
                        graphRef.value.modifiers = value;
                        updateGraph();
                    }
                }),
                metrics: computed({
                    get: () => graphRef.value?.metrics || {},
                    set: (value: Metrics) => {
                        graphRef.value.metrics = value;
                    }
                }),

                updateData
            };
        };

        const useRooflineStoreGraph = (
            id: string,
            graphRef: Ref<StoreGraphRoofline>
        ) => {
            // Not using computed (in combination with watcher) for better manual control
            const generateQueries = (): GraphQuery[] => {
                let queries: GraphQuery[] = [];
                const jobIds = graphRef.value.query.jobIds;
                jobIds.forEach((jobId) => {
                    const jobNodes = Object.keys(graphRef.value.nodes[jobId]);
                    if (!jobNodes?.length) return;
                    // Note that jobNodes[0] might be different than the reference node used in the query
                    // The reference node provides the peak values while the jobNodes[0] is used for the actual data
                    queries.push(
                        createQuery(jobId, "cpu", "FLOPS", "node", jobNodes[0]),
                        createQuery(
                            jobId,
                            "memory",
                            "Data Volume",
                            "node",
                            jobNodes[0]
                        )
                    );
                });
                return queries;
            };
            const updateData = async () => {
                if (!graphRef.value) registerGraph(id, type);

                graphRef.value.loading = true;

                const queries = generateQueries();

                let res: boolean[] = [];
                await mutex.runExclusive(async () => {
                    res = await Promise.all(
                        queries.map((x) => fetchMeasurements(x))
                    );
                });

                if (res?.includes(false)) {
                    graphs.value[id].loading = false;
                    return;
                }

                updateGraph();
            };

            return {
                query: computed({
                    get: () => graphRef.value?.query || {},
                    set: (value: GraphQueryRoofline) => {
                        if (deepEqual(graphRef.value.query, value)) {
                            return;
                        }

                        graphRef.value.query = value;
                        updateData();
                    }
                }),
                benchmarks: computed({
                    get: () => graphRef.value.benchmarks || {},
                    set: (value: NodeBenchmarks) => {
                        graphRef.value.benchmarks = value;
                    }
                }),
                updateData,
                generateQueries
            };
        };

        const shared = {
            graph: computed({
                get: () => graphRef.value?.graph || null,
                set: (value: Graph) => {
                    graphRef.value.graph = value;
                }
            }),
            nodes: computed({
                get: () => graphRef.value?.nodes || {},
                set: (value: { [key: string]: NodeMap }) => {
                    graphRef.value.nodes = value;
                }
            }),
            styling: computed({
                get: () => graphRef.value?.styling || {},
                set: (value: GraphStyling) => {
                    if (deepEqual(graphRef.value.styling, value)) return;
                    graphRef.value.styling = value;
                    updateGraph();
                }
            }),

            noData: computed({
                get: () => graphRef.value?.noData || false,
                set: (value: boolean) => {
                    graphRef.value.noData = value;
                }
            }),
            preferences: computed({
                get: () => preferences.value,
                set: (values: Partial<GeneralGraphSettings>) => {
                    Object.assign(preferences.value, values);
                    updateAllGraphs();
                }
            }),
            overrides: computed({
                get: () => overrides.value,
                set: (value: GraphOverrides) => {
                    if (deepEqual(overrides.value, value)) return;
                    overrides.value.prefixes = {
                        ...overrides.value.prefixes,
                        ...value.prefixes
                    };
                    overrides.value.traces = {
                        ...overrides.value.traces,
                        ...value.traces
                    };
                    updateGraph();
                }
            }),
            loading: computed({
                get: () => graphRef.value?.loading || false,
                set: (value: boolean) => {
                    graphRef.value.loading = value;
                }
            }),
            updateGraph,
            id
        };

        if (type === "default") {
            return {
                ...shared,
                ...useDefaultStoreGraph(id, graphRef as Ref<StoreGraph>)
            } as StoreGraphReturnDefault;
        } else {
            return {
                ...shared,
                ...useRooflineStoreGraph(
                    id,
                    graphRef as Ref<StoreGraphRoofline>
                )
            } as StoreGraphReturnRoofline;
        }
    }

    return {
        // measurements
        measurements,
        fetchMeasurements,
        getMeasurements,
        bustCache,
        createQuery,
        //
        preferences,
        syncColorPalette,
        //
        registerGraph,
        unregisterGraph,
        getQuery,
        graphs,
        useStoreGraph,
        updateAllGraphs,
        setPreference
    };
});

export default useGraphStore;
