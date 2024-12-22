"""Utils methods for file and asset manipulation in the context of batch processing."""
from __future__ import annotations

import os
import re
from datetime import datetime as dt

import ee
import httplib2
import numpy as np
from anyascii import anyascii
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.colors import to_rgba


def format_description(description: str) -> str:
    """Format a name to be accepted as a Task description.

    The rule is:
    The description must contain only the following characters: a..z, A..Z,0..9, ".", ",", ":", ";",
    "_" or "-". The description must be at most 100 characters long.

    Args:
        description: The description to format.

    Returns:
        The formatted description.
    """
    replacements = [
        [[" "], "_"],
        [["/"], "-"],
        [["?", "!", "¿", "*"], "."],
        [["(", ")", "[", "]", "{", "}"], ":"],
    ]

    desc = anyascii(description)
    for chars, rep in replacements:
        pattern = "|".join(re.escape(c) for c in chars)
        desc = re.sub(pattern, rep, desc)  # type: ignore

    return desc[:100]


def format_asset_id(description: str) -> str:
    """Format a name to be accepted as an asset Id.

    The rule is:
    Each segment must contain only the following characters: a..z, A..Z, 0..9, "_" or "-".
    Each segment must be at least 1 character long and at most 100 characters long.

    Args:
        description: The description to format.

    Returns:
        The formatted description.
    """
    replacements = [
        [[" "], "_"],
        [["/"], "-"],
        [["?", "!", "¿", "*"], "."],
        [["(", ")", "[", "]", "{", "}", ";", ":", ",", "."], "_"],
    ]

    desc = anyascii(description)
    for chars, rep in replacements:
        pattern = "|".join(re.escape(c) for c in chars)
        desc = re.sub(pattern, rep, desc)  # type: ignore

    return desc


def plot_data(
    type: str,
    data: dict,
    label_name: str,
    colors: list = [],
    ax: Axes | None = None,
    **kwargs,
) -> Axes:
    """Plotting mechanism used in all the plotting functions.

    It binds the matplotlib capabilities with the data aggregated by different xes.
    the shape of the data should as follows:

    .. code-block::

        {
            "label1": {"properties1": value1, "properties2": value2, ...}
            "label2": {"properties1": value1, "properties2": value2, ...},
            ...
        }

    Args:
        type: The type of plot to use. can be any type of plot from the python lib `matplotlib.pyplot`. If the one you need is missing open an issue!
        data: the data to use as inputs of the graph. Please follow the format specified in the documentation.
        label_name: The name of the property that was used to generate the labels
        property_names: The list of names that was used to name the values. They will be used to order the keys of the data dictionary.
        colors: A list of colors to use for the plot. If not provided, the default colors from the matplotlib library will be used.
        ax: The matplotlib axes to use. If not provided, the plot will be sent to a new figure.
        kwargs: Additional arguments from the ``pyplot`` chat type selected.
    """
    # define the ax if not provided by the user
    if ax is None:
        _, ax = plt.subplots()

    # gather the data from parameters
    labels = list(data.keys())
    props = list(data[labels[0]].keys())
    colors = colors if colors else plt.get_cmap("tab10").colors

    # draw the chart based on the type
    if type == "plot":
        for i, label in enumerate(labels):
            kwargs["color"] = colors[i]
            name = props[0] if len(props) == 1 else "Properties values"
            values = list(data[label].values())
            ax.plot(props, values, label=label, **kwargs)
            ax.set_ylabel(name)
            ax.set_xlabel(f"Features (labeled by {label_name})")
            grid_axis = "y"

    elif type == "scatter":
        for i, label in enumerate(labels):
            kwargs["color"] = colors[i]
            name = props[0] if len(props) == 1 else "Properties values"
            values = list(data[label].values())
            ax.scatter(props, values, label=label, **kwargs)
            ax.set_ylabel(name)
            ax.set_xlabel(f"Features (labeled by {label_name})")
            grid_axis = "y"

    elif type == "fill_between":
        for i, label in enumerate(labels):
            kwargs["facecolor"] = to_rgba(colors[i], 0.2)
            kwargs["edgecolor"] = to_rgba(colors[i], 1)
            name = props[0] if len(props) == 1 else "Properties values"
            values = list(data[label].values())
            ax.fill_between(props, values, label=label, **kwargs)
            ax.set_ylabel(name)
            ax.set_xlabel(f"Features (labeled by {label_name})")
            grid_axis = "y"

    elif type == "bar":
        x = np.arange(len(props))
        width = 1 / (len(labels) + 0.8)
        margin = width / 10
        kwargs["width"] = width - margin
        ax.set_xticks(x + width * len(labels) / 2, props)
        for i, label in enumerate(labels):
            kwargs["color"] = colors[i]
            values = list(data[label].values())
            ax.bar(x + width * i, values, label=label, **kwargs)
        grid_axis = "y"

    elif type == "barh":
        y = np.arange(len(props))
        height = 1 / (len(labels) + 0.8)
        margin = height / 10
        kwargs["height"] = height - margin
        ax.set_yticks(y + height * len(labels) / 2, props)
        for i, label in enumerate(labels):
            kwargs["color"] = colors[i]
            values = list(data[label].values())
            ax.barh(y + height * i, values, label=label, **kwargs)
        grid_axis = "x"

    elif type == "stacked":
        x = np.arange(len(props))
        bottom = np.zeros(len(props))
        ax.set_xticks(x, props)
        for i, label in enumerate(labels):
            kwargs.update(color=colors[i], bottom=bottom)
            values = list(data[label].values())
            ax.bar(x, values, label=label, **kwargs)
            bottom += values
        grid_axis = "y"

    elif type == "pie":
        if len(labels) != 1:
            raise ValueError("Pie chart can only be used with one property")
        kwargs["autopct"] = kwargs.get("autopct", "%1.1f%%")
        kwargs["normalize"] = kwargs.get("normalize", True)
        kwargs["labeldistance"] = kwargs.get("labeldistance", None)
        kwargs["wedgeprops"] = kwargs.get("wedgeprops", {"edgecolor": "w"})
        kwargs["textprops"] = kwargs.get("textprops", {"color": "w"})
        kwargs.update(autopct="%1.1f%%", colors=colors)
        values = [data[labels[0]][p] for p in props]
        ax.pie(values, labels=props, **kwargs)
        grid_axis = "y"

    elif type == "donut":
        if len(labels) != 1:
            raise ValueError("Pie chart can only be used with one property")
        kwargs["autopct"] = kwargs.get("autopct", "%1.1f%%")
        kwargs["normalize"] = kwargs.get("normalize", True)
        kwargs["labeldistance"] = kwargs.get("labeldistance", None)
        kwargs["wedgeprops"] = kwargs.get("wedgeprops", {"width": 0.6, "edgecolor": "w"})
        kwargs["textprops"] = kwargs.get("textprops", {"color": "w"})
        kwargs["pctdistance"] = kwargs.get("pctdistance", 0.7)
        kwargs.update(autopct="%1.1f%%", colors=colors)
        values = [data[labels[0]][p] for p in props]
        ax.pie(values, labels=props, **kwargs)
        grid_axis = "y"

    elif type == "date":
        for i, label in enumerate(labels):
            kwargs["color"] = colors[i]
            x, y = list(data[label].keys()), list(data[label].values())
            ax.plot(x, y, label=label, **kwargs)
        ax.set_xlabel("Date")
        grid_axis = "both"

    elif type == "doy":
        xmin, xmax = 366, 0  # inverted initialization to get the first iteration values
        for i, label in enumerate(labels):
            kwargs["color"] = colors[i]
            x, y = list(data[label].keys()), list(data[label].values())
            ax.plot(x, y, label=label, **kwargs)
            ax.set_xlabel("Day of year")
            grid_axis = "both"
            dates = [dt(2023, i + 1, 1) for i in range(12)]
            idates = [int(d.strftime("%j")) - 1 for d in dates]
            ndates = [d.strftime("%B")[:3] for d in dates]
            ax.set_xticks(idates, ndates)
            xmin, xmax = min(xmin, min(x)), max(xmax, max(x))
        ax.set_xlim(xmin - 5, xmax + 5)

    else:
        raise ValueError(f"Type {type} is not (yet?) supported")

    # customize the layout of the axis
    ax.grid(axis=grid_axis)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left")

    # make sure the canvas is only rendered once.
    ax.figure.canvas.draw_idle()

    return ax


def initialize_documentation():
    """Initialize Earth Engine Python API in the context of the Documentation build.

    Warning:
        This method is only used in the documentation build and should not be used in a production environment.
        ``geetools`` need to be imported prior to import this function.
    """
    # use a saved service account key if available
    if "EARTHENGINE_SERVICE_ACCOUNT" in os.environ:
        private_key = os.environ["EARTHENGINE_SERVICE_ACCOUNT"]
        # small massage of the key to remove the quotes coming from RDT
        private_key = (
            private_key[1:-1] if re.compile(r"^'[^']*'$").match(private_key) else private_key
        )
        ee.Initialize.geetools.from_service_account(private_key)

    elif "EARTHENGINE_PROJECT" in os.environ:
        ee.Initialize(project=os.environ["EARTHENGINE_PROJECT"], http_transport=httplib2.Http())

    else:
        raise ValueError(
            "EARTHENGINE_SERVICE_ACCOUNT or EARTHENGINE_PROJECT environment variable is missing"
        )

    pass
