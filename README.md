# Q.Industrialist
Инструмент для планирования перевозок, построения планов изготовления модулей, кораблей, отслеживания процесса выполнения контрактов.

<img src="https://raw.githubusercontent.com/Qandra-Si/q.industrialist/master/examples/004-conveyor_v0.7.1.png" height="80%" width="80%">

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

### Шаг 1. Настройка среды разработки

Откройте окно программы `Git Bash`, [настройте](https://git-scm.com/book/ru/v2/%D0%92%D0%B2%D0%B5%D0%B4%D0%B5%D0%BD%D0%B8%D0%B5-%D0%9F%D0%B5%D1%80%D0%B2%D0%BE%D0%BD%D0%B0%D1%87%D0%B0%D0%BB%D1%8C%D0%BD%D0%B0%D1%8F-%D0%BD%D0%B0%D1%81%D1%82%D1%80%D0%BE%D0%B9%D0%BA%D0%B0-Git) среду `Git` для первого использования, создайте каталог в который будут скачаны и распакованы файлы Q.Industrialist, скачайте файлы:

```bash
# set your user name and email address
git config --global user.name "Qandra Si"
git config --global user.email qandra.si@gmail.com
# configure the default text editor that will be used when Git needs you to type in a message
git config --global core.editor nano
# create workspace directory q_industrialist in your home dir
cd
mkdir q_industrialist && cd q_industrialist
# upload Q.Industrialist files into workspace dir
git clone --origin github --branch master --single-branch https://github.com/Qandra-Si/q.industrialist.git .
```

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

Также скопируйте все прочие файлы с настройками, предназначенные для запуска различных модулей Q.Industrialist, внесите в них изменения по желанию (модуль `q_blueprints.py` и/или модуль `q_workspace.py` имеют независимые и отдельные настройки в соответствующих файлах `q_blueprints_settings.py` и `q_workspace_settings.py`). Без подготовки файлов с настройками одноимённый модуль запустить не удастся (к данному шагу можно вернуться впоследствии).

```bash
# get list of files with template (default) settings 
ls -1 *_settings.py.template
# for example:
#   q_blueprints_settings.py.template
#   q_conveyor_settings.py.template
#   q_industrialist_settings.py.template
#   q_logist_settings.py.template
# copy each of them except q_industrialist_settings (see previous step)
cp q_blueprints_settings.py.template q_industrialist_settings.py
cp q_conveyor_settings.py.template q_conveyor_settings.py
cp q_logist_settings.py.template q_logist_settings.py
# copy each of them
nano q_blueprints_settings.py
nano q_conveyor_settings.py
nano q_logist_settings.py
```

Скачайте и распакуйте последнюю версию статического набора данных [Static Data Export (SDE)](https://developers.eveonline.com/resource/resources) в каталог с названием "2", с сохранением структуры каталогов. Запустите конвертацию `.yaml` файлов в `.json` файлы с помощью программы eve_sde_tools.py в каталог с временными файлами `.q_industrialist`. Процедура конвертации длительная и требовательная к памяти ЭВМ, потребуется не менее 4 Гб памяти, т.ч. при недостаточном кол-ве ОП рекомендуется закрыть лишние программы.

```bash
# unpack here sde.zip from https://developers.eveonline.com/resource/resources
echo "$HOME/q_industrialist/2"
ls -1 $HOME/q_industrialist/2
# for example:
#   readme.txt
#   sde/
# run .jaml to .json convertation (4 Gb memory required)
mkdir ./.q_industrialist
time python eve_sde_tools.py --cache_dir=./.q_industrialist
# for example:
#   Rebuilding typeIDs.yaml file...
#   Rebuilding invPositions.yaml file...
```
