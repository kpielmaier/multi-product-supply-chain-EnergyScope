import os
import json
import matplotlib.pyplot as plt
import pandas as pd

# ============================================================
# GLOBAL STYLE — MATCHES ZERO-PRICE & SOLVE-TIME PLOTS
# ============================================================
plt.rcParams.update({
    "text.usetex": False,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 16,
})

# ============================================================
# DIRECTORIES
# ============================================================
script_dir = os.path.dirname(os.path.abspath(__file__))
data_low   = os.path.join(script_dir, "..", "DataNormalPrice")
pareto_low = os.path.join(script_dir, "..", "ResultsNormalPrice", "Figures", "Pareto")

elasticity_files = {
    "elast_10pct":  "pareto_SW_vs_GWP_elast_10pct.json",
    "elast_5pct":   "pareto_SW_vs_GWP_elast_5pct.json",
    "elast_2_5pct": "pareto_SW_vs_GWP_elast_2_5pct.json",
    "demand_fixed": "pareto_SW_vs_GWP_demand_fixed.json",
}

# ============================================================
# COLORS (match other figures)
# ============================================================
colors_elasticity = {
    "demand_fixed": "#000000",
    "elast_2_5pct": "#d62728",
    "elast_5pct":   "#1f77b4",
    "elast_10pct":  "#2ca02c",
}

# ============================================================
# LEGEND LABELS
# ============================================================
legend_names = {
    "demand_fixed": "Fixed demand",
    "elast_2_5pct": "Elasticity = 2.5%",
    "elast_5pct":   "Elasticity = 5%",
    "elast_10pct":  "Elasticity = 10%",
}

# ============================================================
# LOAD JSON FRONTIER
# ============================================================
def load_pareto_jsons(folder):
    result = {}
    for tag, fname in elasticity_files.items():
        path = os.path.join(folder, fname)
        if os.path.exists(path):
            with open(path, "r") as f:
                result[tag] = json.load(f)
        else:
            print(f"[WARNING] Missing file: {path}")
    return result

fronts_low = load_pareto_jsons(pareto_low)

# ============================================================
# PRICE FILE HELPERS
# ============================================================
def load_price_file(path):
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    df = df[df["p"] == "ELECTRICITY"].copy()
    if df.empty:
        return None
    df["hours_rep"] = df["mult"] * df["t_op"]
    return df

def count_peak_price_hours(path, threshold=400.0):
    df = load_price_file(path)
    if df is None:
        return None
    return df.loc[df["price_€_per_MWh"] > threshold, "hours_rep"].sum()

def folder_from_point(tag, point):
    eps = point.get("epsilon")
    if eps is None:
        return None
    if isinstance(eps, str):
        return f"{tag}_eps_{eps}"
    return f"{tag}_eps_{eps:.2f}"

# ============================================================
# PLOT — PEAK PRICE HOURS (NORMAL PRICE SCENARIO)
# ============================================================
fig, ax = plt.subplots(figsize=(10, 6))

print("\n================ PEAK PRICE HOURS (Normal Price Scenario) ================")

for tag, pts in fronts_low.items():
    gwps = []
    peak_hours = []

    print(f"\n--- {legend_names.get(tag, tag)} ---")

    for p in pts:
        folder = folder_from_point(tag, p)
        if folder is None:
            continue

        price_csv = os.path.join(data_low, folder, "price.csv")
        hours = count_peak_price_hours(price_csv)
        if hours is None:
            continue

        GWP = p["TotalGWP"]

        # PRINT VALUES TO TERMINAL
        print(f"GWP = {GWP:10.2f}   peak-price hours = {hours:10.2f}")

        gwps.append(GWP)
        peak_hours.append(hours)

    if not gwps:
        continue

    color = colors_elasticity.get(tag, "#000000")
    label = legend_names.get(tag, tag)

    ax.plot(
        gwps,
        peak_hours,
        marker="o",
        linestyle="-",
        color=color,
        linewidth=2,
        label=label,
    )

# ============================================================
# AESTHETICS
# ============================================================
ax.set_xlabel("Total GWP [ktCO$_2$/year]")
ax.set_ylabel("Number of peak-price hours per year (>400 €/MWh)")
ax.grid(True)
ax.legend(fontsize=16)

plt.tight_layout()

# ============================================================
# SAVE
# ============================================================
save_path = os.path.join(pareto_low, "PeakPriceHours_vs_GWP_NormalOnly.pdf")
os.makedirs(os.path.dirname(save_path), exist_ok=True)
plt.savefig(save_path, dpi=250, bbox_inches="tight")
plt.close()

print("\nSaved peak-price plot to:")
print(" ", save_path)
print("\n==========================================================================\n")
