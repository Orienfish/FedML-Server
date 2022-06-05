# Usage:
#   Run FedML Server
#     bash ./run_server.sh mnist fedavg noniid 0
#   Dataset choices: mnist, fashionmnist, cifar10, Shakespeare, Synthetic, HAR, HPWREN
#   Server choices: fedavg, fedasync
#   Data distribution choices: iid, noniid
#     (Note: the Shakespeare, HAR and HPWREN datasets are naturally noniid,
#     so only noniid selection is available)
#   Last param: trial number

MQTT_HOST=132.239.17.132
MQTT_PORT=61613
TOTAL_CLIENTS=10
CLIENTS_PER_ROUND=10

# Set proper global rounds
if [ "$2" = "fedavg" ] ; then
  rounds=30
elif [ "$2" = "fedasync" ] ; then
  rounds=1000
fi

# iid
if [ "$3" = "iid" ] ; then
  python3 app_CNN.py --method "$2" --dataset "$1" --partition_method iid --lr 0.01 --momentum 0.9 \
    --data_size_per_client 600 --client_num_in_total "$TOTAL_CLIENTS" --client_num_per_round "$CLIENTS_PER_ROUND" \
    --comm_round "$rounds" --epochs 5 \
    --backend MQTT --mqtt_host "$MQTT_HOST" --mqtt_port "$MQTT_PORT" --server_ip "$MQTT_HOST" --trial "$4"
fi

# non-iid, all labels from one class on one client
#if [ "$3" = "noniid" ] ; then
#  python3 app_CNN.py --method "$2" --dataset "$1" --partition_method noniid --partition_label uniform \
#    --partition_alpha 1.0 --partition_secondary --data_size_per_client 600 --lr 0.01 --momentum 0.9 \
#    --client_num_in_total "$TOTAL_CLIENTS" --client_num_per_round "$CLIENTS_PER_ROUND" \
#    --comm_round "$rounds" --epochs 5 \
#    --backend MQTT --mqtt_host "$MQTT_HOST" --mqtt_port "$MQTT_PORT" --server_ip "$MQTT_HOST" --trial "$4"
#fi

# non-iid, all labels from one major class and equally from the rest classes
if [ "$3" = "noniid" ] ; then
  python3 app_CNN.py --method "$2" --dataset "$1" --partition_method noniid --partition_label uniform \
    --partition_alpha 0.5 --data_size_per_client 600 --lr 0.01 --momentum 0.9 \
    --client_num_in_total "$TOTAL_CLIENTS" --client_num_per_round "$CLIENTS_PER_ROUND" \
    --comm_round "$rounds" --epochs 5 \
    --backend MQTT --mqtt_host "$MQTT_HOST" --mqtt_port "$MQTT_PORT" --server_ip "$MQTT_HOST" --trial "$4"
fi