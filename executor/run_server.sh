# Usage:
#   Run FedML Server
#     bash ./run_server.sh mnist fedavg noniid random 0
#   Dataset choices: mnist, fashionmnist, cifar10, Shakespeare, Synthetic, HAR, HPWREN
#   Server choices: fedavg, fedasync
#   Data distribution choices: iid, noniid
#     (Note: the Shakespeare, HAR and HPWREN datasets are naturally noniid,
#     so only noniid selection is available)
#   Client selection choices: random, high_loss_first, short_latency_first,
#     short_latency_high_loss_first, divfl, coreset, tier
#   Last param: trial number

MQTT_HOST=132.239.17.132
MQTT_PORT=61613
TOTAL_CLIENTS=10
CLIENTS_PER_ROUND=5

# Set proper global rounds
if [ "$1" = "mnist" ] ; then
  target_acc=0.9
elif [ "$1" = "fashionmnist" ] ; then
  target_acc=0.8
fi

# iid
if [ "$3" = "iid" ] ; then
  python3 app_CNN.py --method "$2" --dataset "$1" --partition_method iid --lr 0.01 --momentum 0.9 \
    --data_size_per_client 600 --client_num_in_total "$TOTAL_CLIENTS" --client_num_per_round "$CLIENTS_PER_ROUND" \
    --target_accuracy "$target_acc" --epochs 5 --selection "$4" \
    --backend MQTT --mqtt_host "$MQTT_HOST" --mqtt_port "$MQTT_PORT" --server_ip "$MQTT_HOST" --trial "$5"
fi

# non-iid, all labels equally from a random number of classes between 1 and 5
if [ "$3" = "noniid" ] ; then
  python3 app_CNN.py --method "$2" --dataset "$1" --partition_method noniid --partition_label uniform \
    --partition_min_cls 1 --partition_max_cls 5 --data_size_per_client 600 --lr 0.01 --momentum 0.9 \
    --client_num_in_total "$TOTAL_CLIENTS" --client_num_per_round "$CLIENTS_PER_ROUND" \
    --target_accuracy "$target_acc" --epochs 5 --selection "$4" \
    --backend MQTT --mqtt_host "$MQTT_HOST" --mqtt_port "$MQTT_PORT" --server_ip "$MQTT_HOST" --trial "$5"
fi