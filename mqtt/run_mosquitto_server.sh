if [ "$1" = "local" ] ; then
  mosquitto -c ./mosquitto_local.conf -v 2>&1 | tee output.log
else
  mosquitto -c ./mosquitto.conf -v 2>&1 | tee output.log
fi
