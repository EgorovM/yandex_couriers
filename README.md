# Сласти от всех напастей

REST-API для курьерского сервиса "Сласти от всех напастей" в рамках тестового задания от "Яндекс-Академии"

## Описание

Сайт написан на языке Python 3.8 с использованием фреймворка Django 3.1.7

Все зависимости находятся по пути:
`requirements/base.txt`

Тесты в файлах `tests.py` в папках `orders` и `couriers`

В виртуальной машине сервис запущен со связкой nginx и gunicorn с использованием systemctl. Всего запросы обрабатывают 8 процессов.

Файлы Gunicorn: `/etc/systemd/system/gunicorn.service`
Файлы Nginx: `/etc/nginx/sites-available/yandex_couriers`

Все сервисы перезапускаются после перезагрузки машины, скрипт, который запускается после включения находится в файле /home/entrant/bash-autoreload.sh. Это реализовано с помощью `crontab`


## Запуск сервиса

### Python и зависимости

Сначала нужно сделать клон репозитория себе на локальную сеть:

```
$ git clone https://github.com/EgorovM/yandex_couriers.git
```

Устанавливаем вируальное окружение:

Если у вас Ubuntu:
```
$ sudo apt update
$ sudo apt install python3-venv python3-pip
```

Если у вас другая операционная система, то погуглите :)

Создаем виртуальное окружение и активируем его

```
$ python3 -m venv ~/.virtualenvs/yandex_couriers
$ . ~/.virtualenvs/yandex_couriers/bin/activate
```

Устанавливаем нужные зависимости

```
$ pip install -r requirements/base.txt
```

### PostgreSQL

В качестве базы данных используется PostgreSQL. Установим его, создадим базу данных, пользователя и пропишем права

```
$ sudo apt install libpq-dev postgresql postgresql-contrib
$ sudo -u postgres psql
```

``` 
postgres=# CREATE DATABASE yandex_couriers;
postgres=# CREATE USER django WITH PASSWORD 'NewPassword123';
postgres=# ALTER ROLE django SET client_encoding TO 'utf8';
postgres=# ALTER ROLE django SET default_transaction_isolation TO 'read committed';
postgres=# ALTER ROLE django SET timezone TO 'UTC';
postgres=# GRANT ALL PRIVILEGES ON DATABASE myproject TO myprojectuser;
postgres=# \q
```

Теперь настройка Postgres завершена, и Django может подключаться к базе данных и управлять своей информацией в базе данных.

### Django

Делаем миграции:

```
$ python manage.py migrate
```

Запускаем сервис:

```
$ python manage.py runserver 0.0.0.0:8000
```

### Gunicorn

Мы проверили, что Django успешно запускается, теперь сделаем так, чтобы сервис работал на постоянной основе с помощью Gunicorn и Nginx перенаправлял запросы к нему.


Создадим файл `gunicorn.socket`

```
$ sudo vim /etc/systemd/system/gunicorn.socket
```

Со следующим содержимым:

```bash
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target
```

Затем файл sudo nano `gunicorn.service`

```
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
User=entrant
Group=www-data
WorkingDirectory=/home/entrant/yandex_couriers
ExecStart=/home/entrant/.virtualenvs/yandex_couriers/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/run/gunicorn.sock \
          wsgi_production.wsgi:application

[Install]
WantedBy=multi-user.target
```

Запустим и активируем сокет gunicorn:

```
$ sudo systemctl start gunicorn.socket
$ sudo systemctl enable gunicorn.socket
$ sudo systemctl daemon-reload
$ sudo systemctl restart gunicorn
```

### Nginx

Установим 

```
$ sudo apt install nginx
```

Добавим конфигурационный файл и перенаправим все запросы в gunicorn(по заданию порт 8000):

```
$ sudo vim /etc/nginx/sites-available/yandex_couriers
```

Со следующим содержимым

```
server {
    listen 8000;
    server_name 178.154.206.74; # у вас может быть другое

    location = /favicon.ico { access_log off; log_not_found off; }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
```

Добавим права:

```
$ sudo ufw allow 'Nginx Full'
$ sudo systemctl restart nginx
```

Все, теперь если перейдем по адресу 178.154.206.74:8000, то увидим созданный сервис

## Тесты

Чтобы запустить тесты нужно активировать созданное виртуальное окружение и ввести команду:

```
$ python manage.py test
```