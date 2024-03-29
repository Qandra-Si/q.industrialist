﻿<?php header("Location: " . $_SERVER['HTTP_REFERER']); ?>

<?php
include 'qi_tools_and_utils.php';

if (!extension_loaded('pgsql')) return;

include_once '.settings.php';


function get_conn() {
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
        or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    return $conn;
}

if (isset($_GET['module'])) {
    $method = htmlentities($_GET['module']);
    if ($method == 'workflow') {
        if (isset($_GET['action']) && isset($_GET['fit'])) {
            $action = htmlentities($_GET['action']);
            $wmj_id = htmlentities($_GET['fit']);
            if (is_numeric($wmj_id) && (get_numeric($wmj_id) >= 1)) {
                $query = NULL;
                $params = NULL;
                if ($action == 'del') {
                    $query = 'DELETE FROM workflow_monthly_jobs WHERE wmj_id=$1;';
                    $params = array($wmj_id);
                }
                elseif ($action == 'act' || $action == 'deact') {
                    $query = 'UPDATE workflow_monthly_jobs SET wmj_active=$2 WHERE wmj_id=$1;';
                    $params = array($wmj_id, ($action == 'act') ? 1 : 0);
                }
                if (!is_null($query)) {
                    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
                            or die('pg_connect err: '.pg_last_error());
                    pg_exec($conn, "SET search_path TO qi");
                    pg_query_params($conn, $query, $params)
                            or die('pg_query_params err: '.pg_last_error());
                    pg_exec($conn, 'COMMIT;');
                    pg_close($conn);
                }
            }
        }
    }
    elseif ($method == 'regroup') {
        if (isset($_GET['action']) && isset($_GET['fit'])) {
            $action = htmlentities($_GET['action']);
            $rs_id = htmlentities($_GET['fit']);
            if (is_numeric($rs_id) && (get_numeric($rs_id) >= 1)) {
                $query = NULL;
                $params = NULL;
                if ($action == 'del') {
                    $query = 'DELETE FROM regroup_stock WHERE rs_id=$1;';
                    $params = array($rs_id);
                }
                elseif ($action == 'act' || $action == 'deact') {
                    $query = 'UPDATE regroup_stock SET rs_active=$2 WHERE rs_id=$1;';
                    $params = array($rs_id, ($action == 'act') ? 1 : 0);
                }
                if (!is_null($query)) {
                    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
                            or die('pg_connect err: '.pg_last_error());
                    pg_exec($conn, "SET search_path TO qi");
                    pg_query_params($conn, $query, $params)
                            or die('pg_query_params err: '.pg_last_error());
                    pg_exec($conn, 'COMMIT;');
                    pg_close($conn);
                }
            }
        }
    }
}

elseif (isset($_POST['module'])) {
    $method = htmlentities($_POST['module']);
    if ($method == 'workflow') {
        if (isset($_POST['action'])) {
            $conn = NULL;
            $query = NULL;
            $params = NULL;
            //---
            $action = htmlentities($_POST['action']);
            if (($action == 'edit') &&
                isset($_POST['fit']) &&
                isset($_POST['quantity']) &&
                isset($_POST['eft']))
            {
                $wmj_id = htmlentities($_POST['fit']);
                $wmj_conveyor = isset($_POST['conveyor']) ? 't' : 'f'; // всегда установлен в on (в список не попадают off значения)
                $wmj_quantity = htmlentities($_POST['quantity']);
                if (is_numeric($wmj_id) && is_numeric($wmj_quantity) &&
                    (get_numeric($wmj_id) >= 1) && (get_numeric($wmj_quantity) >= 1)) {
                    $wmj_eft = $_POST['eft'];
                    if (!empty($wmj_eft)) {
                        $query = 'UPDATE workflow_monthly_jobs SET wmj_quantity=$2,wmj_eft=$3,wmj_conveyor=$4 WHERE wmj_id=$1;';
                        $params = array($wmj_id, $wmj_quantity, $wmj_eft, $wmj_conveyor);
                        if (isset($_POST['remarks'])) {
                            $wmj_remarks = $_POST['remarks'];
                            if (!empty($wmj_remarks)) {
                                $query = 'UPDATE workflow_monthly_jobs SET wmj_quantity=$2,wmj_eft=$3,wmj_conveyor=$4,wmj_remarks=$5 WHERE wmj_id=$1;';
                                array_push($params, $wmj_remarks);
                            }
                        }
                    }
                }
            }
            //---
            elseif (($action == 'add') &&
                    isset($_POST['quantity']) &&
                    isset($_POST['eft'])) {
                $wmj_conveyor = isset($_POST['conveyor']) ? 't' : 'f'; // всегда установлен в on (в список не попадают off значения)
                $wmj_quantity = htmlentities($_POST['quantity']);
                if (is_numeric($wmj_quantity) && (get_numeric($wmj_quantity) >= 1)) {
                    $wmj_eft = $_POST['eft'];
                    if (!empty($wmj_eft)) {
                        $query = 'INSERT INTO workflow_monthly_jobs(wmj_quantity,wmj_eft,wmj_conveyor) VALUES($1,$2,$3);';
                        $params = array($wmj_quantity, $wmj_eft, $wmj_conveyor);
                        if (isset($_POST['remarks'])) {
                            $wmj_remarks = $_POST['remarks'];
                            if (!empty($wmj_remarks)) {
                                $query = 'INSERT INTO workflow_monthly_jobs(wmj_quantity,wmj_eft,wmj_conveyor,wmj_remarks) VALUES($1,$2,$3,$4);';
                                array_push($params, $wmj_remarks);
                            }
                        }
                    }
                }
            }
            //---
            elseif (($action == 'settings') && isset($_POST['id']) && isset($_POST['name']) && isset($_POST['hangars'])) {
                $ms_val_id = htmlentities($_POST['id']);
                $ms_val_name = htmlentities($_POST['name']);
                $ms_val_hangars = htmlentities($_POST['hangars']);
                $station_num = ''; // 1
                if (isset($_POST['station_num'])) {
                    $station_num = htmlentities($_POST['station_num']);
                    if ($station_num == '1')
                        $station_num = '';
                    else if (!is_numeric($station_num))
                        $station_num = '';
                }
                if (is_numeric($ms_val_id)) {
                    $query = <<<EOD
UPDATE modules_settings SET ms_val=v.v
FROM (VALUES ($1,$2),($3,$4),($5,$6)) AS v(k,v)
WHERE ms_key=v.k AND ms_module IN (SELECT ml_id FROM modules_list WHERE ml_name=$7);
EOD;
                    $params = array(
                        'factory:station_id'.$station_num, $ms_val_id,
                        'factory:station_name'.$station_num, $ms_val_name,
                        'factory:blueprints_hangars'.$station_num, '['.$ms_val_hangars.']',
                        'workflow'
                    );
                }
            }
            //---
            elseif ($action == 'containers') {
                $conn = get_conn();
                $containers_cursor = pg_query($conn, 'SELECT wfc_id,wfc_name,wfc_active,wfc_disabled FROM workflow_factory_containers;')
                        or die('pg_query err: '.pg_last_error());
                $containers = pg_fetch_all($containers_cursor);
                //print_r($containers);
                foreach($containers as &$cont) {
                    if ($cont['wfc_disabled'] == 't') continue;  # пропускаем контейнеры, помеченные "отсутствующими", пока они не будут снова актуализированы
                    $id = $cont['wfc_id'];
                    $on = isset($_POST[$id]) ? 't' : 'f'; // всегда установлен в on (в список не попадают off значения)
                    $active = $cont['wfc_active'];
                    if ($on != $active) {
                        $query = 'UPDATE workflow_factory_containers SET wfc_active=$1 WHERE wfc_id=$2;';
                        $params = array($on, $id);
                        pg_query_params($conn, $query, $params)
                                or die('pg_query_params err: '.pg_last_error());
                    }
                }
                pg_query($conn, 'COMMIT;');
                pg_close($conn);
                return; // или $query = NULL;
            }
            //---
            if (!is_null($query)) {
                $conn = get_conn();
                pg_query_params($conn, $query, $params)
                        or die('pg_query_params err: '.pg_last_error());
                pg_query($conn, 'COMMIT;');
                pg_close($conn);
            }
        }
    }
    else if ($method == 'industry') {
        $conn = NULL;
        $query = NULL;
        $params = NULL;
        $action = htmlentities($_POST['action']);
        if (($action == 'settings') && isset($_POST['conveyor_boxes'])) {
            $ms_val_convboxes = htmlentities($_POST['conveyor_boxes']);
            $query = <<<EOD
UPDATE modules_settings SET ms_val=v.v
FROM (VALUES ($2,$3)) AS v(k,v)
WHERE ms_key=v.k AND ms_module IN (SELECT ml_id FROM modules_list WHERE ml_name=$1);
EOD;
            $params = array(
                'workflow',
                'industry:conveyor_boxes', '['.$ms_val_convboxes.']'
            );
        }
        //---
        if (!is_null($query)) {
            $conn = get_conn();
            pg_query_params($conn, $query, $params)
                    or die('pg_query_params err: '.pg_last_error());
            pg_query($conn, 'COMMIT;');
            pg_close($conn);
        }
    }
    elseif ($method == 'regroup') {
        if (isset($_POST['action'])) {
            $conn = NULL;
            $query = NULL;
            $params = NULL;
            //---
            $action = htmlentities($_POST['action']);
            if (($action == 'edit') &&
                isset($_POST['fit']) &&
                isset($_POST['quantity']) &&
                isset($_POST['eft']) &&
                isset($_POST['station']) &&
                isset($_POST['container']))
            {
                $rs_id = htmlentities($_POST['fit']);
                $rs_quantity = htmlentities($_POST['quantity']);
                $rs_eft = $_POST['eft'];
                $rs_station = $_POST['station'];
                $rs_container = $_POST['container'];
                if (is_numeric($rs_id) && is_numeric($rs_quantity) &&
                    (get_numeric($rs_id) >= 1) && (get_numeric($rs_quantity) >= 1) &&
                    !empty($rs_eft) &&
                    !empty($rs_station) && !empty($rs_container))
                {
                    $query = 'UPDATE regroup_stock SET rs_quantity=$2,rs_eft=$3,rs_station=$4,rs_container=$5,rs_remarks=NULL WHERE rs_id=$1;';
                    $params = array($rs_id, $rs_quantity, $rs_eft, $rs_station, $rs_container);
                    if (isset($_POST['remarks'])) {
                        $rs_remarks = $_POST['remarks'];
                        if (!empty($rs_remarks)) {
                            $query = 'UPDATE regroup_stock SET rs_quantity=$2,rs_eft=$3,rs_station=$4,rs_container=$5,rs_remarks=$6 WHERE rs_id=$1;';
                            array_push($params, $rs_remarks);
                        }
                    }
                }
            }
            //---
            elseif (($action == 'add') &&
                    isset($_POST['quantity']) &&
                    isset($_POST['eft']) &&
                    isset($_POST['station']) &&
                    isset($_POST['container']))
            {
                $rs_quantity = htmlentities($_POST['quantity']);
                if (is_numeric($rs_quantity) && (get_numeric($rs_quantity) >= 1)) {
                    $rs_eft = $_POST['eft'];
                    $rs_station = $_POST['station'];
                    $rs_container = $_POST['container'];
                    if (!empty($rs_eft)) {
                        $query = 'INSERT INTO regroup_stock(rs_quantity,rs_eft,rs_station,rs_container) VALUES($1,$2,$3,$4);';
                        $params = array($rs_quantity, $rs_eft, $rs_station, $rs_container);
                        if (isset($_POST['remarks'])) {
                            $rs_remarks = $_POST['remarks'];
                            if (!empty($rs_remarks)) {
                                $query = 'INSERT INTO regroup_stock(rs_quantity,rs_eft,rs_station,rs_container,rs_remarks) VALUES($1,$2,$3,$4,$5);';
                                array_push($params, $rs_remarks);
                            }
                        }
                    }
                }
            }
            //---
            if (!is_null($query)) {
                $conn = get_conn();
                pg_query_params($conn, $query, $params)
                        or die('pg_query_params err: '.pg_last_error());
                pg_query($conn, 'COMMIT;');
                pg_close($conn);
            }
        }
    }
}
?>
