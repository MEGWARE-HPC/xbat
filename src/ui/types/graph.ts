// ---------------------------------------------------------------------------
// Layout — ECharts-oriented; structurally compatible with Plotly.Layout for
// the legacy ReactiveGraph renderer (spike/spikexxx fields kept for that path)
// ---------------------------------------------------------------------------
export interface GraphLayout {
    showlegend?: boolean;
    paper_bgcolor?: string;
    plot_bgcolor?: string;
    font?: { family?: string; size?: number; color?: string };
    autosize?: boolean;
    hovermode?: string;
    hoverdistance?: number;
    legend?: { valign?: string; bgcolor?: string };
    margin?: { l?: number; r?: number; b?: number; t?: number; pad?: number };
    annotations?: Array<{
        text?: string;
        xref?: string;
        yref?: string;
        showarrow?: boolean;
        font?: { size?: number };
    }>;
    xaxis?: {
        showgrid?: boolean;
        zeroline?: boolean;
        rangemode?: string;
        range?: number[];
        nticks?: number;
        autorange?: boolean | "reversed";
        autotick?: boolean;
        title?: { text?: string };
        type?: string;
        rangeslider?: Record<string, unknown> | object;
        // Plotly crosshair/spike — ignored by ECharts, used by ReactiveGraph
        spikesnap?: string;
        spikethickness?: number;
        spikecolor?: string;
        spikemode?: string;
        spikedash?: string;
    };
    yaxis?: {
        showline?: boolean;
        rangemode?: string;
        range?: number[];
        autorange?: boolean | "reversed";
        title?: { text?: string };
        type?: string;
        spikesnap?: string;
        spikethickness?: number;
        spikecolor?: string;
        spikemode?: string;
        spikedash?: string;
    };
}

export interface Graph {
    traces: Trace[];
    layout: GraphLayout;
}

export interface GraphFont {
    family: string;
    size: number;
    color: string;
}

export interface GraphLegend {
    valign: string;
    bgcolor: string;
}

export interface GraphAxis {
    showgrid?: boolean;
    zeroline?: boolean;
    range: number[];
    rangemode: string;
    spikesnap: string;
    spikethickness: number;
    spikecolor: string;
    spikemode: string;
    spikedash: string;
    nticks?: number;
    autorange: boolean;
    title: string | null;
    type: string;
    showline?: boolean;
}

export interface GraphQuery {
    jobIds: number[];
    node: string;
    group: string;
    metric: string;
    level: GraphLevel;
    deciles: boolean;
}

export interface GraphSettings {
    visible: string[];
    visibleStatistics: string[];
    // used to preserved toggled traces when switching between levels
    prevVisibleTables: string[];
}

export interface GraphStyling {
    colorPalette: string;
    showLegend?: boolean;
}

export interface GraphModifiers {
    filterRange: string | null;
    filterBy: null | string;
    filter0: string | number | undefined;
    operator0: null | string;
    filter1: string | number | undefined;
    operator1: null | string;
    systemBenchmarks: string[];
    systemBenchmarksScalingFactor: number;
}

export interface Trace {
    jobId: number;
    group: string;
    description: string[];
    metric: string;
    level: string;
    node: string;
    start: Date;
    stop: Date;
    interval: number;
    unit: string;
    rawUnit: string;
    stacked: boolean;
    table: string;
    variant: string;
    iteration: number;
    deciles: boolean;
    name: string;
    rawName: string;
    rawValues: number[];
    legend_group: string;
    values: number[];
    id: string;
    uid: string;
    statistics: Statistics;
    auxiliary?: boolean;
    visible?: string | boolean;
    tableName?: string;
    displayName: string;
    stackgroup?: string;
    fill?: string;
    // Fields populated by createTrace / createRooflineTrace
    x?: string[] | number[];
    y?: number[];
    mode?: string;
    type?: string;
    hoverinfo?: string;
    legendgroup?: string;
    line?: { width?: number; color?: string };
    marker?: { color?: string; size?: number; symbol?: string };
}

export interface Statistics {
    min: number;
    max: number;
    std: number;
    avg: number;
    var: number;
    median: number;
    sum: number;
}

export interface StatisticsValues {
    min: number[];
    max: number[];
    avg: number[];
}

export interface GraphRawData {
    traces: Trace[];
    statistics: {
        [key: string]: {
            values: StatisticsValues;
            general: Statistics;
        };
    };
}

export type GraphLevel =
    | "thread"
    | "core"
    | "numa"
    | "socket"
    | "device"
    | "node"
    | "job";

export type Metrics = Record<string, MetricGroup>;

export type MetricGroup = Record<string, MetricMeta>;

export type MetricMeta = {
    metrics: TableMetrics;
    unit?: string;
    description?: string;
    aggregation?: string;
    uri?: string;
    level_min?: string;
    stack_min_level?: string;
    stacked?: boolean;
};

export type TableMetrics = Record<
    string,
    string | { name: string; description?: string }
>;

export type GraphOverrides = {
    prefixes: Record<string, string>;
    traces: Record<string, { name?: string; color?: string }>;
};
