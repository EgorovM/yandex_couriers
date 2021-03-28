from django.test import TestCase
from django.test import Client

from couriers.models import Courier
from orders.models import Region, Order


class CourierTest(TestCase):
    def setUp(self):
        r1 = Region.objects.create(
            name='Фрунзенский'
        )
        r2 = Region.objects.create(
            name='Центральный'
        )

        c1 = Courier.objects.create(
            courier_type='foot',
            working_hours='09:00-10:00',
        )
        c1.regions.add(r1)
        c1.save()

        c2 = Courier.objects.create(
            courier_type='bike',
            working_hours='09:00-10:00',
        )
        c2.regions.add(r1)
        c2.regions.add(r2)
        c2.save()

        c3 = Courier.objects.create(
            courier_type='car',
            working_hours='09:00-10:00',
        )
        c3.regions.add(r2)
        c3.save()
    
    def test_courier_to_json(self):
        courier = Courier.objects.get(id=1)
        courier_json = courier.to_json()

        self.assertIsNotNone(courier_json)

        self.assertDictEqual(courier_json, {
            "courier_id": 1, 
            "courier_type": "foot", 
            "regions": [1], 
            "working_hours": ["09:00-10:00"]
        })

    def test_courier_from_json(self):
        courier_json = {
            "courier_id": 4, 
            "courier_type": "foot", 
            "regions": [1], 
            "working_hours": ["09:00-12:00"]
        }

        courier_from_json = Courier.from_json(courier_json)
        
        self.assertIsNotNone(courier_from_json)
        self.assertEqual(courier_from_json.to_json(), courier_json)

    def test_post_couriers_right(self):
        c = Client()
        body = {
            "data": [
                {
                    "courier_id": 4,
                    "courier_type": "foot",
                    "regions": [1,],
                    "working_hours": ["11:35-14:05", "09:00-11:00"]
                },
                {
                    "courier_id": 5,
                    "courier_type": "bike",
                    "regions": [1],
                    "working_hours": ["09:00-18:00"]
                },
                {
                    "courier_id": 6,
                    "courier_type": "car",
                    "regions": [1, 2],
                    "working_hours": []
                },
            ]
        }

        response = c.post('/couriers/', body)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(eval(response.content), {
            "couriers": [{"id": 4}, {"id": 5}, {"id": 6}]
        })

    def test_post_couriers_false(self):
        c = Client()
        body = {
            "data": [
                {
                    "courier_id": 4,
                    "courier_type": "foot",
                    "regions": [1, 12, 22],
                },
                {
                    "courier_id": 5,
                    "regions": [22],
                    "working_hours": ["09:00-18:00"]
                },
                {
                    "courier_id": 6,
                    "courier_type": "car",
                    "regions": [3],
                    "working_hours": []
                },
                {
                    "courier_id": 7,
                    "courier_type": "car",
                    "regions": [2],
                    "working_hours": []
                },
            ]
        }

        response = c.post('/couriers/', body)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(eval(response.content), {
            "validation_error": {
                "couriers": [{"id": 4}, {"id": 5}, {"id": 6}]
            }
        })

    def test_courier_patch(self):
        c = Client()

        body = {
            "regions": [1, 2],
            "courier_type": "car",
            "working_hours": ["11:35-14:05", "09:00-11:00"]
        }

        response = c.patch('/couriers/1', body)

        courier = Courier.objects.get(id=1)
        courier_json = courier.to_json(fields=['regions', 'courier_type'])

        #TODO: снятые заказы из-за изменения грузоподъемность

        self.assertEqual(response.status_code, 200)
        self.assertEqual(eval(response.content), {
            "courier_id": 1,
            "courier_type": "car",
            "regions": [1, 2],
            "working_hours": ["11:35-14:05", "09:00-11:00"]
        })

