chcp 1251

psql --file=001.create_db.sql           --echo-errors --log-file=001.create_db.log           postgres postgres
psql --file=002.create_schema.sql       --echo-errors --log-file=002.create_schema.log       qi_db qi_user
psql --file=003.create_esi_schema.sql   --echo-errors --log-file=003.create_esi_schema.log   qi_db qi_user
psql --file=004.create_dictionaries.sql --echo-errors --log-file=004.create_dictionaries.log qi_db qi_user
psql --file=005.create_esi_views.sql    --echo-errors --log-file=005.create_esi_views.log    qi_db qi_user
psql --file=006.create_esi_logic.sql    --echo-errors --log-file=006.create_esi_logic.log    qi_db qi_user
psql --file=007.load_test_data.sql      --echo-errors --log-file=007.load_test_data.log      qi_db qi_user
psql --file=008.trade_hubs.sql          --echo-errors --log-file=008.trade_hubs.log          qi_db qi_user
psql --file=009.conveyor.sql            --echo-errors --log-file=009.conveyor.log            qi_db qi_user

@rem pg_restore --exit-on-error --clean --if-exists --no-owner --verbose --format=c --dbname=qi_db --username=qi_user postgres-20201029-TRANQUILITY-schema.dmp

pause