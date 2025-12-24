import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from Colors import colors_end_use_type


# ---------------------------------------------------------
# USER SETTINGS
# ---------------------------------------------------------

TARGET_HOUR = 12         # hour to plot
TARGET_TD   = 6          # typical day to plot
CASE_DIR    = "DataNormalPrice\elast_5pct_eps_26670.39"   # relative to project root


# ---------------------------------------------------------
# Path setup
# ---------------------------------------------------------

script_dir   = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
case_dir     = os.path.join(project_root, CASE_DIR)

print(f"\n=== Processing case: {case_dir} ===\n")

data_dir   = case_dir
output_dir = case_dir


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def read_param_csv(filename, value_col, data_dir):
    df = pd.read_csv(os.path.join(data_dir, filename))
    rename_map = {
        "index0": "k", "index1": "ct", "index2": "n",
        "index3": "h", "index4": "td", value_col: "val"
    }
    df.rename(columns=rename_map, inplace=True)
    return df


def to_dict(df):
    val_col = [c for c in df.columns if c not in ["k", "ct", "n", "h", "td"]][0]
    return {(r.k, r.ct, r.n, r.h, r.td): getattr(r, val_col)
            for r in df.itertuples(index=False)}


def to_dict_simple(df, val_col):
    return {(r.ct, r.n, r.h, r.td): getattr(r, val_col)
            for r in df.itertuples(index=False)}


# ---------------------------------------------------------
# Load CSVs for the selected case
# ---------------------------------------------------------

a_df     = read_param_csv("a.csv",     "a.val", data_dir)
b_df     = read_param_csv("b.csv",     "b.val", data_dir)
D_df     = read_param_csv("D.csv",     "D.val", data_dir)
p_pw_df  = read_param_csv("p_pw.csv",  "p_pw.val", data_dir)

d_ref_df   = pd.read_csv(os.path.join(data_dir, "d_ref.csv"))
p_ref_df   = pd.read_csv(os.path.join(data_dir, "p_ref.csv"))
price_df   = pd.read_csv(os.path.join(data_dir, "price.csv"))
d_vals     = pd.read_csv(os.path.join(data_dir, "d_vals.csv"))

# Convert to dictionaries
a_dict, b_dict, D_dict, p_pw_dict = map(to_dict, [a_df, b_df, D_df, p_pw_df])
d_ref_dict     = to_dict_simple(d_ref_df, "d_ref")
p_ref_dict     = to_dict_simple(p_ref_df, "p_ref")
d_actual_dict  = to_dict_simple(d_vals,   "val")

# Metadata
end_uses   = sorted(a_df["ct"].unique())
node_ref   = sorted(a_df["n"].unique())[0]
available_hours = sorted(a_df["h"].unique())
available_td    = sorted(a_df["td"].unique())


# ---------------------------------------------------------
# Validate requested TD + hour
# ---------------------------------------------------------

if TARGET_HOUR not in available_hours:
    raise ValueError(f"Requested hour {TARGET_HOUR} not found. Available: {available_hours}")

if TARGET_TD not in available_td:
    raise ValueError(f"Requested TD {TARGET_TD} not found. Available: {available_td}")

h  = TARGET_HOUR
td = TARGET_TD

print(f"Generating plot: Typical Day {td}, Hour {h}\n")


# ---------------------------------------------------------
# Helper functions dependent on loaded data
# ---------------------------------------------------------

def get_price(ct, n, h, td):
    match = price_df[
        (price_df["p"] == ct) &
        (price_df["n"] == n) &
        (price_df["h"] == h) &
        (price_df["td"] == td)
    ]
    return match["price_M€_per_GWh"].values[0] if not match.empty else np.nan


def get_curve(ct, n, h, td):
    seg_keys = sorted({
        k for (k, ct_i, n_i, h_i, td_i) in a_dict.keys()
        if (ct_i, n_i, h_i, td_i) == (ct, n, h, td)
    })
    d_curve = [0.0]
    p_curve = [p_pw_dict.get((0, ct, n, h, td), np.nan)]
    cum = 0.0
    for k in seg_keys:
        cum += D_dict.get((k, ct, n, h, td), 0)
        d_curve.append(cum)
        p_curve.append(p_pw_dict.get((k, ct, n, h, td), np.nan))
    return d_curve, p_curve, seg_keys


# ---------------------------------------------------------
# Single TD + hour plot
# ---------------------------------------------------------

fig, axes = plt.subplots(2, 2, figsize=(12, 8))
axes = axes.flatten()

for i, ct in enumerate(end_uses):
    ax = axes[i]

    d_curve, p_curve, segments = get_curve(ct, node_ref, h, td)
    if not segments:
        ax.axis("off")
        continue

    is_voll = all(b_dict[(k, ct, node_ref, h, td)] == 0 for k in segments)

    # ------------ VOLL CASE ------------
    if is_voll:
        voll_price = p_pw_dict[(0, ct, node_ref, h, td)]
        d_ref      = d_ref_dict[(ct, node_ref, h, td)]

        ax.plot([0, d_ref], [voll_price, voll_price],
                linewidth=2, color=colors_end_use_type.get(ct, "black"))

        ax.set_title(ct + " (VOLL)")
        ax.set_xlabel("Demand [GW]")
        ax.set_ylabel("Price [M€/GWh]")
        ax.grid(True)
        ax.set_xlim(0, d_ref * 1.15)
        ax.set_ylim(0, voll_price * 1.15)
        continue

    # ------------ ELASTIC CASE ------------
    d_ref = d_ref_dict.get((ct, node_ref, h, td), np.nan)
    p_ref = p_ref_dict.get((ct, node_ref, h, td), np.nan)
    d_act = d_actual_dict.get((ct, node_ref, h, td), np.nan)
    p_act = get_price(ct, node_ref, h, td)

    # Elasticity computation (unchanged)
    cum_limits = np.cumsum([D_dict[(k, ct, node_ref, h, td)] for k in segments])
    seg_idx_d  = min(int(np.searchsorted(cum_limits, d_ref, side="right")),
                     len(segments) - 1)

    cum_before = 0 if seg_idx_d == 0 else cum_limits[seg_idx_d - 1]
    a_ref_d    = a_dict[(segments[seg_idx_d], ct, node_ref, h, td)]
    b_ref_d    = b_dict[(segments[seg_idx_d], ct, node_ref, h, td)]
    p_ref_d    = a_ref_d - b_ref_d * (d_ref - cum_before)
    elast_d    = -1 / b_ref_d * (p_ref_d / d_ref)

    # Reference price elasticity
    p_end   = [a_dict[(k, ct, node_ref, h, td)] - b_dict[(k, ct, node_ref, h, td)] * D_dict[(k, ct, node_ref, h, td)]
               for k in segments]
    p_start = [a_dict[(k, ct, node_ref, h, td)] for k in segments]

    seg_idx_p = next(
        (idx for idx in range(len(segments)) if p_start[idx] >= p_ref >= p_end[idx]),
        len(segments) - 1
    )

    a_ref_p      = a_dict[(segments[seg_idx_p], ct, node_ref, h, td)]
    b_ref_p      = b_dict[(segments[seg_idx_p], ct, node_ref, h, td)]
    cum_before_p = 0 if seg_idx_p == 0 else cum_limits[seg_idx_p - 1]
    d_at_ref_p   = (a_ref_p - p_ref) / b_ref_p + cum_before_p
    elast_p      = -1 / b_ref_p * (p_ref / d_at_ref_p)

    # ------------ PLOT ------------
    color = colors_end_use_type.get(ct, "black")
    ax.plot(d_curve, p_curve, linewidth=2, color=color)

    if not np.isnan(d_ref):
        ax.axvline(d_ref, color="gray", linestyle=":")
    if not np.isnan(p_ref):
        ax.axhline(p_ref, color="red", linestyle=":")
    if not np.isnan(d_act):
        ax.axvline(d_act, color="green", linestyle="--")
    if not np.isnan(p_act):
        ax.axhline(p_act, color="green", linestyle="--")
        ax.scatter(d_act, p_act, color="green", s=40, marker="x")

    ax.text(
        0.15, 0.30,
        f"ε @ Ref D = {elast_d:.2f}\nε @ Ref P = {elast_p:.2f}",
        fontsize=9, transform=ax.transAxes,
        bbox=dict(facecolor="white", alpha=0.8, edgecolor="black")
    )

    ax.set_title(ct)
    ax.set_xlabel("Demand [GW]")
    ax.set_ylabel("Price [M€/GWh]")
    ax.grid(True)
    ax.set_xlim(0, max(d_curve) * 1.05)
    ax.set_ylim(0, max(p_curve) * 1.05)


# ---------------------------------------------------------
# Final Figure Save
# ---------------------------------------------------------

plt.suptitle(
    f"PWL Inverse Demand Curves (Node {node_ref}, TD {td}, Hour {h})",
    fontsize=13
)
plt.tight_layout(rect=[0, 0, 1, 0.95])

out_path = os.path.join(output_dir, f"Demand_TD{td}_H{h}.png")
plt.savefig(out_path, dpi=300, bbox_inches="tight")
plt.close()

print(f"Saved figure to: {out_path}")
