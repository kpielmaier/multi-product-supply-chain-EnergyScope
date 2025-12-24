### Sets ###
# Time
set PERIODS := 1 .. 8760;
set HOURS := 1..24;
set TYPICAL_DAYS:= 1 .. 12;
set T_H_TD within {PERIODS, HOURS, TYPICAL_DAYS};
set HOUR_OF_PERIOD {t in PERIODS} := setof {h in HOURS, td in TYPICAL_DAYS: (t,h,td) in T_H_TD} h;
set TYPICAL_DAY_OF_PERIOD {t in PERIODS} := setof {h in HOURS, td in TYPICAL_DAYS: (t,h,td) in T_H_TD} td;

# Space
set NODES;

# Sectors
set SECTORS;

# End-uses
set END_USES_INPUT;
set END_USES_CATEGORIES;
set END_USES_TYPES_OF_CATEGORY {END_USES_CATEGORIES};
set END_USES_TYPES := setof {i in END_USES_CATEGORIES, j in END_USES_TYPES_OF_CATEGORY[i]} j;

# Resources
set RESOURCES;
set RES_IMPORT_CONSTANT within RESOURCES;
# set EXPORT within RESOURCES;
set RE_RESOURCES within RESOURCES;

# Technologies
set TECHNOLOGIES_OF_END_USES_TYPE {END_USES_TYPES};
set STORAGE_TECH;
set STORAGE_DAILY within STORAGE_TECH;
set STORAGE_OF_END_USES_TYPES {END_USES_TYPES} within STORAGE_TECH;
set TS_OF_DEC_TECH {TECHNOLOGIES_OF_END_USES_TYPE["HEAT_LOW_T_DECEN"] diff {"DEC_SOLAR"}};
set INFRASTRUCTURE;
set TECHNOLOGIES := (setof {i in END_USES_TYPES, j in TECHNOLOGIES_OF_END_USES_TYPE [i]} j) union STORAGE_TECH union INFRASTRUCTURE;
set TECHNOLOGIES_OF_END_USES_CATEGORY {i in END_USES_CATEGORIES} within TECHNOLOGIES := setof {j in END_USES_TYPES_OF_CATEGORY[i], k in TECHNOLOGIES_OF_END_USES_TYPE[j]} k;
set COGEN within TECHNOLOGIES;
set BOILERS within TECHNOLOGIES;

# Stakeholders -> not essential but helps with clarity
set CONSUMER_TYPES := END_USES_TYPES;
set CONSUMERS := setof {ct in CONSUMER_TYPES, n in NODES, h in HOURS, td in TYPICAL_DAYS} (ct,n,h,td);
set SUPPLIER_TYPES := RESOURCES;
set SUPPLIERS := setof {st in SUPPLIER_TYPES, n in NODES, h in HOURS, td in TYPICAL_DAYS} (st,n,h,td);
set PROCESSOR_TYPES := TECHNOLOGIES diff STORAGE_TECH diff INFRASTRUCTURE;
set PROCESSORS := setof {pt in PROCESSOR_TYPES, n in NODES, h in HOURS, td in TYPICAL_DAYS} (pt,n,h,td);
set STORAGE_TYPES := STORAGE_TECH;
set STORAGES := setof {stot in STORAGE_TYPES, n in NODES, h in HOURS, td in TYPICAL_DAYS} (stot,n,h,td);
# set TRANSPORTER_TYPES := INFRASTRUCTURE;
# set TRANSPORTERS := setof {tt in TRANSPORTER_TYPES, nf in NODES, nt in NODES, h in HOURS, td in TYPICAL_DAYS} (tt,nf,nt,h,td);

# Products
set PRODUCTS := RESOURCES union END_USES_TYPES; # vs set LAYERS := (RESOURCES diff EXPORT) union END_USES_TYPES;

### Parameters ###
# Time
param mult {h in HOURS, td in TYPICAL_DAYS} := card {t in PERIODS: (t,h,td) in T_H_TD}; # [1/year]
param t_op {HOURS, TYPICAL_DAYS} default 1; # [h]
param total_time := sum {t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (t_op[h,td]); # [h/year]
param i_rate > 0; # []
# param gwp_limit >= 0; # [ktCO2-eq./year]
param use_epsilon; # []
param epsilon_value; # [ktCO2-eq./year]
# param co2_price >= 0; # [M€/ktCO2-eq.]

# Time series
param c_p_t {TECHNOLOGIES, HOURS, TYPICAL_DAYS} default 1; # []
param electricity_time_series {HOURS, TYPICAL_DAYS} >= 0, <= 1; # []
param heating_time_series {HOURS, TYPICAL_DAYS} >= 0, <= 1; # []

# End-uses
param end_uses_demand_year {END_USES_INPUT, SECTORS} >= 0 default 0; # [GWh]
param end_uses_input {i in END_USES_INPUT} := sum {s in SECTORS} (end_uses_demand_year[i,s]); # [GWh]
# param share_heat_dhn_min >= 0, <= 1; # []
# param share_heat_dhn_max >= 0, <= 1; # []
param loss_network {END_USES_TYPES} >= 0 default 0; # []

# Consumers
param prod_ct {i in CONSUMER_TYPES} symbolic in PRODUCTS := i;
param prod_d {(ct,n,h,td) in CONSUMERS} symbolic in PRODUCTS := prod_ct[ct];
param alpha_ct {CONSUMER_TYPES} >= 0; # [M€/GWh=€/kWh]
param alpha_d {(ct,n,h,td) in CONSUMERS} := alpha_ct[ct];
param Share_heat_dhn; # [] vs var Share_heat_dhn, >= share_heat_dhn_min, <= share_heat_dhn_max;
param End_uses {p in PRODUCTS, h in HOURS, td in TYPICAL_DAYS} :=
    if p = "ELECTRICITY" then
        end_uses_input["LIGHTING"] / total_time + end_uses_input["ELECTRICITY"] * electricity_time_series[h,td] / t_op[h,td] # switched ELECTRICITY and LIGHTING wrt EnergyScope core version
    else if p = "HEAT_LOW_T_DHN" then
        (end_uses_input["HEAT_LOW_T_HW"] / total_time + end_uses_input["HEAT_LOW_T_SH"] * heating_time_series[h,td] / t_op[h,td]) * Share_heat_dhn # + Network_losses[p,h,td]
    else if p = "HEAT_LOW_T_DECEN" then
        (end_uses_input["HEAT_LOW_T_HW"] / total_time + end_uses_input["HEAT_LOW_T_SH"] * heating_time_series[h,td] / t_op[h,td]) * (1 - Share_heat_dhn)
    else if p = "HEAT_HIGH_T" then
        end_uses_input["HEAT_HIGH_T"] / total_time
    else
        0;  # [GW] vs var End_uses {LAYERS, HOURS, TYPICAL_DAYS} >= 0;
param VOLL; # [M€/GWh]
param elasticity; # []
param beta {ct in CONSUMER_TYPES, n in NODES, h in HOURS, td in TYPICAL_DAYS} := 1/elasticity; # []
param d_ref {ct in CONSUMER_TYPES, n in NODES, h in HOURS, td in TYPICAL_DAYS} := End_uses[prod_ct[ct],h,td]; # [GW]
param p_ref {ct in CONSUMER_TYPES, n in NODES, h in HOURS, td in TYPICAL_DAYS} := alpha_d[ct,n,h,td]; # [M€/GWh]
param A {(ct,n,h,td) in CONSUMERS} := p_ref[ct,n,h,td] / (d_ref[ct,n,h,td] ** beta[ct,n,h,td]);
param fix_demand default 0;

# PWL
param K = 5;
set SEGMENTS := 1..K;
set BREAKPOINTS := 0..K;
param d_mult {k in BREAKPOINTS} :=
    if k = 0 then 0.1
    else 0.95 + (k - 1) * (1.1 - 0.95) / (K - 1);
param d_pw {k in BREAKPOINTS, ct in CONSUMER_TYPES, n in NODES, h in HOURS, td in TYPICAL_DAYS} :=
    if k = 0 then 0
    else d_mult[k] * d_ref[ct,n,h,td];
param p_pw {k in BREAKPOINTS, ct in CONSUMER_TYPES, n in NODES, h in HOURS, td in TYPICAL_DAYS} :=
    if k = 0 then VOLL
    else if k = K then 0
    else A[ct,n,h,td] * (d_pw[k,ct,n,h,td] ** beta[ct,n,h,td]);
param D {k in SEGMENTS, ct in CONSUMER_TYPES, n in NODES, h in HOURS, td in TYPICAL_DAYS} := 
    d_pw[k,ct,n,h,td] - d_pw[k-1,ct,n,h,td];
param b {k in SEGMENTS, ct in CONSUMER_TYPES, n in NODES, h in HOURS, td in TYPICAL_DAYS} >= 0 := 
    (p_pw[k-1,ct,n,h,td] - p_pw[k,ct,n,h,td]) / D[k,ct,n,h,td];
param a {k in SEGMENTS, ct in CONSUMER_TYPES, n in NODES, h in HOURS, td in TYPICAL_DAYS} := 
    p_pw[k-1,ct,n,h,td];

# Resources
param prod_st {i in SUPPLIER_TYPES} symbolic in PRODUCTS := i;
param prod_s {(st,n,h,td) in SUPPLIERS} symbolic in PRODUCTS := prod_st[st];
param avail {RESOURCES} >= 0; # [GWh/year]
param gwp_op {RESOURCES} >= 0; # [ktCO2-eq./GWh]
param c_op {RESOURCES} >= 0; # [M€/GWh=€/kWh]
param alpha_s {(st,n,h,td) in SUPPLIERS} := c_op[st];

# Technologies
param alpha {TECHNOLOGIES} := 0.0; # [M€/GWh=€/kWh], now always 0.0 but kept in case of additional variable operating costs
param c_inv {TECHNOLOGIES} >= 0; # [M€/GW], storage [M€/GWh]
param c_maint {TECHNOLOGIES} >= 0; # [M€/GW/year], storage [M€/GWh]
param gwp_constr {TECHNOLOGIES} >= 0; # [ktCO2-eq./GW]
param lifetime {TECHNOLOGIES} >= 1; # [year]
param tau {j in TECHNOLOGIES} :=  i_rate * (1 + i_rate) ^ lifetime[j] / (((1 + i_rate) ^ lifetime[j]) - 1); # [1/year]
param c_p {TECHNOLOGIES} >= 0, <= 1 default 1; # []
param fmin_perc {TECHNOLOGIES} >= 0, <= 1 default 0; # []
param fmax_perc {TECHNOLOGIES} >= 0, <= 1 default 1; # []
param f_min {TECHNOLOGIES} >= 0; # [GW], storage [GWh]
param f_max {TECHNOLOGIES} >= 0; # [GW], storage [GWh]
param solar_area >= 0; # [km2]
param power_density_pv >=0 default 0; # [GW/km2]
param power_density_solar_thermal >=0 default 0; # []

# Processors
param layers_in_out {PROCESSOR_TYPES, PRODUCTS}; # [] vs param layers_in_out {RESOURCES union TECHNOLOGIES, LAYERS}
param alpha_e {(pt,n,h,td) in PROCESSORS} := alpha[pt];

# Storage
# param alpha_sto {(stot,n,h,td) in STORAGE_TYPES} := alpha[stot];
param storage_eff_in {STORAGE_TECH, PRODUCTS} >= 0, <= 1; # []
param storage_eff_out {STORAGE_TECH, PRODUCTS} >= 0, <= 1; # []
param storage_charge_time {STORAGE_TECH} >= 0; # [h]
param storage_discharge_time {STORAGE_TECH} >= 0; # [h]
param storage_availability {STORAGE_TECH} >= 0 default 1; # []
param storage_losses {STORAGE_TECH} >= 0, <= 1; # []

# Transporters
# param prod_tt {i in TRANSPORTER_TYPES} symbolic in PRODUCTS := i;
# param prod_f {(tt,nf,nt,h,td) in TRANSPORTERS} symbolic in PRODUCTS := prod_tt[tt];
# param alpha_f {(tt,nf,nt,h,td) in TRANSPORTERS} := alpha[tt];
param c_grid_extra >= 0; # [M€/GW]

### Variables ###
# Independent
var d_seg {(ct,n,h,td) in CONSUMERS, k in SEGMENTS} >= 0; # [GW]
var d {(ct,n,h,td) in CONSUMERS} >= 0; # [GW]
var Shares_lowT_dec {TECHNOLOGIES_OF_END_USES_TYPE["HEAT_LOW_T_DECEN"] diff {"DEC_SOLAR"}} >=0; # []
var s {(st,n,h,td) in SUPPLIERS} >= 0; # [GW]
var F {TECHNOLOGIES} >= 0; # [GW], storage [GWh]
var F_solar {TECHNOLOGIES_OF_END_USES_TYPE["HEAT_LOW_T_DECEN"] diff {"DEC_SOLAR"}} >=0; # []
var e {(pt,n,h,td) in PROCESSORS} >= 0; # [GW]
var F_t_solar {TECHNOLOGIES_OF_END_USES_TYPE["HEAT_LOW_T_DECEN"] diff {"DEC_SOLAR"}, h in HOURS, td in TYPICAL_DAYS} >= 0; # [GW]
var Storage_in {STORAGE_TECH, PRODUCTS, NODES, HOURS, TYPICAL_DAYS} >= 0; # [GW]
var Storage_out {STORAGE_TECH, PRODUCTS, NODES, HOURS, TYPICAL_DAYS} >= 0; # [GW]
# var f {(tt,nf,nt,h,td) in TRANSPORTERS} >= 0; # [GW]

# Dependent
var Storage_level {STORAGE_TECH, NODES, PERIODS} >= 0; # [GWh]
var Storage_level_daily {STORAGE_DAILY, NODES, HOURS, TYPICAL_DAYS} >= 0; # [GWh]
var d_diff {CONSUMER_TYPES, NODES, HOURS, TYPICAL_DAYS}; # [GW]
var Network_losses {END_USES_TYPES, HOURS, TYPICAL_DAYS} >= 0; # [GW]
var Import_constant {RES_IMPORT_CONSTANT} >= 0; # [GWh]
var TotalCost >= 0; # [M€/year]
var C_inv {TECHNOLOGIES} >= 0; # [M€]
var C_maint {TECHNOLOGIES} >= 0; # [M€/year]
var C_op {RESOURCES} >= 0; # [M€/year]
var TotalGWP >= 0; # [ktCO2-eq./year]
var GWP_constr {TECHNOLOGIES} >= 0; # [ktCO2-eq.]
var GWP_op {RESOURCES} >= 0; # [ktCO2-eq.]

### Constraints ###
# Consumers
subject to satisfy_demand {ct in CONSUMER_TYPES, n in NODES, h in HOURS, td in TYPICAL_DAYS}:
    fix_demand * d[ct,n,h,td] = fix_demand * d_ref[ct,n,h,td];

subject to d_diff_def {ct in CONSUMER_TYPES, n in NODES, h in HOURS, td in TYPICAL_DAYS}:
    d_diff[ct,n,h,td] = d[ct,n,h,td] - d_ref[ct,n,h,td];

subject to seg_bounds {(ct,n,h,td) in CONSUMERS, k in SEGMENTS}:
    d_seg[ct,n,h,td,k] <= D[k,ct,n,h,td];
# subject to seg_bounds {(ct,n,h,td) in CONSUMERS, k in SEGMENTS}:
#     (1 - fix_demand) * d_seg[ct,n,h,td,k] <= (1 - fix_demand) * D[k,ct,n,h,td];

subject to demand_partition {(ct,n,h,td) in CONSUMERS}:
    sum{k in SEGMENTS} d_seg[ct,n,h,td,k] = d[ct,n,h,td];
# subject to demand_partition {(ct,n,h,td) in CONSUMERS}:
#     (1 - fix_demand) * sum{k in SEGMENTS} d_seg[ct,n,h,td,k] = d[ct,n,h,td];

subject to network_losses {eut in END_USES_TYPES, h in HOURS, td in TYPICAL_DAYS}:
    Network_losses[eut,h,td] =
        (sum {n in NODES, st in SUPPLIER_TYPES: st = eut} s[st,n,h,td]
        + sum {n in NODES, pt in PROCESSOR_TYPES: layers_in_out[pt,eut] > 0} layers_in_out[pt,eut] * e[pt,n,h,td])
        * loss_network[eut];

# Resources
subject to resource_availability {i in RESOURCES}:
    sum {n in NODES, t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (s[i,n,h,td] * t_op[h,td]) <= avail[i];

subject to resource_constant_import {i in RES_IMPORT_CONSTANT, h in HOURS, td in TYPICAL_DAYS}:
	sum {n in NODES} s[i,n,h,td] * t_op[h,td] = Import_constant[i];

# Technologies
subject to size_limit {j in TECHNOLOGIES}:
	f_min[j] <= F[j] <= f_max[j];

# Processors
subject to process_capacity_factor_t {pt in PROCESSOR_TYPES, h in HOURS, td in TYPICAL_DAYS}:
    sum {n in NODES} e[pt,n,h,td] <= F[pt] * c_p_t[pt,h,td];

subject to process_capacity_factor {pt in PROCESSOR_TYPES}:
    sum {n in NODES, t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (e[pt,n,h,td] * t_op[h,td]) <= F[pt] * c_p[pt] * total_time;

subject to f_min_perc {eut in END_USES_TYPES, j in TECHNOLOGIES_OF_END_USES_TYPE[eut]}:
	sum {n in NODES, t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (e[j,n,h,td]  * t_op[h,td]) >= fmin_perc[j] * sum {j2 in TECHNOLOGIES_OF_END_USES_TYPE[eut], n in NODES, t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (e[j2,n,h,td] *  t_op[h,td]);
subject to f_max_perc {eut in END_USES_TYPES, j in TECHNOLOGIES_OF_END_USES_TYPE[eut]}:
	sum {n in NODES, t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (e[j,n,h,td]  * t_op[h,td]) <= fmax_perc[j] * sum {j2 in TECHNOLOGIES_OF_END_USES_TYPE[eut], n in NODES, t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (e[j2,n,h,td] * t_op[h,td]);

subject to solar_area_limited:
	F["PV"] / power_density_pv + (F["DEC_SOLAR"] + F["DHN_SOLAR"]) / power_density_solar_thermal <= solar_area;
	
subject to thermal_solar_total_capacity:
	F["DEC_SOLAR"] = sum {j in TECHNOLOGIES_OF_END_USES_TYPE["HEAT_LOW_T_DECEN"] diff {"DEC_SOLAR"}} F_solar[j];

subject to thermal_solar_capacity_factor {j in TECHNOLOGIES_OF_END_USES_TYPE["HEAT_LOW_T_DECEN"] diff {"DEC_SOLAR"}, h in HOURS, td in TYPICAL_DAYS}:
	F_t_solar[j,h,td] <= F_solar[j] * c_p_t["DEC_SOLAR",h,td];

subject to decentralised_heating_balance {j in TECHNOLOGIES_OF_END_USES_TYPE["HEAT_LOW_T_DECEN"] diff {"DEC_SOLAR"}, i in TS_OF_DEC_TECH[j], h in HOURS, td in TYPICAL_DAYS}:
	sum {n in NODES} e[j,n,h,td] + F_t_solar[j,h,td] + sum {p in PRODUCTS, n in NODES} (Storage_out[i,p,n,h,td] - Storage_in[i,p,n,h,td])  
		= Shares_lowT_dec[j] * (end_uses_input["HEAT_LOW_T_HW"] / total_time + end_uses_input["HEAT_LOW_T_SH"] * heating_time_series[h,td] / t_op[h,td]);

# Storage
subject to storage_level {j in STORAGE_TECH, n in NODES, t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]}:
	Storage_level[j,n,t] = (if t == 1 then
	 			Storage_level[j,n,card(PERIODS)] * (1.0 -  storage_losses[j])
				+ t_op[h,td] * (   (sum {p in PRODUCTS: storage_eff_in[j,p] > 0} (Storage_in[j,p,n,h,td] * storage_eff_in[j,p])) 
				                 - (sum {p in PRODUCTS: storage_eff_out[j,p] > 0} (Storage_out[j,p,n,h,td] / storage_eff_out[j,p])))
	else
	 			Storage_level[j,n,t-1] * (1.0 -  storage_losses[j])
				+ t_op[h,td] * (   (sum {p in PRODUCTS: storage_eff_in[j,p] > 0} (Storage_in[j,p,n,h,td] * storage_eff_in[j,p])) 
				                 - (sum {p in PRODUCTS: storage_eff_out[j,p] > 0} (Storage_out[j,p,n,h,td] / storage_eff_out[j,p])))
				);

subject to impose_daily_storage {j in STORAGE_DAILY, n in NODES, t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]}:
	Storage_level[j,n,t] = Storage_level_daily[j,n,h,td];

subject to daily_storage_capacity {j in STORAGE_DAILY, n in NODES, h in HOURS, td in TYPICAL_DAYS}:
    Storage_level_daily[j,n,h,td] <= F[j];

subject to limit_energy_stored_to_maximum {j in STORAGE_TECH diff STORAGE_DAILY, n in NODES, t in PERIODS}:
	Storage_level[j,n,t] <= F[j];

subject to storage_layer_in {j in STORAGE_TECH, p in PRODUCTS, n in NODES, h in HOURS, td in TYPICAL_DAYS}:
	Storage_in[j,p,n,h,td] * (ceil (storage_eff_in[j,p]) - 1) = 0;
subject to storage_layer_out {j in STORAGE_TECH, p in PRODUCTS, n in NODES, h in HOURS, td in TYPICAL_DAYS}:
	Storage_out[j,p,n,h,td] * (ceil (storage_eff_out[j,p]) - 1) = 0;

subject to limit_energy_to_power_ratio {j in STORAGE_TECH, p in PRODUCTS, n in NODES, h in HOURS, td in TYPICAL_DAYS}:
	Storage_in[j,p,n,h,td] * storage_charge_time[j] + Storage_out [j,p,n,h,td] * storage_discharge_time[j] <=  F[j] * storage_availability[j];

# Transporters -> Infrastructure
subject to extra_efficiency:
	F["EFFICIENCY"] = 1 / (1 + i_rate);

subject to extra_grid:
	F["GRID"] = 1 + (c_grid_extra / c_inv["GRID"]) * ((F["WIND_ONSHORE"] + F["WIND_OFFSHORE"] + F["PV"]) - (f_min["WIND_ONSHORE"] + f_min["WIND_OFFSHORE"] + f_min["PV"]));

subject to extra_dhn:
	F["DHN"] = sum {pt in PROCESSOR_TYPES: layers_in_out[pt,"HEAT_LOW_T_DHN"] > 0} (layers_in_out[pt,"HEAT_LOW_T_DHN"] * F[pt]);

# subject to transport_F {(tt,nf,nt,h,td) in TRANSPORTERS}:
#     f[tt,nf,nt,h,td] <= F[tt] * c_p_t[tt,h,td];

# subject to transport_F_yearly {tt in TRANSPORTER_TYPES}:
#     sum {nf in NODES, nt in NODES, t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (f[tt,nf,nt,h,td] * t_op[h,td]) <= F[tt] * c_p[tt] * total_time;

# Cost
subject to total_cost_cal:
	TotalCost = sum {j in TECHNOLOGIES} (tau[j]  * C_inv[j] + C_maint[j]) + sum {i in RESOURCES} C_op[i];

subject to investment_cost_calc {j in TECHNOLOGIES}: 
	C_inv[j] = c_inv[j] * F[j];

subject to maintenance_cost_calc {j in TECHNOLOGIES}: 
	C_maint[j] = c_maint[j] * F[j];

subject to operation_cost_calc {i in RESOURCES}:
	C_op[i] = sum {n in NODES, t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (c_op[i] * s[i,n,h,td] * t_op[h,td]);

# Emission
subject to totalGWP_calc:
	TotalGWP = sum {i in RESOURCES} GWP_op[i];
# just RESOURCES: TotalGWP = sum {i in RESOURCES} GWP_op[i];
# including GREY EMISSIONS: TotalGWP = sum {j in TECHNOLOGIES} (GWP_constr[j] / lifetime[j]) + sum {i in RESOURCES} GWP_op[i];
	 
subject to gwp_constr_calc {j in TECHNOLOGIES}:
	GWP_constr[j] = gwp_constr[j] * F[j];
 
subject to gwp_op_calc {i in RESOURCES}:
	GWP_op[i] = sum {n in NODES, t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (gwp_op[i] * s[i,n,h,td] * t_op[h,td]);

# subject to Minimum_GWP_reduction:
# 	TotalGWP <= gwp_limit;

subject to Minimum_GWP_constraint:
    TotalGWP <= (if use_epsilon = 1 then epsilon_value else 1e6);

# Balance
subject to balance {p in PRODUCTS, n in NODES, h in HOURS, td in TYPICAL_DAYS}:
    sum {ct in CONSUMER_TYPES: prod_ct[ct] = p} d[ct,n,h,td]
    + sum {pt in PROCESSOR_TYPES: layers_in_out[pt,p] < 0} (-layers_in_out[pt,p]) * e[pt,n,h,td]
    + sum {stot in STORAGE_TYPES} Storage_in[stot,p,n,h,td]
#   + sum {(tt,nf,nt,h,td) in TRANSPORTERS: nf = n and prod_f[tt,nf,nt,h,td] = p} f[tt,nf,nt,h,td]
  =
    sum {st in SUPPLIER_TYPES: prod_st[st]=p} s[st,n,h,td]
    + sum {pt in PROCESSOR_TYPES: layers_in_out[pt,p] > 0} layers_in_out[pt,p] * e[pt,n,h,td]
    + sum {stot in STORAGE_TYPES} Storage_out[stot,p,n,h,td];
#   + sum {(tt,nf,nt,h,td) in TRANSPORTERS: nt = n and prod_f[tt,nf,nt,h,td] = p} f[tt,nf,nt,h,td]

### Objective [M€/year] ###
maximize SocialWelfare:
    # (1 - fix_demand) * 
    sum {(ct,n,h,td) in CONSUMERS, k in SEGMENTS}
          (a[k,ct,n,h,td] * d_seg[ct,n,h,td,k] - 0.5 * b[k,ct,n,h,td] * (d_seg[ct,n,h,td,k]) ** 2) * mult[h,td] * t_op[h,td]
    - sum {(st,n,h,td) in SUPPLIERS}
          alpha_s[st,n,h,td] * s[st,n,h,td] * mult[h,td] * t_op[h,td]
    - sum {(pt,n,h,td) in PROCESSORS}
          alpha_e[pt,n,h,td] * e[pt,n,h,td] * mult[h,td] * t_op[h,td]
#   - sum {(tt,nf,nt,h,td) in TRANSPORTERS}
#         alpha_f[tt,nf,nt,h,td] * f[tt,nf,nt,h,td] * mult[h,td] * t_op[h,td]
    - sum {j in TECHNOLOGIES} (tau[j] * C_inv[j] + C_maint[j]);
    # - co2_price * TotalGWP;

# minimize TotalCostObjective:
#     TotalCost;

# minimize TotalEmissionObjective:
#     TotalGWP;
