import datetime

from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.test import TestCase
from django.test import Client

from couriers.models import Courier, Order, Region


class OrderTest(TestCase):
    def setUp(self):
        r1 = Region.objects.create(
            name='Фрунзенская'
        )

        r2 = Region.objects.create(
            name='Центральная'
        )

        c = Courier.objects.create(
            courier_type='foot',
            working_hours='07:00-12:00'
        )

        c.regions.add(r1)
        c.save()

        Order.objects.create(
            weight=0.23,
            region=r1,
            delivery_hours="08:00-09:00",
        )

        o = Order.objects.create(
            weight=0.23,
            region=r2,
            delivery_hours="08:00-09:00",
        )

        o.assign(c, parse_datetime("2021-01-10T8:33:01.42Z"))
        o.save()


    def test_order_post_true(self):
        c = Client()
        body = {
            "data": [
                {
                    "order_id": 5,
                    "weight": 0.23,
                    "region": 1,
                    "delivery_hours": ["09:00-18:00"]
                },
                {
                    "order_id": 3,
                    "weight": 15,
                    "region": 1,
                    "delivery_hours": ["09:00-18:00"]
                },
                {
                    "order_id": 4,
                    "weight": 0.01,
                    "region": 2,
                    "delivery_hours": ["09:00-12:00", "16:00-21:30"]
                }
            ]
        }

        response = c.post('/orders/', body)

        self.assertEqual(response.status_code, 201)
        self.assertDictEqual(eval(response.content),
            {'orders': [{'id': 5}, {'id': 3}, {'id': 4}]}
        )

    def test_order_post_false(self):
        c = Client()
        body = {
            "data": [
                {
                    "order_id": 1,
                    "weight": 0.23,
                    "region": 1,
                    "delivery_hours": ["09:00-18:00"]
                },
                {
                    "order_id": 4,
                    "weight": -2,
                    "region": 1,
                    "delivery_hours": ["09:00-18:00"]
                },
                {
                    "order_id": 5,
                    "weight": 0.01,
                    "region": 3,
                    "delivery_hours": ["09:00-12:00", "16:00-21:30"]
                }
            ]
        }

        response = c.post('/orders/', body)

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(eval(response.content), {
            'validation_error': 
                {'orders': [
                    {
                        'id': 1, 
                        'errors': {
                            'order_id': {
                                'code': 3,
                                'description': 'Некорректный идентификатор'
                            }
                        }
                    }, 
                    {
                        'id': 4,
                        'errors': {
                            'weight': {
                                'code': 2,
                                'description': 'Не соответствует формату'
                            }
                        }
                    }, 
                    {
                        'id': 5,
                        'errors': {
                            'region': {
                                'code': 3,
                                'description': 'Некорректный идентификатор' 
                            }
                        }
                    }]
                }
            }
        )

    def test_order_assing_to_courier(self):
        c = Client()

        body = {
            'courier_id': 1
        }

        response = c.post('/orders/assign/', body)

        order = Order.objects.get(id=1)
        courier = Courier.objects.get(id=1)

        self.assertEqual(response.status_code, 200)
        self.assertEquals(eval(response.content)['orders'], [{'id': 1}])
        self.assertTrue(
            'assign_time' in eval(response.content)
        )
        self.assertEqual(
            order.courier,
            courier
        )

    def test_order_complete_true(self):
        c = Client()

        body = {
            "courier_id": 1,
            "order_id": 2,
            "complete_time": "2021-01-10T10:33:01.42Z"
        }

        response = c.post('/orders/complete/', body)

        self.assertEqual(response.status_code, 200)
        self.assertEquals(eval(response.content), {
            'order_id': 2
        })

    def test_order_complete_false(self):
        c = Client()

        body = {
            "courier_id": 1,
            "order_id": 1,
            "complete_time": "2021-01-10T10:33:01.42Z"
        }

        response = c.post('/orders/complete/', body)

        self.assertEqual(response.status_code, 400)

    def test_courier_statistic(self):
        c = Client()

        body = {
            "courier_id": 1,
            "order_id": 2,
            "complete_time": "2021-01-10T8:40:02.42Z"
        }

        response = c.post('/orders/complete/', body)

        self.assertEqual(response.status_code, 200)
        self.assertEquals(eval(response.content), {
            'order_id': 2
        })

        response = c.get('/couriers/1/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(eval(response.content), {
            "courier_id": 1, 
            "courier_type": "foot", 
            "regions": [1], 
            "rating": "4.42", 
            "earnings": 1000, 
            "working_hours": ["07:00-12:00"]
        })
    
    def test_courier_earning_depends_type(self):
        c = Courier.objects.get(id=1)
        r = Region.objects.get(id=1)

        o = Order.objects.create(
            weight=0.23,
            region=r,
            delivery_hours="08:00-09:00",
        )

        o.assign(c, parse_datetime("2021-01-10T8:33:01.42Z"))
        o.save()
        o.complete(c.id, parse_datetime("2021-01-10T8:46:01.42Z"))

        self.assertEqual(c.earnings, 1000)

        c.patch({'courier_type': 'car'})

        o = Order.objects.create(
            weight=0.23,
            region=r,
            delivery_hours="08:00-09:00",
        )

        o.assign(c, parse_datetime("2021-01-10T8:48:01.42Z"))
        o.save()
        o.complete(c.id, parse_datetime("2021-01-10T8:59:01.42Z"))

        self.assertEqual(c.earnings, 5500)

    def test_courier_rating_depends_orders(self):
        c = Courier.objects.get(id=1)
        r = Region.objects.get(id=1)

        o = Order.objects.create(
            weight=0.23,
            region=r,
            delivery_hours="08:00-09:00",
        )

        o.assign(c, parse_datetime("2021-01-10T8:33:01.42Z"))
        o.save()
        o.complete(c.id, parse_datetime("2021-01-10T8:46:01.42Z"))

        self.assertEqual(c.rating, 3.92)

        c.patch({'courier_type': 'car'})

        o = Order.objects.create(
            weight=0.23,
            region=r,
            delivery_hours="08:00-09:00",
        )

        o.assign(c, parse_datetime("2021-01-10T8:48:01.42Z"))
        o.save()
        o.complete(c.id, parse_datetime("2021-01-10T8:59:01.42Z"))

        self.assertEqual(c.rating, 4.38)
        
