import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

from Colors import (
    colors_proc,
    colors_ren,
    colors_nonren,
    colors_end_use_type,
    colors_storage,
)

plt.rcParams.update({
    "text.usetex": False,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 16,
})

# ------------------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(script_dir, "..", "DataNormalPrice", "demand_fixed_eps_0.00")
output_dir = os.path.join(script_dir, "..", "Results", "Figures", "Flow")
os.makedirs(output_dir, exist_ok=True)

# ------------------------------------------------------------------------------
# Read Data
# ------------------------------------------------------------------------------
s_vals = pd.read_csv(os.path.join(data_dir, "s_vals.csv"))
d_vals = pd.read_csv(os.path.join(data_dir, "d_vals.csv"))
e_vals = pd.read_csv(os.path.join(data_dir, "e_vals.csv"))
d_diff_vals = pd.read_csv(os.path.join(data_dir, "d_diff_vals.csv"))
d_ref_df = pd.read_csv(os.path.join(data_dir, "d_ref.csv"))
tech_map = pd.read_csv(os.path.join(data_dir, "tech_of_end_use.csv"))
storage_map = pd.read_csv(os.path.join(data_dir, "storage_of_end_use.csv"))
storage_discharge = pd.read_csv(os.path.join(data_dir, "storage_discharge.csv"))
storage_in = pd.read_csv(os.path.join(data_dir, "storage_charge.csv"))
layers = pd.read_csv(os.path.join(data_dir, "layers_in_out.csv"))

# ------------------------------------------------------------------------------
# Preprocess Storage
# ------------------------------------------------------------------------------
storage_in["val"] = -abs(storage_in["val"])

# ------------------------------------------------------------------------------
# Pivot helper
# ------------------------------------------------------------------------------
def pivot_results(df: pd.DataFrame, col: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    return (
        df.pivot_table(index="h", columns=col, values="val", aggfunc="sum")
        .fillna(0)
        .sort_index()
    )

# ------------------------------------------------------------------------------
# Build mapping tech -> primary END_USE_TYPE
# ------------------------------------------------------------------------------
tech_to_eut = dict(zip(tech_map["TECHNOLOGY"], tech_map["END_USE_TYPE"]))

def get_proc_color(tech: str, eut_plot: str) -> str:
    """
    Special rule:
    - If plotted in ELECTRICITY panel
    - AND technology ends with _ELEC
    - AND its primary END_USE_TYPE is NOT ELECTRICITY
    → use the color of its true end-use type.

    Otherwise:
    → use the normal color from its primary end-use category.
    """
    eut_home = tech_to_eut.get(tech)

    # 🔴 SPECIAL CROSS-END-USE ELECTRICITY RULE
    if eut_plot == "ELECTRICITY" and tech.endswith("_ELEC") and eut_home != "ELECTRICITY":
        return colors_end_use_type.get(eut_home, "gray")

    # ✅ Normal coloring
    if eut_home in colors_proc:
        return colors_proc[eut_home].get(tech, "gray")

    # Fallback lookup
    for _, cmap in colors_proc.items():
        if tech in cmap:
            return cmap[tech]

    return "gray"

# ------------------------------------------------------------------------------
# Time loops
# ------------------------------------------------------------------------------
typical_days = sorted(s_vals["td"].unique())
end_uses = ["ELECTRICITY", "HEAT_HIGH_T", "HEAT_LOW_T_DHN", "HEAT_LOW_T_DECEN"]
renewables = {"RES_WIND", "RES_SOLAR", "RES_HYDRO", "RES_GEO"}

# ------------------------------------------------------------------------------
# MAIN LOOP
# ------------------------------------------------------------------------------
for td in typical_days:
    fig, axes = plt.subplots(5, 2, figsize=(18, 18))
    axes = axes.flatten()

    # --------------------------------------------------------------------------
    # Supplier flows
    # --------------------------------------------------------------------------
    s_td = s_vals[s_vals["td"] == td]

    s_ren_hourly = pivot_results(s_td[s_td["st"].isin(renewables)], "st")
    if not s_ren_hourly.empty:
        s_ren_hourly = s_ren_hourly.loc[:, (s_ren_hourly.abs().sum(axis=0) > 1e-6)]

    s_nonren_hourly = pivot_results(s_td[~s_td["st"].isin(renewables)], "st")
    if not s_nonren_hourly.empty:
        s_nonren_hourly = s_nonren_hourly.loc[:, (s_nonren_hourly.abs().sum(axis=0) > 1e-6)]

    # --- Renewables (LEFT) ---
    ax = axes[0]
    if not s_ren_hourly.empty:
        s_ren_hourly.plot(
            kind="area",
            stacked=True,
            ax=ax,
            color=[colors_ren.get(st, "gray") for st in s_ren_hourly.columns],
            linewidth=0
        )
        ax.legend(fontsize=12, loc="center left", bbox_to_anchor=(1.02, 0.5))
    else:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.set_axis_off()

    ax.set_title("Renewable Suppliers")
    ax.set_xlabel("Hour")
    ax.set_ylabel("Power [GW]")
    ax.grid(True)

    ymin, ymax = ax.get_ylim()
    if ymax < 1:
        ax.set_ylim(ymin, 1)

    # --- Non-renewables (RIGHT) ---
    ax = axes[1]
    if not s_nonren_hourly.empty:
        s_nonren_hourly.plot(
            kind="area",
            stacked=True,
            ax=ax,
            color=[colors_nonren.get(st, "gray") for st in s_nonren_hourly.columns],
            linewidth=0
        )
        ax.legend(fontsize=12, loc="center left", bbox_to_anchor=(1.02, 0.5))
    else:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.set_axis_off()

    ax.set_title("Non-renewable Suppliers")
    ax.set_xlabel("Hour")
    ax.set_ylabel("Power [GW]")
    ax.grid(True)

    ymin, ymax = ax.get_ylim()
    if ymax < 1:
        ax.set_ylim(ymin, 1)

    # --------------------------------------------------------------------------
    # Processor + Storage flows for each END-USE TYPE
    # --------------------------------------------------------------------------
    for i, eut in enumerate(end_uses):

        ax_flow = axes[(i + 1) * 2]

        techs = layers[layers["p"] == eut]["pt"].unique()
        sto_techs = storage_map.loc[
            storage_map["END_USE_TYPE"] == eut, "STORAGE_TECH"
        ].tolist()

        e_td = e_vals[e_vals["td"] == td].merge(layers, on="pt", how="left")
        e_td = e_td[
            (e_td["p"] == eut)
            & (e_td["pt"].isin(techs))
            & (e_td["layers_in_out"] != 0)
        ]
        e_td["val"] = e_td["val"] * e_td["layers_in_out"]
        e_td_form = e_td[["h", "pt", "val"]].rename(columns={"pt": "tech"})

        sto_out = storage_discharge[
            (storage_discharge["td"] == td)
            & (storage_discharge["j"].isin(sto_techs))
        ][["h", "j", "val"]].rename(columns={"j": "tech"})

        sto_in = storage_in[
            (storage_in["td"] == td)
            & (storage_in["j"].isin(sto_techs))
        ][["h", "j", "val"]].rename(columns={"j": "tech"})

        combined = pd.concat([e_td_form, sto_out, sto_in], ignore_index=True)

        if combined.empty:
            ax_flow.text(0.5, 0.5, f"No supply for {eut}", ha="center", va="center")
            ax_flow.set_axis_off()
            continue

        ch = pivot_results(combined, "tech")

        if eut == "ELECTRICITY":
            def elec_stack_priority(tech):
                eut_home = tech_to_eut.get(tech)
                if tech.endswith("_ELEC") and eut_home != "ELECTRICITY":
                    if eut_home == "HEAT_HIGH_T":
                        return 1
                    if eut_home == "HEAT_LOW_T_DHN":
                        return 2
                    if eut_home == "HEAT_LOW_T_DECEN":
                        return 3
                    return 99
                return 0  # normal electricity processors stay at the bottom
            sorted_techs = sorted(ch.columns, key=elec_stack_priority)
            ch = ch[sorted_techs]

        ax_flow.set_title(f"{eut} – Processors + Storage", color=colors_end_use_type[eut])
        ax_flow.set_xlabel("Hour")
        ax_flow.set_ylabel("Power [GW]")
        ax_flow.grid(True)

        positive = ch.clip(lower=0)
        negative = ch.clip(upper=0)

        pos_bottom = pd.Series(0, index=positive.index)
        neg_bottom = pd.Series(0, index=negative.index)

        handles = []

        for tech in ch.columns:
            y_pos = positive[tech]
            y_neg = negative[tech]

            if y_pos.abs().max() < 1e-6 and y_neg.abs().max() < 1e-6:
                continue

            # --- STORAGE: HATCHED ---
            if tech in sto_techs:
                c = colors_storage[eut].get(tech, "gray")

                if (y_pos > 0).any():
                    ax_flow.fill_between(
                        y_pos.index,
                        pos_bottom,
                        pos_bottom + y_pos,
                        facecolor="none",
                        edgecolor=c,
                        hatch="///",
                        linewidth=1.0,
                    )
                    pos_bottom += y_pos

                if (y_neg < 0).any():
                    ax_flow.fill_between(
                        y_neg.index,
                        neg_bottom,
                        neg_bottom + y_neg,
                        facecolor="none",
                        edgecolor=c,
                        hatch="///",
                        linewidth=1.0,
                    )
                    neg_bottom += y_neg

                handles.append(
                    mpatches.Patch(facecolor="none", edgecolor=c, hatch="///", label=tech)
                )
                continue

            # --- PROCESSORS: PURE COLOR ---
            c = get_proc_color(tech, eut)

            if (y_pos > 0).any():
                ax_flow.fill_between(
                    y_pos.index,
                    pos_bottom,
                    pos_bottom + y_pos,
                    facecolor=c,
                    edgecolor=c,
                    linewidth=0,
                )
                pos_bottom += y_pos

            if (y_neg < 0).any():
                ax_flow.fill_between(
                    y_neg.index,
                    neg_bottom,
                    neg_bottom + y_neg,
                    facecolor=c,
                    edgecolor=c,
                    linewidth=0,
                )
                neg_bottom += y_neg

            handles.append(mpatches.Patch(facecolor=c, edgecolor=c, label=tech))

        ax_flow.axhline(0, color="black", linewidth=1.0)
        ax_flow.legend(handles=handles, fontsize=12, loc="center left", bbox_to_anchor=(1.02, 0.5))

    # --------------------------------------------------------------------------
    # DEMAND PANELS
    # --------------------------------------------------------------------------
    for i, eut in enumerate(end_uses):
        ax_c = axes[(i + 1) * 2 + 1]

        d_td = d_vals[(d_vals["td"] == td) & (d_vals["ct"] == eut)]
        d_diff = d_diff_vals[(d_diff_vals["td"] == td) & (d_diff_vals["ct"] == eut)]
        d_ref = d_ref_df[(d_ref_df["td"] == td) & (d_ref_df["ct"] == eut)]

        d_h = pivot_results(d_td, "ct")
        d_diff_h = pivot_results(d_diff, "ct")

        d_sum = d_h.sum(axis=1) if not d_h.empty else pd.Series(0, index=range(1, 25))
        d_diff_sum = d_diff_h.sum(axis=1) if not d_diff_h.empty else pd.Series(0, index=d_sum.index)
        d_ref_sum = d_ref.groupby("h")["d_ref"].sum().reindex(d_sum.index, fill_value=0)

        ax_c.fill_between(d_ref_sum.index, 0, d_ref_sum, color="darkgray", alpha=0.4)
        ax_c.plot(d_ref_sum.index, d_ref_sum, color="black", linewidth=1.2)
        ax_c.plot(d_sum.index, d_sum, color=colors_end_use_type[eut], linewidth=2)

        pos = d_diff_sum.clip(lower=0)
        neg = d_diff_sum.clip(upper=0)

        ax_c.fill_between(d_ref_sum.index, d_ref_sum, d_ref_sum + pos, color="green", alpha=0.3)
        ax_c.fill_between(d_ref_sum.index, d_ref_sum + neg, d_ref_sum, color="red", alpha=0.3)

        ax_c.set_title(f"{eut} – Consumers", color=colors_end_use_type[eut])
        ax_c.set_xlabel("Hour")
        ax_c.set_ylabel("Power [GW]")
        ax_c.grid(True)

        reference_handle = (
            mpatches.Patch(facecolor="darkgray", alpha=0.4),
            Line2D([0], [0], color="black", linewidth=1.2),
        )

        legend_handles = [
            reference_handle,
            Line2D([0], [0], color=colors_end_use_type[eut], linewidth=2),
            mpatches.Patch(color="green", alpha=0.3),
            mpatches.Patch(color="red", alpha=0.3),
        ]

        legend_labels = [
            "Reference demand",
            "Actual demand",
            "Demand increase",
            "Demand decrease",
        ]

        ax_c.legend(
            handles=legend_handles,
            labels=legend_labels,
            fontsize=12,
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            frameon=True,
            framealpha=0.9,
        )

    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.savefig(os.path.join(output_dir, f"Flow_TD{td}.pdf"), dpi=300, bbox_inches="tight")
    plt.close(fig)
