import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# ---------------------------------------------------------
# Matplotlib defaults
# ---------------------------------------------------------

plt.rcParams.update({
    "text.usetex": False,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 16,
})

# ---------------------------------------------------------
# USER SETTINGS
# ---------------------------------------------------------

COMPARE_CASES = {
    "elast_2_5pct": r"DataNormalPrice\elast_2_5pct_eps_0.00",
    "elast_5pct":   r"DataNormalPrice\elast_5pct_eps_0.00",
    "elast_10pct":  r"DataNormalPrice\elast_10pct_eps_0.00",
}

LEGEND_NAMES = {
    "elast_2_5pct": "Elasticity = 2.5%",
    "elast_5pct":   "Elasticity = 5%",
    "elast_10pct":  "Elasticity = 10%",
}

COLORS_ELASTICITY = {
    "elast_2_5pct": "#d62728",
    "elast_5pct":   "#1f77b4",
    "elast_10pct":  "#2ca02c",
}

TARGET_CT   = "ELECTRICITY"
TARGET_HOUR = 12
TARGET_TD   = 6

# ---------------------------------------------------------
# PATH SETUP
# ---------------------------------------------------------

script_dir   = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

# ---------------------------------------------------------
# Helper CSV readers
# ---------------------------------------------------------

def read_param_csv(filename, value_col, data_dir):
    df = pd.read_csv(os.path.join(data_dir, filename))
    df.rename(columns={
        "index0": "k", "index1": "ct", "index2": "n",
        "index3": "h", "index4": "td", value_col: "val"
    }, inplace=True)
    return df

def to_dict(df):
    val_col = [c for c in df.columns if c not in ["k", "ct", "n", "h", "td"]][0]
    return {(r.k, r.ct, r.n, r.h, r.td): getattr(r, val_col)
            for r in df.itertuples(index=False)}

def to_dict_simple(df, val_col):
    return {(r.ct, r.n, r.h, r.td): getattr(r, val_col)
            for r in df.itertuples(index=False)}

# ---------------------------------------------------------
# Load a single case (with reference values)
# ---------------------------------------------------------

def load_case(case_dir, load_ref=False):
    a_df     = read_param_csv("a.csv", "a.val", case_dir)
    D_df     = read_param_csv("D.csv", "D.val", case_dir)
    p_pw_df  = read_param_csv("p_pw.csv", "p_pw.val", case_dir)

    p_pw_df["p_pw"] *= 1000.0

    data = {
        "a": to_dict(a_df),
        "D": to_dict(D_df),
        "p_pw": to_dict(p_pw_df),
        "nodes": sorted(a_df["n"].unique()),
    }

    if load_ref:
        d_ref_df = pd.read_csv(os.path.join(case_dir, "d_ref.csv"))
        p_ref_df = pd.read_csv(os.path.join(case_dir, "p_ref.csv"))
        p_ref_df["p_ref"] *= 1000.0

        data["d_ref"] = to_dict_simple(d_ref_df, "d_ref")
        data["p_ref"] = to_dict_simple(p_ref_df, "p_ref")

    return data

# ---------------------------------------------------------
# Load all cases
# ---------------------------------------------------------

case_data = {}

for tag, rel_path in COMPARE_CASES.items():
    case_path = os.path.join(project_root, rel_path)
    print(f"Loading case: {case_path}")
    case_data[tag] = load_case(case_path, load_ref=(tag == "elast_5pct"))

# Base case for references
base = case_data["elast_5pct"]
node_ref = base["nodes"][0]
h  = TARGET_HOUR
td = TARGET_TD
ct = TARGET_CT

# ---------------------------------------------------------
# Plot setup
# ---------------------------------------------------------

fig, ax = plt.subplots(figsize=(8, 6))

legend_handles = []

# ---------------------------------------------------------
# Plot inverse demand curves
# ---------------------------------------------------------

for tag, data in case_data.items():

    a_dict    = data["a"]
    D_dict    = data["D"]
    p_pw_dict = data["p_pw"]

    seg_keys = sorted({
        k for (k, ct_i, n_i, h_i, td_i) in a_dict.keys()
        if (ct_i, n_i, h_i, td_i) == (ct, node_ref, h, td)
    })

    d_curve = [0.0]
    p_curve = [p_pw_dict.get((0, ct, node_ref, h, td), np.nan)]

    cum = 0.0
    for k in seg_keys:
        cum += D_dict[(k, ct, node_ref, h, td)]
        d_curve.append(cum)
        p_curve.append(p_pw_dict[(k, ct, node_ref, h, td)])

    ax.plot(
        d_curve,
        p_curve,
        lw=2.5,
        color=COLORS_ELASTICITY[tag],
        zorder=2
    )

    legend_handles.append(
        Line2D([], [], color=COLORS_ELASTICITY[tag], lw=2.5,
               label=LEGEND_NAMES[tag])
    )

# ---------------------------------------------------------
# Reference lines + operating point
# ---------------------------------------------------------

d_ref = base["d_ref"].get((ct, node_ref, h, td), np.nan)
p_ref = base["p_ref"].get((ct, node_ref, h, td), np.nan)

# Reference demand (legend, no number)
if not np.isnan(d_ref):
    ax.axvline(d_ref, color="black", linewidth=1.5, zorder=5)
    legend_handles.append(
        Line2D([], [], color="black", lw=1.5,
               label="Reference demand")
    )

# Reference price (two-line legend entry)
if not np.isnan(p_ref):
    ax.axhline(p_ref, color="gray", linestyle="--", linewidth=1.5, zorder=5)

    legend_handles.append(
        Line2D(
            [], [],
            color="gray",
            linestyle="--",
            lw=1.5,
            marker="x",
            markersize=8,
            markeredgewidth=2,
            markeredgecolor="gray",
            markerfacecolor="none",
            label="Reference price"
        )
    )
    legend_handles.append(
        Line2D([], [], color="none", lw=0,
               label=f"= {p_ref:.2f} €/MWh")
    )

# Operating point (cross), not in legend
if not np.isnan(d_ref) and not np.isnan(p_ref):
    ax.scatter(
        d_ref, p_ref,
        color="gray",
        marker="x",
        s=70,
        linewidth=2,
        zorder=6
    )

# ---------------------------------------------------------
# Axes and formatting
# ---------------------------------------------------------

ax.set_xlabel("Demand [GW]")
ax.set_ylabel("Price [€/MWh]")
ax.grid(True)

ax.set_xlim(0.75 * max(d_curve), 1.1 * max(d_curve))
ax.set_ylim(0, max(p_curve) * 0.1)

ax.legend(
    handles=legend_handles,
    fontsize=16,
    loc="upper right",
    frameon=True,
    edgecolor="gray"
)

# ---------------------------------------------------------
# Save figure
# ---------------------------------------------------------

output_dir = os.path.join(project_root, COMPARE_CASES["elast_5pct"])
save_path = os.path.join(
    output_dir,
    f"Demand_Elasticity_Comparison_{ct}_TD{td}_H{h}_NormalPrice.pdf"
)

plt.tight_layout()
plt.savefig(save_path, dpi=300)
plt.close()

print(f"\nSaved figure to:\n{save_path}\n")
