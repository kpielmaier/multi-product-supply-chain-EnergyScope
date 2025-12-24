import os
import pandas as pd
import matplotlib.pyplot as plt

# ---------------------------------------------------------
# GLOBAL STYLE
# ---------------------------------------------------------
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 16,
})

# ---------------------------------------------------------
# USER SETTINGS
# ---------------------------------------------------------
CASE_DIR = r"DataNormalPrice\elast_5pct_eps_0.00"
TARGET_STORAGE = "BATT_LI"
TARGET_TD = 9  # typical day

# ---------------------------------------------------------
# STORAGE PARAMETERS (FROM .dat FILE — HARD CODED)
# ---------------------------------------------------------
STORAGE_PARAMS = {
    "BATT_LI": {
        "energy_capacity": 79.80714732229796,  # GWh
        "charge_time": 4.0,                    # h
        "discharge_time": 4.0,                 # h
        "availability": 1.0
    }
}

# ---------------------------------------------------------
# PATH SETUP
# ---------------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
data_dir = os.path.join(project_root, CASE_DIR)

output_dir = os.path.join(data_dir, "StoragePlots", "Daily")
os.makedirs(output_dir, exist_ok=True)

# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------
daily_df = pd.read_csv(os.path.join(data_dir, "storage_level_daily.csv"))
charge_df = pd.read_csv(os.path.join(data_dir, "storage_charge.csv"))
dis_df = pd.read_csv(os.path.join(data_dir, "storage_discharge.csv"))

# ---------------------------------------------------------
# FILTER STORAGE + TYPICAL DAY
# ---------------------------------------------------------
daily_df = daily_df[daily_df["j"] == TARGET_STORAGE]
charge_df = charge_df[charge_df["j"] == TARGET_STORAGE]
dis_df = dis_df[dis_df["j"] == TARGET_STORAGE]

soc = daily_df[daily_df["td"] == TARGET_TD].sort_values("h")
chg = charge_df[charge_df["td"] == TARGET_TD].sort_values("h").copy()
dis = dis_df[dis_df["td"] == TARGET_TD].sort_values("h").copy()

chg["val"] = chg["val"].abs()
dis["val"] = dis["val"].abs()

# ---------------------------------------------------------
# STORAGE LIMITS
# ---------------------------------------------------------
params = STORAGE_PARAMS[TARGET_STORAGE]

soc_max = params["energy_capacity"]
charge_limit = soc_max / params["charge_time"] * params["availability"]
discharge_limit = soc_max / params["discharge_time"] * params["availability"]

# ---------------------------------------------------------
# PLOT
# ---------------------------------------------------------
fig, ax = plt.subplots(figsize=(12, 6))

# ---- LEFT AXIS: STATE OF CHARGE ----
soc_line, = ax.plot(
    soc["h"], soc["val"],
    color="black", linewidth=2.5,
    label="SoC"
)

soc_lim_line = ax.axhline(
    soc_max,
    color="black", linestyle=":", linewidth=2,
    label="SoC limit"
)

ax.set_xlabel("Hour")
ax.set_ylabel("SoC [GWh]")
ax.set_ylim(0, 85)

# ---- RIGHT AXIS: CHARGE / DISCHARGE ----
ax2 = ax.twinx()

chg_patch = ax2.fill_between(
    chg["h"], 0, chg["val"],
    color="green", alpha=0.35,
    label="Charging"
)

dis_patch = ax2.fill_between(
    dis["h"], 0, -dis["val"],
    color="red", alpha=0.35,
    label="Discharging"
)

chg_lim_line = ax2.axhline(
    charge_limit,
    color="green", linestyle="--", linewidth=2,
    label="Charging limit"
)

dis_lim_line = ax2.axhline(
    -discharge_limit,
    color="red", linestyle="--", linewidth=2,
    label="Discharging limit"
)

ax2.axhline(0, color="black", linewidth=1)
ax2.set_ylabel("Charge / discharge [GW]")

# ---- RIGHT AXIS LIMITS ----
ax2.set_ylim(-50, 50)
ax.grid(True)

# ---------------------------------------------------------
# LEGEND: column-major ordering to force row-wise pairing
# ---------------------------------------------------------
handles = [
    soc_line,       # col 1, row 1
    chg_patch,      # col 1, row 2
    dis_patch,      # col 1, row 3
    soc_lim_line,   # col 2, row 1
    chg_lim_line,   # col 2, row 2
    dis_lim_line,   # col 2, row 3
]
labels = [
    "SoC",
    "Charging",
    "Discharging",
    "SoC limit",
    "Charging limit",
    "Discharging limit",
]

ax.legend(
    handles,
    labels,
    loc="lower right",
    ncol=2,
    columnspacing=1.5,
    handletextpad=0.6,
    frameon=True
)

# ---------------------------------------------------------
# SAVE FIGURE
# ---------------------------------------------------------
save_path = os.path.join(
    output_dir,
    f"Daily_{TARGET_STORAGE}_TD{TARGET_TD}_SoC_and_Flows.pdf"
)

plt.tight_layout()
plt.savefig(save_path, dpi=300)
plt.close()

print(f"Saved: {save_path}")
