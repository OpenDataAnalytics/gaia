#!/usr/bin/env bash

# First, clear out any old mapnik or node.js installs that might conflict
sudo apt-get purge libmapnik libmapnik-dev mapnik-utils nodejs

# Also clear out any old ppa's that might conflict
sudo rm /etc/apt/sources.list.d/*mapnik*
sudo rm /etc/apt/sources.list.d/*developmentseed*
sudo rm /etc/apt/sources.list.d/*chris-lea*

# add new ppa's
echo 'yes' | sudo apt-add-repository ppa:chris-lea/node.js
echo 'yes' | sudo apt-add-repository ppa:mapnik/v2.2.0

# update
sudo apt-get -y update
sudo apt-get -y upgrade

# install nodejs latest and a few tilemill deps
sudo apt-get install -y nodejs git build-essential libgtk2.0-dev \
 libwebkitgtk-dev protobuf-compiler libprotobuf-lite7 libprotobuf-dev \
 libgdal1-dev


# Now, either install mapnik latest from packages
# Or see file below for installing mapnik from source
# and skip this line
sudo apt-get install -y libmapnik-dev mapnik-utils

# set up postgres
POSTGRES_VERSION=9.1 # you may need to change this depending on ubuntu version
POSTGIS_VERSION="1.5" # you may need to change this depending on ubuntu version
sudo apt-get install -y postgresql postgresql-server-dev-$POSTGRES_VERSION postgresql-$POSTGRES_VERSION-postgis
sudo su postgres
# we lost variables, reset them
POSTGRES_VERSION=9.1 # you may need to change this
POSTGIS_VERSION="1.5" # you may need to change this
createuser <your user> # yes to super
createdb template_postgis
createlang -d template_postgis plpgsql # you may not need this
POSTGIS_PATH=`pg_config --sharedir`/contrib/postgis-$POSTGIS_VERSION
psql -d template_postgis -f $POSTGIS_PATH/postgis.sql
psql -d template_postgis -f $POSTGIS_PATH/spatial_ref_sys.sql
exit

# build tilemill
git clone https://github.com/mapbox/tilemill.git
cd tilemill
npm install

# then start it...
# if you are running a desktop server then just boot using all the defaults
./index.js # should open a window automatically, but you can also view at http://localhost:20009

# if you are running a headless/remote server then you can connect either
# by ssh connection forwarding or by opening up public access to the machine.
# for details on ssh forwarding see http://www.mapbox.com/tilemill/docs/guides/ubuntu-service/#ssh_connection_forwarding
# for details on viewing via the remote ip see http://www.mapbox.com/tilemill/docs/guides/ubuntu-service/#configuring_to_listen_for_public_traffic
