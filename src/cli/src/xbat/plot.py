import importlib
import json
from pathlib import Path
from typing import Iterable, List, Tuple
from matplotlib import pyplot as plt
from matplotlib.axes import Axes

importlib.import_module("scienceplots")


def plot_metric(
    paths: Iterable[Path],
    output_path: Path | str | None = None,
    show: bool = False,
    ax: Axes | None = None,
    figsize: Tuple[float, float] | None = None,
    iteration_in_label: bool = True,
    style: List[str] = ["default", "grid"],
    dpi: float = 300,
) -> Axes:
    if ax is not None and figsize is not None:
        raise ValueError('Parameters "ax" and "figsize" are mutually exclusive.')
    metric = None
    with plt.style.context(style):
        if ax is None:
            if figsize is None:
                figsize = (7, 2.5)
            fig = plt.figure(figsize=figsize)
            ax = fig.add_subplot(111)
        for path in paths:
            data = json.loads(path.read_text())
            traces = data["traces"]
            for trace in traces:
                variant = trace["variant"]
                iteration = trace["iteration"]
                if metric and metric != trace["metric"]:
                    raise ValueError("Metrics are not the same across traces.")
                metric = trace["metric"]
                interval = trace["interval"]
                unit = trace["unit"]
                y = trace["values"]
                x = [i * interval for i in range(len(y))]
                label = variant
                if iteration_in_label:
                    label += f" #{iteration}"
                ax.plot(x, y, label=label)
                ax.set_ylabel(f"{metric} [{unit}]")
        ax.set_xlabel("Time [s]")
        ax.legend()
    if output_path:
        plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    if show:
        plt.show()
    return ax
