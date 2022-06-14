# Usage:
#   Run FedML Server experiments
#     bash ./run_exp.sh

#bash ./run_server.sh mnist fedasync noniid tier "$1" | tee fedasync_noniid.log;
for sel in coreset
do
  #bash ./run_server.sh mnist fedavg iid "$sel" 0 2>&1 | tee fedavg_iid.log;
  #bash ./run_server.sh mnist fedasync iid "$sel" 0 2>&1 | tee fedasync_iid.log;
  bash ./run_server.sh mnist fedasync noniid "$sel" 0 2>&1 | tee fedasync_noniid_"$sel".log;
  bash ./run_server.sh mnist fedavg noniid "$sel" 0 2>&1 | tee fedavg_noniid_"$sel".log;
done
