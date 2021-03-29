import json

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404
from django.http import JsonResponse

from couriers.models import Courier


def generate_objects_by_id(key, ids_list, problems=None):
    values = [{'id': i} for i in ids_list]

    if problems:
        for d in values:
            d['errors'] = problems[d['id']]

    return {
        key: values
    }
    

@csrf_exempt
def couriers(request):
    if request.method == 'POST':
        problems = {}
        invalid_ids = []
        couriers = []

        for data in request.POST.getlist('data'):
            courier_json = eval(data)

            courier = Courier.from_json(courier_json)

            if not isinstance(courier, Courier):
                invalid_ids.append(courier_json['courier_id'])
                problems[courier_json['courier_id']] = courier

            couriers.append(courier)

        if invalid_ids:
            return JsonResponse(
                {
                    'validation_error': 
                            generate_objects_by_id('couriers', invalid_ids, problems)
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


@csrf_exempt
def courier_view(request, courier_id):
    data = {}
    courier = Courier.objects.filter(id=courier_id).first()

    if not courier:
        return JsonResponse({"error": 0}, status=400)

    if request.method == "PATCH":
        body_unicode = request.body.decode('utf-8')
        body = eval(body_unicode)

        courier = courier.patch(body)

        if isinstance(courier, Courier):
            return JsonResponse(courier.to_json(), status=200)

        return JsonResponse(
            courier,
            status=400
        )

    if courier:
        data = courier.to_json(
            fields=['courier_id', 'courier_type', 'regions', 'working_hours', 'rating', 'earnings']
        )

    return JsonResponse(data, safe=True)