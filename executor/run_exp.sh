# Usage:
#   Run FedML Server experiments
#     bash ./run_exp.sh 0
#   Last param: trial number

#bash ./run_server.sh mnist fedavg iid "$1" 2>&1 | tee fedavg_iid.log;
bash ./run_server.sh mnist fedasync iid "$1" 2>&1 | tee fedasync_iid.log;
#bash ./run_server.sh mnist fedavg noniid "$1" | tee fedavg_noniid.log;
#bash ./run_server.sh mnist fedasync noniid "$1" | tee fedasync_noniid.log;
