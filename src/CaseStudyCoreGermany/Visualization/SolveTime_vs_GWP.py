import os
import json
import matplotlib.pyplot as plt
import pandas as pd

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

pareto_normal = os.path.join(script_dir, "..", "ResultsNormalPrice", "Figures", "Pareto")
csv_root      = os.path.join(script_dir, "..", "DataNormalPrice", "EnergyScope")

elasticity_files = {
    "elast_10pct":  "pareto_SW_vs_GWP_elast_10pct.json",
    "elast_5pct":   "pareto_SW_vs_GWP_elast_5pct.json",
    "elast_2_5pct": "pareto_SW_vs_GWP_elast_2_5pct.json",
    "demand_fixed": "pareto_SW_vs_GWP_demand_fixed.json",
}

# ============================================================
# COLORS (from Colors.py)
# ============================================================
colors_elasticity = {
    "demand_fixed": "#000000",
    "elast_2_5pct": "#d62728",
    "elast_5pct":   "#1f77b4",
    "elast_10pct":  "#2ca02c",
}

# ============================================================
# CLEAN LEGEND LABELS
# ============================================================
legend_names = {
    "demand_fixed": "Fixed demand (quadratic)",
    "elast_2_5pct": "Elasticity = 2.5% (quadratic)",
    "elast_5pct":   "Elasticity = 5% (quadratic)",
    "elast_10pct":  "Elasticity = 10% (quadratic)",
}

# ============================================================
# LOAD JSON PARETO FRONT DATA
# ============================================================
def load_pareto_jsons(folder):
    result = {}
    for tag, fname in elasticity_files.items():
        path = os.path.join(folder, fname)
        if not os.path.exists(path):
            print(f"[WARNING] Missing: {path}")
            continue
        with open(path, "r") as fh:
            result[tag] = json.load(fh)
    return result

fronts_normal = load_pareto_jsons(pareto_normal)

# ============================================================
# LOAD CSV SOLVE-TIME SUMMARY (GWP read from CSV, not filename)
# ============================================================
csv_points = []

for fname in os.listdir(csv_root):
    if not fname.startswith("run_results_") or not fname.endswith(".csv"):
        continue

    full_path = os.path.join(csv_root, fname)
    df = pd.read_csv(full_path)

    # extract GWP directly from the CSV content
    gwp_val = float(df["TotalGWP"].iloc[0])

    # extract solve time (prefer gurobi_solve_time unless NaN)
    solve_time = df["gurobi_solve_time"].iloc[0]
    if pd.isna(solve_time):
        solve_time = df["python_wall_clock_time"].iloc[0]

    csv_points.append({
        "gwp": gwp_val,
        "solve_time": solve_time,
    })

# Sort CSV points by increasing GWP
csv_points = sorted(csv_points, key=lambda x: x["gwp"])

# ============================================================
# PLOT: SOLVE TIME VS GWP
# ============================================================
fig, ax = plt.subplots(figsize=(10, 6))

# --- plot Pareto front solve times ---
for tag, pts in fronts_normal.items():

    color = colors_elasticity.get(tag, "#000000")
    label = legend_names.get(tag, tag)

    solve_times = [p["solve_time"] for p in pts]
    gwp_vals    = [p["TotalGWP"] for p in pts]

    ax.plot(
        gwp_vals,
        solve_times,
        marker='o',
        linestyle='-',
        color=color,
        label=label
    )

# --- plot CSV reference solve-time points ---
csv_gwp = [p["gwp"] for p in csv_points]
csv_st  = [p["solve_time"] for p in csv_points]

ax.plot(
    csv_gwp,
    csv_st,
    marker='o',
    linestyle='--',
    color="grey",
    label="EnergyScope (linear)"
)

# ============================================================
# AESTHETICS
# ============================================================
ax.set_xlabel("Total GWP [ktCO$_2$/year]")
ax.set_ylabel("Solve time [s]")
ax.grid(True)

# Force y-axis to start at 0
ax.set_ylim(bottom=0)

ax.legend(fontsize=16)
plt.tight_layout()

# ============================================================
# SAVE FIGURE
# ============================================================
save_path = os.path.join(pareto_normal, "SolveTime_vs_GWP_NormalPriceOnly.pdf")
os.makedirs(os.path.dirname(save_path), exist_ok=True)
plt.savefig(save_path, dpi=250, bbox_inches="tight")
plt.close()

print("Saved solve-time plot with CSV runs to:")
print(" ", save_path)
