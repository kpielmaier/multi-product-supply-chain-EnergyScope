import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# === GLOBAL FONT SETTINGS ===
plt.rcParams.update({
    "font.size": 14,
    "text.usetex": False,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
})

# === IMPORT COLOR MAPS ===
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, "Visualization"))
from Colors import colors_proc_electricity

# === SETTINGS ===
END_USE_TO_PLOT = "ELECTRICITY"
CAPACITY_THRESHOLD = 0.01   # ignore tiny capacities
LABEL_THRESHOLD = 0.02      # only print % if >= 2%

data_root   = os.path.join(script_dir, "..", "DataNormalPrice")
case_zero   = os.path.join(data_root, "elast_5pct_eps_0.00")
case_none   = os.path.join(data_root, "elast_5pct_eps_NONE")

output_file = os.path.join(data_root, "ElectricityCapacityPie_eps0p00_vs_NONE.png")


# -------------------------------------------------------------
# Helper: load capacities for one case
# -------------------------------------------------------------
def load_case(case_folder):
    capacity_csv = os.path.join(case_folder, "F_capacities.csv")
    mapping_csv  = os.path.join(case_folder, "tech_of_end_use.csv")

    df_cap = pd.read_csv(capacity_csv)
    df_map = pd.read_csv(mapping_csv)

    # Merge and keep only selected end-use type
    df = df_cap.merge(df_map, left_on="index", right_on="TECHNOLOGY", how="inner")
    df = df[df["END_USE_TYPE"] == END_USE_TO_PLOT].copy()

    # Filter small capacities
    df_major = df[df["capacity"] >= CAPACITY_THRESHOLD].copy()
    other_sum = df[df["capacity"] < CAPACITY_THRESHOLD]["capacity"].sum()
    if other_sum > 0:
        df_major.loc[len(df_major)] = {
            "index": "Other",
            "capacity": other_sum,
            "TECHNOLOGY": "Other",
            "END_USE_TYPE": END_USE_TO_PLOT,
        }

    df_major = df_major.sort_values(by="capacity", ascending=False)

    labels = df_major["index"].tolist()
    sizes  = df_major["capacity"].tolist()
    return labels, sizes


# Load both cases
labels_zero, sizes_zero = load_case(case_zero)
labels_none, sizes_none = load_case(case_none)

# Union of labels for legend (keep "Other" last if present)
all_labels = sorted(set(labels_zero + labels_none) - {"Other"})
if "Other" in labels_zero or "Other" in labels_none:
    all_labels.append("Other")

# Colors per technology (same for both pies)
def get_color(label):
    if label == "Other":
        return "#bbbbbb"
    return colors_proc_electricity.get(label, "#bbbbbb")

colors_zero = [get_color(l) for l in labels_zero]
colors_none = [get_color(l) for l in labels_none]

# Legend handles
legend_colors = [get_color(l) for l in all_labels]
legend_handles = [
    Patch(facecolor=c, edgecolor="white", label=l)
    for l, c in zip(all_labels, legend_colors)
]


# -------------------------------------------------------------
# Plot with two pies and one shared legend
# -------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))

def autopct_filter(pct):
    return f"{pct:.1f}%" if pct >= LABEL_THRESHOLD * 100 else ""

# Left pie: zero-emissions case
wedges1, texts1, autotexts1 = ax1.pie(
    sizes_zero,
    colors=colors_zero,
    labels=None,
    autopct=autopct_filter,
    pctdistance=0.55,
    radius=0.55,
    startangle=90,
    wedgeprops={"linewidth": 1, "edgecolor": "white"},
)
ax1.set_title("Zero emissions (ε = 0.00)", fontsize=16)
ax1.axis("equal")

# Right pie: no-constraint case
wedges2, texts2, autotexts2 = ax2.pie(
    sizes_none,
    colors=colors_none,
    labels=None,
    autopct=autopct_filter,
    pctdistance=0.55,
    radius=0.55,
    startangle=90,
    wedgeprops={"linewidth": 1, "edgecolor": "white"},
)
ax2.set_title("No emission constraint (ε = NONE)", fontsize=16)
ax2.axis("equal")

# Make % labels a bit larger
for t in autotexts1 + autotexts2:
    t.set_fontsize(14)

# Overall title
fig.suptitle(
    "ELECTRICITY Capacities — Normal Price Scenario\n"
    "(comparison: ε = 0.00 vs ε = NONE)",
    fontsize=18,
)

# Room on the right for a single legend
plt.subplots_adjust(right=0.80, wspace=0.3)

fig.legend(
    handles=legend_handles,
    loc="center right",
    bbox_to_anchor=(0.98, 0.5),
    title="Technologies",
    fontsize=12,
    title_fontsize=14,
)

plt.tight_layout(rect=[0.0, 0.0, 0.80, 0.95])

os.makedirs(data_root, exist_ok=True)
plt.savefig(output_file, dpi=300, bbox_inches="tight")
plt.close()

print(f"Saved comparison pie chart to:\n  {output_file}")
