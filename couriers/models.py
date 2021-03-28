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


    @property
    def courier_id(self):
        return self.id

    @property
    def lifting_capacity(self):
        return self.LIFTION_CAPACITY[self.courier_type]

    @property
    def get_regions(self):
        return [r.id for r in self.regions.all()]

    @property
    def working_hours_list(self):
        return self.working_hours.split(';')

    def __str__(self):
        return "courier %s" % self.id

    def set_rating(self):
        orders = self.get_completed_orders()

        regions = defaultdict(lambda: [0, 0])

        for order in orders:
            region_id = order.get_region().id

            regions[region_id][0] += order.delivery_time_in_seconds
            regions[region_id][1] += 1

        min_t = min(map(lambda x: x[1] / x[0], regions.values()))

        self.rating =  (60 * 60 - min(min_t, 60 * 60)) / (60*60) * 5 
        
    def set_earning(self):
        orders = self.get_completed_orders()

        self.earning = len(orders) * 500 * self.get_earning_coef()

    def get_completed_orders(self):
        return (Order.objects
                    .filter(completed_by=self, complete_time__isnull=False))

    def get_earning_coef(self):
        return self.COEF_BY_TYPE[self.courier_type]

    def is_handy_time(self, time):
        def t_d(time):
            return datetime.datetime.strptime(time, '%H:%M')

        start_time, end_time = time.split('-')

        for working_hour in self.working_hours_list:
            w_start_time, w_end_time = working_hour.split('-')

            if t_d(w_end_time) > t_d(start_time) or t_d(end_time) > t_d(w_start_time):
                return True

        return False

    def can_assign_order(self, order):
        return (
            order.weight <= self.lifting_capacity and
            order.region.id in [r.id for r in self.regions.all()] and
            any([self.is_handy_time(time) for time in order.delivery_hours_list])
        )

    def to_json(self, fields=None):
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
        fields = ['courier_id', 'courier_type', 'working_hours']

        courier = Courier()

        for field in fields:
            if not field in data:
                return

        methods = [
            courier.set_id, 
            courier.set_courier_type, 
            courier.set_working_hours]

        for method, field in zip(methods, fields):
            if method(data[field]) != 1:
                return

        courier.save()

        if not data.get('regions'):
            return

        if not courier.set_regions(data.get('regions')):
            return

        courier.save()

        return courier

    def patch(self, params):
        """
        При редактировании следует учесть случаи, когда меняется график 
        и уменьшается грузоподъемность и появляются заказы,
        которые курьер уже не сможет развести — такие заказы должны сниматься 
        и быть доступными для выдачи другим курьерам.
        """ 
        field_setters = self.get_setters_by_field(params.keys())

        for field, value in params.items():
            if not field_setters[field](value):
                return

        self.save()

    def get_setters_by_field(self, fields):
        field_set = {
            'courier_id': self.set_id,
            'courier_type': self.set_courier_type,
            'regions': self.set_regions,
            'working_hours': self.set_working_hours,
        }

        return {field: field_set[field] for field in fields}

    def set_id(self, new_id):
        if not Courier.objects.filter(id=new_id).first():
            self.id = new_id
            return 1

    def set_courier_type(self, courier_type):
        if courier_type in dict(self.COURIER_TYPES):
            self.courier_type = courier_type
            return 1

    def set_regions(self, regions):
        self.regions.clear()

        for region_id in regions:
            if Region.objects.filter(id=region_id).first():
                region = Region.objects.get(id=region_id)
                self.regions.add(region)
            else:
                return
                
        return 1

    def set_working_hours(self, working_hours):
        self.working_hours = ';'.join(working_hours)
        return 1