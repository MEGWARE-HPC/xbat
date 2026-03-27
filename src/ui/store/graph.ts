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
import { useEventBus } from "@vueuse/core";
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

    const cacheClearEvent = useEventBus<string>("graph-cache-clear");

    const addMeasurements = (
        query: GraphQuery,
        payload: GraphRawData
    ): void => {
        measurements.set(createAccessString(query), payload);
    };

    const fetchMeasurements = async (
        query: GraphQuery,
        refresh: boolean = false
    ): Promise<boolean> => {
        // graphs are client-only and should not be fetched on the server
        // as this can lead to errors since NuxtInstance might not be available yet
        if (process.server) return false;

        const { $api } = useNuxtApp();

        if (!query.metric || !query.level) return false;

        // check if data is already cached (unless refresh is forced)
        if (
            !refresh &&
            measurements.get(createAccessString(query)) !== undefined
        )
            return true;

        const result = await $api.measurements.get(query);
        if (!result) return false;

        addMeasurements(query, result);

        return !!result.traces?.length;
    };

    const bustCache = (jobIds: number[]) => {
        measurements.forEach((_value, key) => {
            if (jobIds.some((jobId) => key.startsWith(`${jobId}.`))) {
                measurements.delete(key);
            }
        });

        cacheClearEvent.emit("graph-cache-clear", jobIds);
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
                loading: false
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
            if (!graphRef.value) registerGraph(id, type);
            graphRef.value.loading = true;
            if (type === "default") graphRef.value.graph = generateGraph(id);
            else graphRef.value.graph = generateRooflineGraph(id);
            // loading state is reset when graph is rendered
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
            const updateData = async (refresh = false) => {
                if (!graphRef.value) registerGraph(id, type);

                graphRef.value.loading = true;
                let res: boolean[] = [];
                const jobIds = graphRef.value.query.jobIds;
                // Use mutex as updateData might be triggered multiple times.
                // This prevents duplicate API calls as it ensures that the second request uses the cache instead of firing again.
                // Since this mutex is specific to this graph, it does not prevent duplicate requests from other graphs
                await mutex.runExclusive(async () => {
                    res = await Promise.all(
                        jobIds.map((x) =>
                            fetchMeasurements(
                                {
                                    ...graphRef.value.query,
                                    jobIds: [x]
                                },
                                refresh
                            )
                        )
                    );
                });

                if (res?.includes(false)) {
                    graphs.value[id].loading = false;
                    return;
                }

                let raw: { [key: string]: GraphRawData } = {};

                // save raw data for export as JSON/CSV
                jobIds.forEach((x) => {
                    const m = getMeasurements({
                        ...graphRef.value.query,
                        jobIds: [x]
                    });
                    if (!m) return;
                    raw[x] = m;
                });

                graphRef.value.raw = raw;
                updateGraph();
            };
            return {
                query: computed({
                    get: () => graphRef.value?.query || {},
                    set: (value: GraphQuery) => {
                        if (deepEqual(graphRef.value.query, value)) {
                            return;
                        }

                        const prevQuery = graphRef.value.query;
                        graphRef.value.raw = {};
                        graphRef.value.query = value;

                        // Determine previously visible tables to (partially) preserve metric selection when only level changes
                        const onlyLevelChange =
                            prevQuery.group === value.group &&
                            prevQuery.metric === value.metric;
                        const traces = graphRef.value.graph?.traces;
                        const visibleTables: string[] =
                            traces
                                ?.map((trace) =>
                                    graphRef.value.settings.visible.includes(
                                        trace.uid
                                    )
                                        ? trace.table
                                        : undefined
                                )
                                .filter((v): v is string => v !== undefined) ??
                            [];

                        graphRef.value.settings = {
                            ...defaultSettings,
                            prevVisibleTables:
                                onlyLevelChange && visibleTables.length
                                    ? Array.from(new Set(visibleTables))
                                    : []
                        };

                        updateData();
                    }
                }),
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
        cacheClearEvent,
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
