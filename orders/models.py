import datetime

from django.utils.dateparse import parse_datetime
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

    def __str__(self):
        return "order %d" % self.id

    @property
    def delivery_time_in_seconds(self):
        if self.complete_time:
            return self.get_delivery_time().total_seconds()

    @property
    def delivery_hours_list(self):
        return self.delivery_hours.split(';')
        
    def get_delivery_time(self):
        if self.complete_time:
            return self.complete_time - self.assign_time

    def get_region(self):
        return self.order.region

    @staticmethod
    def from_json(data):
        fields = ['order_id', 'weight', 'region', 'delivery_hours']

        order = Order()

        for field in fields:
            if not field in data:
                return

        methods = [
            order.set_id, 
            order.set_weight, 
            order.set_region,
            order.set_delivery_hours]

        for method, field in zip(methods, fields):
            if method(data[field]) != 1:
                return

        order.save()

        return order

    def set_id(self, new_id):
        if not Order.objects.filter(id=new_id).first():
            self.id = new_id
            return 1

    def set_weight(self, weight):
        if weight > 0:
            self.weight = weight
            return 1

    def set_region(self, region_id):
        r = Region.objects.filter(id=region_id).first()

        if r:
            self.region = r
            return 1

    def set_delivery_hours(self, delivery_hours):
        self.delivery_hours = ';'.join(delivery_hours)
        return 1

    def set_assign_time(self, assign_time):
        self.assign_time = assign_time

    def set_courier(self, courier):
        self.courier = courier

    def assign(self, courier, assign_time):
        self.set_courier(courier)
        self.set_assign_time(assign_time)

    def complete(self, courier_id, complete_time_str):
        if not (self.courier or self.courier.id == courier_id):
            return
        
        self.complete_time = parse_datetime(complete_time_str)

        return self
