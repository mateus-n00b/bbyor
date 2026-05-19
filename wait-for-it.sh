#!/bin/sh
HOST_IP=$1
PORTA=$2

if [ -z "$HOST_IP" ] || [ -z "$PORTA" ]; then
  echo "Uso: $0 <HOST_IP> <PORTA>"
  exit 1
fi

for i in $(seq 1 100)
do
	curl -X POST -d {} http://$HOST_IP:$PORTA/topic/connections > /dev/null 2>/dev/null && break
	sleep 3 
	i=1
done
