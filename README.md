# Q.Industrialist
[![GitHub issues](https://img.shields.io/github/issues/Qandra-Si/q.industrialist)](https://github.com/Qandra-Si/q.industrialist/issues)
[![GitHub forks](https://img.shields.io/github/forks/Qandra-Si/q.industrialist)](https://github.com/Qandra-Si/q.industrialist/network)
[![GitHub stars](https://img.shields.io/github/stars/Qandra-Si/q.industrialist)](https://github.com/Qandra-Si/q.industrialist/stargazers)
[![GitHub license](https://img.shields.io/github/license/Qandra-Si/q.industrialist)](https://github.com/Qandra-Si/q.industrialist/blob/master/LICENSE)

Инструмент для планирования перевозок, построения планов изготовления модулей, кораблей, отслеживания процесса выполнения контрактов, отслеживания торговых операций.

<img src="https://qandra-si.github.io/q.industrialist/006-router_v1.0-DarkFman.png" height="80%" width="80%">

## Возможности текущей версии
Q.Industrialist версии v1.1-Imine является набором утилит выполненных в виде python-скриптов. Скрипты принимают аргументы командной строки, таким образом, например, настраивается выбор имени пилота, от имени которого будут запрашиваться данные с серверов CCP.

[![EVE - Ночной цех №46 новые инструменты RI4](https://img.youtube.com/vi/Gxh2vXRkL_I/0.jpg)](https://www.youtube.com/watch?v=Gxh2vXRkL_I "EVE - Ночной цех №46 новые инструменты RI4")

В выпуске "Ночной цех №46" на youtube-канале [z85tv](https://www.youtube.com/channel/UC_H7mou0O9GbMB_mvKZe-uw) в сентябре 2020 года состоялся обзор возможностей отчётов, которые были сгенерированы утилитами Q.Industrialist версии v0.6.x. Таким образом можно бегло получить представление о возможностях и способу использования программного обеспечения Q.Industrialist.

[![EVE - Ночной цех №57 Vendetta и Q.Industrialist](https://img.youtube.com/vi/cEzYDjQpLAY/0.jpg)](https://www.youtube.com/watch?v=cEzYDjQpLAY "EVE - Ночной цех №57 Vendetta и Q.Industrialist")

В выпуске "Ночной цех №57" в январе 2023 года анонсируются новые возможности программного обеспечения Q.Industrialist, интеграция расчётов рентабельности в производстенные процессы.

Плейлисты, в которых публикуются обучающие видеоролики по функционалу Q.Industrialist можно посмотреть на [Rutube](https://rutube.ru/plst/661088/) и [YouTube](https://www.youtube.com/watch?v=LEEtZPG-xsE&list=PLKoH6-WjvAiyRt-NRIjMsT9mZhS8fI-Ol&index=3).

### Требования
Для получения данных по корпорации, с которыми работают утилиты Q.Industrialist в большинстве случаев [требуется](https://esi.evetech.net/ui/#/Assets/get_corporations_corporation_id_assets) директорская роль. **Внимание, требуется именно Director role, а не должность Директора!** Программы анализируют информацию об имуществе корпорации, т.н. assets/ассеты, анализируют корпоративные ордера и запущенные работы корпоративного производства, состояние подразделений кошелька. В том числе, для работы отдельных утилит Q.Industrialist потребуются и другие роли, общий список требуемых ролей:
* Director - для доступа к имуществу корпорации, спискам чертежей 
* Factory_Manager - для доступа к списку производственных работ, списку POS-ов
* Accountant или Junior_Accountant - для доступа к информации о балансе корпоративных кошельков
* Station_Manager - для получения информации о корпоративных структурах (станциях)

Утилиты Q.Industrialist поддерживают работу с несколькими учётными записями пилотов одновременно. Как указано выше, каждый такой пилот должен иметь роль Director в своей корпорации. Таким образом, утилиты позволяют получать информацию и строить отчёты по нескольким корпорациям одновременно.

В общем случае вы можете не иметь ingame доступа к учётной записи пилота с директорской ролью (я умышленно пишу здесь не *"директорской должности"*, а именно к *"директорской роли"*, т.к. в игре EVE Online это разные вещи). Вам, как техническому специалисту в корпорации, могут предоставить доступ к данным пилота с директорской ролью, пройдя за вас аутентификацию и переслав вам ключ, полученный в процессе (подробнее см. в разделе [Первый запуск программного обеспечения Q.Industrialist, авторизация](https://github.com/Qandra-Si/q.industrialist#%D1%88%D0%B0%D0%B3-5-%D0%BF%D0%B5%D1%80%D0%B2%D1%8B%D0%B9-%D0%B7%D0%B0%D0%BF%D1%83%D1%81%D0%BA-%D0%BF%D1%80%D0%BE%D0%B3%D1%80%D0%B0%D0%BC%D0%BC%D0%BD%D0%BE%D0%B3%D0%BE-%D0%BE%D0%B1%D0%B5%D1%81%D0%BF%D0%B5%D1%87%D0%B5%D0%BD%D0%B8%D1%8F-qindustrialist-%D0%B0%D0%B2%D1%82%D0%BE%D1%80%D0%B8%D0%B7%D0%B0%D1%86%D0%B8%D1%8F)). Q.Industrialist сохранит информацию и позволит от имени учётной записи пилота прошедшего аутентификацию считывать данные с серверов CCP.

# Установка и настройка

## Установка и настройка на сервере
Для автономного запуска скриптов и круглосуточной доступности отчётов с помощью веб-сервера, следуйте инструкции ниже.

Для нормальной работы Q.Industrialist вам понадобится VPS-сервер с Linux и как минимум, 1 Gb RAM, 1 Core CPU, 20 Gb SSD.

Последовательно выполните команды по установке необходимых для работы зависимостей:

```bash
sudo apt install \
    python3 python3-venv python3-psycopg python3-psycopg2 \
    gcc git python3-dev \
    postgresql libpq-dev \
    wget

# настраиваем русскую локаль для того, чтобы с комфортом редактировать файлы с настройками
# (пояснения даны на русском языке)
sudo locale-gen ru_RU
sudo locale-gen ru_RU.UTF-8
sudo update-locale
sudo dpkg-reconfigure locales
localectl set-locale LANG=ru_RU.UTF-8
unset LANG
LANG=ru_RU.UTF-8

mkdir ~/q_industrialist
cd ~/q_industrialist

git clone https://github.com/Qandra-Si/q.industrialist.git .
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt

# если на этом этапе во время установки зависимостей появится сообщение об
# ошибке, обратитесь к разработчику (контакты см. ниже)

# если ошибок не появилось, то перейдите к созданию базы данных:
sudo -u postgres psql --port=5432 postgres postgres
```

Продолжайте вводить команды в терминале psql:

```sql
CREATE DATABASE qi_db WITH ENCODING = 'UTF8' TABLESPACE = pg_default CONNECTION LIMIT = -1;
CREATE USER qi_user WITH LOGIN PASSWORD 'придумайте-и-запишите-пароль' NOSUPERUSER INHERIT NOCREATEDB NOCREATEROLE NOREPLICATION;
GRANT ALL ON DATABASE qi_db TO qi_user;
quit
```

После создания базы данных выполните настройку сервера БД. Откройте файл `pg_hba.conf` в режиме редактирования, добавьте в него нового пользователя:

```bash
sudo nano /etc/postgresql/16/main/pg_hba.conf
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   qi_db           qi_user                                 md5

# после сохранения изменения выполните перезагрузку конфигурации
sudo systemctl reload postgresql

# после чего можно перейти к настройке создании таблиц в базе данных:
cd ~/q_industrialist/database
./run_scripts.sh

# внимание! обновление схемы базы данных неавтоматизировано, но разработчик
# при переходе на новую версию выпускает upgrades.sql таким образом,
# чтобы сохранить накопленную информацию в базе данных и выполнить её обновление
# с сохранением информации

# не запускайте скрипт создания таблиц в базе данных повторно, скрипт всё удалит

# следите за обновлением программного обеспечения и при переходе выполняйте
# команды из соответствующих upgrades.sql, которые появились при обновлении

# если на данном этапе вам нужна помощь, обратитесь к разработчику (контакты см. ниже)
```

Создайте своё ESI приложение по [pэтой ссылке](https://developers.eveonline.com/applications). Нажмите кнопку "Create New Application", введите название приложения, например "Q.Industrialist моей корпорации", введите примечание, выберите режим "Authentication & API Access", укажите Callback URL "https://localhost/callback/ ", последовательно добавьте следующие разрешения:

```txt
esi-location.read_location.v1
esi-wallet.read_character_wallet.v1
esi-universe.read_structures.v1
esi-corporations.read_corporation_membership.v1
esi-assets.read_assets.v1
esi-fittings.read_fittings.v1
esi-markets.structure_markets.v1
esi-corporations.read_structures.v1
esi-characters.read_blueprints.v1
esi-contracts.read_character_contracts.v1
esi-wallet.read_corporation_wallets.v1
esi-corporations.read_divisions.v1
esi-assets.read_corporation_assets.v1
esi-corporations.read_blueprints.v1
esi-contracts.read_corporation_contracts.v1
esi-corporations.read_starbases.v1
esi-industry.read_corporation_jobs.v1
esi-markets.read_corporation_orders.v1
esi-industry.read_corporation_mining.v1
esi-planets.read_customs_offices.v1
esi-corporations.read_facilities.v1
```

После ввода всех параметров нажмите кнопку "Create Application".

Снова откройте карточку приложения, нажмите кнопку "View Applicaiton", вам будет показаны два параметра: "Client ID" и "Secret Key".

```bash
# настройте подключение к базе данных, для этого скопируйте файл с шаблонными
# настройками и отредактируейте его
cp ~/q_industrialist/q_industrialist_settings.py.template ~/q_industrialist/q_industrialist_settings.py
# отредактируйте файл q_industrialist_settings.py
# найдите в секции g_database поле password и замените его на ваш пароль
# найдите параметр g_client_id и введите "Client ID" вашего ESI-приложения
nano ~/q_industrialist/q_industrialist_settings.py

# укажите производственные станции и структуры, также воспользовавшись шаблонными
# настройками, отредактировав их:
cp ~/q_industrialist/q_router_settings.py.template ~/q_industrialist/q_router_settings.py
# отредактируйте файл q_router_settings.py
# найдите в секции g_database поле password и замените его на ваш пароль
nano ~/q_industrialist/q_router_settings.py
```

После создания базы данных потребуется скачать файлы с игровых серверов EVE Online и выполнить их конвертацию (конвертация и скачивание необходимых данных будет выполняться около часа, при необходимости запускайте следующие команды в screen-е):

```bash
# создаём директорию в которой во время работы будет сохраняться множество файлов
# получаемых с серверов EVE Online
mkdir -p $HOME/.q_industrialist

cd ~/q_industrialist/static_data_interface

# скачиваем файл с данными static data interface (SDE) с серверов EVE Online
wget -O sde.zip https://eve-static-data-export.s3-eu-west-1.amazonaws.com/tranquility/sde.zip
# если с доступом к файлу будут какие-то проблемы, то скачайте файл вручную отсюда:
# https://developers.eveonline.com/resource/resources

unzip sde.zip


# следующая программа потребует не менее 1 Гб памяти на конвертацию файлов
cd ~/q_industrialist
.venv/bin/python eve_sde_tools.py --cache_dir=$HOME/.q_industrialist

# файл и распакованную из него информацию можно удалить после обработки
rm -f ~/q_industrialist/static_data_interface/sde.zip
rm -rf ~/q_industrialist/static_data_interface/{bsd,fsd,universe}

# следующая программа задаст несколько вопросов, рекомендуется ответить утвердительно
cd ~/q_industrialist
.venv/bin/python q_dictionaries.py --category=all --cache_dir=$HOME/.q_industrialist

# Are you sure to cleanup type_ids in database?
# Too much afterward overheads!!!
# Please type 'yes': yes
# Are you sure to cleanup conveyor_formulas in database?
# Too much afterward overheads!!!
# Please type 'yes' or 'append': yes

# на следующем этапе от вас потребуется выполнить аутентификацию с использованием
# браузера от имени персонажа у которого есть права на чтение корпоративных данных
# если вы выполняете авторизацию персонажа другого человека, попросите у него
# токен, который выдаст браузер в адресной строке (после перехода по указанной ссылке)
cd ~/q_industrialist
.venv/bin/python q_universe_preloader.py --category=all --pilot="Qandra Si" --online --cache_dir=$HOME/.q_industrialist

# Open the following link in your browser:
#
# https://login.eveonline.com/v2/oauth/authorize/?response_type=code&redire......e=unique-state
#
# Copy the "code" query parameter and enter it here: 0000000000000000000000
# Copy your SSO application's secret key and enter it here: zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz

# Если вы всё введёте правильно, начнётся загрузка данных и первичное заполнение базы данных
```
    
Внимание! когда разработчики игры EVE Online выпускают очередное обновление, добавляют в игру новые предметы или меняют настройки производства, следует повторять сценарий приведённый выше.

Выполните настройку требуемых вам модулей (отдельно можно использовать модуль Cynonetwork, или Blueprints, или Router). Если вы решите не настраивать модуль, то отключите его также в файле `run-all-with-preload.sh` (см. инструкцию ниже).

```bash
cd ~/q_industrialist
# вам следует выполнить настройку следующих модулей:
ls -1 *_settings.py.template
# модули, которые вы уже настроили:
ls -1 *_settings.py

# выполните копирование шаблонного файла, откройте копию и отредактируейте (например):
cp q_capital_settings.py.template q_capital_settings.py
nano q_capital_settings.py
```

После загрузки данных переходим к установке и настройке web-сервера. Если вы захотите настроить https на сервере, то воспользуйтесь [этой инструкцией](https://letsencrypt.org/ru/getting-started/).

```bash
sudo apt install nginx php8.3-fpm php-pgsql

# создайте пароли для пользователей закрытой части сервера
sudo sh -c "echo -n 'pilot1:' >> /etc/nginx/.htpasswd"
sudo sh -c "openssl passwd -apr1 >> /etc/nginx/.htpasswd"
sudo sh -c "echo -n 'pilot2:' >> /etc/nginx/.htpasswd"
sudo sh -c "openssl passwd -apr1 >> /etc/nginx/.htpasswd"

# настройте подключение к базе данных, для этого скопируйте файл с шаблонными
# настройками и отредактируейте его
cp ~/q_industrialist/php_interface/.settings.php.template ~/q_industrialist/php_interface/.settings.php
# отредактируйте файл .settings.php
# найдите поле DB_PASSWORD и замените его на ваш пароль
nano ~/q_industrialist/php_interface/.settings.php

# скопируйте необходимые файлы в корень сервера
sudo mkdir -p /var/www/html
sudo cp -rf ~/q_industrialist/offline_resources/favicon/* /var/www/html/
sudo rm /var/www/html/README.md
sudo chmod $USER:www-data -R /var/www/cat
```

Отредактируйте файл конфигурации `/etc/nginx/sites-enabled/default` сервера nginx.

```conf
server {
  root /var/www/html;
  index index.html index.htm;
  server_name  <здесь-доменное-имя-вашего-сервера>;
  location / {
    try_files $uri $uri/ =404;
  }
  location /qbot {
    alias /var/www/qindustrialist_bot;
    index welcome.html;
    try_files $uri $uri/ =404;
  }
  location ~ \.php$ {
    # путь к директории, где расположены файлы Q.Industrialist
    # например /home/user/q_industrialist
    root /<директория программ Q.Industrialist>/php_interface;
    include snippets/fastcgi-php.conf;
    fastcgi_pass unix:/run/php/php8.3-fpm.sock;
    auth_basic "Restricted Content";
    auth_basic_user_file /etc/nginx/.htpasswd;
    # increase request timeout
    proxy_read_timeout 520;
    proxy_connect_timeout 520;
    proxy_send_timeout 520;
  }
  location ~ /\.ht {
   deny all;
  }
  location ~ /\.env {
   deny all;
  }
}
```

Подготовьте скрипты для планировщика с запуском модулей:

Файл `~/run-ALL.sh`
```bash
#!/bin/bash
/home/user/run-database.sh
/home/user/run-all-with-preload.sh
```

Файл `~/run-database.sh`
```bash
#!/bin/bash
# можно указать нескольких директоров разных корпораций
if /home/user/q_industrialist/.venv/bin/python /home/user/q_industrialist/q_universe_preloader.py \
     --category=corporation --category=industry_systems --category=market_prices --category=conveyor_formulas \
     --pilot="Qandra Si" \
     --online --cache_dir=/home/user/.q_industrialist
then
  /home/user/run-router.sh
fi
```

Файл `~/run-router.sh`
```bash
#!/bin/bash
function cmp_files {
 local a=`if [ -f $1 ]; then md5sum $1 | cut -d' ' -f1 ; else echo "" ; fi`
 local b=`if [ -f $2 ]; then md5sum $2 | cut -d' ' -f1 ; else echo "" ; fi`
 if [ -n "$a" ] && [ -n "$b" ]; then
  if [[ "$a" != "$b" ]]; then
   echo 1 #"diff $a <> $b"
  else
   echo 0 #"same $a == $b"
  fi
 else
  echo -1 #"no file"
 fi
}

# можно указать названия нескольких корпораций
if /home/user/q_industrialist/.venv/bin/python /home/user/q_industrialist/q_router.py \
    --corporation="R Industry" --corporation="R Strike" \
    --offline --cache_dir=/home/user/.q_industrialist
then
  f0s="user/.q_industrialist/router.html"
  f0d="/var/www/html/router.html"
  echo "$f0d is outdated and will be replaced"
  cp $f0s $f0d

  f1s="user/q_industrialist/render_stylesheet_dark.css"
  f1d="/var/www/html/render_stylesheet_dark.css"
  f2s="user/q_industrialist/render_html_conveyor.js"
  f2d="/var/www/html/render_html_conveyor.js"
  f3s="/home/user/q_industrialist/render_html_conveyor.css"
  f3d="/var/www/html/render_html_conveyor.css"
  if [[ "`cmp_files $f1s $f1d`" != "0" ]]; then
   cp $f1s $f1d
  fi
  if [[ "`cmp_files $f2s $f2d`" != "0" ]]; then
   cp $f2s $f2d
  fi
  if [[ "`cmp_files $f3s $f3d`" != "0" ]]; then
   cp $f3s $f3d
  fi
fi
```

Файл `~/run-all-with-preload.sh`
```bash
#!/bin/bash

# можно указать нескольких директоров разных корпораций
if /home/user/q_industrialist/.venv/bin/python /home/user/q_industrialist/q_preloader.py \
       --pilot="Kekuit Void" \
       --online --cache_dir=/home/user/.q_industrialist
then
  #/home/user/q_industrialist/.venv/bin/python /home/user/q_industrialist/q_shareholders.py --pilot="Kekuit Void" --offline --cache_dir=/home/user/.q_industrialist
  #cp /home/user/.q_industrialist/shareholders_*.html /var/www/html
  /home/user/q_industrialist/.venv/bin/python /home/user/q_industrialist/q_logist.py --pilot="Kekuit Void" --offline --cache_dir=/home/user/.q_industrialist
  cp /home/user/.q_industrialist/cynonetwork.html /var/www/html
  /home/user/q_industrialist/.venv/bin/python /home/user/q_industrialist/q_conveyor.py --pilot="Kekuit Void" --offline --cache_dir=/home/user/.q_industrialist
  cp /home/user/.q_industrialist/conveyor.html /var/www/html
  cp /home/user/.q_industrialist/conveyor{0,1,2,3,4,5,6,7,8,9}.html /var/www/html
  /home/user/q_industrialist/.venv/bin/python /home/user/q_industrialist/q_accounting.py --pilot="Kekuit Void" --offline --cache_dir=/home/user/.q_industrialist
  cp /home/user/.q_industrialist/accounting.html /var/www/html
  /home/user/q_industrialist/.venv/bin/python /home/user/q_industrialist/q_blueprints.py --pilot="Kekuit Void" --offline --cache_dir=/home/user/.q_industrialist
    cp /home/user/.q_industrialist/blueprints*.html /var/www/html
  # используется esi_corporation_industry_jobs, т.ч. для успешной работы требуется запуск master-версии
  /home/user/q_industrialist/.venv/bin/python /home/user/q_industrialist/q_workflow.py --pilot="Kekuit Void" --offline --cache_dir=/home/user/.q_industrialist
  cp /home/user/.q_industrialist/workflow.html /var/www/html
  cp /home/user/.q_industrialist/industry.html /var/www/html
  /home/user/q_industrialist/.venv/bin/python /home/user/q_industrialist/q_regroup.py --pilot="Kekuit Void" --offline --cache_dir=/home/user/.q_industrialist
  cp /home/user/.q_industrialist/regroup.html /var/www/html
  # НЕЛЬЗЯ СЮДА ДОБАВЛЯТЬ РЕГИОНЫ БЕЗ СОГЛАСОВАНИЯ С ССР, ИНАЧЕ БУДЕТ БАН: You have been banned from using ESI. Please contact Technical Support. (support@eveonline.com)
  # /home/user/q_industrialist/q_market_analyzer.py --pilot="Kekuit Void" --offline --cache_dir=/home/user/.q_industrialist
  #cp /home/user/.q_industrialist/markets_analyzer*.html /var/www/html
  /home/user/q_industrialist/.venv/bin/python /home/user/q_industrialist/render_html_index.py --cache_dir=/home/user/.q_industrialist
  cp /home/user/.q_industrialist/index.html /var/www/html
  # Upwell Palatine Keepstar (rewrite)
  ## /home/user/q_industrialist/.venv/bin/python /home/user/q_upwell_palatine_keepstar/q_capital.py --pilot="Fritz Perlz" --pilot="olegez" --online --cache_dir=/home/user/q_upwell_palatine_keepstar/.q_industrialist
  ## cp /home/user/q_upwell_palatine_keepstar/.q_industrialist/upwell_palatine_keepstar.html /var/www/html
fi
```

Файл `~/run-public-rare.sh`
```bash
#!/bin/bash
# можно указать нескольких директоров разных корпораций
/home/user/q_industrialist/.venv/bin/python /home/user/q_industrialist/q_universe_preloader.py \
    --category=public --category=rare --category=trade_hubs \
    --pilot="Qandra Si" \
    --online --cache_dir=/home/user/.q_industrialist-rare
```

Для корректной работы скриптов потребуется создать несколько дополнительных директорий:

```bash
mkdir -p ~/.q_industrialist-rare
cd ~/.q_industrialist-rare
ln -s ~/.q_industrialist/auth_cache auth_cache
```

После чего проверить работу всех программ (убедиться, что все настройки заданы, подключенный пилот имеет доступ к корпоративным данным, программы не запрашивают токены ESI-приложений и т.п.) то есть, что программы способны будут работать в фоновом режиме:

```bash
~/run-public-rare.sh
~/run-database.sh
~/run-all-with-preload.sh
```

Отредактируйте файл с планом обновления информации с серверов EVE Online запустив команду `crontab -e` (замените путь `/home/user` на вашу домашнюю директорию):

```txt
# регулярная чистка кеша
39,59 * * * * /usr/bin/flock -w 0 /tmp/qind.lockfile rm --verbose /home/user/.q_industrialist/esi_cache/.cache_corporations_*_{assets,blueprints}.json >> /tmp/tmp.cron 2>&1
59 3  * * * /usr/bin/flock -w 0 /tmp/qind.lockfile rm --verbose /home/user/.q_industrialist/esi_cache/.cache_*.json >> /tmp/tmp.cron 2>&1
59 13 * * * /usr/bin/flock -w 0 /tmp/qind.lockfile rm --verbose /home/user/.q_industrialist/esi_cache/.cache_*.json >> /tmp/tmp.cron 2>&1
# генерирование основных отчётов
*/5 * * * * /usr/bin/flock -w 0 /tmp/qind.lockfile /home/user/run-ALL.sh >> /tmp/tmp.cron 2>&1
# market prices, industry indicies, adjusted prices
39 */2 * * * /usr/bin/flock -w 0 /tmp/qind-rare.lockfile /home/user/run-public-rare.sh >> /tmp/tmp-rare.cron 2>&1
9 */3 * * * /usr/bin/flock -w 0 /tmp/qind-rare.lockfile /home/user/run-public-rare.sh >> /tmp/tmp-rare.cron 2>&1
# capital trackers
# 19,49 * * * * /usr/bin/flock -w 0 /tmp/qind-once.lockfile /home/user/run-capitals.sh >> /tmp/tmp-once.cron 2>&1
```

Если для вас инструкция оказалось слишком сложной, или вы столкнулись с техническими сложностями, то вы можете запросить *Помощь зала*, обратившись за помощью в [Discord-канале z85.tv](https://discord.com/invite/QH7YZ75), упомянув что помощью нужна именно по Q.Industrialist.

## Установка и настройка среды разработчика (локальный запуск)

**Внимание! следующая инструкция устарела.**

В разделе [выше](https://github.com/Qandra-Si/q.industrialist#%D1%83%D1%81%D1%82%D0%B0%D0%BD%D0%BE%D0%B2%D0%BA%D0%B0-%D0%B8-%D0%BD%D0%B0%D1%81%D1%82%D1%80%D0%BE%D0%B9%D0%BA%D0%B0-%D0%BD%D0%B0-%D1%81%D0%B5%D1%80%D0%B2%D0%B5%D1%80%D0%B5) приведены инструкции по настройке и запуску Q.Industrialist в операционной системе Linux. В следующем разделе приведены инструкции по настройке Q.Industrialist в операционной системе Windows.

Для продолжения вам понадобятся установленное ПО:
1. Python 3 - [python.org](https://www.python.org/downloads/windows/)
1. Git - [git-scm.com](https://git-scm.com/download/win), см. также [инструкцию](https://git-scm.com/book/ru/v2/%D0%92%D0%B2%D0%B5%D0%B4%D0%B5%D0%BD%D0%B8%D0%B5-%D0%A3%D1%81%D1%82%D0%B0%D0%BD%D0%BE%D0%B2%D0%BA%D0%B0-Git)
1. TortoiseGit (необязательный графический пакет) - [tortoisegit.org](https://tortoisegit.org/download/)

### Шаг 0. Настройка среды разработки

Откройте окно программы `Git Bash`, [настройте](https://git-scm.com/book/ru/v2/%D0%92%D0%B2%D0%B5%D0%B4%D0%B5%D0%BD%D0%B8%D0%B5-%D0%9F%D0%B5%D1%80%D0%B2%D0%BE%D0%BD%D0%B0%D1%87%D0%B0%D0%BB%D1%8C%D0%BD%D0%B0%D1%8F-%D0%BD%D0%B0%D1%81%D1%82%D1%80%D0%BE%D0%B9%D0%BA%D0%B0-Git) среду `Git` для первого использования.

```bash
# set your user name and email address
git config --global user.name "Qandra Si"
git config --global user.email qandra.si@gmail.com
# configure the default text editor that will be used when Git needs you to type in a message
git config --global core.editor nano
```

### Шаг 1. Создание копии репозитория Q.Industrialist

Для начала вам следут определиться:
1. вы планируете использовать готовое программное обеспечение Q.Industrialist
1. или же вы планируете заняться разработкой дополнительных модулей в составе программного обеспечения Q.Industrialist.

Если вы желаете пользоваться готовым программным обеспечением Q.Industrialist, то переходите к этапу созданию каталога и получению файлов из репозитория. Если в ваши намерения входит модификация программного обеспечения Q.Industrialist и доработка его под собственные нужды, то вам следует:
+ убедиться, что вы залогинены на GitHub под своим аккаунтом
+ нажать на кнопку Fork в правом верхнем углу этого репозитория Q.Industrialist
+ на этапе скачивания файлов с GitHub использовать url на свой собственный репозиторий-ответвление, например https://github.com/glorden/q.industrialist.git

Создайте каталог в который будут скачаны и распакованы файлы Q.Industrialist, скачайте файлы:

```bash
# create workspace directory q_industrialist in your home dir
cd
mkdir q_industrialist && cd q_industrialist
# upload Q.Industrialist files into workspace dir
git clone --origin github --branch master --single-branch https://github.com/Qandra-Si/q.industrialist.git .
```

### Шаг 2. Настройка локальной копии репозитория Q.Industrialist

Повторно запустите программу `Git Bash` с правами администратора (щелчок правой кнопкой мыши по ранее запущенной программе `Git Bash`, снова щелчок по пункту "Git Bash", выберите пункт "Запуск от имени администратора"). В каталоге, где были распакованы файлы Q.Industrialist запустите программу `pip` и установите зависимости для `Python 3`. Закройте программу `Git Bash` запущенную с правами администратора, т.к. она более не понадобится.

```bash
cd ~/q_industrialist
# setup Python 3 environment requirements
pip install -r requirements.txt
exit
```

Для продолжения настройки среды разработки перейдите в окно программы `Git Bash`, запущенной в самом начале (без прав администратора). Скопируйте шаблон файла с настройками, внесите изменения в настройки Q.Industrialist.

```bash
# setup Q.Industrialist environment
cd ~/q_industrialist
cp q_industrialist_settings.py.template q_industrialist_settings.py
# edit Q.Industrialist default settings as you wish (to exit nano press Ctrl+X)
nano q_industrialist_settings.py
```

Скачайте и распакуйте последнюю версию статического набора данных [Static Data Export (SDE)](https://developers.eveonline.com/resource/resources) в папке с названием "static_data_interface", с коррекцией структуры каталогов (каталоги "bsd" и "fsd" должны отказаться в папке "static_data_interface"). Запустите конвертацию `.yaml` файлов в `.json` файлы с помощью программы eve_sde_tools.py в каталог с временными файлами `.q_industrialist`. Процедура конвертации длительная и требовательная к памяти ЭВМ, потребуется не менее 4 Гб памяти, т.ч. при недостаточном кол-ве ОП рекомендуется закрыть лишние программы.

```bash
# unpack here sde.zip from https://developers.eveonline.com/resource/resources
echo "$HOME/q_industrialist/static_data_interface"
ls -1 $HOME/q_industrialist/static_data_interface
# for example:
#   bsd/
#   fsd/
#   README.md
# run convertation  from .yaml to .json (too long and 4 Gb memory required)
cd ~/q_industrialist
mkdir ./.q_industrialist
time python eve_sde_tools.py --cache_dir=./.q_industrialist
# for example:
#   Rebuilding typeIDs.yaml file...
#   Rebuilding invPositions.yaml file...
#   ...
#   real 24m39,000s
time python q_dictionaries.py --cache_dir=./.q_industrialist
# for example:
#   real 1m2,000s
```

### Шаг 3. Подготовка к первому запуску программного обеспечения Q.Industrialist

#### Шаг 3.1. Настройка модулей Q.Industrialist

Модулями Q.Industrialist являются отдельные программы, скрипты, выполняющие генерацию отчётов. Каждый модуль выполняет какую-то отдельную задачу, как то, например, построение маршрутов циносети и отслеживание отстатков цинок и топляка на промежуточных станциях циносети; либо же отслеживание остатков чертежей в заданных коробках, а также необходимого или недостающего количества материалов для запуска производства по имеющимся чертежам и т.д. Каждый модуль и каждый отчёт самодостаточен, по желанию можно запускать генерацию лишь какого-то одного отчёта, пользуясь соответствующим модулем. Перед использованием всякий модуль должен быть настроен. Для настройки модулей используются одноимённые файлы, например модуль `q_logist.py` настраивается с помощью скрипта `q_logist_settings.py`. По умолчанию, рабочая копия Q.Industrialist не содержит settings-файлов, их необходимо создать используя заранее подготовленные шаблоны, в частности для скрипта `q_logist_settings.py` в рабочей копии имеется шаблон `q_logist_settings.py.template`. Для остальных модулей, если это требуется, имеются аналогичные файлы с шаблонными настройками.

Программный комплект Q.Industrialist содержит следующие модули:
* q_accounting.py- модуль для построения балансового отчёта корпорации по имеющимся остаткам на складах в разных частях Вселенной EVE Online
* q_blueprints.py - модуль для построения отчёта по имеющимся чертежам в имуществе корпорации для их анализа, поиска, отслеживания контрактов в которых упомянуты чертежи
* q_capital.py - модуль для построения отчёта по прогрессу производства капитальных кораблей, отслеживания имеющегося количества материалов для постройки, чертежей и отдельных компонентов
* q_conveyor.py - модуль для построение отчёта для отслеживания остатков чертежей в заданных коробках, а также необходимого или недостающего количества материалов для запуска производства по имеющимся чертежам
* q_logist.py - модуль для построения отчёта с остатками цинок и топляка по маршрутам циносети, отслеживание их отстатков на промежуточных станциях циносети
* q_workflow - модуль для построения отчёта по прогрессу производства по заданному ежемесячному плану

К служебным (вспомогательным) модулям относятся:
* q_preloader.py - модуль для централизованной загрузки всех необходимых данных для генерации отчётов другими модулями, подробнее см. раздел [Запуск модулей в offline-режиме](https://github.com/Qandra-Si/q.industrialist#%D0%B7%D0%B0%D0%BF%D1%83%D1%81%D0%BA-%D0%BC%D0%BE%D0%B4%D1%83%D0%BB%D0%B5%D0%B9-%D0%B2-offline-%D1%80%D0%B5%D0%B6%D0%B8%D0%BC%D0%B5)

К отладочным модулям относятся:
* q_assets.py - модуль для построения дерева ассетов корпорации
* q_bpos.py - модуль для построения отчётов по имеющимся БПО и БПЦ в виде электронных таблиц, а также дерева чертежей корпорации, где иерархическим представлением служит market-дерево

Скопируйте файлы с настройками, предназначенные для запуска различных модулей Q.Industrialist, внесите в них изменения по желанию. Как указано выше, модуль `q_blueprints.py` и/или модуль `q_workspace.py` имеют независимые и отдельные настройки в соответствующих файлах `q_blueprints_settings.py` и `q_workspace_settings.py`. Без подготовки файлов с настройками одноимённый модуль запустить не удастся.

```bash
cd ~/q_industrialist
# get list of files with template (default) settings 
ls -1 *_settings.py.template
# for example:
#   q_blueprints_settings.py.template
#   q_conveyor_settings.py.template
#   q_industrialist_settings.py.template
#   q_logist_settings.py.template
#   q_workflow_settings.py.template
# copy each of them except q_industrialist_settings (see previous step)
cp q_industrialist_settings.py.template q_industrialist_settings.py
cp q_conveyor_settings.py.template q_conveyor_settings.py
cp q_logist_settings.py.template q_logist_settings.py
cp q_workflow_settings.py.template q_workflow_settings.py
# copy each of them
nano q_blueprints_settings.py
nano q_conveyor_settings.py
nano q_logist_settings.py
nano q_workflow_settings.py
```

#### Шаг 3.2. Настройка модуля q_logist.py (анализ маршрутов циносети)

Выполните первый запуск любого понравившегося модуля.

*Ниже рассмотрен пример настройки и запуска модуля `q_logist.py`, который включает в себя пример первичной настройки, редактирование зависимостей, получение подрочной информации, запуск программы, регистрацию собстенного ESI-приложения, авторизацию вашего пилота и т.д. Пример рассмотрен достаточно подробно, включает в себя все подготовительные шаги, большинство из которых выполняется лишь однократно и не потребуются в дальнейшем, однако каждый такой этап является важным при первом запуске программного комплекта Q.Industrialist.*

Для настройки модуля генерации отчёта по маршрутам циносети воспользуйтесь [Jump planner на dotlan.net](https://evemaps.dotlan.net/jump). Выберите для себя подходящий маршрут и получите адресную строку следующего вида:
> https://evemaps.dotlan.net/jump/Rhea,544/Shafrak:Zayi:Leran:Heydieles

В конце адресной строки будут упомянуты названия солнечных систем по циномаршруту, в данном случае упомянуты системы `Shafrak`, `Zayi`, `Leran` и `Heydieles`. Необходимо получить и вписать в файл настроек идентификаторы станций, находящихся в перечисленных системах.

Получить идентификаторы NPC-станций, которые упомянуты в статическом набора данных (SDE) можно с помощью поиска по `.yaml` SDE-файлам, либо по файлу `.converted_typeIDs.json`, например (идентификаторы NPC-станций имеют номера от 60000000 до 64000000, см. [справочную информацию](https://docs.esi.evetech.net/docs/asset_location_id) по идентификаторам в EVE Online):

```bash
# searching inventory names by filter (for example 'Jita')
cd ~/q_industrialist
python -c "import eve_sde_tools
names = eve_sde_tools.read_converted('./.q_industrialist', 'invNames')
systems = ['Shafrak', 'Zayi', 'Leran', 'Heydieles']
for filter in systems:
  print(*[(int(nm),names[nm]) for nm in names if
    (names[nm].find(filter)>=0) and (int(nm)>=60000000) and (int(nm)<=64000000)],sep='\n')"
# for example:
#   (60001120, 'Shafrak VIII - Moon 13 - Kaalakiota Corporation Factory')
#   (60008443, 'Shafrak VIII - Moon 9 - Amarr Navy Assembly Plant')
#   (60011464, 'Zayi X - Moon 7 - Pend Insurance Depository')
#   (60008824, 'Leran VI - Civic Court Accounting')
#   (60010933, 'Heydieles III - Moon 13 - Duvolle Laboratories Factory')
#   (60010939, 'Heydieles IV - Moon 19 - Duvolle Laboratories Warehouse')
```

Таким образом, с помощью подручных средств (утилит программного пакета Q.Industrialist), либо же с помощью поиска по текстовым файлам, могут быть получены идентификаторы станций, перечисленных в маршруте Jump planner-а. Вносим полученные идентификаторы станций в файл настроек `q_logist_settings.py`. В качестве идентификаторов могут использоваться не только идентификаторы станций, но и идентификаторы солнечных систем, или идентификаторы контейнеров; в зависимости от уровня детализации в отчёт по циносети попадут либо ассеты на всех станциях солнечной системы, либо ассеты в конкретном контейнере на станции.

```bash
# edit Cyno Network routes and settings (to exit nano press Ctrl+X)
nano q_logist_settings.py
# show modified Cyno Network routes and settings
cat q_logist_settings.py
# for example:
#   g_cynonetworks = [
#     {  # route for url: "https://evemaps.dotlan.net/jump/Rhea,544/Shafrak:Zayi:Leran:Heydieles"
#       "route": [
#         60001120,  # Shafrak VIII - Moon 13 - Kaalakiota Corporation Factory
#         60011464,  # Zayi X - Moon 7 - Pend Insurance Depository
#         60008824,  # Leran VI - Civic Court Accounting
#         60010939   # Heydieles IV - Moon 19 - Duvolle Laboratories Warehouse
#       ]
#     }
#  ]
```

*Примечание: идентификаторы структур (не NPC-станций) получить сложнее, для этого потребуется запустить модуль `q_assets.py`, однако на данном этапе этот шаг умышленно пропущен, т.к. для начала потребуется закончить подготовку модуля `q_logist.py` к первому запуску.*

### Шаг 4. Создание своего собственного ESI-приложения

После того, как настройка модуля `q_logist.py` завершена, перед запуском требуется определиться:
1. создать ли своё новое ESI-приложение
1. использовать готовое ESI-приложение Q.Industrialist'

Если вы планируете только пользоваться готовым программным обеспечением Q.Industrialist, то вам подойдёт второй вариант. Если в ваши намерения входит собственная разработка программ на языке Python и модификация программного комплекта Q.Industrilaist, то вам подойдёт первый вариант, в этом случае воспользуйтесь созданием и регистрацией ESI-приложения по [этой ссылке](https://developers.eveonline.com/applications).

### Шаг 5. Первый запуск программного обеспечения Q.Industrialist, авторизация

Запустите модуль `q_logist.py`, указав в командной строке имя пилота, расположение сконвертированных во время шага №2 файлов, а также другие параметры запуска (с полным перечнем вы можете ознакомиться в разделе [Параметры командной строки модулей Q.Industrialist](https://github.com/Qandra-Si/q.industrialist#%D0%BF%D0%B0%D1%80%D0%B0%D0%BC%D0%B5%D1%82%D1%80%D1%8B-%D0%BA%D0%BE%D0%BC%D0%B0%D0%BD%D0%B4%D0%BD%D0%BE%D0%B9-%D1%81%D1%82%D1%80%D0%BE%D0%BA%D0%B8-%D0%BC%D0%BE%D0%B4%D1%83%D0%BB%D0%B5%D0%B9-qindustrialist)). В процессе первого запуска вам будет предложено ввести идентификатор вашего ESI-приложения, или воспользоваться существующим. Также вам будет предложено пройти авторизацию по ссылке, которую надо скопировать и вставить в адресную строку браузера. После завершения авторизации вашего пилота браузер перейдёт на несуществующую страницу, например:
> `https://localhost/callback/?code=HgII28v2fs64mrPFdcCbCA&state=unique-state`

вернитесь в окно программы `Git Bash` и введите значение параметра `code`. Дождитесь завершения работы модуля генерации страницы с отчётом по циносети от Shafrak до Heydieles.

*Также вы можете отправить предложенную ссылку для прохождения авторизации другому пилоту, с тем чтобы он самостоятельно прошёл авторизацию, предоставив вам доступ к получению данных с использованием роли Director. Риска утраты доступа к аккаунту, или риска какого-то на него воздействия, в такой операции нет. Операция безопасна. Программное обеспечение Q.Industrialist при работе использует лишь необходимый и достаточный набор scope (разрешений). Со списком разрешений можно ознакомиться на этапе авторизации. При желании другой пилот всегда может отменить доступ к данным корпорации по этой ссылке: [https://community.eveonline.com/support/third-party-applications/](https://community.eveonline.com/support/third-party-applications/). В этом случае приложение Q.Industrialist будет отключено, генерация отчётов остановлена.* 

```bash
# first time Q.Industrialist run
python q_logist.py --pilot="Qandra Si" --online --cache_dir=./.q_industrialist
# for example:
#   Follow the prompts and enter the info asked for.
#   Copy your SSO application's client ID and enter it here [press 'Enter' for default Q.Industrialist app]:
#   Open the following link in your browser:
#   https://login.eveonline.com/v2/oauth/authorize/?response_type=code&redirect_uri=...
#   Once you have logged in as a character you will get redirected to https://localhost/callback/.
#   Copy the "code" query parameter and enter it here: HgII28v2fs64mrPFdcCbCA
#
#   Qandra Si is from 'R Initiative 4' corporation
#   'R Initiative 4' corporation has 30826 assets
#   'R Initiative 4' corporation has 162 custom asset's names
#   'R Initiative 4' corporation has offices in 40 foreign stations
#   Building cyno network report...
#   Done
```

Откройте сформированный отчёт `cynonetwork.html`, расположенный в папке с временными файлами `.q_industrialist`.

<img src="https://qandra-si.github.io/q.industrialist/005-cynonetwork_v0.7.1.png" height="80%" width="80%">

Полученный отчёт может быть настроен указанием корабля Anshar, Ark, Nomad или Rhea, также указанием скилов пилота. Кроме того поддерживается генерация нескольких маршрутов циносети, перечисленных в файле с настройками. С примером отчёта, полученным в результате действий приведённых выше, можно ознакомиться по следующей ссылке [cynonetwork-v0.7.1.html](https://qandra-si.github.io/q.industrialist/cynonetwork-v0.7.1.html).

### Шаг 6. Разработка своих модулей в составе Q.Industrialist

Ваша рабочая копия Q.Industrialist настроена и подготовлена к использованию. Теперь вы можете заняться разработкой своих собственных модулей, используя библиотеки и утилиты из состава программного обеспечения Q.Industrialist.

В качестве рекомендации, предложу вам следовать простым правилам:
* называйте своим модули **мнемоничными названиями**, например `q_market.py` или `q_pilots.py` соответственно той тематике, для которой предназначен модуль
* при необходимости, **создавайте отдельные файлы с настройками** для своих модулей в виде файлов-шаблонов, например `q_market_settings.py.template` или `q_pilots_settings.py.template`
  * учтите, что реальные файлы с настройками `q_*_settings.py` не будут версифицироваться, т.к. добавлены в `.gitignore` файл, с тем чтобы **при их редактировании рабочая копия не менялась**!
* **создавайте файлы-генераторы отчётов** для своих модулей соответственно их названиям `render_html_market.py` или `render_html_pilots.py`
* не изобретайте велосипед, пользуйтесь готовыми модулями, пакетам и утилитами:
  * утилиты для работы с данными из набора Static Data Interface (SDE) вы найдёте в скрипте `eve_sde_tools.py`
  * утилиты для работы с OpenAPI for EVEOnline (т.н. EVE Swagger Interface) вы найдёте в пакете `eve_esi_interface`, а также скрипте `eve_esi_tools.py`
  * утилиты для работы с аргументами командной строки вы найдёте в скрипте `console_app.py`
* пользуясь исходными кодами программного обеспечения Q.Industrialist, не забывайте ставить ссылку на первоисточник, см. также [LICENSE](https://github.com/Qandra-Si/q.industrialist/blob/master/LICENSE)!

## Параметры командной строки модулей Q.Industrialist

...дописать

### Запуск модулей в offline-режиме

...дописать
