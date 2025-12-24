import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
from Colors import colors_elasticity   # uses keys: demand_fixed, elast_2_5pct, elast_5pct, elast_10pct

plt.rcParams.update({
    "text.usetex": False,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 12,
})

# =====================================================
# Paths
# =====================================================
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

base_dir = os.path.join(project_root, "DataLowPrice")

# =====================================================
# Elasticity cases (matching color dict keys)
# =====================================================
cases = {
    "demand_fixed": "demand_fixed_eps_0.00",
    "elast_2_5pct": "elast_2_5pct_eps_0.00",
    "elast_5pct":   "elast_5pct_eps_0.00",
    "elast_10pct":  "elast_10pct_eps_0.00",
}

# Legend names for human-readable plot labels
legend_names = {
    "demand_fixed": "Fixed demand",
    "elast_2_5pct": "Elasticity = 2.5%",
    "elast_5pct":   "Elasticity = 5%",
    "elast_10pct":  "Elasticity = 10%",
}

# =====================================================
# Output dirs
# =====================================================
fig_dir = os.path.join(project_root, "Results", "Figures", "Storage")
daily_dir = os.path.join(fig_dir, "Daily")
seasonal_dir = os.path.join(fig_dir, "Seasonal")
os.makedirs(daily_dir, exist_ok=True)
os.makedirs(seasonal_dir, exist_ok=True)

# =====================================================
# Load tech sets from sample case
# =====================================================
sample_folder = list(cases.values())[0]
sample_dir = os.path.join(base_dir, sample_folder)

tech_set = pd.read_csv(os.path.join(sample_dir, "storage_tech.csv"))["STORAGE_TECH"].tolist()
daily_set = pd.read_csv(os.path.join(sample_dir, "storage_daily.csv"))["STORAGE_DAILY"].tolist()

storage_map = pd.read_csv(os.path.join(sample_dir, "storage_of_end_use.csv"))
storage_to_enduse = {r["STORAGE_TECH"]: r["END_USE_TYPE"] for _, r in storage_map.iterrows()}

mapping_df = pd.read_csv(os.path.join(sample_dir, "t_h_td_mapping.csv"))

SEASONAL_THRESHOLD = 1e-3
DAILY_THRESHOLD = 1e-3

# =====================================================
# Helper loader
# =====================================================
def load_storage(folder):
    """Load and merge seasonal + daily storage levels."""
    ddir = os.path.join(base_dir, folder)

    seasonal_df = pd.read_csv(os.path.join(ddir, "storage_level_seasonal.csv"))
    daily_df = pd.read_csv(os.path.join(ddir, "storage_level_daily.csv"))

    daily_m = daily_df.merge(mapping_df, on=["h", "td"])
    daily_final = daily_m[["j", "n", "t", "val"]]

    comb = seasonal_df.merge(
        daily_final, on=["j", "n", "t"], how="left", suffixes=("_s", "_d")
    )

    comb["val"] = comb.apply(
        lambda r: r["val_d"] if (r["j"] in daily_set and pd.notna(r["val_d"]))
        else r["val_s"],
        axis=1
    )

    return comb.merge(mapping_df, on="t")

# =====================================================
# SEASONAL PLOTS
# =====================================================
for j in sorted(tech_set):

    if j in daily_set:
        continue

    plt.figure(figsize=(12, 5))
    ymax = 0
    anything_plotted = False

    for key, folder in cases.items():

        comb = load_storage(folder)
        dfj = comb[comb["j"] == j]

        df_season = dfj.groupby("t")["val"].sum().reset_index()

        if df_season["val"].abs().max() < SEASONAL_THRESHOLD:
            continue

        df_season["val"] = df_season["val"].mask(df_season["val"].abs() < SEASONAL_THRESHOLD, 0)

        plt.plot(
            df_season["t"],
            df_season["val"],
            linewidth=2,
            label=legend_names[key],
            color=colors_elasticity[key]
        )

        anything_plotted = True
        ymax = max(ymax, df_season["val"].max())

    if not anything_plotted:
        plt.close()
        continue

    plt.xlabel("Period")
    plt.ylabel("Energy [GWh]")

    ax = plt.gca()
    ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=False))
    ax.ticklabel_format(style="plain", axis="y")

    plt.ylim(0, ymax * 1.05)
    plt.grid(True)
    plt.legend(fontsize=10)
    plt.tight_layout()

    out = os.path.join(seasonal_dir, f"Seasonal_{j}.png")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()

# =====================================================
# DAILY PLOTS
# =====================================================
for j in sorted(tech_set):

    if j not in daily_set:
        continue

    active_days = set()
    case_data = {}

    for key, folder in cases.items():

        comb = load_storage(folder)
        dfj = comb[comb["j"] == j]

        df_daily = dfj.groupby(["td", "h"])["val"].sum().reset_index()
        df_daily["val"] = df_daily["val"].mask(df_daily["val"].abs() < DAILY_THRESHOLD, 0)

        case_data[key] = df_daily

        active_days |= set(df_daily[df_daily["val"] > 0]["td"].unique().tolist())

    active_days = sorted(active_days)
    if not active_days:
        continue

    fig, axes = plt.subplots(len(active_days), 1,
                             figsize=(10, 4 * len(active_days)),
                             sharex=True)

    if len(active_days) == 1:
        axes = [axes]

    for ax, td_val in zip(axes, active_days):
        ymax = 0

        for key, df_daily in case_data.items():

            dfd = df_daily[df_daily["td"] == td_val]
            if dfd.empty:
                continue

            ymax = max(ymax, dfd["val"].max())

            ax.plot(
                dfd["h"],
                dfd["val"],
                linewidth=2,
                label=legend_names[key],
                color=colors_elasticity[key]
            )

        ax.grid(True)
        ax.set_ylabel("Energy [GWh]")
        ax.set_ylim(0, ymax * 1.05)

        ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=False))
        ax.ticklabel_format(style="plain", axis="y")

    axes[-1].set_xlabel("Hour")

    plt.legend(fontsize=10, bbox_to_anchor=(1.0, 1.02))
    plt.tight_layout()

    out = os.path.join(daily_dir, f"Daily_{j}.png")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()

print("Finished all storage comparison plots.")
