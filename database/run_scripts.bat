chcp 1251

"c:\Program Files\PostgreSQL\10\bin\psql" --file=001.create_db.sql --echo-errors --log-file=001.create_db.log postgres postgres
"c:\Program Files\PostgreSQL\10\bin\psql" --file=002.create_schema.sql --echo-errors --log-file=002.create_schema.log qi_db qi_user

"c:\Program Files\PostgreSQL\10\bin\psql" --file=004.load_test_data.sql --echo-errors --log-file=004.load_test_data.log qi_db qi_user

pause