### Sets ###
# Space
set NODES;

# Time
set PERIODS := 1 .. 8760;
set HOURS := 1..24;
set TYPICAL_DAYS:= 1 .. 12;
set T_H_TD within {PERIODS, HOURS, TYPICAL_DAYS};
set HOUR_OF_PERIOD {t in PERIODS} := setof {h in HOURS, td in TYPICAL_DAYS: (t,h,td) in T_H_TD} h;
set TYPICAL_DAY_OF_PERIOD {t in PERIODS} := setof {h in HOURS, td in TYPICAL_DAYS: (t,h,td) in T_H_TD} td;

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

# Stakeholders -> interface between EnergyScope and multi-product supply chain framework
set CONSUMERS := END_USES_TYPES;
set SUPPLIERS := RESOURCES;
set PROCESSORS := TECHNOLOGIES diff STORAGE_TECH diff INFRASTRUCTURE;
set STORAGES := STORAGE_TECH;
# set TRANSPORTERS := INFRASTRUCTURE;

# Products -> layers
set LAYERS := RESOURCES union END_USES_TYPES;

### Parameters ###
# Time
param w {h in HOURS, td in TYPICAL_DAYS} := card {t in PERIODS: (t,h,td) in T_H_TD}; # [1/year], yearly weight of each hour and typical day pair
param t_op {HOURS, TYPICAL_DAYS} default 1; # [h]
param total_time := sum {t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (t_op[h,td]); # [h/year]
param i_rate > 0; # []

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

# Layers
param layers_in_out {SUPPLIERS union PROCESSORS, LAYERS}; # []

# Consumers
param Share_heat_dhn; # [], parametrized var Share_heat_dhn, >= share_heat_dhn_min, <= share_heat_dhn_max;
param End_uses {l in LAYERS, h in HOURS, td in TYPICAL_DAYS} :=
    if l = "ELECTRICITY" then
        end_uses_input["LIGHTING"] / total_time + end_uses_input["ELECTRICITY"] * electricity_time_series[h,td] / t_op[h,td] # switched ELECTRICITY and LIGHTING wrt EnergyScope core version
    else if l = "HEAT_LOW_T_DHN" then
        (end_uses_input["HEAT_LOW_T_HW"] / total_time + end_uses_input["HEAT_LOW_T_SH"] * heating_time_series[h,td] / t_op[h,td]) * Share_heat_dhn # + Network_losses[p,h,td]
    else if l = "HEAT_LOW_T_DECEN" then
        (end_uses_input["HEAT_LOW_T_HW"] / total_time + end_uses_input["HEAT_LOW_T_SH"] * heating_time_series[h,td] / t_op[h,td]) * (1 - Share_heat_dhn)
    else if l = "HEAT_HIGH_T" then
        end_uses_input["HEAT_HIGH_T"] / total_time
    else
        0;  # [GW], parametrized var End_uses {LAYERS, HOURS, TYPICAL_DAYS} >= 0;
param VOLL; # [M€/GWh], value-of-lost-load
param elasticity; # [], price elasticity of demand
param beta {CONSUMERS, NODES, HOURS, TYPICAL_DAYS} := (-1/elasticity); # [], log-log demand curve exponent
param d_ref {c in CONSUMERS, NODES, h in HOURS, td in TYPICAL_DAYS} := End_uses[c,h,td]; # [GW], reference demand
param alpha_d {CONSUMERS} >= 0; # [M€/GWh=€/kWh], consumer bid value
param p_ref {c in CONSUMERS, n in NODES, h in HOURS, td in TYPICAL_DAYS} := alpha_d[c]; # [M€/GWh=€/kWh], reference price
param A {c in CONSUMERS, n in NODES, h in HOURS, td in TYPICAL_DAYS} := p_ref[c,n,h,td] / (d_ref[c,n,h,td]^beta[c,n,h,td]); # log-log demand curve parameter
param fix_demand default 0; # [], flag to enforce fixed demand if set to 1

# PWL
param K = 5; # [], number of segments
set SEGMENTS := 1..K; # segments
set BREAKPOINTS := 0..K; # breakpoints
param d_mult {b in BREAKPOINTS} := # [], demand multipliers at breakpoints
    if b = 0 then 0
    else 0.95 + (b - 1) * (1.1 - 0.95) / (K - 1);
param d_pwl {b in BREAKPOINTS, c in CONSUMERS, n in NODES, h in HOURS, td in TYPICAL_DAYS} := # [GW], demand at breakpoints
    d_mult[b] * d_ref[c,n,h,td];
param p_pwl {b in BREAKPOINTS, c in CONSUMERS, n in NODES, h in HOURS, td in TYPICAL_DAYS} := # [M€/GWh=€/kWh], price at breakpoints
    if b = 0 then VOLL
    else if b = K then 0
    else A[c,n,h,td] * (d_pwl[b,c,n,h,td] ** beta[c,n,h,td]);
param D {k in SEGMENTS, c in CONSUMERS, n in NODES, h in HOURS, td in TYPICAL_DAYS} := # [GW], segment width
    d_pwl[k,c,n,h,td] - d_pwl[k-1,c,n,h,td];
param b {k in SEGMENTS, c in CONSUMERS, n in NODES, h in HOURS, td in TYPICAL_DAYS} >= 0 := # [M€/GWh^2=€/kWh^2], segment slope
    (p_pwl[k-1,c,n,h,td] - p_pwl[k,c,n,h,td]) / D[k,c,n,h,td];
param a {k in SEGMENTS, c in CONSUMERS, n in NODES, h in HOURS, td in TYPICAL_DAYS} := # [M€/GWh=€/kWh], segment intercept
    p_pwl[k-1,c,n,h,td];

# Resources
param avail {RESOURCES} >= 0; # [GWh/year]
param gwp_op {RESOURCES} >= 0; # [ktCO2-eq./GWh]
param c_op {RESOURCES} >= 0; # [M€/GWh=€/kWh]

# Technologies
param c_inv {TECHNOLOGIES} >= 0; # [M€/GW], storage [M€/GWh]
param c_maint {TECHNOLOGIES} >= 0; # [M€/GW/year], storage [M€/GWh/year]
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

# Storage
param storage_eff_in {STORAGE_TECH, LAYERS} >= 0, <= 1; # []
param storage_eff_out {STORAGE_TECH, LAYERS} >= 0, <= 1; # []
param storage_charge_time {STORAGE_TECH} >= 0; # [h]
param storage_discharge_time {STORAGE_TECH} >= 0; # [h]
param storage_availability {STORAGE_TECH} >= 0 default 1; # []
param storage_losses {STORAGE_TECH} >= 0, <= 1; # []

# Transporters -> Infrastructure
param c_grid_extra >= 0; # [M€/GW]

# Emissions
param use_epsilon; # [], flag to use epsilon constraint if set to 1
param epsilon_value; # [ktCO2-eq./year], maximum allowed GWP when using epsilon constraint

### Variables ###
# Independent
var d_seg {SEGMENTS, CONSUMERS, NODES, HOURS, TYPICAL_DAYS} >= 0; # [GW], demand in each segment
var d {CONSUMERS, NODES, HOURS, TYPICAL_DAYS} >= 0; # [GW], consumer flow variable
var Shares_lowT_dec {TECHNOLOGIES_OF_END_USES_TYPE["HEAT_LOW_T_DECEN"] diff {"DEC_SOLAR"}} >=0; # []
var g {SUPPLIERS, NODES, HOURS, TYPICAL_DAYS} >= 0; # [GW], supplier flow variable
var F {TECHNOLOGIES} >= 0; # [GW], storage [GWh]
var F_solar {TECHNOLOGIES_OF_END_USES_TYPE["HEAT_LOW_T_DECEN"] diff {"DEC_SOLAR"}} >=0; # []
var e {PROCESSORS, NODES, HOURS, TYPICAL_DAYS} >= 0; # [GW], processor flow variable
var F_t_solar {TECHNOLOGIES_OF_END_USES_TYPE["HEAT_LOW_T_DECEN"] diff {"DEC_SOLAR"}, HOURS, TYPICAL_DAYS} >= 0; # [GW]
var Storage_in {STORAGE_TECH, LAYERS, NODES, HOURS, TYPICAL_DAYS} >= 0; # [GW]
var Storage_out {STORAGE_TECH, LAYERS, NODES, HOURS, TYPICAL_DAYS} >= 0; # [GW]

# Dependent
var Storage_level {STORAGE_TECH, NODES, PERIODS} >= 0; # [GWh]
var Storage_level_daily {STORAGE_DAILY, NODES, HOURS, TYPICAL_DAYS} >= 0; # [GWh], daily storage level (replacement for F_t in core EnergyScope)
var d_diff {CONSUMERS, NODES, HOURS, TYPICAL_DAYS}; # [GW], difference between actual and reference demand
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
subject to satisfy_demand {c in CONSUMERS, n in NODES, h in HOURS, td in TYPICAL_DAYS}: # fixed demand if fix_demand = 1
    fix_demand * d[c,n,h,td] = fix_demand * d_ref[c,n,h,td];

subject to d_diff_def {c in CONSUMERS, n in NODES, h in HOURS, td in TYPICAL_DAYS}: # track demand difference
    d_diff[c,n,h,td] = d[c,n,h,td] - d_ref[c,n,h,td];

subject to seg_bounds {k in SEGMENTS, c in CONSUMERS, n in NODES, h in HOURS, td in TYPICAL_DAYS}: # segment upper bounds
    d_seg[k,c,n,h,td] <= D[k,c,n,h,td];

subject to demand_partition {c in CONSUMERS, n in NODES, h in HOURS, td in TYPICAL_DAYS}: # demand partitioning over segments
    sum{k in SEGMENTS} d_seg[k,c,n,h,td] = d[c,n,h,td];

subject to network_losses {eut in END_USES_TYPES, h in HOURS, td in TYPICAL_DAYS}:
    Network_losses[eut,h,td] =
        (sum {n in NODES, s in SUPPLIERS: layers_in_out[s,eut] > 0} (layers_in_out[s,eut] * g[s,n,h,td])
        + sum {n in NODES, p in PROCESSORS: layers_in_out[p,eut] > 0} (layers_in_out[p,eut] * e[p,n,h,td]))
        * loss_network[eut];

# Resources
subject to resource_availability {i in RESOURCES}:
    sum {n in NODES, t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (g[i,n,h,td] * t_op[h,td]) <= avail[i];

subject to resource_constant_import {i in RES_IMPORT_CONSTANT, h in HOURS, td in TYPICAL_DAYS}:
	sum {n in NODES} g[i,n,h,td] * t_op[h,td] = Import_constant[i];

# Technologies
subject to size_limit {j in TECHNOLOGIES}:
	f_min[j] <= F[j] <= f_max[j];

# Processors
subject to process_capacity_factor_t {p in PROCESSORS, h in HOURS, td in TYPICAL_DAYS}:
    sum {n in NODES} e[p,n,h,td] <= F[p] * c_p_t[p,h,td];

subject to process_capacity_factor {p in PROCESSORS}:
    sum {n in NODES, t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (e[p,n,h,td] * t_op[h,td]) <= F[p] * c_p[p] * total_time;

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
	sum {n in NODES} e[j,n,h,td] + F_t_solar[j,h,td] + sum {l in LAYERS, n in NODES} (Storage_out[i,l,n,h,td] - Storage_in[i,l,n,h,td])  
		= Shares_lowT_dec[j] * (end_uses_input["HEAT_LOW_T_HW"] / total_time + end_uses_input["HEAT_LOW_T_SH"] * heating_time_series[h,td] / t_op[h,td]);

# Storage
subject to storage_level {j in STORAGE_TECH, n in NODES, t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]}:
	Storage_level[j,n,t] = (if t == 1 then
	 			Storage_level[j,n,card(PERIODS)] * (1.0 -  storage_losses[j])
				+ t_op[h,td] * (   (sum {l in LAYERS: storage_eff_in[j,l] > 0} (Storage_in[j,l,n,h,td] * storage_eff_in[j,l])) 
				                 - (sum {l in LAYERS: storage_eff_out[j,l] > 0} (Storage_out[j,l,n,h,td] / storage_eff_out[j,l])))
	else
	 			Storage_level[j,n,t-1] * (1.0 -  storage_losses[j])
				+ t_op[h,td] * (   (sum {l in LAYERS: storage_eff_in[j,l] > 0} (Storage_in[j,l,n,h,td] * storage_eff_in[j,l])) 
				                 - (sum {l in LAYERS: storage_eff_out[j,l] > 0} (Storage_out[j,l,n,h,td] / storage_eff_out[j,l])))
				);

subject to impose_daily_storage {j in STORAGE_DAILY, n in NODES, t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]}: # daily storage level consistency (replacement for F_t in core EnergyScope)
	Storage_level[j,n,t] = Storage_level_daily[j,n,h,td];

subject to daily_storage_capacity {j in STORAGE_DAILY, n in NODES, h in HOURS, td in TYPICAL_DAYS}:
    Storage_level_daily[j,n,h,td] <= F[j];

subject to limit_energy_stored_to_maximum {j in STORAGE_TECH diff STORAGE_DAILY, n in NODES, t in PERIODS}:
	Storage_level[j,n,t] <= F[j];

subject to storage_layer_in {j in STORAGE_TECH, l in LAYERS, n in NODES, h in HOURS, td in TYPICAL_DAYS}:
	Storage_in[j,l,n,h,td] * (ceil (storage_eff_in[j,l]) - 1) = 0;
subject to storage_layer_out {j in STORAGE_TECH, l in LAYERS, n in NODES, h in HOURS, td in TYPICAL_DAYS}:
	Storage_out[j,l,n,h,td] * (ceil (storage_eff_out[j,l]) - 1) = 0;

subject to limit_energy_to_power_ratio {j in STORAGE_TECH, l in LAYERS, n in NODES, h in HOURS, td in TYPICAL_DAYS}:
	Storage_in[j,l,n,h,td] * storage_charge_time[j] + Storage_out [j,l,n,h,td] * storage_discharge_time[j] <=  F[j] * storage_availability[j];

# Transporters -> Infrastructure
subject to extra_efficiency:
	F["EFFICIENCY"] = 1 / (1 + i_rate);

subject to extra_grid:
	F["GRID"] = 1 + (c_grid_extra / c_inv["GRID"]) * ((F["WIND_ONSHORE"] + F["WIND_OFFSHORE"] + F["PV"]) - (f_min["WIND_ONSHORE"] + f_min["WIND_OFFSHORE"] + f_min["PV"]));

subject to extra_dhn:
	F["DHN"] = sum {p in PROCESSORS: layers_in_out[p,"HEAT_LOW_T_DHN"] > 0} (layers_in_out[p,"HEAT_LOW_T_DHN"] * F[p]);

# Cost
subject to total_cost_cal:
	TotalCost = sum {j in TECHNOLOGIES} (tau[j]  * C_inv[j] + C_maint[j]) + sum {i in RESOURCES} C_op[i];

subject to investment_cost_calc {j in TECHNOLOGIES}: 
	C_inv[j] = c_inv[j] * F[j];

subject to maintenance_cost_calc {j in TECHNOLOGIES}: 
	C_maint[j] = c_maint[j] * F[j];

subject to operation_cost_calc {i in RESOURCES}:
	C_op[i] = sum {n in NODES, t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (c_op[i] * g[i,n,h,td] * t_op[h,td]);

# Emission
subject to totalGWP_calc:
	TotalGWP = sum {i in RESOURCES} GWP_op[i];
# just RESOURCES: TotalGWP = sum {i in RESOURCES} GWP_op[i];
# including GREY EMISSIONS: TotalGWP = sum {j in TECHNOLOGIES} (GWP_constr[j] / lifetime[j]) + sum {i in RESOURCES} GWP_op[i];
	 
subject to gwp_constr_calc {j in TECHNOLOGIES}:
	GWP_constr[j] = gwp_constr[j] * F[j];
 
subject to gwp_op_calc {i in RESOURCES}:
	GWP_op[i] = sum {n in NODES, t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (gwp_op[i] * g[i,n,h,td] * t_op[h,td]);

subject to Minimum_GWP_constraint:
    TotalGWP <= (if use_epsilon = 1 then epsilon_value else 1e6);

# Balance
subject to balance {l in LAYERS, n in NODES, h in HOURS, td in TYPICAL_DAYS}:
    sum {c in CONSUMERS: c = l} d[c,n,h,td]
    + sum {p in PROCESSORS: layers_in_out[p,l] < 0} (-layers_in_out[p,l]) * e[p,n,h,td]
    + sum {sto in STORAGES} Storage_in[sto,l,n,h,td]
  =
    sum {s in SUPPLIERS} layers_in_out[s,l] * g[s,n,h,td]
    + sum {p in PROCESSORS: layers_in_out[p,l] > 0} layers_in_out[p,l] * e[p,n,h,td]
    + sum {sto in STORAGES} Storage_out[sto,l,n,h,td];

### Objective [M€/year] ###
maximize SocialWelfare:
    sum {n in NODES, h in HOURS, td in TYPICAL_DAYS}
        ((sum {c in CONSUMERS, k in SEGMENTS} (a[k,c,n,h,td] * d_seg[k,c,n,h,td] - 0.5 * b[k,c,n,h,td] * (d_seg[k,c,n,h,td])^2)
          - sum {s in SUPPLIERS} c_op[s] * g[s,n,h,td]) * w[h,td] * t_op[h,td])
  - sum {j in TECHNOLOGIES} (tau[j] * C_inv[j] + C_maint[j]);
