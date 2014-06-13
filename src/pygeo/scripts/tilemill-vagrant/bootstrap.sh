#!/usr/bin/env bash

# Also clear out any old ppa's that might conflict
rm -f /etc/apt/sources.list.d/*mapnik*
rm -f /etc/apt/sources.list.d/*developmentseed*
rm -f /etc/apt/sources.list.d/*chris-lea*

export DEBIAN_FRONTEND=noninteractive
# update
apt-get -y update
apt-get -y upgrade

# Install some utilities 
apt-get install -y software-properties-common python-software-properties

# add new ppa's
apt-add-repository -y ppa:chris-lea/node.js
apt-add-repository -y ppa:mapnik/v2.2.0

apt-get -y update

# First, clear out any old mapnik or node.js installs that might conflict
apt-get purge -qq libmapnik libmapnik-dev mapnik-utils nodejs


# install nodejs latest and a few tilemill deps
apt-get install -y nodejs git build-essential libgtk2.0-dev \
libwebkitgtk-dev protobuf-compiler libprotobuf-lite7 libprotobuf-dev \
libgdal1-dev


# Now, either install mapnik latest from packages
# Or see file below for installing mapnik from source
# and skip this line
apt-get install -y libmapnik-dev mapnik-utils

# set up postgres
export POSTGRES_VERSION=9.1 # you may need to change this depending on ubuntu version
export POSTGIS_VERSION="1.5" # you may need to change this depending on ubuntu version
apt-get install -y postgresql postgresql-server-dev-$POSTGRES_VERSION postgresql-$POSTGRES_VERSION-postgis
#createuser <your user> # yes to super
sudo -E -u postgres createdb template_postgis
sudo -E -u postgres createlang -d template_postgis plpgsql # you may not need this
export POSTGIS_PATH=`pg_config --sharedir`/contrib/postgis-$POSTGIS_VERSION
sudo -E -u postgres psql -d template_postgis -f $POSTGIS_PATH/postgis.sql
sudo -E -u postgres psql -d template_postgis -f $POSTGIS_PATH/spatial_ref_sys.sql

# build tilemill

sudo -u vagrant git clone https://github.com/mapbox/tilemill.git /home/vagrant/tilemill
cd /home/vagrant/tilemill
npm install

# then start it...
# if you are running a desktop server then just boot using all the defaults
#/home/vagrant/tilemill/index.js tile
#/home/vagrant/tilemill/index.js core --listenHost=0.0.0.0 # should open a window automatically, but you can also view at http://localhost:20009

# if you are running a headless/remote server then you can connect either
# by ssh connection forwarding or by opening up public access to the machine.
# for details on ssh forwarding see http://www.mapbox.com/tilemill/docs/guides/ubuntu-service/#ssh_connection_forwarding
# for details on viewing via the remote ip see http://www.mapbox.com/tilemill/docs/guides/ubuntu-service/#configuring_to_listen_for_public_traffic
