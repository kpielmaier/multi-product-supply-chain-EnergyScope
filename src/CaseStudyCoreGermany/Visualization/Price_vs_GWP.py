import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from Colors import colors_elasticity

# -----------------------------------------------
# Global style
# -----------------------------------------------
plt.rcParams.update({
    "text.usetex": False,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 16,
})

script_dir = os.path.dirname(os.path.abspath(__file__))

# -----------------------------------------------
# Directory structure
# -----------------------------------------------
pareto_dirs = {
    "high":   os.path.join(script_dir, "..", "ResultsHighPrice",   "Figures", "Pareto"),
    "low":    os.path.join(script_dir, "..", "ResultsLowPrice",    "Figures", "Pareto"),
    "normal": os.path.join(script_dir, "..", "ResultsNormalPrice", "Figures", "Pareto"),
}

data_dirs = {
    "high":   os.path.join(script_dir, "..", "DataHighPrice"),
    "low":    os.path.join(script_dir, "..", "DataLowPrice"),
    "normal": os.path.join(script_dir, "..", "DataNormalPrice"),
}

elasticity_files = {
    "elast_10pct":  "pareto_SW_vs_GWP_elast_10pct.json",
    "elast_5pct":   "pareto_SW_vs_GWP_elast_5pct.json",
    "elast_2_5pct": "pareto_SW_vs_GWP_elast_2_5pct.json",
    "demand_fixed": "pareto_SW_vs_GWP_demand_fixed.json",
}

legend_names = {
    "demand_fixed": "Fixed demand",
    "elast_2_5pct": "Elasticity = 2.5%",
    "elast_5pct":   "Elasticity = 5%",
    "elast_10pct":  "Elasticity = 10%",
}

# -----------------------------------------------
# JSON loader
# -----------------------------------------------
def load_pareto_jsons(folder):
    result = {}
    for tag, fname in elasticity_files.items():
        path = os.path.join(folder, fname)
        if os.path.exists(path):
            with open(path, "r") as fh:
                result[tag] = json.load(fh)
        else:
            print(f"[WARNING] Missing Pareto file: {path}")
    return result

# -----------------------------------------------
# Compute weighted annual average electricity price
# -----------------------------------------------
def compute_avg_price(folder_path):
    file = os.path.join(folder_path, "price.csv")
    if not os.path.exists(file):
        return None

    df = pd.read_csv(file)
    df = df[df["p"] == "ELECTRICITY"]
    if df.empty:
        return None

    df["price"] = df["price_M€_per_GWh"] * 1000
    df["weight"] = df["mult"] * df["t_op"]

    return float((df["price"] * df["weight"]).sum() / df["weight"].sum())

# -----------------------------------------------
# Construct subfolder name from Pareto point
# -----------------------------------------------
def folder_from_point(pt):
    eps = "NONE" if pt["epsilon"] is None else f"{pt['epsilon']:.2f}"
    return f"{pt['elasticity_tag']}_eps_{eps}"

# -----------------------------------------------
# Main plotting function
# -----------------------------------------------
def make_price_plot(pareto_dict, data_root, output_file):

    fig, (ax_top, ax_bottom) = plt.subplots(
        2, 1, figsize=(10, 8), sharex=True,
        gridspec_kw={"height_ratios": [1, 2]}
    )

    plot_data = {}
    all_prices = []

    # Collect price curves
    for tag, pts in pareto_dict.items():
        values = []
        for pt in pts:
            folder = folder_from_point(pt)
            avg_price = compute_avg_price(os.path.join(data_root, folder))
            if avg_price is not None:
                values.append((pt["TotalGWP"], avg_price))
                all_prices.append(avg_price)

        if values:
            plot_data[tag] = sorted(values)

    # Define zoom regions
    high_min = max(all_prices) - 8
    high_max = max(all_prices) + 1
    low_min  = min(all_prices) - 1
    low_max  = min(all_prices) + 6

    # Plot
    for tag, pairs in plot_data.items():
        gwp, prices = zip(*pairs)
        color = colors_elasticity.get(tag, "black")
        label = legend_names.get(tag, tag)

        ax_top.plot(gwp, prices, marker="o", linestyle="-", linewidth=2,
                    color=color, label=label)
        ax_bottom.plot(gwp, prices, marker="o", linestyle="-", linewidth=2,
                       color=color)

    # Apply zoom
    ax_top.set_ylim(high_min, high_max)
    ax_bottom.set_ylim(low_min, low_max)
    ax_top.set_xlim(ax_bottom.get_xlim())

    # Remove adjoining spines
    ax_top.spines["bottom"].set_visible(False)
    ax_bottom.spines["top"].set_visible(False)

    # Remove all x-axis ticks and labels from the top subplot
    ax_top.tick_params(axis="x", which="both", bottom=False, top=False, labelbottom=False)


    # Break marks
    d = 0.015  # size of break marks

    # arguments for the lines
    kwargs = dict(transform=ax_top.transAxes, color='k', clip_on=False)
    ax_top.plot((-d, +d), (0, 0), **kwargs)       # left diagonal
    ax_top.plot((1-d, 1+d), (0, 0), **kwargs)     # right diagonal

    kwargs.update(transform=ax_bottom.transAxes)
    ax_bottom.plot((-d, +d), (1, 1), **kwargs)    # left diagonal
    ax_bottom.plot((1-d, 1+d), (1, 1), **kwargs)  # right diagonal
    
    # Axis labels
    ax_bottom.set_ylabel("Yearly Average Electricity Price [€/MWh]")
    ax_bottom.yaxis.set_label_coords(-0.05, 0.75)
    ax_bottom.set_xlabel("Total GWP [ktCO$_2$/year]")

    # Grid
    ax_top.grid(True)
    ax_bottom.grid(True)

    # Legend (top axis only)
    ax_top.legend(fontsize=16, loc="upper right")

    # Save
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_file, dpi=250, bbox_inches="tight")
    plt.close()

    print(f"Saved: {output_file}")

# -----------------------------------------------
# Run for all scenarios
# -----------------------------------------------
for scenario in ["high", "low", "normal"]:
    make_price_plot(
        load_pareto_jsons(pareto_dirs[scenario]),
        data_dirs[scenario],
        os.path.join(pareto_dirs[scenario], f"Price_vs_GWP_{scenario.capitalize()}.pdf")
    )
