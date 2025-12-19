import { deepClone } from "~/utils/misc";
import { toDDHHMMSS } from "~/utils/date";
import Plotly from "plotly.js-basic-dist-min";

export const LEGEND_WIDTH = 180;

export const groupLabels: { [key: string]: string } = {
    cache: "Cache",
    cpu: "CPU",
    disk: "Disk",
    memory: "Memory",
    energy: "Energy",
    interconnect: "Interconnect",
    gpu: "GPU"
};

const graphMarginsWithRangeslider: Plotly.Margin = {
    l: 60,
    r: LEGEND_WIDTH,
    b: 10,
    t: 20,
    pad: 0
};

const graphMargins: Plotly.Margin = {
    l: 60,
    r: LEGEND_WIDTH,
    b: 60,
    t: 20,
    pad: 0
};

const spike: Partial<Plotly.LayoutAxis> = {
    spikesnap: "cursor",
    spikethickness: -2,
    spikecolor: "gray",
    spikemode: "across",
    spikedash: "3px"
};

const defaultLayout: Partial<Plotly.Layout> = {
    xaxis: {
        showgrid: true,
        zeroline: false,
        range: [0, 100],
        rangemode: "tozero",
        // TODO tickformat https://github.com/d3/d3-time-format/blob/main/README.md,
        ...spike
    },
    yaxis: {
        showline: true,
        rangemode: "tozero",
        range: [0, 100],
        title: {
            text: ""
        },
        type: "linear",
        ...spike
    },
    font: {
        family: "Source Code Pro",
        size: 12,
        color: ""
    },
    // always show legend for consistent alignment between graphs
    showlegend: true,
    autosize: true,
    margin: graphMargins,
    hovermode: "x unified",
    hoverdistance: -1,
    legend: {
        valign: "top",
        bgcolor: "rgba(0,0,0,0)"
    }
};

export const useGraphBase = () => {
    const { flopTitles } = useNodeBenchmarks();
    const traceDisplayNameOverride: Record<string, string> = {
        ...Object.fromEntries(
            Object.entries(flopTitles.value).map(([k, v]) => [k, `Peak ${v}`])
        ),
        bandwidth_mem: "Peak Memory Bandwidth"
    };

    const getColors = () => {
        const el = document.getElementsByTagName("body")[0];
        const background = `rgb(${getComputedStyle(el).getPropertyValue(
            "--v-theme-surface"
        )})`;
        const fontColor = `rgb(${getComputedStyle(el).getPropertyValue(
            "--v-theme-font-light"
        )})`;

        let font = defaultLayout.font || {};
        font.color = fontColor;

        return {
            paper_bgcolor: background,
            plot_bgcolor: background,
            font
        };
    };

    const calculateTimestamps = (points: number, interval: number) => {
        let timestamps = [];
        let seconds = 0;
        for (let i = 0; i < points; i++) {
            timestamps.push(toDDHHMMSS(seconds));
            seconds += interval;
        }
        return timestamps;
    };

    const createLayout = ({
        dataCount,
        yTitle = "",
        xTitle = "",
        autorange = false,
        rangeslider = true,
        xType = "-",
        yType = "-",
        xAutotick = false,
        noData = false,
        showLegend
    }: {
        dataCount: number;
        yTitle?: string;
        xTitle?: string;
        autorange?: Plotly.LayoutAxis["autorange"];
        rangeslider?: boolean;
        xType?: Plotly.LayoutAxis["type"];
        yType?: Plotly.LayoutAxis["type"];
        xAutotick?: Plotly.LayoutAxis["autotick"];
        noData?: boolean;
        showLegend?: boolean;
    }): Partial<Plotly.Layout> => {
        let layout = deepClone(defaultLayout);
        // always retrieve current colors as they may change when switching themes
        const layoutColors = process.client ? getColors() : {};

        layout = { ...layout, ...layoutColors };

        layout.showlegend = showLegend;

        if (!showLegend) {
            layout.margin = { ...graphMargins, r: 60 };
        } else {
            layout.margin = graphMargins;
        }

        if (rangeslider) {
            if (!showLegend) {
                layout.margin = { ...graphMarginsWithRangeslider, r: 60 };
            } else {
                layout.margin = graphMarginsWithRangeslider;
            }
        }
        // for proper non-zero x-axis on missing data
        dataCount = dataCount || 100;

        if (noData || dataCount == 0) {
            layout.annotations = [
                {
                    text: "no data available or matching filters",
                    xref: "paper",
                    yref: "paper",
                    showarrow: false,
                    font: {
                        size: 12
                    }
                }
            ];
        }

        if (layout.xaxis) {
            layout.xaxis.range = [0, dataCount - 1];

            layout.xaxis.nticks = 7;
            layout.xaxis.autorange = autorange;
            layout.xaxis.title = xTitle ? { text: xTitle } : undefined;
            if (xType) layout.xaxis.type = xType;
            if (xAutotick) layout.xaxis.autotick = true;

            if (rangeslider) {
                layout.xaxis.rangeslider = {};
                if (showLegend) {
                    layout.margin = graphMarginsWithRangeslider;
                }
            }
        }

        if (layout.yaxis) {
            layout.yaxis.title = { text: yTitle };
            layout.yaxis.autorange = autorange;
            if (yType) layout.yaxis.type = yType;
        }

        if (layout.margin && !xTitle) layout.margin.b = 40;

        return layout;
    };

    // TODO type scattergl yields better performance but requires larger plotly bundle and may run into "Too many active WebGL contexts"
    // needs further evaluation including custom plotlyjs bundle and virtual WebGL contexts
    const createTrace = ({
        name,
        y,
        legendgroup = "",
        interval = 5,
        x = [],
        fill = "",
        width = 1,
        color = "",
        mode = "lines",
        type = "scatter",
        visible = true,
        auxiliary = false,
        rawName = "",
        tableName = "",
        table = "",
        unit = "",
        id = "",
        uid = ""
    }: {
        name: string;
        y: number[];
        legendgroup?: string;
        interval?: number;
        x?: string[] | number[];
        fill?: string;
        width?: number;
        color?: string;
        mode?: string;
        type?: string;
        visible?: string | boolean;
        auxiliary?: boolean;
        rawName?: string;
        tableName?: string;
        table?: string;
        unit?: string;
        id?: string;
        uid?: string;
    }) => {
        let legendName = name;
        // overrides are for roofline graph
        if (legendName in traceDisplayNameOverride) {
            legendName = traceDisplayNameOverride[legendName];
        } else if (legendName.length > 12) {
            // TODO adjust for longer names requiring multiple breaks
            // TODO couple to LEGEND_WIDTH
            // plotly does not support specifying a max-width for the legend -> insert manual breaks
            legendName = name.replace(/(.{12,}?)\s?\b/g, "$1<br>");
            if (legendName.endsWith("<br>"))
                legendName = legendName.substring(0, legendName.length - 4);
        }

        return {
            x: x.length ? x : calculateTimestamps(y.length, interval),
            y: y,
            name: legendName,
            displayName: name,
            legendgroup: legendgroup,
            mode: mode,
            type: type,
            line: {
                width: width,
                color: color
            },
            visible: visible,
            fill: fill,
            hoverinfo: "none",
            rawName: rawName,
            table: table,
            unit: unit,
            auxiliary: auxiliary,
            id: id,
            tableName: tableName,
            uid: uid
        };
    };
    return { calculateTimestamps, createTrace, createLayout };
};
