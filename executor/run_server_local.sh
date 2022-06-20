python3 app_CNN_server.py --method fedasync --dataset hpwren --partition_method noniid \
--client_num_in_total 1 --client_num_per_gateway 1 --gateway_num 1 \
--target_accuracy 0.8 --backend MQTT --mqtt_host 127.0.0.1 --mqtt_port 61614 \
--server_ip 127.0.0.1 --trial 0
