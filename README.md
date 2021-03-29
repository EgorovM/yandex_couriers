# Сласти от всех напастей

REST-API для курьерского сервиса "Сласти от всех напастей" в рамках тестового задания от "Яндекс-Академии"

## Описание

Сайт написан на языке Python 3.8 с использованием фреймворка Django 3.1.7

Все зависимости находятся по пути:
`requirements/base.txt`

Тесты в файлах `tests.py` в папках `orders` и `couriers`


## Запуск

Сначала нужно сделать клон репозитория себе на локальную сеть:

```
$ git clone https://github.com/EgorovM/yandex_courier.git
```

Устанавливаем вируальное окружение:

Если у вас Ubuntu:
```
$ sudo apt-get update
$ sudo apt-get install python3-venv
$ sudo apt-get install python3-pip
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

Запускаем сервис:

```
$ python manage.py runserver 0.0.0.0:8000
```

## Тесты

Чтобы запустить тесты нужно активировать созданное виртуальное окружение и ввести команду:

```
$ python manage.py test
```