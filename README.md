# Q.Industrialist
Инструмент для планирования перевозок, построения планов изготовления модулей, кораблей, отслеживания процесса выполнения контрактов.

<img src="https://qandra-si.github.io/q.industrialist/004-conveyor_v0.7.1.png" height="80%" width="80%">

## Возможности текущей версии
Q.Industrialist версии v0.7.0 является набором утилит выполненных в виде python-скриптов. Скрипты принимают аргументы командной строки, таким образом, например, настраивается выбор имени пилота, от имени которого будут запрашиваться данные с серверов CCP.

[![EVE - Ночной цех №46 новые инструменты RI4](https://img.youtube.com/vi/Gxh2vXRkL_I/0.jpg)](https://www.youtube.com/watch?v=Gxh2vXRkL_I "EVE - Ночной цех №46 новые инструменты RI4")

В выпуске "Ночной цех №46" на youtube-канале [z85tv](https://www.youtube.com/channel/UC_H7mou0O9GbMB_mvKZe-uw) в сентябре 2020 года состоялся обзор возможностей отчётов, которые были сгенерированы утилитами Q.Industrialist версии v0.6.x. Таким образом можно бегло получить представление о возможностях и способу использования программного обеспечения Q.Industrialist.

### Требования
Для получения данных по корпорации, с которыми работают утилиты Q.Industrialist в большинстве случаев требуется директорская роль. *Внимание, требуется именно Director role, а не должность Директора!* Поскольку утилиты оперируют информацией об имуществе корпорации, т.н. assets/ассеты, для доступа к этим данным [требуется](https://esi.evetech.net/ui/#/Assets/get_corporations_corporation_id_assets) директорская роль. В том числе, для работы отдельных утилит Q.Industrialist потребуются и другие роли, общий список требуемых ролей:
* Director - для доступа к имуществу корпорации, спискам чертежей 
* Factory_Manager - для доступа к списку производственных работ, списку POS-ов
* Accountant или Junior_Accountant - для доступа к информации о балансе корпоративных кошельков
* Station_Manager - для получения информации о корпоративных структурах (станциях)

Утилиты Q.Industrialist поддерживают работу с несколькими учётными записями пилотов одновременно. Как указано выше, каждый такой пилот должен иметь роль Director в своей корпорации. Таким образом, утилиты позволяют получать информацию и строить отчёты по нескольким корпорациям одновременно.

В общем случае вы можете не иметь ingame доступа к учётной записи пилота с директорской ролью (я умышленно пишу здесь не *"директорской должности"*, а именно к *"директорской роли"*, т.к. в игре EVE Online это разные вещи). Вам, как техническому специалисту в корпорации, могут предоставить доступ к данным пилота с директорской ролью, пройдя за вас аутентификацию и переслав вам ключ, полученный в процессе. Q.Industrialist сохранит информацию и позволит от имени учётной записи пилота прошедшего аутентификацию считывать данные с серверов CCP.

# Установка и настройка

## Установка и настройка на сервере
Для автономного запуска скриптов и круглосуточной доступности отчётов с помощью веб-сервера, следуйте инструкции ниже. Если у вас есть свой сервер, подключенный к сети интернет, можете перейти к шагу №2.

### Шаг 1. Настройка VPS-сервера
Если у вас нет сервера, подключенного к сети интернет, то предлагаю рассмотреть возможность начать использовать VPS-сервер, это т.н. выделенный виртуальный сервер, который приобретается в аренду на один день, неделю или месяц и дольше.

Предложений аренды VPS-серверов в сети интернет довольно много, вы самостоятельно можете выбрать подходящую площадку, ознакомившись с тарифами и возможностями. В настоящий момент времени разработка программного обеспечения Q.Industrialist ведётся на серверах SimpleCloud, нареканий в надёжности и стабильности доступа к которым нет. Всвязи с чем предлагаю партнёрскую ссылку https://simplecloud.ru/start/82673 (с самой партнёрской программой можно ознакомиться [по ссылке](https://simplecloud.ru/partners/)) зарегистрировавшись по которой вы сможете поддержать дальнейшую разработку Q.Industrialist :+1:

Для нормальной работы Q.Industrialist вам понадобится VPS-сервер с, как минимум, 1 Гб оперативной памяти. По тарифам на площадке по ссылке приведённой выше: 1 Gb RAM, 1 Core CPU, 20 Gb SSD с безлимитным трафиком обходятся в 250 руб/мес.

*Итак... если ваш бюджет позволит вам оплачивать автономную работу Q.Industrialist для вашей корпорации, а также у вашего пилота имеется роль Director (см. раздел Требования выше)... продолжим. Если нет, то либо заранее решите вопрос с доступом, либо перейдите в раздел Установка и настройка среды разработки с возможностью локального запуска утилит Q.Industrialist. Однако локальный запуск не позволит пилотам вашей корпорации просматривать отчёты, полученные в результате работы программ, такая возможность будет локально только у вас.*

На VPS-сервере вам необходимо установить операционную систему Linux, дистрибутив можете выбрать тот который вам привычнее. В примерах ниже инструкции по установке и настройке программного обеспечения приведены для ОС Debian GNU/Linux. После того, как ваша площадка на VPS-сервере подготовлена, вам необходимо подключиться к серверу по протоколу ssh. Если опыта работы с программами по ssh-протоколу у вас нет, то для ОС Windows в качестве программы-терминала рекомендую [PuTTY](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html), а для обмена файлами с сервером програму [WinSCP](https://winscp.net/eng/docs/lang:ru).

...дописать

### Шаг 2. Установка Q.Industrialist на сервере

...дописать

### Шаг 3. Настройка Q.Industrialist на сервере

...дописать

### Помощь зала?
Если для вас инструкция оказалось слишком сложной, или вы столкнулись с техническими сложностями, то вы можете запросить *Помощь зала*, обратившись за помощью в [Discord-канале z85.tv](https://discord.com/invite/QH7YZ75), упомянув что помощью нужна именно по Q.Industrialist.

## Установка и настройка среды разработчика (локальный запуск)

В разделе выше приведены инструкции по настройке и запуску Q.Industrialist в операционной системе Linux. В следующем разделе приведены инструкции по настройке Q.Industrialist в операционной системе Windows.

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
+ нажать на кнопку Fork в плавом верхнем углу этого репозитория Q.Industrialist
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
```

### Шаг 2. Настройка модулей Q.Industrialist

Модулями Q.Industrialist являются отдельные программы, скрипты, выполняющие генерацию отчётов. Каждый модуль выполняет какую-то отдельную задачу, как то, например, построение маршрутов циносети и отслеживание отстатков цинок и топляка на промежуточных станциях циносети; либо же отслеживание остатков чертежей в заданных коробках, а также необходимого или недостающего количества материалов для запуска производства по имеющимся чертежам и т.д. Каждый модуль и каждый отчёт самодостаточен, по желанию можно запускать генерацию лишь какого-то одного отчёта, пользуясь соответствующим модулем. Перед использованием всякий модуль должен быть настроен. Для настройки модулей используются одноимённые файлы, например модуль `q_logist.py` настраивается с помощью скрипта `q_logist_settings.py`. По умолчанию, рабочая копия Q.Industrialist не содержит settings-файлов, их необходимо создать используя заранее подготовленные шаблоны, в частности для скрипта `q_logist_settings.py` в рабочей копии имеется шаблон `q_logist_settings.py.template`. Для остальных модулей, если это требуется, имеются аналогичные файлы с шаблонными настройками.

Программный комплект Q.Industrialist содержит следующие модули:
* q_accounting.py- модуль для построения балансового отчёта корпорации по имеющимся остаткам на складах в разных частях Вселенной EVE Online
* q_blueprints.py - модуль для построения отчёта по имеющимся чертежам в имуществе корпорации для их анализа, поиска, отслеживания контрактов в которых упомянуты чертежи
* q_capital.py - модуль для построения отчёта по прогрессу производства капитальных кораблей, отслеживания имеющегося количества материалов для постройки, чертежей и отдельных компонентов
* q_conveyor.py - модуль для построение отчёта для отслеживания остатков чертежей в заданных коробках, а также необходимого или недостающего количества материалов для запуска производства по имеющимся чертежам
* q_logist.py - модуль для построения отчёта с остатками цинок и топляка по маршрутам циносети, отслеживание их отстатков на промежуточных станциях циносети
* q_workflow - модуль для построения отчёта по прогрессу производства по заданному ежемесячному плану

К служебным (вспомогательным) модулям относятся:
* q_preloader.py - модуль для централизованной загрузки всех необходимых данных для генерации отчётов другими модулями, подробнее см. раздел "Запуск модулей в offline-режиме"

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
cp q_blueprints_settings.py.template q_industrialist_settings.py
cp q_conveyor_settings.py.template q_conveyor_settings.py
cp q_logist_settings.py.template q_logist_settings.py
cp q_workflow_settings.py.template q_workflow_settings.py
# copy each of them
nano q_blueprints_settings.py
nano q_conveyor_settings.py
nano q_logist_settings.py
nano q_workflow_settings.py
```

### Шаг 3. Первый запуск Q.Industrialist и создание своего ESI-приложения

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

После того, как настройка модуля `q_logist.py` завершена, перед запуском требуется определиться:
1. создать ли своё новое ESI-приложение
1. использовать готовое ESI-приложение Q.Industrialist'

Если вы планируете только пользоваться готовым программным обеспечением Q.Industrialist, то вам подойдёт второй вариант. Если в ваши намерения входит собственная разработка программ на языке Python и модификация программного комплекта Q.Industrilaist, то вам подойдёт первый вариант, в этом случае воспользуйтесь созданием и регистрацией ESI-приложения по [этой ссылке](https://developers.eveonline.com/applications).

Запустите модуль `q_logist.py`, указав в командной строке имя пилота, расположение сконвертированных во время шага №1 файлов, а также другие параметры запуска (с полным перечнем вы можете ознакомиться в разделе "Параметры командной строки модулей Q.Industrialist"). В процессе первого запуска вам будет предложено ввести идентификатор вашего ESI-приложения, или воспользоваться существующим. Также вам будет предложено пройти авторизацию по ссылке, которую надо скопировать и вставить в адресную строку браузера. После завершения авторизации вашего пилота браузер перейдёт на несуществующую страницу, например, `https://localhost/callback/?code=HgII28v2fs64mrPFdcCbCA&state=unique-state` вернитесь в окно программы `Git Bash` и введите значение параметра `code`. Дождитесь завершения работы модуля генерации страницы с отчётом по циносети от Shafrak до Heydieles.

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

### Шаг 4. Разработка своих модулей в составе Q.Industrialist

Ваша рабочая копия Q.Industrialist настроена и подготовлена к использованию. Теперь вы можете заняться разработкой своих собственных модулей, используя библиотеки и утилиты из состава программного обеспечения Q.Industrialist.

В качестве рекомендации, предложу вам следовать простым правилам:
* называйте своим модули **мнемоничными названиями**, например `q_market.py` или `q_pilots.py` соответственно той тематике, для которой предназначен модуль
* при необходимости, **создавайте отдельные файлы с настройками** для своих модулей в виде файлов-шаблонов, например `q_market_settings.py.template` или `q_pilots_settings.py.template`; учтите, что реальные файлы с настройками `q_*_settings.py` не будут версифицироваться, т.к. добавлены в `.gitignore` файл, с тем чтобы **при их редактировании рабочая копия не менялась**!
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
