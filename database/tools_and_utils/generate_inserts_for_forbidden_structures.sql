select
concat('INSERT INTO qi.esi_universe_structures(\n eus_structure_id,\n eus_name,\n eus_owner_id,\n'
' eus_system_id,\n eus_type_id,\n eus_x,eus_y,eus_z,\n eus_forbidden,\n',
' eus_created_at, eus_updated_at)\nVALUES (\n ',
us.structure_id,',\n ''',us.name ,''',\n ',
us.owner_id,',\n ',
us.solar_system_id,',\n ',
us.type_id,',\n ',
us.x,',',us.y,',',us.z,',\n ',
'true,\n ',
'''',us.created_at,''',\n '
'''',us.updated_at,''')\n',
'ON CONFLICT ON CONSTRAINT pk_eus DO UPDATE SET\n',
' eus_forbidden=true,\n'
' eus_updated_at=CURRENT_TIMESTAMP AT TIME ZONE ''GMT'';'
) as `sql`,
 us.*
from universe_structures us
where structure_id in (1027239335923
,1034343573248
,1034877491366
,1029816928118
,1034450013691
,1032110505696);

-- INSERT INTO qi.esi_universe_structures(
--  eus_structure_id,
--  eus_name,
--  eus_owner_id,
--  eus_system_id,
--  eus_type_id,
--  eus_x,eus_y,eus_z,
--  eus_forbidden,
--  eus_created_at, eus_updated_at)
-- VALUES (
--  1027239335923,
--  '3GD6-8 - CONTENT',
--  98444656,
--  30001200,
--  35832,
--  98436120634,-22336623815,16831125457,
--  true,
--  '2021-01-19 12:49:09',
--  '2021-01-19 12:49:09')
-- ON CONFLICT ON CONSTRAINT pk_eus DO UPDATE SET
--  eus_forbidden=true,
--  eus_updated_at=CURRENT_TIMESTAMP AT TIME ZONE 'GMT';
-- INSERT INTO qi.esi_universe_structures(
--  eus_structure_id,
--  eus_name,
--  eus_owner_id,
--  eus_system_id,
--  eus_type_id,
--  eus_x,eus_y,eus_z,
--  eus_forbidden,
--  eus_created_at, eus_updated_at)
-- VALUES (
--  1029816928118,
--  'L-5JCJ - Immensea Supreme Court',
--  98621532,
--  30002142,
--  35834,
--  -2645305831602,533916215530,-6264811239557,
--  true,
--  '2020-02-08 02:31:26',
--  '2020-02-28 18:08:07')
-- ON CONFLICT ON CONSTRAINT pk_eus DO UPDATE SET
--  eus_forbidden=true,
--  eus_updated_at=CURRENT_TIMESTAMP AT TIME ZONE 'GMT';
-- INSERT INTO qi.esi_universe_structures(
--  eus_structure_id,
--  eus_name,
--  eus_owner_id,
--  eus_system_id,
--  eus_type_id,
--  eus_x,eus_y,eus_z,
--  eus_forbidden,
--  eus_created_at, eus_updated_at)
-- VALUES (
--  1032110505696,
--  'GE-8JV - Mothership Bellicose',
--  98199293,
--  30001198,
--  35834,
--  -685380858595,-3420347766,-1586013126492,
--  true,
--  '2020-04-08 00:12:11',
--  '2020-04-08 00:12:11')
-- ON CONFLICT ON CONSTRAINT pk_eus DO UPDATE SET
--  eus_forbidden=true,
--  eus_updated_at=CURRENT_TIMESTAMP AT TIME ZONE 'GMT';
-- INSERT INTO qi.esi_universe_structures(
--  eus_structure_id,
--  eus_name,
--  eus_owner_id,
--  eus_system_id,
--  eus_type_id,
--  eus_x,eus_y,eus_z,
--  eus_forbidden,
--  eus_created_at, eus_updated_at)
-- VALUES (
--  1034343573248,
--  'NRT4-U - hut',
--  98444656,
--  30001962,
--  35832,
--  -339938442417,58899708369,234754729281,
--  true,
--  '2021-01-19 13:32:10',
--  '2021-01-19 13:32:10')
-- ON CONFLICT ON CONSTRAINT pk_eus DO UPDATE SET
--  eus_forbidden=true,
--  eus_updated_at=CURRENT_TIMESTAMP AT TIME ZONE 'GMT';
-- INSERT INTO qi.esi_universe_structures(
--  eus_structure_id,
--  eus_name,
--  eus_owner_id,
--  eus_system_id,
--  eus_type_id,
--  eus_x,eus_y,eus_z,
--  eus_forbidden,
--  eus_created_at, eus_updated_at)
-- VALUES (
--  1034450013691,
--  '8QT-H4 - NT AT THE GATES OF MORDOR',
--  98480154,
--  30004012,
--  35834,
--  -2405463987288,1721469787508,-1412163146836,
--  true,
--  '2021-01-19 12:50:12',
--  '2021-01-19 12:50:12')
-- ON CONFLICT ON CONSTRAINT pk_eus DO UPDATE SET
--  eus_forbidden=true,
--  eus_updated_at=CURRENT_TIMESTAMP AT TIME ZONE 'GMT';
-- INSERT INTO qi.esi_universe_structures(
--  eus_structure_id,
--  eus_name,
--  eus_owner_id,
--  eus_system_id,
--  eus_type_id,
--  eus_x,eus_y,eus_z,
--  eus_forbidden,
--  eus_created_at, eus_updated_at)
-- VALUES (
--  1034877491366,
--  'T5ZI-S - The Tower of Legends',
--  416584095,
--  30004735,
--  35834,
--  -1206278198291,625115288542,-980863853871,
--  true,
--  '2021-01-19 12:49:20',
--  '2021-01-19 12:49:20')
-- ON CONFLICT ON CONSTRAINT pk_eus DO UPDATE SET
--  eus_forbidden=true,
--  eus_updated_at=CURRENT_TIMESTAMP AT TIME ZONE 'GMT';
