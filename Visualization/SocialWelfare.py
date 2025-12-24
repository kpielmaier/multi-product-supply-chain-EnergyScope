import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from Colors import colors_end_use_type

# ---------------------------------------------------------
# Matplotlib configuration
# ---------------------------------------------------------

plt.rcParams.update({
    "text.usetex": False,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 16,
})

LW = 2  # global line width

# ---------------------------------------------------------
# USER SETTINGS
# ---------------------------------------------------------

CASE_DIR    = r"DataNormalPrice\elast_5pct_eps_0.00"
TARGET_CT   = "ELECTRICITY"
TARGET_HOUR = 19
TARGET_TD   = 3

# ---------------------------------------------------------
# PATH SETUP
# ---------------------------------------------------------

script_dir   = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
case_dir     = os.path.join(project_root, CASE_DIR)

print(f"\n=== Processing case: {case_dir} ===")

data_dir   = case_dir
output_dir = case_dir

# ---------------------------------------------------------
# Helper reading functions
# ---------------------------------------------------------

def read_param_csv(filename, value_col, data_dir):
    df = pd.read_csv(os.path.join(data_dir, filename))
    df.rename(columns={
        "index0": "k",
        "index1": "ct",
        "index2": "n",
        "index3": "h",
        "index4": "td",
        value_col: "val",
    }, inplace=True)
    return df


def to_dict(df):
    val_col = [c for c in df.columns if c not in ["k", "ct", "n", "h", "td"]][0]
    return {
        (r.k, r.ct, r.n, r.h, r.td): getattr(r, val_col)
        for r in df.itertuples(index=False)
    }


def to_dict_simple(df, val_col):
    return {
        (r.ct, r.n, r.h, r.td): getattr(r, val_col)
        for r in df.itertuples(index=False)
    }

# ---------------------------------------------------------
# Load CSVs
# ---------------------------------------------------------

a_df     = read_param_csv("a.csv",    "a.val",    data_dir)
b_df     = read_param_csv("b.csv",    "b.val",    data_dir)
D_df     = read_param_csv("D.csv",    "D.val",    data_dir)
p_pw_df  = read_param_csv("p_pw.csv", "p_pw.val", data_dir)

price_df = pd.read_csv(os.path.join(data_dir, "price.csv"))
d_vals   = pd.read_csv(os.path.join(data_dir, "d_vals.csv"))

p_pw_df["p_pw"] *= 1000.0

a_dict, b_dict, D_dict, p_pw_dict = map(to_dict, [a_df, b_df, D_df, p_pw_df])
d_actual_dict = to_dict_simple(d_vals, "val")

d_ref_df = pd.read_csv(os.path.join(data_dir, "d_ref.csv"))
d_ref_dict = to_dict_simple(d_ref_df, "d_ref")

# ---------------------------------------------------------
# Metadata
# ---------------------------------------------------------

node_ref = sorted(a_df["n"].unique())[0]
h  = TARGET_HOUR
td = TARGET_TD
ct = TARGET_CT

# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def get_price(ct, n, h, td):
    match = price_df[
        (price_df["p"]  == ct) &
        (price_df["n"]  == n)  &
        (price_df["h"]  == h)  &
        (price_df["td"] == td)
    ]
    return match["price_€_per_MWh"].values[0]


def get_demand_curve(ct, n, h, td):
    seg_keys = sorted(
        k for (k, ct_i, n_i, h_i, td_i) in a_dict
        if (ct_i, n_i, h_i, td_i) == (ct, n, h, td)
    )

    d_curve = [0.0]
    p_curve = [p_pw_dict[(0, ct, n, h, td)]]

    cum = 0.0
    for k in seg_keys:
        cum += D_dict[(k, ct, n, h, td)]
        d_curve.append(cum)
        p_curve.append(p_pw_dict[(k, ct, n, h, td)])

    return np.array(d_curve), np.array(p_curve)


def fake_merit_order(d_star, p_star, renew_share=0.825, n_steps=6):
    """
    Stylized merit-order curve with:
    - Zero marginal cost renewables up to renew_share * d_star
    - Uniform step heights
    - One step exactly at the market-clearing price
    """

    # Renewable block
    d_renew = renew_share * d_star
    d_max   = 1.4 * d_star

    # Demand steps (even)
    d_steps = np.linspace(d_renew, d_max, n_steps + 1)

    # Identify clearing step
    step_idx = np.searchsorted(d_steps, d_star) - 1
    step_idx = max(step_idx, 0)

    # Uniform price step size
    dp = 0.5 * p_star

    # Construct evenly spaced prices centered on clearing price
    p_steps = p_star + dp * (np.arange(n_steps) - step_idx)

    # Ensure non-negative prices
    p_steps = np.clip(p_steps, 0.0, None)

    # Assemble stepwise curve
    x = [0.0, d_renew]
    y = [0.0, 0.0]

    for i in range(n_steps):
        x.extend([d_steps[i], d_steps[i + 1]])
        y.extend([p_steps[i], p_steps[i]])

    return np.array(x), np.array(y)

# ---------------------------------------------------------
# Plot
# ---------------------------------------------------------

fig, ax = plt.subplots(figsize=(9, 6))
legend_handles = []

d_curve, p_curve = get_demand_curve(ct, node_ref, h, td)
d_act = d_actual_dict[(ct, node_ref, h, td)]
p_act = get_price(ct, node_ref, h, td)
d_ref = d_ref_dict[(ct, node_ref, h, td)]

# Demand
ax.plot(d_curve, p_curve, lw=LW,
        color=colors_end_use_type.get(ct, "blue"), zorder=4)

legend_handles.append(
    Line2D([], [], lw=LW, color=colors_end_use_type.get(ct, "blue"),
           label="Elastic demand")
)

# Supply
d_mo, p_mo = fake_merit_order(d_act, p_act)
ax.plot(d_mo, p_mo, lw=LW, color="red", zorder=3)

legend_handles.append(
    Line2D([], [], lw=LW, color="red", label="Supply (merit order)")
)

# Reference demand (black)
ax.axvline(d_ref, color="black", lw=LW, linestyle="-", zorder=4)

legend_handles.append(
    Line2D([], [], lw=LW, color="black", label="Fixed demand")
)

# Actual demand (green)
ax.axvline(d_act, color="green", lw=LW, zorder=5)
ax.axhline(p_act, color="green", lw=LW, linestyle="--", zorder=5)
ax.scatter(d_act, p_act, color="green", marker="x", s=70, lw=LW, zorder=10)

legend_handles.append(
    Line2D([], [], lw=LW, color="green", label="Actual demand")
)

legend_handles.append(
    Line2D([], [], lw=LW, linestyle="--", color="green",
           label="Market clearing price")
)

# ---------------------------------------------------------
# Surplus and cost shading
# ---------------------------------------------------------

d_fine = np.linspace(0, d_act, 600)
p_demand_fine = np.interp(d_fine, d_curve, p_curve)
p_supply_fine = np.interp(d_fine, d_mo, p_mo)

# Consumer surplus
ax.fill_between(
    d_fine, p_demand_fine, p_act,
    where=p_demand_fine >= p_act,
    facecolor="none", hatch="///",
    edgecolor=colors_end_use_type.get(ct, "blue"),
    zorder=1
)

legend_handles.append(
    Patch(facecolor="none", hatch="///",
          edgecolor=colors_end_use_type.get(ct, "blue"),
          label="Consumer surplus")
)

# Producer surplus
ax.fill_between(
    d_fine, p_act, p_supply_fine,
    where=p_act >= p_supply_fine,
    facecolor="none", hatch="///",
    edgecolor="red",
    zorder=1
)

legend_handles.append(
    Patch(facecolor="none", hatch="///",
          edgecolor="red",
          label="Producer surplus")
)

# Total cost (area under supply)
ax.fill_between(
    d_fine, 0.0, p_supply_fine,
    facecolor="none", hatch="///",
    edgecolor="orange",
    zorder=0
)

legend_handles.append(
    Patch(facecolor="none", hatch="///",
          edgecolor="orange",
          label="Operating costs")
)

# ---------------------------------------------------------
# Formatting
# ---------------------------------------------------------

ax.set_xlabel("Demand [GW]")
ax.set_ylabel("Price [€/MWh]")
ax.grid(True)
ax.set_xlim(max(d_curve) * 0.7, max(d_curve) * 1.1)
ax.set_ylim(0, max(p_curve) * 0.025)

ax.legend(
    handles=legend_handles,
    loc="center left",
    bbox_to_anchor=(1.02, 0.5),
    frameon=True,
    edgecolor="gray",
    fontsize=16
)

plt.tight_layout()
plt.savefig(
    os.path.join(output_dir,
    f"Demand_Surplus_TotalCost_{ct}_TD{td}_H{h}.pdf"),
    dpi=300,
    bbox_inches="tight"
)
plt.close()

print("Saved surplus + total cost figure.")
