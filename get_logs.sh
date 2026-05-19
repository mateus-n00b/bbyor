N_NODES=15
for i in {0..16}
do
   podman logs bbyor_node${i}_1 > /tmp/logs${i}_0.txt
done

