select
 j.ethp_type_id,
 tid.sdet_type_name,
 j.ethp_sell as "jita sell",
 --j.ethp_buy as "jita buy",
 --a.ethp_sell as "amarr sell",
 a.ethp_buy as "amarr buy",
 j.ethp_sell_volume as "jita volume",
 a.ethp_buy_volume as "amarr volume",
 floor(8825.3 / tid.sdet_volume) as "Sigil/T1 volume",
 floor(8825.3 / tid.sdet_volume * j.ethp_sell) as "Sigil/T1 price",
-- round((floor(8825.3 / tid.sdet_volume) * (a.ethp_buy - j.ethp_sell*1.0113))::numeric, 2) as "Sigil/T1 profit"
 floor(floor(8825.3 / tid.sdet_volume) * (a.ethp_buy - j.ethp_sell*1.0167)) as "Sigil/T1 profit"
from
 (select * from qi.esi_trade_hub_prices where ethp_location_id = 60003760) as j
  left outer join qi.eve_sde_type_ids tid on (j.ethp_type_id = tid.sdet_type_id),
 (select * from qi.esi_trade_hub_prices where ethp_location_id = 60008494) as a
where
 j.ethp_type_id = a.ethp_type_id and
 --(j.ethp_sell*1.0113) < a.ethp_buy
 (j.ethp_sell*1.0167) < a.ethp_buy
order by 8 desc

-- ethp_type_id	sdet_type_name	jita sell	amarr buy	jita volume	amarr volume	Sigil/T1 volume	Sigil/T1 price	Sigil/T1 profit
-- 43 753	Retriever Amarr Industrial Livery SKIN	4 895 000	5 004 000	10	5	882 529	4 319 984 349 999	24 052 004 101
-- 47 890	Raging Exotic Filament	5 998 000	6 211 000	3 552	1 011	88 252	529 341 493 999	9 957 773 216
-- 34 207	Optimized Attainment Decryptor	3 237 000	3 501 000	723	472	88 252	285 674 960 999	18 527 810 209
-- 15 605	Caldari Navy Vice Admiral Insignia I	1 850 000	1 906 000	11 715	19	88 252	163 268 049 999	2 215 566 460
-- 19 207	Pith X-Type Large Shield Booster	319 500 000	326 100 000	82	10	353	112 787 333 999	446 315 550
-- 46 005	Agency 'Overclocker' SB5 Dose II	5 946 000	6 109 000	1 925	166	8 825	52 475 233 799	562 168 385
-- 25 606	Ward Console	23 290	25 100	306 950	17 986	882 529	20 554 123 699	1 254 124 013
-- 17 494	Republic Fleet Small Armor Repairer	8 000 000	8 206 000	28	9	1 765	14 120 480 000	127 786 000
-- 23 138	Yan Jung Null Shell	890 100	1 000 000	108	976	8 825	7 855 399 529	838 686 787
-- 30 024	Cartesian Temporal Coordinator	8 852	9 050	152 753	1 014 826	882 529	7 812 155 559	44 277 891
-- 45 609	Loki Offensive - Support Processor	32 580 000	33 320 000	106	18	220	7 188 206 850	43 101 080
-- 47 888	Agitated Exotic Filament	42 410	54 300	10 760	2 158	88 252	3 742 809 729	986 812 065
-- 18 811	Corelum B-Type Kinetic Energized Membrane	1 967 000	2 007 000	188	14	1 765	3 471 873 020	12 621 691
-- 22 291	Ballistic Control System II	1 197 000	1 222 000	15 863	338	1 765	2 112 776 820	8 842 826
-- 25 598	Tripped Power Circuit	2 097	2 301	1 647 759	554 137	882 529	1 850 665 409	149 129 838
-- 2 038	Cargo Scanner II	763 400	781 500	3 967	51	1 765	1 347 446 804	9 444 903
-- 47 927	Mystic S	957,8	988	1 962 449	10 076 926	882 529	845 287 233	12 536 094
-- 21 640	Valkyrie II	900 000	959 000	5 447	1 008	882	794 277 000	38 781 540
-- 39	Zydrine	898,9	920,1	29 086 583	4 486 859	882 529	793 306 216	5 461 415
-- 17 959	Vanadium Hafnite	11 750	12 000	603 436	1 102 817	44 126	518 486 374	2 372 875
-- 19 406	7th Tier Overseer's Personal Effects	507 500	545 100	684	29	882	447 883 975	25 688 029
-- 37 825	Dread Guristas Shield Flux Coil	190 100	200 900	154	61	1 765	335 537 906	13 458 707
-- 394	Shield Recharger II	179 300	192 500	4 821	59	1 765	316 475 258	18 013 042
-- 16 683	Ferrogel	29 000	30 080	1 285 817	88 317	8 825	255 933 699	5 257 052
-- 16 671	Titanium Carbide	193,7	206,8	170 008 060	11 573 035	882 529	170 946 060	8 706 333
-- 16 672	Tungsten Carbide	181,3	188,7	178 480 527	8 148 762	882 529	160 002 689	3 858 672
-- 7 663	Modal Ion Particle Accelerator I	170 900	202 600	769	406	882	150 824 377	25 442 145
-- 27 383	Guristas Mjolnir Light Missile	194,9	200,1	18 486	10 201 984	588 353	114 670 064	1 144 446
-- 28 999	Optimal Range Script	7 786	10 000	41 526	1 174	8 825	68 713 785	18 391 068
-- 42 529	Shield Command Burst I	377 000	402 300	1 052	127	147	55 452 301	2 793 602
-- 42 527	Information Command Burst I	319 900	394 800	758	10	147	47 053 557	10 224 977
-- 16 679	Fullerides	776,1	810,2	44 426 029	5 219 422	58 835	45 662 102	1 243 720
-- 28 437	Compressed Gelidus	488 600	510 600	23 694	3 014	88	43 120 415	1 217 953
-- 27 331	Guristas Scourge Rocket	23,95	25	3 635 744	1 527 163	1 765 059	42 273 186	1 147 350
-- 8 117	Prototype 'Arbalest' Torpedo Launcher	83 340	86 110	2 832	1 173	441	36 775 025	607 795
-- 27 379	Guristas Nova Light Missile	57,81	100,1	226 581	10 028 825	588 353	34 012 706	24 313 436
-- 7 997	XR-3200 Heavy Missile Bay	37 780	41 200	2 264	1 002	882	33 341 983	2 459 963
-- 28 665	Vargur	1 656 000 000	1 706 000 000	56	4	0	32 477 103	0
-- 54 295	Enduring Thermal Shield Hardener	17 330	19 450	339	1 224	1 765	30 588 489	3 230 989
-- 22 546	Skiff	271 300 000	277 200 000	108	20	0	23 943 038	0
-- 3 777	Long-limb Roes	2 497	2 788,62	777	2 925	8 825	22 036 774	2 205 544
-- 29 990	Loki	192 700 000	199 600 000	216	17	0	21 257 941	0
-- 217	Iridium Charge S	6	6,21	10 394 602	1 141 349	3 530 119	21 180 719	387 607
-- 14 017	Domination EM Coating	11 040	11 440	50	82	1 765	19 486 262	380 590
-- 29 984	Tengu	189 300 000	195 400 000	285	16	0	18 159 014	0
-- 1 875	Rapid Light Missile Launcher I	20 450	22 220	1 794	193	882	18 047 738	1 259 923
-- 11 182	Cheetah	26 210 000	28 080 000	190	23	0	13 293 742	0
-- 11 192	Buzzard	25 180 000	25 660 000	229	31	0	11 454 693	0
-- 6 437	Small C5-L Compact Shield Booster	6 399	6 704	2 691	201	1 765	11 294 618	349 711
-- 9 521	Initiated Enduring Multispectral ECM	6 023	6 666	14 719	10 782	1 765	10 630 956	957 364
-- 6 673	Small Focused Afocal Pulse Maser I	5 815	7 226	295	1 386	1 765	10 263 823	2 319 014
-- 35 683	Hecate	52 480 000	55 470 000	278	70	0	9 854 292	0
-- 11 172	Helios	24 410 000	26 900 000	202	12	0	9 366 329	0
-- 11 174	Keres	22 100 000	23 880 000	132	17	0	8 479 962	0
-- 11 188	Anathema	25 190 000	26 660 000	242	32	0	7 911 363	0
-- 12 038	Purifier	25 100 000	26 670 000	312	43	0	7 883 097	0
-- 2 305	Autotrophs	6,63	8	365 226 011	47 639 380	882 529	5 851 173	1 111 350
-- 2 286	Planktic Colonies	6,61	7	60 089 562	42 570 718	882 529	5 833 523	246 766
-- 5 321	C-IR Compact Guidance Disruptor	3 010	5 263	556	1 036	1 765	5 312 830	3 887 823
-- 9 670	Small Rudimentary Concussion Bomb I	1 001	2 660	99	2 639	1 765	1 766 825	2 898 630
-- 5 743	Small 'Hope' Hull Reconstructor I	1 001	3 720	137	556	1 765	1 766 825	4 769 530
-- 2 308	Suspended Plasma	1,67	1,96	353 986 704	31 946 448	882 529	1 473 825	231 320
-- 5 245	Particle Bore Compact Mining Laser	800,4	1 007	13 783	2 813	1 765	1 412 754	341 056
-- 648	Badger	936 100	1 549 000	236	27	0	33 045	0
-- 3 651	Civilian Miner	0,23	1	93 176	8 085	1 765	405	1 352