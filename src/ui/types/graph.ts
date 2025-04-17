import Plotly from "plotly.js-basic-dist-min";

export interface Graph {
    traces: Trace[];
    layout: Partial<Plotly.Layout>;
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
