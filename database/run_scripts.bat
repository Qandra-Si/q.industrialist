chcp 1251

psql --file=001.create_db.sql --echo-errors --log-file=001.create_db.log postgres postgres
psql --file=002.create_schema.sql --echo-errors --log-file=002.create_schema.log qi_db qi_user

psql --file=004.load_test_data.sql --echo-errors --log-file=004.load_test_data.log qi_db qi_user

pause