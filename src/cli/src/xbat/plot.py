import importlib
import json
from pathlib import Path
import sys
from typing import Iterable
from matplotlib import pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.axes import Axes
import numpy as np
from rich import print

try:
    importlib.import_module("scienceplots")
except ModuleNotFoundError:
    print("[yellow]Could not import additional styles.[/yellow]", file=sys.stderr)


def metric(
    paths: Iterable[Path],
    table: str | None = None,
    output_path: Path | str | None = None,
    show: bool = False,
    ax: Axes | None = None,
    figsize: tuple[float, float] | None = None,
    iteration_in_label: bool = True,
    style: list[str] = ["default", "grid"],
    dpi: float = 300,
) -> Axes:
    if ax is not None and figsize is not None:
        raise ValueError('Parameters "ax" and "figsize" are mutually exclusive.')
    description = None
    with plt.style.context(style):
        if ax is None:
            if figsize is None:
                figsize = (7, 2.5)
            fig = plt.figure(figsize=figsize)
            ax = fig.add_subplot(111)
        for path in paths:
            data = json.loads(path.read_text())
            traces = {t["table"]: t for t in data["traces"]}
            if len(traces) > 1:
                if not table:
                    raise ValueError(
                        f"File contains multiple traces (table must be specified): {path}"
                    )
                if table not in traces:
                    print(
                        f'[bold yellow]Warning![/bold yellow] No trace for table "{table}" in this file: {path}'
                    )
                    continue
            trace = traces[table] if table else list(traces.values())[0]
            job_id = trace["jobId"]
            variant = trace.get("variant")
            iteration = trace.get("iteration")
            if len(trace["description"]) != 1:
                raise NotImplementedError()
            description = trace["description"][0]
            # Support unit-less metrics
            interval = trace["interval"]
            unit = trace.get("unit", "")
            y = trace["values"]
            x = [i * interval for i in range(len(y))]
            label = variant if variant else f"Job {job_id}"
            if iteration_in_label and iteration is not None:
                label += f" #{iteration}"
            ax.plot(x, y, label=label)
            ax.set_ylabel(description + (f" [{unit}]" if len(unit) > 0 else ""))
        ax.set_xlabel("Time [s]")
        ax.legend()
    if output_path:
        plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    if show:
        plt.show()
    return ax


def roofline_model(
    path: Path,
    precision: str = "dp",
    output_path: Path | str | None = None,
    show: bool = False,
    ax: Axes | None = None,
    figsize: tuple[float, float] | None = None,
    style: list[str] = ["default", "grid"],
    dpi: float = 300,
) -> Axes:
    data = json.loads(path.read_text())
    node_benchmarks = data["node_benchmarks"]
    assert precision in ["sp", "dp"]
    result_type = "peak"
    jobs = {k: v["results"][precision][result_type] for k, v in data["jobs"].items()}
    roofline_model: dict[str, float] = dict()
    if len(node_benchmarks) > 1:
        print(
            "[yellow]Multiple node types used! (Using lowest values for roofline ceiling.)[/yellow]"
        )
    for benchmark_data in node_benchmarks.values():
        for k, v in benchmark_data.items():
            roofline_model[k] = min(roofline_model.get(k, v), v)
    labels = [
        "BW " + k.split("_")[1].replace("mem", "dram").upper()
        for k in roofline_model.keys()
        if k.startswith("bandwidth")
    ]
    bandwidths = [v for k, v in roofline_model.items() if k.startswith("bandwidth")]
    peak_flops = roofline_model[
        "peakflops_avx512_fma" if precision == "dp" else "peakflops_sp_avx512_fma"
    ]
    ridge_points = [peak_flops / bw for bw in bandwidths]
    min_x = min([v["operational_intensity"] for v in jobs.values()])
    max_x = max([v["operational_intensity"] for v in jobs.values()] + ridge_points)
    oi = np.logspace(np.log10(min_x / 10), np.log10(max_x * 10), 500)

    def plot_roofline(ax, oi, bw_bytes, peak_flops, label, color=None, linestyle="--"):
        # Ridge point (intersection with peak)
        oi_ridge = peak_flops / bw_bytes

        # Bandwidth segment: left of ridge
        mask_bw = oi <= oi_ridge
        ax.loglog(
            oi[mask_bw],
            bw_bytes * oi[mask_bw],
            label=label,
            color=color,
            linestyle=linestyle,
        )

        # Compute segment: right of ridge
        mask_cp = oi >= oi_ridge
        ax.loglog(
            oi[mask_cp], np.full_like(oi[mask_cp], peak_flops), color=color, linewidth=2
        )

        return oi_ridge

    with plt.style.context(style):
        if ax is None:
            if figsize is None:
                figsize = (9, 6)
            fig = plt.figure(figsize=figsize)
            ax = fig.add_subplot(111)
        ridge_points = []
        for i, (bw, label) in enumerate(zip(bandwidths, labels)):
            ridge = plot_roofline(ax, oi, bw, peak_flops, label, color=f"C{i}")
            ridge_points.append(ridge)
        ax.loglog(
            oi,
            np.full_like(oi, peak_flops),
            color="k",
            linewidth=2,
            label=f"{precision.upper()} Peak FLOPs",
        )
        markers = ["o", "s", "^", "D", "v", "*"]  # Cycle through
        job_handles = []
        min_performance = np.inf
        for i, (job, v) in enumerate(jobs.items()):
            performance = v["performance"]
            min_performance = min(min_performance, performance)
            marker = markers[i % len(markers)]
            handle = ax.scatter(
                v["operational_intensity"],
                performance,
                s=80,
                marker=marker,
                zorder=10,
                label=job,
            )
            job_handles.append(handle)
        for x in ridge_points:
            ax.vlines(x, 0, peak_flops, "grey", linestyles=":", zorder=5)
        ax.set_ylim(bottom=min_performance / 10)
        ax.set_xlabel("Operational Intensity [FLOPs / Byte]")
        ax.set_ylabel("Performance [FLOPs / s]")
        ax.set_title("Roofline Model")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.grid(True, which="both", linestyle=":", linewidth=0.5)

        def format_x_ticks(value, tick_number):
            value_fmtd = str(value)
            if value_fmtd.endswith(".0"):
                value_fmtd = value_fmtd[:-2]
            return value_fmtd

        def format_y_ticks(value, tick_number):
            suffixes = [""] + list("kMGTPE")
            for i in range(len(suffixes)):
                if abs(value) < 1000:
                    break
                value /= 1000
            value_fmtd = str(value)
            if value_fmtd.endswith(".0"):
                value_fmtd = value_fmtd[:-2]
            return f"{value_fmtd}{suffixes[i]}"

        ax.xaxis.set_major_formatter(mticker.FuncFormatter(format_x_ticks))
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(format_y_ticks))
        handles, labels_ = ax.get_legend_handles_labels()
        bw_peak_handles = handles[: len(bandwidths) + 1]
        bw_peak_labels = labels_[: len(bandwidths) + 1]
        legend1 = ax.legend(
            bw_peak_handles,
            bw_peak_labels,
            loc="upper left",
            fontsize=9,
        )
        legend2 = ax.legend(
            job_handles,
            jobs.keys(),
            loc="lower right",
            fontsize=9,
            title="Jobs",
        )
        ax.add_artist(legend1)  # Keep the first legend
        for legend in [legend1, legend2]:
            legend.set_frame_on(True)
            frame = legend.get_frame()
            frame.set_facecolor(ax.get_facecolor())  # Match axes background
            frame.set_alpha(1)
        if output_path:
            plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
        if show:
            plt.show()
        return ax
