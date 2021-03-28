import datetime

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

        Order.objects.create(
            weight=0.23,
            region=r1,
            delivery_hours="08:00-09:00",
        )

        o = Order.objects.create(
            weight=0.23,
            region=r1,
            delivery_hours="08:00-09:00",
        )

        c = Courier.objects.create(
            courier_type='foot',
            working_hours='07:00-12:00'
        )

        c.regions.add(r1)
        c.save()

        o.assign(c, timezone.now())
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
            'validation_error': {'orders': [{'id': 1}, {'id': 4}, {'id': 5}]}
        })

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