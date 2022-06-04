if [ "$1" = "local" ] ; then
  mosquitto -c ./mosquitto_local.conf -v
else
  mosquitto -c ./mosquitto.conf -v
fi
