#!/bin/sh
for f in $(ls -1 *tar.gz); do tar xfz $f; done

ln -s GeoLite2-City_*/GeoLite2-City.mmdb .
ln -s GeoLite2-Country_*/GeoLite2-Country.mmdb .
