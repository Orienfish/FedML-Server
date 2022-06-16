# Usage:
#   Run FedML gateway with $uuid
#     bash ./run_client.sh $uuid
# The script will run continuously run clients, with one minute interval between two trials

while true
do
  python3 app_CNN_gateway.py --server_ip http://132.239.17.132:5000 --client_uuid $1 2>&1 | tee output_gw_$1.log
  sleep 60s
done
