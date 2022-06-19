# Usage:
#   Run FedML Server experiments
#     bash ./run_exp.sh dataset

bash ./run_server.sh "$1" fedasync noniid high_loss_first random 0 2>&1 | tee "$1"_fedasync_noniid_high_loss_first_random.log;
bash ./run_server.sh "$1" fedasync noniid coreset gurobi 0 2>&1 | tee "$1"_fedasync_noniid_coreset_gurobi.log;
bash ./run_server.sh "$1" fedavg noniid random random 0 2>&1 | tee "$1"_fedavg_noniid_random_random.log;
bash ./run_server.sh "$1" fedavg noniid tier random 0 2>&1 | tee "$1"_fedavg_noniid_tier_random.log;
bash ./run_server.sh "$1" fedavg noniid divfl random 0 2>&1 | tee "$1"_fedavg_noniid_divfl_random.log;