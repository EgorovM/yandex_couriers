import datetime

from django.http import JsonResponse
from django.utils import timezone

from couriers.models import Courier, Order, Region


def generate_objects_by_id(key, ids_list):
    return {
        key: [{'id': i} for i in ids_list]
    }


def orders(request):
    if request.method == "POST":
        error = False
        invalid_ids = []
        orders = []

        for data in request.POST.getlist('data'):
            data = eval(data)
            order = Order.from_json(data)

            if not order:
                error = True
                invalid_ids.append(data['order_id'])

            orders.append(order)

        if error:
            return JsonResponse({
                    'validation_error': generate_objects_by_id('orders', invalid_ids)
                },
                status=400)

        for order in orders:
            order.save()
        
        return JsonResponse(
            generate_objects_by_id('orders', [o.id for o in orders]),
            status=201)

    return JsonResponse({})


def assign(request):
    courier_id = request.POST['courier_id']

    courier = Courier.objects.filter(id=courier_id).first()

    if not courier:
        return JsonResponse({}, status=400)

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
    

def complete(request):
    if request.method == "POST":
        courier_id = request.POST['courier_id']
        order_id = request.POST['order_id']
        complete_time = request.POST['complete_time']

        order = Order.objects.filter(id=order_id).first()

        if not (order and order.courier and order.complete(courier_id, complete_time)):
            return JsonResponse({}, status=400)

        order.save()

        return JsonResponse({'order_id': order.id})
            
    return JsonResponse({}, status=200)