import os
import json
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams.update({
    "text.usetex": False,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 12,
})

script_dir = os.path.dirname(os.path.abspath(__file__))

# === HIGH / LOW / NORMAL RESULTS FOLDERS ===
data_high   = os.path.join(script_dir, "..", "DataHighPrice")
data_low    = os.path.join(script_dir, "..", "DataLowPrice")
data_normal = os.path.join(script_dir, "..", "DataNormalPrice")

pareto_high   = os.path.join(script_dir, "..", "ResultsHighPrice",   "Figures", "Pareto")
pareto_low    = os.path.join(script_dir, "..", "ResultsLowPrice",    "Figures", "Pareto")
pareto_normal = os.path.join(script_dir, "..", "ResultsNormalPrice", "Figures", "Pareto")

elasticity_files = {
    "elast_10pct":  "pareto_SW_vs_GWP_elast_10pct.json",
    "elast_5pct":   "pareto_SW_vs_GWP_elast_5pct.json",
    "elast_2_5pct": "pareto_SW_vs_GWP_elast_2_5pct.json",
    "demand_fixed": "pareto_SW_vs_GWP_demand_fixed.json",
}

# === Load JSONs ===
def load_pareto_jsons(folder):
    result = {}
    for tag, f in elasticity_files.items():
        path = os.path.join(folder, f)
        if not os.path.exists(path):
            print(f"[WARNING] Missing: {path}")
            continue
        with open(path, "r") as fh:
            result[tag] = json.load(fh)
    return result

fronts_high   = load_pareto_jsons(pareto_high)
fronts_low    = load_pareto_jsons(pareto_low)
fronts_normal = load_pareto_jsons(pareto_normal)

# === Color map ===
available_colors = plt.cm.tab10.colors
elasticity_colors = {
    "elast_10pct":  available_colors[0],
    "elast_5pct":   available_colors[1],
    "elast_2_5pct": available_colors[2],
}

color_high_fixed   = "black"
color_low_fixed    = "gray"
color_normal_fixed = "lightgray"

# ============================================================================
# === Load and weight electricity price rows ===
# ============================================================================
def load_price_file(price_csv_path):
    """Loads price_df with only electricity rows + hours_rep = mult * t_op."""
    if not os.path.exists(price_csv_path):
        return None

    df = pd.read_csv(price_csv_path)
    df = df[df["p"] == "ELECTRICITY"].copy()

    if df.empty:
        return None

    df["hours_rep"] = df["mult"] * df["t_op"]
    return df


def count_peak_price_hours(price_csv_path, threshold=200.0):
    """Weighted hours with price > threshold €/MWh."""
    df = load_price_file(price_csv_path)
    if df is None:
        return None

    return df.loc[df["price_€_per_MWh"] > threshold, "hours_rep"].sum()


# === Helper: build folder name ===
def folder_from_point(tag, point):
    eps = point.get("epsilon", None)
    if eps is None:
        return None
    if isinstance(eps, str):
        return f"{tag}_eps_{eps}"
    return f"{tag}_eps_{float(eps):.2f}"

# === Plot combined ===
fig, ax = plt.subplots(figsize=(10, 6))

def process_scenario(fronts, data_folder, linestyle, marker, label_suffix, fixed_color):
    for tag, pts in fronts.items():
        gwps = []
        peak_hours = []

        for p in pts:
            folder = folder_from_point(tag, p)
            if folder is None:
                continue

            price_csv = os.path.join(data_folder, folder, "price.csv")
            print("Checking:", price_csv, "Exists:", os.path.exists(price_csv))

            h = count_peak_price_hours(price_csv)
            if h is None:
                continue

            gwps.append(p["TotalGWP"])
            peak_hours.append(h)

        if len(gwps) == 0:
            continue

        color = elasticity_colors.get(tag, fixed_color)

        ax.plot(
            gwps,
            peak_hours,
            marker=marker,
            linestyle=linestyle,
            color=color,
            label=f"{tag} ({label_suffix})"
        )


# HIGH (solid)
process_scenario(fronts_high, data_high, "-", "o", "High", color_high_fixed)

# LOW (dashed)
process_scenario(fronts_low, data_low, "--", "x", "Low", color_low_fixed)

# NORMAL (dotted)
process_scenario(fronts_normal, data_normal, ":", "^", "Normal", color_normal_fixed)

# === Aesthetics ===
# ax.set_title("Number of Peak-Price Hours (>400 €/MWh) vs GWP — High / Low / Normal Scenarios")
ax.set_xlabel(r"Total GWP [ktCO$_2$/year]")
ax.set_ylabel("Number of peak-price hours per year (>400 €/MWh)")
ax.grid(True)
ax.legend()

# === Save ===
save_high   = os.path.join(pareto_high,   "PeakPriceHours_vs_GWP_Combined.png")
save_low    = os.path.join(pareto_low,    "PeakPriceHours_vs_GWP_Combined.png")
save_normal = os.path.join(pareto_normal, "PeakPriceHours_vs_GWP_Combined.png")

for path in [save_high, save_low, save_normal]:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.savefig(path, dpi=250)

plt.close()

print("Saved weighted peak-price plots to:")
print(" ", save_high)
print(" ", save_low)
print(" ", save_normal)
