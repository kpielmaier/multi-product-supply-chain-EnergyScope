import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from Colors import colors_end_use_type

plt.rcParams.update({
    "text.usetex": False,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 16,
})

# ---------------------------------------------------------
# USER SETTINGS
# ---------------------------------------------------------

CASE_DIR    = r"DataNormalPrice\elast_5pct_eps_0.00"   # <-- choose case
TARGET_HOUR = 12                                      # <-- choose hour
TARGET_TD   = 6                                     # <-- choose typical day
TARGET_CT   = "ELECTRICITY"                         # <-- only plot electricity

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
# Load CSVs
# ---------------------------------------------------------

a_df     = read_param_csv("a.csv", "a.val", data_dir)
b_df     = read_param_csv("b.csv", "b.val", data_dir)
D_df     = read_param_csv("D.csv", "D.val", data_dir)
p_pw_df  = read_param_csv("p_pw.csv", "p_pw.val", data_dir)

d_ref_df = pd.read_csv(os.path.join(data_dir, "d_ref.csv"))
p_ref_df = pd.read_csv(os.path.join(data_dir, "p_ref.csv"))
price_df = pd.read_csv(os.path.join(data_dir, "price.csv"))
d_vals   = pd.read_csv(os.path.join(data_dir, "d_vals.csv"))

p_pw_df["p_pw"] *= 1000.0
p_ref_df["p_ref"]   *= 1000.0

# Convert to dictionaries
a_dict, b_dict, D_dict, p_pw_dict = map(to_dict, [a_df, b_df, D_df, p_pw_df])
d_ref_dict    = to_dict_simple(d_ref_df, "d_ref")
p_ref_dict    = to_dict_simple(p_ref_df, "p_ref")
d_actual_dict = to_dict_simple(d_vals,   "val")


# ---------------------------------------------------------
# Metadata
# ---------------------------------------------------------

node_ref     = sorted(a_df["n"].unique())[0]
available_h  = sorted(a_df["h"].unique())
available_td = sorted(a_df["td"].unique())

if TARGET_HOUR not in available_h:
    raise ValueError(f"Hour {TARGET_HOUR} not available.")
if TARGET_TD not in available_td:
    raise ValueError(f"Typical day {TARGET_TD} not available.")

h  = TARGET_HOUR
td = TARGET_TD

print(f"Plotting for: CT={TARGET_CT}, TD={td}, hour={h}")


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def get_price(ct, n, h, td):
    match = price_df[
        (price_df["p"] == ct) &
        (price_df["n"] == n) &
        (price_df["h"] == h) &
        (price_df["td"] == td)
    ]
    return match["price_€_per_MWh"].values[0] if not match.empty else np.nan


def get_curve(ct, n, h, td):
    seg_keys = sorted({
        k for (k, ct_i, n_i, h_i, td_i) in a_dict.keys()
        if (ct_i, n_i, h_i, td_i) == (ct, n, h, td)
    })

    d_curve = [0.0]
    p_curve = [p_pw_dict.get((0, ct, n, h, td), np.nan)]
    cum = 0

    for k in seg_keys:
        cum += D_dict[(k, ct, n, h, td)]
        d_curve.append(cum)
        p_curve.append(p_pw_dict[(k, ct, n, h, td)])

    return d_curve, p_curve, seg_keys

# ---------------------------------------------------------
# Create SINGLE-PANEL figure for ELECTRICITY
# ---------------------------------------------------------

fig, ax = plt.subplots(figsize=(7, 6))

ct = TARGET_CT

d_curve, p_curve, segments = get_curve(ct, node_ref, h, td)

if not segments:
    raise RuntimeError("No demand segments found for electricity.")

# ---------------------------------------------------------
# VOLL or elastic?
# ---------------------------------------------------------

is_voll = all(b_dict[(k, ct, node_ref, h, td)] == 0 for k in segments)

if is_voll:
    ...
else:
    # Reference + actual values
    d_ref = d_ref_dict.get((ct, node_ref, h, td), np.nan)
    p_ref = p_ref_dict.get((ct, node_ref, h, td), np.nan)
    d_act = d_actual_dict.get((ct, node_ref, h, td), np.nan)
    p_act = get_price(ct, node_ref, h, td)

    # Plot inverse demand curve (no legend entry)
    color = colors_end_use_type.get(ct, "black")
    ax.plot(d_curve, p_curve, lw=2, color=color)

    legend_entries = []

    # --------------------
    # REFERENCE LINES (both red)
    # --------------------
    if not np.isnan(d_ref):
        ax.axvline(d_ref, color="black", linewidth=2)

    if not np.isnan(p_ref):
        ax.axhline(p_ref, color="black", linestyle="--", linewidth=2)

    # Add the red “x” at intersection of reference lines
    if not np.isnan(d_ref) and not np.isnan(p_ref):
        ax.scatter(
            d_ref, p_ref,
            color="black",
            s=60,
            marker="x",
            linewidth=2,
            zorder=10
        )
        legend_entries.append((
            "Reference demand",
            plt.Line2D([], [], color="black", lw=2)
        ))
        # legend_entries.append((
        #     f"= {d_ref:.2f} GW",
        #     plt.Line2D([], [], color="none", lw=0)
        # ))

        legend_entries.append((
            "Reference price",
            plt.Line2D([], [], color="black", linestyle="--", marker="x", lw=2)
        ))
        # legend_entries.append((
        #     f"= {p_ref:.2f} €/MWh",
        #     plt.Line2D([], [], color="none", lw=0)
        # ))

    # # --------------------
    # # ACTUAL VALUES (green)
    # # --------------------
    # if not np.isnan(d_act):
    #     ax.axvline(d_act, color="green", linewidth=2)
    #     legend_entries.append((
    #         "Actual demand",
    #         plt.Line2D([], [], color="green", lw=2)
    #     ))
    #     legend_entries.append((
    #         f"= {d_act:.2f} GW",
    #         plt.Line2D([], [], color="none", lw=0)
    #     ))

    # if not np.isnan(p_act):
    #     ax.axhline(p_act, color="green", linestyle="--", linewidth=2)
    #     ax.scatter(
    #         d_act, p_act,
    #         color="green",
    #         s=60,
    #         marker="x",
    #         linewidth=2,
    #         zorder=10
    #     )
    #     legend_entries.append((
    #         "Actual price",
    #         plt.Line2D([], [], color="green", linestyle="--", marker="x", lw=2)
    #     ))
    #     legend_entries.append((
    #         f"= {p_act:.2f} €/MWh",
    #         plt.Line2D([], [], color="none", lw=0)
    #     ))

    # Build legend
    ax.legend(
        [e[1] for e in legend_entries],
        [e[0] for e in legend_entries],
        fontsize=16,
        loc="upper right",
        frameon=True,
        edgecolor="gray"
    )


# ---------------------------------------------------------
# Axes, formatting
# ---------------------------------------------------------

ax.set_xlabel("Demand [GW]")
ax.set_ylabel("Price [€/MWh]")
ax.grid(True)
ax.set_title("")

# Zoom
ax.set_xlim(0.75 * max(d_curve), max(d_curve) * 1.1)
ax.set_ylim(0, max(p_curve) * 0.025)


# ---------------------------------------------------------
# Save figure
# ---------------------------------------------------------

save_path = os.path.join(output_dir, f"Demand_Zoomed_{ct}_TD{td}_H{h}.pdf")
plt.tight_layout()
plt.savefig(save_path, dpi=300)
plt.close()

print(f"\nSaved ELECTRICITY-only zoomed figure to:\n{save_path}\n")
