import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from Colors import colors_elasticity

# =====================================================
# Global Style (MATCHES Pareto + Price plots)
# =====================================================
plt.rcParams.update({
    "text.usetex": False,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 16,
})

legend_names = {
    "demand_fixed": "Fixed demand",
    "elast_2_5pct": "Elasticity = 2.5%",
    "elast_5pct":   "Elasticity = 5%",
    "elast_10pct":  "Elasticity = 10%",
}

# =====================================================
# USER SETTINGS
# =====================================================

TARGET_STORAGE = "BATT_LI"
TARGET_TD      = 9

# =====================================================
# Paths
# =====================================================

script_dir   = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

data_root = os.path.join(project_root, "DataNormalPrice")
save_dir  = os.path.join(project_root, "ResultsNormalPrice", "Figures", "Storage")

os.makedirs(save_dir, exist_ok=True)

cases = {
    "demand_fixed": "demand_fixed_eps_0.00",
    "elast_2_5pct": "elast_2_5pct_eps_0.00",
    "elast_5pct":   "elast_5pct_eps_0.00",
    "elast_10pct":  "elast_10pct_eps_0.00",
}

# =====================================================
# Plot setup
# =====================================================

plt.figure(figsize=(10, 6))
ymax = 0

# =====================================================
# Process elasticity cases
# =====================================================

for tag, folder in cases.items():

    data_dir = os.path.join(data_root, folder)

    chg_path = os.path.join(data_dir, "storage_charge.csv")
    dis_path = os.path.join(data_dir, "storage_discharge.csv")

    if not os.path.exists(chg_path) or not os.path.exists(dis_path):
        print(f"[WARNING] Missing storage files for {tag}")
        continue

    chg = pd.read_csv(chg_path)
    dis = pd.read_csv(dis_path)

    # --- Filter storage + TD ---
    chg = chg[(chg["j"] == TARGET_STORAGE) & (chg["td"] == TARGET_TD)]
    dis = dis[(dis["j"] == TARGET_STORAGE) & (dis["td"] == TARGET_TD)]

    if chg.empty and dis.empty:
        print(f"[WARNING] No storage activity for {tag}")
        continue

    # --- Absolute values ---
    chg["val"] = chg["val"].abs()
    dis["val"] = dis["val"].abs()

    # --- Aggregate per hour ---
    chg_h = chg.groupby("h")["val"].sum()
    dis_h = dis.groupby("h")["val"].sum()

    # --- Net power: charge positive, discharge negative ---
    net = chg_h.sub(dis_h, fill_value=0).reset_index(name="net_GW")

    # --- Plot ---
    plt.plot(
        net["h"],
        net["net_GW"],
        linewidth=2,
        marker="o",
        label=legend_names.get(tag, tag),
        color=colors_elasticity.get(tag, "gray")
    )

    ymax = max(ymax, abs(net["net_GW"]).max())

# =====================================================
# Formatting
# =====================================================

plt.axhline(0, color="black", linewidth=1)
plt.xlabel("Hour")
plt.ylabel("Net Storage Power [GW]")

plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.1f}"))
plt.ylim(-ymax * 1.1, ymax * 1.1)

plt.grid(True)
plt.legend(fontsize=16)
plt.tight_layout()

# =====================================================
# Save
# =====================================================

save_path = os.path.join(
    save_dir,
    f"Storage_Net_Dispatch_{TARGET_STORAGE}_TD{TARGET_TD}.png"
)

plt.savefig(save_path, dpi=300, bbox_inches="tight")
plt.close()

print("✅ Saved plot to:")
print(" ", save_path)
