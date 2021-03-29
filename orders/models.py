import datetime

from django.db import models


class Region(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class Order(models.Model):
    weight = models.DecimalField(max_digits=6, decimal_places=2)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    delivery_hours = models.CharField(max_length=1024)

    courier = models.ForeignKey('couriers.Courier', on_delete=models.CASCADE, blank=True, null=True)
    assign_time = models.DateTimeField(blank=True, null=True)
    complete_time = models.DateTimeField(blank=True, null=True)

    completed_courier_type = models.CharField(max_length=4, blank=True, null=True)

    VALIDATION_ERRORS = {
        1: 'Не задано значение',
        2: 'Не соответствует формату',
        3: 'Некорректный идентификатор'
    }

    def __str__(self):
        return "order %d" % self.id

    @property
    def delivery_time_in_seconds(self):
        """ Время доставки заказа в секундах

        Расчитывается как разность между концом и началом заказа
        """
        if self.complete_time:
            return self.get_delivery_time().total_seconds()

    @property
    def delivery_hours_list(self):
        return self.delivery_hours.split(';')
        
    def get_delivery_time(self):
        """ Время доставки
        
        Returns:
            None, если заказ еще не закончен
            datetime, если заказ закочен
        """

        if self.complete_time:
            return self.complete_time - self.assign_time

    def get_region(self):
        return self.region

    @staticmethod
    def from_json(data):
        """Получение объекта из json

        Args:
            data (dict): словарь с атрибутами и их значениями

        Returns:
            dict: коды и описания ошибок, если не прошло валидацию
            Order: сформированный заказ
        """
        problems = {}

        fields = ['order_id', 'weight', 'region', 'delivery_hours']

        order = Order()

        for field in fields:
            if not field in data:
                problems[field] = {
                    'code': 2,
                    'desciption': 'не задано'
                }

        if problems:
            return problems

        methods = [
            order.set_id, 
            order.set_weight, 
            order.set_region,
            order.set_delivery_hours]

        for method, field in zip(methods, fields):
            code = method(data[field])

            if code != 0:
                problems[field] = {
                    'code': code,
                    'description': order.VALIDATION_ERRORS[code]
                }

        if problems:
            return problems
            

        order.save()

        return order

    def set_id(self, new_id):
        """ Изменение id 

        Args:
            new_id (int): новый id
        Returns: 
            None, если некорректно
            0, если корректно
            <int:id>, если вызвалась ошибка
        """

        if not Order.objects.filter(id=new_id).first():
            self.id = new_id
            return 0

        return 3

    def set_weight(self, weight):
        """ Изменение веса 

        Args:
            weight (float): новый вес
        Returns: 
            None, если некорректно
            0, если корректно
            <int:id>, если вызвалась ошибка
        """

        if weight > 0:
            self.weight = weight
            return 0

        return 2

    def set_region(self, region_id):
        """ Изменение региона 

        Args:
            region_id (int): id нового региона
        Returns: 
            None, если некорректно
            0, если корректно
            <int:id>, если вызвалась ошибка
        """

        r = Region.objects.filter(id=region_id).first()

        if r:
            self.region = r
            return 0

        return 3

    def set_delivery_hours(self, delivery_hours):
        """ Изменение времени доставок 

        Args:
            delivery_hours (list[str]): новое время доставок
        Returns: 
            None, если некорректно
            0, если корректно
            <int:id>, если вызвалась ошибка
        """

        self.delivery_hours = ';'.join(delivery_hours)
        return 0

    def set_assign_time(self, assign_time):
        """ Изменение времени одобрения заказа

        Args:
            assign_time (datetime): новое время начала заказа
        Returns: 
            None, если некорректно
            0, если корректно
            <int:id>, если вызвалась ошибка
        """

        self.assign_time = assign_time
        return 0

    def set_courier(self, courier):
        """ Изменение курьера

        Args:
            courier (Courier): новый курьер
        Returns: 
            None, если некорректно
            0, если корректно
            <int:id>, если вызвалась ошибка
        """

        self.courier = courier
        self.completed_courier_type = courier.courier_type

        return 0

    def assign(self, courier, assign_time):
        """Сдача заказа курьеру в конкертное время

        Args:
            courier (Courier): курьер
            assign_time (datetime): время начала заказа
        """
        self.set_courier(courier)
        self.set_assign_time(assign_time)

    def complete(self, courier_id, complete_time):
        """Конец заказа

        Args:
            courier_id (id): id исполнителя
            complete_time (datetime): время конца заказа

        Returns:
            None, если некорректно
            Order: сохраненный, завершенный заказ
        """
        
        if not (self.courier or self.courier.id == courier_id):
            return
        
        self.complete_time = complete_time
        self.save()

        self.courier.order_completed()

        return self
