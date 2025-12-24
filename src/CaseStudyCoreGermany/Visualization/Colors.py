colors_end_use_type = {
    "ELECTRICITY": "#1f77b4",
    "HEAT_HIGH_T": "#9467bd",
    "HEAT_LOW_T_DHN": "#d62728",
    "HEAT_LOW_T_DECEN": "#ff7f0e"
}

colors_nonren = {
    "ELECTRICITY": "#1f77b4",
    "LFO": "#d62728",
    "GAS": "#ff7f0e",
    "WOOD": "#8c564b",
    "WET_BIOMASS": "#98df8a",
    "COAL": "#000000",
    "URANIUM": "#e377c2",
    "WASTE": "#7f7f7f",
    "H2": "#17becf",
    "AMMONIA": "#9467bd"
}

colors_ren = {
    "RES_WIND": "#2ca02c",
    "RES_SOLAR": "#ffdd57",
    "RES_HYDRO": "#1f77b4",
    "RES_GEO": "#d62728"
}


colors_proc_electricity = {
    "NUCLEAR": "#e377c2",
    "CCGT": "#ff7f0e",
    "CCGT_AMMONIA": "#9467bd",
    "COAL_US": "#000000",
    "COAL_IGCC": "#4d4d4d",
    "PV": "#ffdd57",
    "WIND_ONSHORE": "#2ca02c",
    "WIND_OFFSHORE": "#98df8a",
    "HYDRO_RIVER": "#1f77b4",
    "GEOTHERMAL": "#d62728"
}

colors_proc_heat_high_t = {
    "IND_COGEN_GAS":   "#ffa54c",
    "IND_COGEN_WOOD":  "#a97457",
    "IND_COGEN_WASTE": "#9e9e9e",
    "IND_BOILER_GAS":   "#ff7f0e",
    "IND_BOILER_WOOD":  "#8c564b",
    "IND_BOILER_OIL":   "#d62728",
    "IND_BOILER_COAL":  "#000000",
    "IND_BOILER_WASTE": "#7f7f7f",
    "IND_DIRECT_ELEC": "#1f77b4"
}

colors_proc_heat_low_t_dhn = {
    "DHN_HP_ELEC": "#1f77b4",
    "DHN_COGEN_GAS": "#ffa54c",
    "DHN_COGEN_WOOD": "#a97457",
    "DHN_COGEN_WASTE": "#9e9e9e",
    "DHN_COGEN_WET_BIOMASS": "#98df8a",
    "DHN_COGEN_BIO_HYDROLYSIS": "#17becf",
    "DHN_BOILER_GAS": "#ff7f0e",
    "DHN_BOILER_WOOD": "#8c564b",
    "DHN_BOILER_OIL": "#d62728",
    "DHN_DEEP_GEO": "#d62728",
    "DHN_SOLAR": "#ffdd57"
}

colors_proc_heat_low_t_decen = {
    "DEC_HP_ELEC":      "#1f77b4",
    "DEC_DIRECT_ELEC":  "#6baed6",
    "DEC_THHP_GAS":     "#ffa54c",
    "DEC_COGEN_GAS":    "#ffa54c",
    "DEC_COGEN_OIL":    "#d62728",
    "DEC_ADVCOGEN_GAS": "#ffa54c",
    "DEC_ADVCOGEN_H2":  "#17becf",
    "DEC_BOILER_GAS":   "#ff7f0e",
    "DEC_BOILER_WOOD":  "#8c564b",
    "DEC_BOILER_OIL":   "#d62728",
    "DEC_SOLAR":        "#ffdd57"
}

colors_proc = {
    "ELECTRICITY": colors_proc_electricity,
    "HEAT_HIGH_T": colors_proc_heat_high_t,
    "HEAT_LOW_T_DHN": colors_proc_heat_low_t_dhn,
    "HEAT_LOW_T_DECEN": colors_proc_heat_low_t_decen
}

colors_storage_electricity = {
    "PHS": "#1f77b4",
    "BATT_LI": "#2ca02c"
}

colors_storage_heat_high_t = {
    "TS_HIGH_TEMP": "#9467bd"
}

colors_storage_heat_low_t_dhn = {
    "TS_DHN_DAILY": "#ffdd57",
    "TS_DHN_SEASONAL": "#d62728"
}

colors_storage_heat_low_t_decen = {
    "TS_DEC_DIRECT_ELEC":  "#6baed6",
    "TS_DEC_HP_ELEC":      "#ff7f0e",
    "TS_DEC_THHP_GAS":     "#ffa54c",
    "TS_DEC_COGEN_GAS":    "#ffa54c",
    "TS_DEC_COGEN_OIL":    "#d62728",
    "TS_DEC_ADVCOGEN_GAS": "#ffa54c",
    "TS_DEC_ADVCOGEN_H2":  "#17becf",
    "TS_DEC_BOILER_GAS":   "#ff7f0e",
    "TS_DEC_BOILER_WOOD":  "#8c564b",
    "TS_DEC_BOILER_OIL":   "#d62728"
}

colors_storage = {
    "ELECTRICITY": colors_storage_electricity,
    "HEAT_HIGH_T": colors_storage_heat_high_t,
    "HEAT_LOW_T_DHN": colors_storage_heat_low_t_dhn,
    "HEAT_LOW_T_DECEN": colors_storage_heat_low_t_decen
}

colors_elasticity = {
    "demand_fixed": "#000000",
    "elast_2_5pct": "#d62728",
    "elast_5pct":   "#1f77b4",
    "elast_10pct":  "#2ca02c",
}