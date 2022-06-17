# Usage:
#   Run FedML Server experiments
#     bash ./run_exp.sh

#bash ./run_server.sh mnist fedasync noniid tier "$1" | tee fedasync_noniid.log;

#bash ./run_server.sh mnist fedavg iid "$sel" 0 2>&1 | tee fedavg_iid.log;
#bash ./run_server.sh mnist fedasync iid "$sel" 0 2>&1 | tee fedasync_iid.log;
bash ./run_server.sh mnist fedasync noniid coreset gurobi 0 2>&1 | tee fedasync_noniid_coreset_gurobi.log;
bash ./run_server.sh mnist fedavg noniid random random 0 2>&1 | tee fedavg_noniid_random_random.log;
bash ./run_server.sh mnist fedasync noniid high_loss_first random 0 2>&1 | tee fedavg_noniid_divfl_random.log;
bash ./run_server.sh mnist fedavg noniid tier random 0 2>&1 | tee fedavg_noniid_tier_random.log;
bash ./run_server.sh mnist fedavg noniid divfl random 0 2>&1 | tee fedavg_noniid_divfl_random.log;