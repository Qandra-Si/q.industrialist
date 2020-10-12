﻿<?php header("Location: " . $_SERVER['HTTP_REFERER']); ?>

<?php
if (!extension_loaded('pgsql')) return;

include_once '.settings.php';


function get_numeric($val) {
    return is_numeric($val) ? ($val + 0) : 0;
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
}

elseif (isset($_POST['module'])) {
    $method = htmlentities($_POST['module']);
    if ($method == 'workflow') {
        if (isset($_POST['action'])) {
            $query = NULL;
            $params = NULL;
            //---
            $action = htmlentities($_POST['action']);
            if (($action == 'edit') && isset($_POST['fit']) && isset($_POST['quantity']) && isset($_POST['eft'])) {
                $wmj_id = htmlentities($_POST['fit']);
                $wmj_quantity = htmlentities($_POST['quantity']);
                if (is_numeric($wmj_id) && is_numeric($wmj_quantity) &&
                    (get_numeric($wmj_id) >= 1) && (get_numeric($wmj_quantity) >= 1)) {
                    $wmj_eft = $_POST['eft'];
                    if (!empty($wmj_eft)) {
                        $query = 'UPDATE workflow_monthly_jobs SET wmj_quantity=$2,wmj_eft=$3 WHERE wmj_id=$1;';
                        $params = array($wmj_id, $wmj_quantity, $wmj_eft);
                        if (isset($_POST['remarks'])) {
                            $wmj_remarks = $_POST['remarks'];
                            if (!empty($wmj_remarks)) {
                                $query = 'UPDATE workflow_monthly_jobs SET wmj_quantity=$2,wmj_eft=$3,wmj_remarks=$4 WHERE wmj_id=$1;';
                                array_push($params, $wmj_remarks);
                            }
                        }
                    }
                }
            }
            //---
            elseif (($action == 'add') && isset($_POST['quantity']) && isset($_POST['eft'])) {
                $wmj_quantity = htmlentities($_POST['quantity']);
                if (is_numeric($wmj_quantity) && (get_numeric($wmj_quantity) >= 1)) {
                    $wmj_eft = $_POST['eft'];
                    if (!empty($wmj_eft)) {
                        $query = 'INSERT INTO workflow_monthly_jobs(wmj_quantity,wmj_eft) VALUES($1,$2);';
                        $params = array($wmj_quantity, $wmj_eft);
                        if (isset($_POST['remarks'])) {
                            $wmj_remarks = $_POST['remarks'];
                            if (!empty($wmj_remarks)) {
                                $query = 'INSERT INTO workflow_monthly_jobs(wmj_quantity,wmj_eft,wmj_remarks) VALUES($1,$2,$3);';
                                array_push($params, $wmj_remarks);
                            }
                        }
                    }
                }
            }
            //---
            if (!is_null($query)) {
                $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
                or die('pg_connect err: '.pg_last_error());
                pg_exec($conn, "SET search_path TO qi");
                pg_query_params($conn, $query, $params)
                or die('pg_query_params err: '.pg_last_error());
                pg_query($conn, 'COMMIT;');
                pg_close($conn);
            }
        }
    }
}
?>
