import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
from Colors import colors_proc, colors_ren, colors_nonren, colors_end_use_type, colors_storage

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
data_dir = os.path.join(project_root, r"Data2024")
output_dir = os.path.join(project_root, "Results", "Figures", "Flow")
os.makedirs(output_dir, exist_ok=True)

s_vals = pd.read_csv(os.path.join(data_dir, "s_vals.csv"))
d_vals = pd.read_csv(os.path.join(data_dir, "d_vals.csv"))
e_vals = pd.read_csv(os.path.join(data_dir, "e_vals.csv"))
d_diff_vals = pd.read_csv(os.path.join(data_dir, "d_diff_vals.csv"))
d_ref_df = pd.read_csv(os.path.join(data_dir, "d_ref.csv"))
tech_map = pd.read_csv(os.path.join(data_dir, "tech_of_end_use.csv"))
storage_map = pd.read_csv(os.path.join(data_dir, "storage_of_end_use.csv"))
storage_discharge = pd.read_csv(os.path.join(data_dir, "storage_discharge.csv"))
storage_in = pd.read_csv(os.path.join(data_dir, "storage_charge.csv"))

storage_in["val"] = -abs(storage_in["val"])

def pivot_results(df, col): return df.pivot_table(index="h", columns=col, values="val", aggfunc="sum").fillna(0) if not df.empty else pd.DataFrame()

typical_days = sorted(s_vals["td"].unique())
end_uses = ["ELECTRICITY", "HEAT_HIGH_T", "HEAT_LOW_T_DHN", "HEAT_LOW_T_DECEN"]
renewables = {"RES_WIND", "RES_SOLAR", "RES_HYDRO", "RES_GEO"}

for td in typical_days:
    fig, axes = plt.subplots(5, 2, figsize=(18, 18)); axes = axes.flatten()

    s_td = s_vals[s_vals["td"] == td]
    s_ren_hourly = pivot_results(s_td[s_td["st"].isin(renewables)], "st")
    s_nonren_hourly = pivot_results(s_td[~s_td["st"].isin(renewables)], "st")

    ax = axes[0]
    if not s_nonren_hourly.empty:
        s_nonren_hourly.plot(kind="area", stacked=True, ax=ax, color=[colors_nonren.get(st, "gray") for st in s_nonren_hourly.columns])
    else: ax.text(0.5,0.5,"No data",ha="center",va="center"); ax.set_axis_off()
    ax.set_title("Non-renewable Suppliers",fontsize=11); ax.set_xlabel("Hour"); ax.set_ylabel("Power [GW]"); ax.grid(True); ax.legend(fontsize=7, loc="center left", bbox_to_anchor=(1.02,0.5), frameon=True, framealpha=0.9)

    ax = axes[1]
    if not s_ren_hourly.empty:
        s_ren_hourly.plot(kind="area", stacked=True, ax=ax, color=[colors_ren.get(st,"gray") for st in s_ren_hourly.columns])
    else: ax.text(0.5,0.5,"No data",ha="center",va="center"); ax.set_axis_off()
    ax.set_title("Renewable Suppliers",fontsize=11); ax.set_xlabel("Hour"); ax.set_ylabel("Power [GW]"); ax.grid(True); ax.legend(fontsize=7, loc="center left", bbox_to_anchor=(1.02,0.5), frameon=True, framealpha=0.9)

    for i, eut in enumerate(end_uses):
        techs = tech_map.loc[tech_map["END_USE_TYPE"] == eut, "TECHNOLOGY"].tolist()
        sto_techs = storage_map.loc[storage_map["END_USE_TYPE"] == eut, "STORAGE_TECH"].tolist()

        e_td_form = e_vals[(e_vals["td"] == td) & (e_vals["pt"].isin(techs))][["h","pt","val"]].rename(columns={"pt":"tech"})
        sto_out = storage_discharge[(storage_discharge["td"] == td) & (storage_discharge["j"].isin(sto_techs))][["h","j","val"]].rename(columns={"j":"tech"})
        sto_in = storage_in[(storage_in["td"] == td) & (storage_in["j"].isin(sto_techs))][["h","j","val"]].rename(columns={"j":"tech"})

        combined_supply = pd.concat([e_td_form, sto_out, sto_in])
        ax_flow = axes[(i+1)*2]

        if combined_supply.empty:
            ax_flow.text(0.5,0.5,f"No supply for {eut}",ha="center",va="center"); ax_flow.set_axis_off()
        else:
            ch = pivot_results(combined_supply,"tech")
            ax_flow.set_title(f"{eut} – Processors + Storage",fontsize=11,color=colors_end_use_type[eut])
            ax_flow.set_xlabel("Hour"); ax_flow.set_ylabel("Power [GW]"); ax_flow.grid(True)

            bottom = pd.Series([0]*24,index=ch.index)
            handles = []

            for tech in ch.columns:
                y = ch[tech]
                if tech in sto_techs and (y > 0).any():
                    c = colors_storage[eut].get(tech,"gray")
                    ax_flow.fill_between(y.index,bottom,bottom+y,facecolor="none",edgecolor=c,hatch="///",linewidth=0.8)
                    handles.append(mpatches.Patch(facecolor="none",edgecolor=c,hatch="///",label=tech))
                elif tech in sto_techs and (y < 0).any():
                    c = colors_storage[eut].get(tech,"gray")
                    ax_flow.fill_between(y.index,bottom,bottom+y,facecolor="none",edgecolor=c,hatch="\\\\\\",linewidth=0.8)
                    handles.append(mpatches.Patch(facecolor="none",edgecolor=c,hatch="\\\\\\",label=tech))
                else:
                    c = colors_proc[eut].get(tech,"gray")
                    ax_flow.fill_between(y.index,bottom,bottom+y,facecolor=c,alpha=0.8,linewidth=0)
                    handles.append(mpatches.Patch(facecolor=c,edgecolor="none",label=tech))
                bottom += y

            ax_flow.legend(handles=handles, fontsize=6, loc="center left", bbox_to_anchor=(1.02,0.5), frameon=True, framealpha=0.9)

        d_td = d_vals[(d_vals["td"]==td)&(d_vals["ct"]==eut)]
        d_diff = d_diff_vals[(d_diff_vals["td"]==td)&(d_diff_vals["ct"]==eut)]
        d_ref = d_ref_df[(d_ref_df["td"]==td)&(d_ref_df["ct"]==eut)]

        d_h = pivot_results(d_td,"ct"); d_diff_h = pivot_results(d_diff,"ct")
        d_sum = d_h.sum(axis=1) if not d_h.empty else pd.Series(0,index=range(1,25))
        d_diff_sum = d_diff_h.sum(axis=1) if not d_diff_h.empty else pd.Series(0,index=d_sum.index)
        d_ref_sum = d_ref.groupby("h")["d_ref"].sum().reindex(d_sum.index,fill_value=0)

        ax_c = axes[(i+1)*2+1]

        ax_c.fill_between(d_ref_sum.index,0,d_ref_sum,color="darkgray",alpha=0.4,label="Reference demand")
        ax_c.plot(d_ref_sum.index,d_ref_sum,"--",color="black",linewidth=1.2,label="Reference curve")
        ax_c.plot(d_sum.index,d_sum,color=colors_end_use_type[eut],linewidth=2,label="Actual demand")

        pos = d_diff_sum.clip(lower=0); neg = d_diff_sum.clip(upper=0)
        ax_c.fill_between(d_ref_sum.index,d_ref_sum,d_ref_sum+pos,color="green",alpha=0.3,label="+d_diff")
        ax_c.fill_between(d_ref_sum.index,d_ref_sum+neg,d_ref_sum,color="red",alpha=0.3,label="-d_diff")

        ax_c.set_title(f"{eut} – Consumer",fontsize=11,color=colors_end_use_type[eut])
        ax_c.set_xlabel("Hour"); ax_c.set_ylabel("Demand [GW]"); ax_c.grid(True); ax_c.legend(fontsize=7, loc="center left", bbox_to_anchor=(1.02,0.5), frameon=True, framealpha=0.9)

    plt.suptitle(f"Flow (Typical Day {td})",fontsize=16)
    plt.tight_layout(rect=[0,0,1,0.97])
    plt.savefig(os.path.join(output_dir,f"Flow_TD{td}.png"),dpi=300,bbox_inches="tight")
    plt.close(fig)
