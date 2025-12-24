from amplpy import AMPL
import json
import os
import pandas as pd
import sys
import time

ampl = AMPL()
ampl.read("CaseStudy_Math.mod")
ampl.read_data("CaseStudy_Math.dat")
ampl.read_data("CaseStudyPeriods.dat")
ampl.read_data("CaseStudyTimeSeries.dat")

ampl.set_option("solver", "gurobi")
ampl.set_option("solver_msg", 1)
ampl.set_option("gurobi_options", "outlev=1")
ampl.eval("objective SocialWelfare;")
start = time.time()
ampl.solve()
end = time.time()
solve_time = end - start
print(f"Solve time: {solve_time:.3f} seconds")

print("Capacity:")
ampl.display("F")
# print("\Consumer:")
# ampl.display("d")
# print("\Supplier:")
# ampl.display("s")
# print("\nProcessor:")
# ampl.display("e")
# print("\nTransport:")
# ampl.display("f")
# print("\nDemand difference:")
# ampl.display("d_diff")
print("Total Costs:", ampl.getVariable("TotalCost").value())
print("Total Emissions:", ampl.getVariable("TotalGWP").value())
print("Social Welfare:", ampl.get_objective("SocialWelfare").value())

# if len(sys.argv) > 1:
#     data_dir = sys.argv[1]
# else:
#     script_dir = os.path.dirname(os.path.abspath(__file__))
#     data_dir = os.path.join(script_dir, "Data")
# os.makedirs(data_dir, exist_ok=True)

# end_uses_df = ampl.get_set("END_USES_TYPES").get_values().to_pandas()
# if end_uses_df.empty and len(end_uses_df.index) > 0:
#     end_uses_df = pd.DataFrame(end_uses_df.index, columns=["END_USES_TYPES"])
# else:
#     end_uses_df.columns = ["END_USES_TYPES"]
# end_uses_df.to_csv(os.path.join(data_dir, "end_uses_types.csv"), index=False)

# dual_vals = ampl.get_constraint("balance").get_values().to_pandas().reset_index()
# dual_vals.rename(columns={"index0": "p", "index1": "n", "index2": "h", "index3": "td", "balance.dual": "dual_raw"}, inplace=True)
# mult = ampl.get_parameter("mult").get_values().to_pandas().reset_index()
# mult.rename(columns={"index0": "h", "index1": "td", "mult.val": "mult"}, inplace=True)
# t_op = ampl.get_parameter("t_op").get_values().to_pandas().reset_index()
# t_op.rename(columns={"index0": "h", "index1": "td", "t_op.val": "t_op"}, inplace=True)
# price = dual_vals.merge(mult, on=["h", "td"]).merge(t_op, on=["h", "td"])
# price["price_M€_per_GWh"] = price["dual_raw"] / (price["mult"] * price["t_op"])
# price["price_€_per_MWh"] = price["price_M€_per_GWh"] * 1e3

# dual_vals.to_csv(os.path.join(data_dir, "dual_vals.csv"), index=False)
# mult.to_csv(os.path.join(data_dir, "mult.csv"), index=False)
# t_op.to_csv(os.path.join(data_dir, "t_op.csv"), index=False)
# price.to_csv(os.path.join(data_dir, "price.csv"), index=False)

# tech_map_df = []
# tech_of_eut_set = ampl.get_set("TECHNOLOGIES_OF_END_USES_TYPE")

# for eut in ampl.get_set("END_USES_TYPES").get_values().to_list():
#     techs = tech_of_eut_set.get(eut).to_list()
#     for tech in techs:
#         tech_map_df.append({"END_USE_TYPE": eut, "TECHNOLOGY": tech})

# pd.DataFrame(tech_map_df).to_csv(os.path.join(data_dir, "tech_of_end_use.csv"), index=False)

# def get_ampl_var(name, rename_map):
#     df = ampl.get_variable(name).get_values().to_pandas().reset_index()
#     df.rename(columns=rename_map, inplace=True)
#     return df

# def get_ampl_param(name, rename_map):
#     df = ampl.get_parameter(name).get_values().to_pandas().reset_index()
#     df.rename(columns=rename_map, inplace=True)
#     return df

# s_vals = get_ampl_var("s", {"index0": "st", "index1": "n", "index2": "h", "index3": "td", "s.val": "val"})
# d_vals = get_ampl_var("d", {"index0": "ct", "index1": "n", "index2": "h", "index3": "td", "d.val": "val"})
# e_vals = get_ampl_var("e", {"index0": "pt", "index1": "n", "index2": "h", "index3": "td", "e.val": "val"})
# d_diff_vals = get_ampl_var("d_diff", {"index0": "ct", "index1": "n", "index2": "h", "index3": "td", "d_diff.val": "val"})
# d_ref_df = get_ampl_param("d_ref", {"index0": "ct", "index1": "n", "index2": "h", "index3": "td", "d_ref.val": "d_ref"})
# F_vals = get_ampl_var("F", {"index0": "TECHNOLOGY", "F.val": "capacity"})

# s_vals.to_csv(os.path.join(data_dir, "s_vals.csv"), index=False)
# d_vals.to_csv(os.path.join(data_dir, "d_vals.csv"), index=False)
# e_vals.to_csv(os.path.join(data_dir, "e_vals.csv"), index=False)
# d_diff_vals.to_csv(os.path.join(data_dir, "d_diff_vals.csv"), index=False)
# d_ref_df.to_csv(os.path.join(data_dir, "d_ref.csv"), index=False)
# F_vals.to_csv(os.path.join(data_dir, "F_capacities.csv"), index=False)

# def rename_param_cols(df, value_name):
#     cols = list(df.columns)
#     rename_map = {}
#     if "index4" in cols:
#         rename_map.update({
#             "index0": "k",
#             "index1": "ct",
#             "index2": "n",
#             "index3": "h",
#             "index4": "td",
#         })
#     else:
#         rename_map.update({
#             "index0": "ct",
#             "index1": "n",
#             "index2": "h",
#             "index3": "td",
#         })
#     rename_map[value_name] = value_name
#     df.rename(columns=rename_map, inplace=True)
#     return df

# a_vals = ampl.get_parameter("a").get_values().to_pandas().reset_index()
# b_vals = ampl.get_parameter("b").get_values().to_pandas().reset_index()
# D_vals = ampl.get_parameter("D").get_values().to_pandas().reset_index()
# d_ref_vals = ampl.get_parameter("d_ref").get_values().to_pandas().reset_index()
# p_ref_vals = ampl.get_parameter("p_ref").get_values().to_pandas().reset_index()
# p_pw_vals = ampl.get_parameter("p_pw").get_values().to_pandas().reset_index()

# a_vals = rename_param_cols(a_vals, "a.val")
# b_vals = rename_param_cols(b_vals, "b.val")
# D_vals = rename_param_cols(D_vals, "D.val")
# d_ref_vals = rename_param_cols(d_ref_vals, "d_ref.val")
# p_ref_vals = rename_param_cols(p_ref_vals, "p_ref.val")
# p_pw_vals = rename_param_cols(p_pw_vals, "p_pw.val")

# a_vals.to_csv(os.path.join(data_dir, "a.csv"), index=False)
# b_vals.to_csv(os.path.join(data_dir, "b.csv"), index=False)
# D_vals.to_csv(os.path.join(data_dir, "D.csv"), index=False)
# d_ref_vals.to_csv(os.path.join(data_dir, "d_ref.csv"), index=False)
# p_ref_vals.to_csv(os.path.join(data_dir, "p_ref.csv"), index=False)
# p_pw_vals.to_csv(os.path.join(data_dir, "p_pw.csv"), index=False)

# storage_level_seasonal = get_ampl_var("Storage_level", {"index0":"j","index1":"n","index2":"t","Storage_level.val":"val"})
# storage_level_seasonal.to_csv(os.path.join(data_dir,"storage_level_seasonal.csv"),index=False)

# storage_level_daily = get_ampl_var("Storage_level_daily", {"index0":"j","index1":"n","index2":"h","index3":"td","Storage_level_daily.val":"val"})
# storage_level_daily.to_csv(os.path.join(data_dir,"storage_level_daily.csv"),index=False)

# THTD = ampl.get_set("T_H_TD").get_values()
# df_raw = THTD.to_pandas()
# t_h_td_df = pd.DataFrame(df_raw.index.tolist(), columns=["t","h","td"])
# t_h_td_df.to_csv(os.path.join(data_dir,"t_h_td_mapping.csv"),index=False)

# def export_set_to_csv(set_name, filename, colname):
#     s = ampl.get_set(set_name)
#     df = s.get_values().to_pandas()
#     df = pd.DataFrame(df.index, columns=[colname]) if df.empty and len(df.index)>0 else df.rename(columns={df.columns[0]:colname})
#     df.to_csv(os.path.join(data_dir,filename),index=False)

# export_set_to_csv("STORAGE_TECH","storage_tech.csv","STORAGE_TECH")
# export_set_to_csv("STORAGE_DAILY","storage_daily.csv","STORAGE_DAILY")

# storage_map_list = []
# storage_of_eut_set = ampl.get_set("STORAGE_OF_END_USES_TYPES")
# end_use_types = ampl.get_set("END_USES_TYPES").get_values().to_list()

# for eut in end_use_types:
#     try: techs = storage_of_eut_set.get(eut).to_list()
#     except: techs = []
#     for tech in techs: storage_map_list.append({"END_USE_TYPE":eut,"STORAGE_TECH":tech})

# pd.DataFrame(storage_map_list).to_csv(os.path.join(data_dir,"storage_of_end_use.csv"),index=False)

# storage_out = ampl.get_variable("Storage_out").get_values().to_pandas().reset_index()
# storage_out.rename(columns={"index0":"j","index1":"p","index2":"n","index3":"h","index4":"td","Storage_out.val":"val"}, inplace=True)

# storage_out_agg = storage_out.groupby(["j","h","td"])["val"].sum().reset_index()
# storage_out_agg.to_csv(os.path.join(data_dir, "storage_discharge.csv"), index=False)

# storage_in = ampl.get_variable("Storage_in").get_values().to_pandas().reset_index()
# storage_in.rename(columns={"index0":"j","index1":"p","index2":"n","index3":"h","index4":"td","Storage_in.val":"val"}, inplace=True)

# storage_in_agg = storage_in.groupby(["j","h","td"])["val"].sum().reset_index()
# storage_in_agg.to_csv(os.path.join(data_dir, "storage_charge.csv"), index=False)

# layers = ampl.get_parameter("layers_in_out").get_values().to_pandas().reset_index()
# layers.rename(columns={"index0": "pt","index1": "p","layers_in_out.val": "layers_in_out"}, inplace=True)
# layers.to_csv(os.path.join(data_dir, "layers_in_out.csv"), index=False)

# results = {
#     "TotalCost": ampl.getVariable("TotalCost").value(),
#     "TotalGWP": ampl.getVariable("TotalGWP").value(),
#     "SocialWelfare": ampl.get_objective("SocialWelfare").value(),
#     "use_epsilon": ampl.get_parameter("use_epsilon").value(),
#     "epsilon_value": ampl.get_parameter("epsilon_value").value(),
#     "solve_time": solve_time
# }

# outname = os.path.join(data_dir, "last_run.json")
# with open(outname, "w") as f:
#     json.dump(results, f, indent=4)
