#!/bin/bash

sudo -u postgres psql --port=5433 --file=001.create_db.sql --echo-errors --log-file=001.create_db.log postgres postgres
sudo -u postgres psql --port=5433 --file=002.create_schema.sql --echo-errors --log-file=002.create_schema.log qi_db qi_user

sudo -u postgres psql --port=5433 --file=004.load_test_data.sql --echo-errors --log-file=004.load_test_data.log qi_db qi_user