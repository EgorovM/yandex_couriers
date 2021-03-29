import datetime
from collections import defaultdict, namedtuple

from django.db import models

from orders.models import Region, Order


class Courier(models.Model):
    COURIER_TYPES = (
        ('foot', 'пеший курьер'),
        ('bike', 'велокурьер'),
        ('car', 'курьер на автомобиле')
    )

    COEF_BY_TYPE = {
        'foot': 2,
        'bike': 5,
        'car':  9,
    }

    LIFTION_CAPACITY = {
        'foot': 10,
        'bike': 15,
        'car':  50,
    }


    courier_type = models.CharField(max_length=4, choices=COURIER_TYPES)
    regions = models.ManyToManyField(Region)
    working_hours = models.CharField(max_length=1024)

    rating = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    earnings = models.IntegerField(default=0)

    VALIDATION_ERRORS = {
        1: 'Не задано значение',
        2: 'Не соответствует формату',
        3: 'Некорректный идентификатор'
    }

    def __str__(self):
        return "courier %s" % self.id

    @property
    def courier_id(self):
        return self.id

    @property
    def lifting_capacity(self):
        """ Максимальная грузоподъемность в зависимости от типа курьера """

        return self.LIFTION_CAPACITY[self.courier_type]

    @staticmethod
    def get_earning_coef(courier_type):
        """ Коэффицент зависящий от типа курьера """

        return Courier.COEF_BY_TYPE[courier_type]

    @property
    def get_regions(self):
        return [r.id for r in self.regions.all()]

    @property
    def working_hours_list(self):
        return self.working_hours.split(';')

    def set_rating(self):
        """ Расчет рейтинга, будет вызываться каждый раз, 
        когда потребуется информация о курьере

        rating = (60*60 - min(t, 60*60))/(60*60) * 5 
        где  t  - минимальное из средних времен доставки по районам (в секундах),
        t = min(td[1], td[2], ..., td[n]) 
        td[i]  - среднее время доставки заказов по району  i  (в секундах).
        """

        orders = self.get_completed_orders()
        regions = defaultdict(lambda: [0, 0])

        prev_delivery_time = None

        for order in orders:
            if not prev_delivery_time:
                delivery_time = order.delivery_time_in_seconds
            else:
                delivery_time = (order.assign_time - prev_delivery_time).total_seconds()

            region_id = order.get_region().id

            regions[region_id][0] += delivery_time
            regions[region_id][1] += 1
            
            prev_delivery_time = order.complete_time

        min_t = min(map(lambda x: x[0] / x[1], regions.values()))

        self.rating = round((60 * 60 - min(min_t, 60 * 60)) / (60*60) * 5, 2)
        
    def set_earning(self):
        """Заработок рассчитывается как сумма оплаты за каждый завершенный развоз:
        sum = ∑(500 * C),

        C  — коэффициент, зависящий от типа курьера (пеший — 2, велокурьер — 5, авто — 9) 
        на момент формирования развоза.
        """ 

        orders = self.get_completed_orders()
        self.earnings = sum([Courier.get_earning_coef(o.completed_courier_type) * 500 
                             for o in orders])

    def get_completed_orders(self):
        """ Завершенные курьеров заказы """
        return (Order.objects
                    .filter(courier=self, complete_time__isnull=False))

    def is_handy_time(self, time):
        """ Удобно ли курьеру взять заказ в это время
        str: time - время формата %H:%M-%H:%M

        Будем считать, что курьеру удобно, если начало или конец промежутка
        лежит хотя-бы в одном рабочем времени курьера.
        """

        def t_d(time):
            return datetime.datetime.strptime(time, '%H:%M')

        start_time, end_time = time.split('-')

        for working_hour in self.working_hours_list:
            w_start_time, w_end_time = working_hour.split('-')

            if t_d(w_end_time) > t_d(start_time) or t_d(end_time) > t_d(w_start_time):
                return True

        return False

    def can_assign_order(self, order):
        """Может ли курьер забрать заказ 

        Args:
            order (Order): свободный заказ

        Returns:
            bool: удобно ли забрать заказ:
            зависит от грузоподъемности, региона и удобности времени
        """

        return (
            order.weight <= self.lifting_capacity and
            order.region.id in [r.id for r in self.regions.all()] and
            any([self.is_handy_time(time) for time in order.delivery_hours_list])
        )

    def to_json(self, fields=None):
        """Преобразование в json

        Args:
            fields (list[str]): Какие поля нужно включить

        Returns:
            dict: сериализованный объект
        """

        if not fields:
            fields = ['courier_id', 'courier_type', 'regions', 'working_hours']
        
        if 'working_hours' in fields:
            fields[fields.index('working_hours')] = 'working_hours_list'

        data = {}

        for field in fields:
            if not hasattr(self, field):
                return

            if field == 'regions':
                data[field] = [r.id for r in self.regions.all()]
                continue

            data[field] = getattr(self, field)

        if 'working_hours_list' in data:
            data['working_hours'] = data.pop('working_hours_list')

        return data

    @staticmethod
    def from_json(data):
        """Получение объекта из json

        Args:
            data (dict): описание объекта в формате json

        Returns:
            dict: ошибки, если не прошло валидацию
            Courier: не сохраненный объект курьера
        """

        problems = {}
        fields = ['courier_id', 'courier_type', 'working_hours']

        courier = Courier()

        for field in fields:
            if not field in data:
                problems[field] = {
                    'code': 1,
                    'description': courier.VALIDATION_ERRORS[1]
                }

        if problems:
            return problems

        methods = courier.get_setters_by_field(fields).values()

        for method, field in zip(methods, fields):
            c = method(data[field])

            if c != 0:
                problems[field] = {
                    'code': c,
                    'description': courier.VALIDATION_ERRORS[c]
                }

        if problems:
            return problems

        courier.save()

        if not data.get('regions'):
            problems['regions'] = {
                'code': 1,
                'description': courier.VALIDATION_ERRORS[1]
            }
            return problems

        if courier.set_regions(data.get('regions')) != 0:
            problems['regions'] = {
                'code': 3,
                'description': courier.VALIDATION_ERRORS[3]
            }
            return problems

        courier.save()

        return courier

    def patch(self, params):
        """Внесение изменений в объекте

        При редактировании следует учесть случаи, когда меняется график 
        и уменьшается грузоподъемность и появляются заказы,
        которые курьер уже не сможет развести — такие заказы должны сниматься 
        и быть доступными для выдачи другим курьерам.

        Args:
            params (dict): новые параметры

        Returns:
            dict: ошибки, если возникла ошибка
            Courier: сохраненный, измененный курьер
        """

        problems = {}

        field_setters = self.get_setters_by_field(params.keys())

        for field, value in params.items():
            c = field_setters[field](value)

            if c != 0:
                problems[field] = {
                    'code': c,
                    'description': self.VALIDATION_ERRORS[c]
                }

        if problems:
            return problems

        for order in Order.objects.filter(courier=self, complete_time__isnull=True):
            if not self.can_assign_order(order):
                order.courier = None
                order.assign_time = None
                order.save()

        self.save()

        return self

    def order_completed(self):
        """ Закончил заказ. Обновляем статистику """
        
        self.set_earning()
        self.set_rating()
        self.save()

    def get_setters_by_field(self, fields):
        """Получение словаря сеттеров, по названиям атрибутов

        Args:
            fields (list[str]): список атрибутов

        Returns:
            dict: ключи - названия атрибутов, значения - методы сеттеров  
        """

        field_set = {
            'courier_id': self.set_id,
            'courier_type': self.set_courier_type,
            'regions': self.set_regions,
            'working_hours': self.set_working_hours,
        }

        return {field: field_set[field] for field in fields}

    def set_id(self, new_id):
        """ Изменение id 

        Args:
            new_id (int): новый id
        Returns: 
            None, если некорректно
            0, если корректно
            <int:id>, если вызвалась ошибка
        """

        if not Courier.objects.filter(id=new_id).first():
            self.id = new_id
            return 0

        return 3

    def set_courier_type(self, courier_type):
        """ Изменение типа курьера
        
        Args:
            courier_type (str): тип курьера
        Returns: 
            None, если некорректно
            0, если корректно
            <int:id>, если вызвалась ошибка
        """

        if courier_type in dict(self.COURIER_TYPES):
            self.courier_type = courier_type
            return 0

        return 2

    def set_regions(self, regions):
        """ Изменение регионов работы
        
        Args:
            regions (list[int]): id регионов работы
        Returns: 
            None, если некорректно
            0, если корректно
            <int:id>, если вызвалась ошибка
        """
        self.regions.clear()

        for region_id in regions:
            if Region.objects.filter(id=region_id).first():
                region = Region.objects.get(id=region_id)
                self.regions.add(region)
            else:
                return 1
                
        return 0

    def set_working_hours(self, working_hours):
        """ Изменение рабочих часов
        
        Args:
            working_hours (list[str]): список рабочих времени
        Returns: 
            None, если некорректно
            0, если корректно
            <int:id>, если вызвалась ошибка
        """

        self.working_hours = ';'.join(working_hours)
        return 0