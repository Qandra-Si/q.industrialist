# Q.Industrialist discord bot

Создать своё приложение [тут](https://discordapp.com/developers/applications/).

```bash
# добавить содержимое location-example.conf в конфигурацию nginx
sudo systemctl reload nginx.service

# скопировать содержимое www-root в /var/www/qindustrialist_bot

# исправить права доступа к файлам
sudo chown -R www-data: /var/www/qindustrialist_bot

# установить discord.py модуль
python -m pip install -U discord.py

# подготовить настройки запуска бота
cp config.py.template config.py
# ввести параметры подключения к discord и к postgresql
nano config.py
```
