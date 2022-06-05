bash ./run_server.sh mnist fedavg iid | tee log_fedavg_iid;
bash ./run_server.sh mnist fedasync iid | tee log_fedasync_iid;
#bash ./run_server.sh mnist fedavg noniid 1 | tee log_fedavg_noniid;
#bash ./run_server.sh mnist fedasync noniid 1 | tee log_fedasync_noniid;
