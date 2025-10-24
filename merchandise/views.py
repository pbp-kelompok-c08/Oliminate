from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from merchandise.forms import MerchandiseForm
from merchandise.models import Merchandise, Cart, CartItem

def is_organizer(user):
    return getattr(user, 'role', '').upper() == 'ORGANIZER'

def is_regular_user(user):
    return getattr(user, 'role', '').upper() == 'USER'

def merchandise_list(request):
    merchandises = Merchandise.objects.all()
    context = {'merchandises': merchandises}
    return render(request, "merchandise_list.html", context)

def merchandise_detail(request, id):
    merchandise = get_object_or_404(Merchandise, pk=id)
    context = {'merchandise': merchandise}
    
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    template_name = "merchandise_detail.html"
    if is_ajax:
        template_name = "merchandise_detail_fragment.html"
        
    return render(request, template_name, context)

@login_required
@user_passes_test(is_organizer)
def merchandise_create(request):
    form = MerchandiseForm(request.POST or None, request.FILES or None)
    
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if form.is_valid() and request.method == "POST":
        merchandise = form.save(commit=False)
        merchandise.organizer = request.user
        merchandise.save()
        
        if is_ajax:
            return JsonResponse({'success': True, 'merchandise_id': merchandise.id})
        
        return redirect('merchandise:merchandise_list')
    
    context = {
        'form': form,
        'title': 'Tambah Merchandise'
    }

    template_name = "merchandise_form.html"
    if is_ajax:
        template_name = "merchandise_form_fragment.html"

    return render(request, template_name, context)

@login_required
@user_passes_test(is_organizer)
def merchandise_update(request, id):
    merchandise = get_object_or_404(Merchandise, pk=id, organizer=request.user)
    form = MerchandiseForm(request.POST or None, request.FILES or None, instance=merchandise)
    
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if form.is_valid() and request.method == "POST":
        form.save()
        
        if is_ajax:
            return JsonResponse({'success': True, 'merchandise_id': merchandise.id})
        
        return redirect('merchandise:merchandise_list')
    
    context = {
        'form': form,
        'title': f'Edit {merchandise.name}'
    }

    template_name = "merchandise_form.html"
    if is_ajax:
        template_name = "merchandise_form_fragment.html"

    return render(request, template_name, context)

@login_required
@user_passes_test(is_organizer)
def merchandise_delete(request, id):
    merchandise = get_object_or_404(Merchandise, pk=id, organizer=request.user)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        merchandise_name = merchandise.name 
        merchandise.delete()
        
        if is_ajax:
            return JsonResponse({
                'success': True, 
                'message': f"Merchandise '{merchandise_name}' berhasil dihapus."
            })
        
        return redirect('merchandise:merchandise_list')

    context = {'merchandise': merchandise}
    return render(request, "merchandise_confirm_delete.html", context)

@login_required
@user_passes_test(is_regular_user)
def cart_detail(request):
    cart, _ = Cart.objects.get_or_create(user=request.user, status='open')
    items = list(cart.items.select_related('merchandise').all())
    any_overstock = any(item.quantity > item.merchandise.stock for item in items)
    context = {
        'cart': cart,
        'any_overstock': any_overstock
    }
    return render(request, "cart_detail.html", context)

@login_required
@user_passes_test(is_regular_user)
def cart_add_item(request, merchandise_id):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('merchandise:merchandise_detail', args=[merchandise_id]))

    merchandise = get_object_or_404(Merchandise, pk=merchandise_id)
    quantity = int(request.POST.get('quantity', 1))
    if quantity < 1:
        quantity = 1

    cart, _ = Cart.objects.get_or_create(user=request.user, status='open')

    item, created = CartItem.objects.get_or_create(cart=cart, merchandise=merchandise, defaults={'quantity': quantity})
    if not created:
        item.quantity += quantity
        item.save()

    return redirect('merchandise:cart_detail')

@login_required
@user_passes_test(is_regular_user)
def cart_update_item(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    if request.method == 'POST':
        qty = int(request.POST.get('quantity', item.quantity))
        if qty <= 0:
            item.delete()
        else:
            item.quantity = qty
            item.save()
    return redirect('merchandise:cart_detail')

@login_required
@user_passes_test(is_regular_user)
def cart_remove_item(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    if request.method == 'POST':
        item.delete()
    return redirect('merchandise:cart_detail')

@login_required
@user_passes_test(is_regular_user)
def cart_checkout(request):
    cart = get_object_or_404(Cart, user=request.user, status='open')
    if cart.items.count() == 0:
        return redirect('merchandise:cart_detail')

    cart.status = 'checked_out'
    cart.save()
    return cart_pay(request, cart.id)

@login_required
@user_passes_test(is_regular_user)
def cart_pay(request, cart_id):
    cart = get_object_or_404(Cart, pk=cart_id, user=request.user, status='checked_out')

    with transaction.atomic():
        for item in cart.items.select_related('merchandise').all():
            m = item.merchandise
            m.stock -= item.quantity
            if m.stock < 0:
                raise ValueError("Negative stock detected")
            m.save()

        cart.status = 'paid'
        cart.save()

    return render(request, "cart_paid.html", {'cart': cart})