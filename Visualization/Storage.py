import os
import pandas as pd
import matplotlib.pyplot as plt

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
data_dir = os.path.join(project_root, r"DataNormalPrice\elast_5pct_eps_0.00")
output_dir = os.path.join(project_root, "Results", "Figures", "Storage")
os.makedirs(output_dir, exist_ok=True)

daily_dir = os.path.join(output_dir, "Daily")
seasonal_dir = os.path.join(output_dir, "Seasonal")
os.makedirs(daily_dir, exist_ok=True)
os.makedirs(seasonal_dir, exist_ok=True)

seasonal_df = pd.read_csv(os.path.join(data_dir, "storage_level_seasonal.csv"))
daily_df = pd.read_csv(os.path.join(data_dir, "storage_level_daily.csv"))
tech_set = pd.read_csv(os.path.join(data_dir, "storage_tech.csv"))["STORAGE_TECH"].tolist()
daily_set = pd.read_csv(os.path.join(data_dir, "storage_daily.csv"))["STORAGE_DAILY"].tolist()

storage_map_df = pd.read_csv(os.path.join(data_dir, "storage_of_end_use.csv"))
storage_to_enduse = {r["STORAGE_TECH"]: r["END_USE_TYPE"] for _, r in storage_map_df.iterrows()}

map_df = pd.read_csv(os.path.join(data_dir, "t_h_td_mapping.csv"))

daily_merge = daily_df.merge(map_df, on=["h","td"])
daily_final = daily_merge[["j","n","t","val"]]

combined = seasonal_df.merge(daily_final, on=["j","n","t"], how="left", suffixes=("_s","_d"))
combined["val"] = combined.apply(lambda r: r["val_d"] if (r["j"] in daily_set and not pd.isna(r["val_d"])) else r["val_s"], axis=1)
combined = combined[["j","n","t","val"]].merge(map_df, on="t")

seasonal_threshold = 9e-1
daily_threshold = 9e-1

for j in sorted(tech_set):
    eut = storage_to_enduse.get(j, "UNKNOWN")
    dfj = combined[combined["j"] == j]
    if dfj.empty: continue

    if j not in daily_set:
        df_seasonal = dfj.groupby("t")["val"].sum().reset_index()
        if df_seasonal["val"].abs().max() < seasonal_threshold: continue
        df_seasonal["val"] = df_seasonal["val"].apply(lambda x: 0 if abs(x) < seasonal_threshold else x)
        plt.figure(figsize=(14,5))
        plt.plot(df_seasonal["t"], df_seasonal["val"], linewidth=1.5)
        plt.title(f"{j} ({eut}) – Seasonal Storage Level")
        plt.xlabel("Period (t)")
        plt.ylabel("Energy [GWh]")
        plt.grid(True)
        plt.ylim(bottom=0)
        plt.savefig(os.path.join(seasonal_dir, f"Seasonal_{j}.png").replace("/","_"), dpi=300)
        plt.close()
        continue

    df_daily = dfj.groupby(["td","h"])["val"].sum().reset_index()
    df_daily["val"] = df_daily["val"].apply(lambda x: 0 if abs(x) < daily_threshold else x)
    active_days = sorted(df_daily[df_daily["val"] > 0]["td"].unique())
    if len(active_days) == 0: continue

    fig, axes = plt.subplots(len(active_days), 1, figsize=(10, 4*len(active_days)), sharex=True)
    if len(active_days) == 1: axes = [axes]

    for ax, td_val in zip(axes, active_days):
        df_day = df_daily[df_daily["td"] == td_val]
        ax.plot(df_day["h"], df_day["val"], linewidth=2)
        ax.grid(True)
        ax.set_ylabel("Energy [GWh]")
        ax.set_title(f"Typical Day {td_val}")
        ax.set_ylim(bottom=0)

    axes[-1].set_xlabel("Hour")
    plt.suptitle(f"{j} ({eut}) – Daily Storage Level", fontsize=14)
    plt.tight_layout(rect=[0,0,1,0.96])
    plt.savefig(os.path.join(daily_dir, f"Daily_{j}.png").replace("/","_"), dpi=300)
    plt.close()
