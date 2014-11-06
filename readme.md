## Feeding AIS traffic from gr-ais to gpsd
```
ais_rx -s uhd --args=addr=192.168.100.1 -A RX2 -g 18 | nc -l localhost 5000
gpsd -n -N -D4 -b tcp://localhost:5000
```

ais_rx Crashes reliably after about an hour at the moment with:
```
thread[thread-per-block[13]: <block msk_timing_recovery_cc (37)>]: mmse_fir_interpolator_cc: imu out of bounds.
```
Not sure what the source of the issue is quite yet.

## Serving a kml from gpsd AIS traffic:
```
./gpsd_to_kml.py
```

## To forward AIS packets from gpsd to something like marinetraffic.com:
```
gpspipe -r | nc 5.9.207.224 5678
```
