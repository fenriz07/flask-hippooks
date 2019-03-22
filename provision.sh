#!/bin/sh

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install --yes python-dev python-pip mysql-server libmysqlclient-dev libjpeg-dev

pip install -r /vagrant/requirements.txt

sudo mysql -e "CREATE DATABASE hipcooks; GRANT ALL privileges ON hipcooks.* to 'hipcooks'@'localhost' identified by 'hipcooks'"
sudo mysql -e "CREATE DATABASE testing; GRANT ALL privileges ON testing.* to 'hipcooks'@'localhost' identified by 'hipcooks'"
bzcat /vagrant/data/hipcooks.sql.bz2 | mysql -u root hipcooks
