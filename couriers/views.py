import json

from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404
from django.http import JsonResponse

from couriers.models import Courier


def generate_objects_by_id(key, ids_list):
    return {
        key: [{'id': i} for i in ids_list]
    }
    

def couriers(request):
    if request.method == 'POST':
        error = False
        invalid_ids = []
        couriers = []

        for data in request.POST.getlist('data'):
            courier_json = eval(data)

            courier = Courier.from_json(courier_json)

            if courier is None:
                error = True
                invalid_ids.append(courier_json['courier_id'])

            couriers.append(courier)

        if error:
            return JsonResponse(
                {
                    'validation_error': 
                            generate_objects_by_id('couriers', invalid_ids)
                },
                status=400
            )

        
        for c in couriers:
            c.save()

        return JsonResponse(
            generate_objects_by_id(
                'couriers', 
                [c.id for c in couriers]), 
            status=201)

    couriers = Courier.objects.all()

    return JsonResponse({
        'couriers': [c.to_json() for c in couriers]
    })


def courier_view(request, courier_id):
    data = {}
    courier = Courier.objects.filter(id=courier_id).first()

    if not courier:
        return JsonResponse({"error": 0}, code=400)

    if request.method == "PATCH":
        body_unicode = request.body.decode('utf-8')
        body = eval(body_unicode)

        courier.patch(body)

        return JsonResponse(courier.to_json())

    if courier:
        data = courier.to_json(
            fields=['courier_id', 'courier_type', 'regions', 'working_hours', 'rating', 'earnings']
        )

    return JsonResponse(data, safe=True)