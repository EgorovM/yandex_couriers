import json
import datetime

from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
from django.http import JsonResponse
from django.utils import timezone

from couriers.models import Courier, Order, Region


def generate_objects_by_id(key, ids_list, problems=None):
    values = [{'id': i} for i in ids_list]

    if problems:
        for d in values:
            d['errors'] = problems[d['id']]

    return {
        key: values
    }


@csrf_exempt
def orders(request):
    if request.method == "POST":
        problems = {} 
        invalid_ids = []
        orders = []

        if not request.POST:
            data_list = json.loads(request.body)['data']
        else:
            data_list = [eval(d) for d in request.POST.getlist('data')]
        
        for order_data in data_list:
            order = Order.from_json(order_data)

            if not isinstance(order, Order):
                invalid_ids.append(order_data['order_id'])
                problems[order_data['order_id']] = order

            orders.append(order)

        if invalid_ids:
            return JsonResponse({
                    'validation_error': generate_objects_by_id('orders', invalid_ids, problems)
                },
                status=400)

        for order in orders:
            order.save()
        
        return JsonResponse(
            generate_objects_by_id('orders', [o.id for o in orders]),
            status=201)

    return JsonResponse({})


@csrf_exempt
def assign(request):
    if request.method == "GET":
        return JsonResponse({}, status=400)
    
    if not request.POST:
        data = json.loads(request.body)
    else:
        data = request.POST

    courier_id = data['courier_id']

    courier = Courier.objects.filter(id=courier_id).first()

    if not courier:
        return JsonResponse({'courier_id': {'code': 3, 'description': 'Некорректный id'}}, status=400)

    order_list = []

    for order in Order.objects.filter(assign_time__isnull=True):
        if courier.can_assign_order(order):
            order.set_courier(courier)
            order_list.append(order)

    if not order_list:
        return JsonResponse(
            {'orders': []},
            status=200
        )

    assign_time = timezone.now()

    for order in order_list:
        order.set_assign_time(assign_time)
        order.save()

    return JsonResponse({
        'orders': [{'id': o.id} for o in order_list],
        'assign_time': assign_time
    }, status=200)
    

@csrf_exempt
def complete(request):
    if request.method == "POST":
        print(request.POST)
        if not request.POST:
            data = json.loads(request.body)
        else:
            data = request.POST
        
        courier_id = data['courier_id']
        order_id = data['order_id']
        complete_time = parse_datetime(data['complete_time'])

        order = Order.objects.filter(id=order_id).first()

        if not (order and order.courier and order.complete(courier_id, complete_time)):
            return JsonResponse({}, status=400)

        order.save()

        return JsonResponse({'order_id': order.id})
            
    return JsonResponse({}, status=200)