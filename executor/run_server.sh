python3 app_nn.py --dataset mnist --model nn --partition_method homo --lr 0.01 --momentum 0.9 \
  --client_num_in_total 5 --client_num_per_round 5 --comm_round 20 --epochs 5 \
  --backend MQTT --mqtt_host 10.0.137.51 --mqtt_port 61613 --trial 0
