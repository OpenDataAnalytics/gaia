#!/usr/bin/env bash

apt-get update

# Install base packages
apt-get install -y subversion git-core tar unzip wget bzip2 build-essential autoconf libtool libxml2-dev libgeos-dev libpq-dev libbz2-dev proj screen munin-node munin htop libgeos++-dev software-properties-common python-software-properties

# Install proj4
apt-get install -y libproj-dev

locale-gen en_US.UTF-8
update-locale LANG=en_US.UTF-8
export LANGUAGE="en_US.UTF-8"
export LANG="en_US.UTF-8"
export LC_ALL="en_US.UTF-8"

# Install postgis / postgres
apt-get install -y postgresql-9.1-postgis postgresql-contrib-9.1 postgresql-server-dev-9.1

# Install apache-mod-tile
add-apt-repository -y ppa:kakrueger/openstreetmap
apt-get update
export DEBIAN_FRONTEND=noninteractive
apt-get install -y libapache2-mod-tile

# Need to add the port to the url ...
sed -i 's/localhost/localhost:8080/g' /var/www/osm/slippymap.html

# Adjust the tile size
sed -i '$ a\TILESIZE=256' /etc/renderd.conf

# Get map data for north america
wget http://download.geofabrik.de/north-america-latest.osm.pbf

# Note 8000 is 8gb of RAM for cache and 6 is the number of processors to use. 
# So if running in smaller VM reduce as appropriate.
sudo -u postgres osm2pgsql --slim -C 9000 --cache-strategy sparse --number-processes 6 north-america-latest.osm.pbf

sudo -u postgres psql -d gis -c "ALTER TABLE geometry_columns OWNER TO \"www-data\";"
sudo -u postgres psql -d gis -c "ALTER TABLE planet_osm_line OWNER TO \"www-data\";"
sudo -u postgres psql -d gis -c "ALTER TABLE planet_osm_nodes OWNER TO \"www-data\";"
sudo -u postgres psql -d gis -c "ALTER TABLE planet_osm_point OWNER TO \"www-data\";"
sudo -u postgres psql -d gis -c "ALTER TABLE planet_osm_polygon OWNER TO \"www-data\";"
sudo -u postgres psql -d gis -c "ALTER TABLE planet_osm_rels OWNER TO \"www-data\";"
sudo -u postgres psql -d gis -c "ALTER TABLE planet_osm_roads OWNER TO \"www-data\";"
sudo -u postgres psql -d gis -c "ALTER TABLE planet_osm_ways OWNER TO \"www-data\";"
sudo -u postgres psql -d gis -c "ALTER TABLE spatial_ref_sys OWNER TO \"www-data\";"

touch /var/lib/mod_tile/planet-import-complete
service renderd restart
# Pre-render the tiles 0-5
render_list -n 8 -a -z 0 -Z 5 -s /var/run/renderd/renderd.sock
service renderd restart
# Need update the apache config to allow cross origin sharing
sed -i 's/LogLevel info/LogLevel info\n    <IfModule mod_headers.c>\n        <LocationMatch "\.(png)$">\n           Header set Access-Control-Allow-Origin "\*"\n        <\/LocationMatch>\n    <\/IfModule>/g' /etc/apache2/sites-enabled/tileserver_site
service apache2 restart
