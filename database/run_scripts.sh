#!/bin/bash

#sudo -u postgres psql --port=5432 --file=001.create_db.sql           --echo-errors --log-file=/tmp/001.create_db.log           postgres postgres
sudo -u postgres psql --port=5432 --file=002.create_schema.sql       --echo-errors --log-file=/tmp/002.create_schema.log       qi_db qi_user
sudo -u postgres psql --port=5432 --file=003.create_esi_schema.sql   --echo-errors --log-file=/tmp/003.create_esi_schema.log   qi_db qi_user
sudo -u postgres psql --port=5432 --file=004.create_dictionaries.sql --echo-errors --log-file=/tmp/004.create_dictionaries.log qi_db qi_user
sudo -u postgres psql --port=5432 --file=005.create_esi_views.sql    --echo-errors --log-file=/tmp/005.create_esi_views.log    qi_db qi_user
sudo -u postgres psql --port=5432 --file=006.create_esi_logic.sql    --echo-errors --log-file=/tmp/006.create_esi_logic.log    qi_db qi_user
sudo -u postgres psql --port=5432 --file=007.load_test_data.sql      --echo-errors --log-file=/tmp/007.load_test_data.log      qi_db qi_user
sudo -u postgres psql --port=5432 --file=008.trade_hubs.sql          --echo-errors --log-file=/tmp/008.trade_hubs.log          qi_db qi_user
sudo -u postgres psql --port=5432 --file=009.conveyor.sql            --echo-errors --log-file=/tmp/009.conveyor.log            qi_db qi_user

