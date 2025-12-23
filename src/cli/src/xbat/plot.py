import importlib
import json
from pathlib import Path
from typing import Iterable, List, Tuple
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from rich import print

importlib.import_module("scienceplots")


def plot_metric(
    paths: Iterable[Path],
    table: str | None = None,
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
