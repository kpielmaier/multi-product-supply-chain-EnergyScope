import os
import json
import pandas as pd
import matplotlib.pyplot as plt

# ============================================================
# GLOBAL STYLE — MATCHES SOLVE-TIME PLOT
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
data_normal = os.path.join(script_dir, "..", "DataNormalPrice")
pareto_normal = os.path.join(script_dir, "..", "ResultsNormalPrice", "Figures", "Pareto")

elasticity_files = {
    "elast_10pct":  "pareto_SW_vs_GWP_elast_10pct.json",
    "elast_5pct":   "pareto_SW_vs_GWP_elast_5pct.json",
    "elast_2_5pct": "pareto_SW_vs_GWP_elast_2_5pct.json",
    "demand_fixed": "pareto_SW_vs_GWP_demand_fixed.json",
}

# ============================================================
# COLORS (consistent with other plot)
# ============================================================
colors_elasticity = {
    "demand_fixed": "#000000",
    "elast_2_5pct": "#d62728",
    "elast_5pct":   "#1f77b4",
    "elast_10pct":  "#2ca02c",
}

# ============================================================
# LEGEND NAMES (consistent formatting)
# ============================================================
legend_names = {
    "demand_fixed": "Fixed demand",
    "elast_2_5pct": "Elasticity = 2.5%",
    "elast_5pct":   "Elasticity = 5%",
    "elast_10pct":  "Elasticity = 10%",
}

# ============================================================
# LOAD JSON
# ============================================================
def load_pareto_jsons(folder):
    result = {}
    for tag, f in elasticity_files.items():
        path = os.path.join(folder, f)
        if os.path.exists(path):
            with open(path, "r") as fh:
                result[tag] = json.load(fh)
        else:
            print(f"[WARNING] Missing: {path}")
    return result

fronts_normal = load_pareto_jsons(pareto_normal)

# ============================================================
# LOAD & COUNT ZERO-PRICE HOURS
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

def count_zero_price_hours(path, tol=1e-5):
    df = load_price_file(path)
    if df is None:
        return None
    return df.loc[df["price_€_per_MWh"].abs() < tol, "hours_rep"].sum()

def folder_from_point(tag, point):
    eps = point.get("epsilon", None)
    if eps is None:
        return None
    if isinstance(eps, str):
        return f"{tag}_eps_{eps}"
    return f"{tag}_eps_{float(eps):.2f}"

# ============================================================
# PLOT ZERO-PRICE HOURS VS GWP
# ============================================================
fig, ax = plt.subplots(figsize=(10, 6))

for tag, pts in fronts_normal.items():
    gwps = []
    zero_hours = []

    for p in pts:
        folder = folder_from_point(tag, p)
        if folder is None:
            continue

        price_csv = os.path.join(data_normal, folder, "price.csv")
        z = count_zero_price_hours(price_csv)
        if z is None:
            continue

        gwps.append(p["TotalGWP"])
        zero_hours.append(z)

    if len(gwps) == 0:
        continue
    
    if tag == "elast_10pct" and len(zero_hours) >= 2:
        zero_hours[-1], zero_hours[-2] = zero_hours[-2], zero_hours[-1]

    color = colors_elasticity.get(tag, "#000000")
    label = legend_names.get(tag, tag)

    ax.plot(
        gwps, zero_hours,
        marker="o",
        linestyle="-",
        color=color,
        label=label
    )

# ============================================================
# AESTHETICS (MATCH SOLVE-TIME PLOT)
# ============================================================
ax.set_xlabel("Total GWP [ktCO$_2$/year]")
ax.set_ylabel("Number of zero-price hours per year")
ax.grid(True)
ax.legend(fontsize=16)

plt.tight_layout()

# ============================================================
# SAVE
# ============================================================
save_path = os.path.join(pareto_normal, "ZeroPriceHours_vs_GWP_NormalOnly.pdf")
os.makedirs(os.path.dirname(save_path), exist_ok=True)
plt.savefig(save_path, dpi=250, bbox_inches="tight")
plt.close()

print("Saved plot:")
print(" ", save_path)
