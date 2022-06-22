# Usage:
#   Run FedML Server
#     bash ./run_server.sh mnist fedavg noniid coreset gurobi 0
#   Dataset choices: mnist, fashionmnist, cifar10, Shakespeare, Synthetic, HAR, HPWREN
#   Server choices: fedavg, fedasync
#   Data distribution choices: iid, noniid
#     (Note: the Shakespeare, HAR and HPWREN datasets are naturally noniid,
#     so only noniid selection is available)
#   Client selection choices: random, high_loss_first, short_latency_first,
#     short_latency_high_loss_first, divfl, coreset, tier
#   Client association choices: random gurobi
#   Last param: trial number

MQTT_HOST=132.239.17.132
MQTT_PORT=61613
TOTAL_CLIENTS=40
TOTAL_GATEWAYS=3
CLIENTS_PER_GATEWAY=7

# Set proper global parameters for various dataset
if [ "$1" = "mnist" ] ; then
  target_acc=0.8
  rou=1.0
  batch_size=64
elif [ "$1" = "fashionmnist" ] ; then
  target_acc=0.6
  rou=1.0
  batch_size=64
elif [ "$1" = "shakespeare" ] ; then
  target_acc=0.35
  rou=1.0
  batch_size=20
elif [ "$1" = "har" ] ; then
  target_acc=0.9
  rou=0.1
  batch_size=10
elif [ "$1" = "hpwren" ] ; then
  target_acc=100  # Not used because HPWREN uses test loss not accuracy
  rou=0.1
  batch_size=10
fi

# Set proper global parameters for various algorithm
if [ "$2" = "fedavg" ] ; then
  comm_round=3
  gateway_comm_round=2
  adjust_round=1
elif [ "$2" = "fedasync" ] ; then
  comm_round=20
  gateway_comm_round=5
  adjust_round=2
fi

# iid
if [ "$3" = "iid" ] ; then
  python3 app_CNN_server.py --method "$2" --dataset "$1" --partition_method iid --lr 0.01 --momentum 0.9 \
    --data_size_per_client 600 --client_num_in_total "$TOTAL_CLIENTS" --client_num_per_gateway "$CLIENTS_PER_GATEWAY" \
    --target_accuracy "$target_acc" --epochs 5 --selection "$4" --association "$5" \
    --backend MQTT --mqtt_host "$MQTT_HOST" --mqtt_port "$MQTT_PORT" --server_ip "$MQTT_HOST" \
    --gateway_num_in_total "$TOTAL_GATEWAYS" --gateway_comm_round "$gateway_comm_round" \
    --comm_round "$comm_round" --adjust_round "$adjust_round" \
    --batch_size="$batch_size" --rou="$rou" \
    --trial "$6"
fi

# non-iid, all labels equally from a random number of classes between 1 and 5
if [ "$3" = "noniid" ] ; then
  python3 app_CNN_server.py --method "$2" --dataset "$1" --partition_method bias \
    --partition_label normal --partition_alpha 0.8 --partition_secondary \
    --data_size_per_client 600 --lr 0.01 --momentum 0.9 \
    --client_num_in_total "$TOTAL_CLIENTS" --client_num_per_gateway "$CLIENTS_PER_GATEWAY" \
    --target_accuracy "$target_acc" --epochs 5 --selection "$4" --association "$5" \
    --backend MQTT --mqtt_host "$MQTT_HOST" --mqtt_port "$MQTT_PORT" --server_ip "$MQTT_HOST" \
    --gateway_num_in_total "$TOTAL_GATEWAYS" --gateway_comm_round "$gateway_comm_round" \
    --comm_round "$comm_round" --adjust_round "$adjust_round" \
    --batch_size="$batch_size" --rou="$rou" \
    --trial "$6"
fi

#--partition_label uniform --partition_min_cls 1 --partition_max_cls 5 \