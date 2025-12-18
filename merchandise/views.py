from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from merchandise.forms import MerchandiseForm
from merchandise.models import Merchandise, Cart, CartItem
from django.utils.html import strip_tags
import requests
import json

def is_organizer(user):
    return getattr(user, 'role', '').upper() == 'ORGANIZER'

def is_regular_user(user):
    return getattr(user, 'role', '').upper() == 'USER'

def merchandise_list(request):
    merchandises = Merchandise.objects.all()

    category_filter = request.GET.get('category')
    if category_filter:
        merchandises = merchandises.filter(category=category_filter)

    sort_by = request.GET.get('sort_by')
    if sort_by == 'price_asc':
        merchandises = merchandises.order_by('price', 'name')
    elif sort_by == 'price_desc':
        merchandises = merchandises.order_by('-price', 'name')
    else:
        merchandises = merchandises.order_by('name', 'price')

    context = {
        'merchandises': merchandises,
        'current_sort': sort_by,
        'current_category': category_filter,
        'category_choices': Merchandise.CATEGORY_CHOICES 
    }
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

def merchandise_list_flutter(request):
    """
    Returns a JSON response of the merchandise list for mobile apps.
    Supports filtering by 'category' and sorting by 'sort_by'.
    """
    merchandises = Merchandise.objects.all()

    # 1. Handle Filtering by Category
    category_filter = request.GET.get('category')
    if category_filter and category_filter != '':
        merchandises = merchandises.filter(category=category_filter)

    # 2. Handle Sorting
    sort_by = request.GET.get('sort_by')
    if sort_by == 'price_asc':
        merchandises = merchandises.order_by('price', 'name')
    elif sort_by == 'price_desc':
        merchandises = merchandises.order_by('-price', 'name')
    else:
        merchandises = merchandises.order_by('name', 'price')

    # 3. Serialize data manually
    merchandise_data = []
    for merch in merchandises:
        merchandise_data.append({
            'id': str(merch.id),
            'name': merch.name,
            'category': merch.category,
            'price': merch.price,
            'stock': merch.stock,
            'description': merch.description,
            'image_url': merch.image_url,
            'organizer_username': merch.organizer.username if merch.organizer else 'N/A',
        })

    # 4. Return JSON response
    return JsonResponse({
        'merchandises': merchandise_data,
        'category_choices': list(Merchandise.CATEGORY_CHOICES),
        'current_category': category_filter,
        'current_sort': sort_by,
    })

@csrf_exempt
def merchandise_create_flutter(request):
    if request.method == 'POST':
        data = request.POST
        name = strip_tags(data.get("name", ""))  # Strip HTML tags
        category = data.get("category", "")
        price = int(data.get("price", 0))
        stock = int(data.get("stock", 0))
        description = strip_tags(data.get("description", ""))  # Strip HTML tags
        image_url = data.get("image_url", "")
        user = request.user
        
        new_merchandise = Merchandise(
            name=name, 
            category=category,
            price=price,
            stock=stock,
            description=description,
            image_url=image_url,
            organizer=user
        )
        new_merchandise.save()
        
        return JsonResponse({"status": "success"}, status=200)
    else:
        return JsonResponse({"status": "error"}, status=401)

@csrf_exempt
def merchandise_update_flutter(request, id): # Note the primary key (pk) argument
    merchandise = get_object_or_404(Merchandise, pk=id)
    
    if request.method == 'POST':
        # Use request.POST to handle form-encoded data
        data = request.POST 
        
        try:
            # 1. Type Conversion and Validation (similar to your create view)
            price = int(data.get("price", 0)) 
            stock = int(data.get("stock", 0))
        except ValueError:
             return JsonResponse({"status": "error", "message": "Price/Stock must be numbers."}, status=400)
             
        # 2. Update the model instance fields
        merchandise.name = data.get("name", merchandise.name)
        merchandise.category = data.get("category", merchandise.category)
        merchandise.price = price
        merchandise.stock = stock
        merchandise.description = data.get("description", merchandise.description)
        merchandise.image_url = data.get("image_url", merchandise.image_url)
        
        # 3. Save the changes
        merchandise.save()
        
        return JsonResponse({"status": "success", "message": "Merchandise updated successfully."}, status=200)

    return JsonResponse({"status": "error", "message": "Method not allowed."}, status=405)

@csrf_exempt 
def merchandise_delete_flutter(request, id):
    """
    Handles the deletion of a specific Merchandise item identified by pk (primary key).
    Requires the user to be logged in and have the 'organizer' role,
    and must be the owner of the merchandise.
    """
    
    # 1. Require POST method for safe deletion
    if request.method != 'POST':
        # Flutter client code uses .get(), so you may temporarily allow GET
        # for debugging, but POST is strongly recommended for deletion.
        # If the Flutter code is using _authRepo.client.get(url), 
        # change the client code to use postForm or postJson, or change this check.
        # For now, let's keep it POST for best practice:
        return JsonResponse({"status": "error", "message": "Method not allowed. Use POST."}, status=405)

    # 2. Check Authentication
    if not request.user.is_authenticated:
        return JsonResponse({"status": "error", "message": "Authentication required."}, status=401)
        
    # 3. Retrieve the Merchandise object
    try:
        merchandise = Merchandise.objects.get(pk=id)
    except Merchandise.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Merchandise not found."}, status=404)

    # 4. Check Authorization (Role and Ownership)
    # Ensure the user has the 'organizer' role and owns the merchandise
    user_role = getattr(request.user, 'role', '').lower().strip()
    
    # NOTE: Assuming your User model has a 'role' field and the Merchandise model 
    # links to the user via a 'user' ForeignKey field (or similar, like 'owner').
    # I will assume the Merchandise model field is named 'user' for simplicity here.
    
    is_organizer = user_role == 'organizer'
    is_owner = merchandise.organizer == request.user # Check ownership
    
    if not is_organizer or not is_owner:
        return JsonResponse({"status": "error", "message": "You are not authorized to delete this item."}, status=403)

    # 5. Perform Deletion
    try:
        merchandise.delete()
        return JsonResponse({"status": "success", "message": f"Merchandise '{merchandise.name}' deleted successfully."}, status=200)
    except Exception as e:
        # Catch database errors during deletion
        return JsonResponse({"status": "error", "message": f"An error occurred during deletion: {e}"}, status=500)

def proxy_image(request):
    image_url = request.GET.get('url')
    if not image_url:
        return HttpResponse('No URL provided', status=400)
    
    try:
        # Fetch image from external source
        # print(image_url)
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        # Return the image with proper content type
        return HttpResponse(
            response.content,
            content_type=response.headers.get('Content-Type', 'image/jpeg')
        )
    except requests.RequestException as e:
        return HttpResponse(f'Error fetching image: {str(e)}', status=500)
    
@csrf_exempt
def cart_detail_api(request):
    cart, created = Cart.objects.get_or_create(user=request.user, status='open')
    
    cart_items = []
    for item in cart.items.select_related('merchandise').all():
        cart_items.append({
            'id': str(item.id),
            'merchandise_id': str(item.merchandise.id),
            'merchandise_name': item.merchandise.name,
            'merchandise_price': item.merchandise.price,
            'merchandise_image': item.merchandise.image_url,
            'quantity': item.quantity,
            'subtotal': item.subtotal, # Ensure subtotal() is available on the model or calculate it here
            'stock': item.merchandise.stock,
        })

    return JsonResponse({
        'cart_id': str(cart.id),
        'total_price': cart.total_price(),
        'items': cart_items,
    })

@csrf_exempt 
def cart_add_item_api(request, merchandise_id):
    merchandise = get_object_or_404(Merchandise, pk=merchandise_id)
    cart, created = Cart.objects.get_or_create(user=request.user, status='open')
    
    if request.method == 'POST':
        # Try to read JSON body for Flutter/API requests
        try:
            data = json.loads(request.body)
            quantity = data.get('quantity', 1)
            quantity = int(quantity)
        except (json.JSONDecodeError, TypeError):
            # Fallback to POST data for traditional requests
            quantity = int(request.POST.get('quantity', 1))

        if quantity > 0:
            item, created = CartItem.objects.get_or_create(
                cart=cart,
                merchandise=merchandise,
                defaults={'quantity': quantity}
            )
            if not created:
                item.quantity += quantity
                item.save()
            return JsonResponse({'success': True, 'message': f'{merchandise.name} added to cart'}, status=200)

    # For any other method or failed POST, you might want to return an error JSON response
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

@csrf_exempt
def cart_update_item_api(request, item_id):
    """
    Updates the quantity of a specific CartItem.
    Endpoint: /merchandise/cart/item/<uuid:item_id>/update/
    """
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Method not allowed. Use POST."}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({"status": "error", "message": "Authentication required."}, status=401)
    
    # Flutter client sends data in the POST body
    if 'quantity' not in request.POST:
        return JsonResponse({"status": "error", "message": "Missing 'quantity' in form data."}, status=400)
    
    try:
        new_quantity = int(request.POST.get('quantity'))
    except ValueError:
        return JsonResponse({"status": "error", "message": "Invalid quantity value."}, status=400)
    
    # 1. Retrieve the CartItem and ensure it belongs to the current user
    try:
        cart_item = CartItem.objects.get(pk=item_id, cart__user=request.user)
    except CartItem.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Cart item not found or access denied."}, status=404)

    merchandise = cart_item.merchandise
    
    # 2. Check for stock availability
    if new_quantity > merchandise.stock:
        return JsonResponse({
            "status": "error", 
            "message": f"Insufficient stock. Only {merchandise.stock} units available."
        }, status=400)

    # 3. Update or Delete the item
    if new_quantity <= 0:
        cart_item.delete()
        return JsonResponse({"status": "success", "message": "Item removed from cart."}, status=200)
    else:
        cart_item.quantity = new_quantity
        cart_item.save()
        return JsonResponse({"status": "success", "message": "Item quantity updated."}, status=200)


@csrf_exempt
def cart_delete_item_api(request, item_id):
    """
    Removes a specific item from the user's cart.
    Endpoint: /merchandise/cart/item/<uuid:item_id>/remove/
    """
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Method not allowed. Use POST."}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({"status": "error", "message": "Authentication required."}, status=401)
    
    # 1. Retrieve and Delete the CartItem, ensuring ownership
    try:
        cart_item = CartItem.objects.get(pk=item_id, cart__user=request.user)
        cart_item.delete()
        return JsonResponse({"status": "success", "message": "Item successfully removed from cart."}, status=200)
    except CartItem.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Cart item not found or does not belong to user."}, status=404)


@csrf_exempt
def cart_checkout_api(request):
    """
    Finalizes the purchase process (checkout).
    Endpoint: /merchandise/cart/checkout/
    """
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Method not allowed. Use POST."}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({"status": "error", "message": "Authentication required."}, status=401)
    
    # Use a database transaction to ensure atomicity (all or nothing)
    try:
        with transaction.atomic():
            cart, created = Cart.objects.get_or_create(user=request.user, status='open')
            # Assuming CartItem has a reverse relation 'cartitem_set'
            cart_items = cart.items.select_related('merchandise').all()

            if not cart_items.exists():
                return JsonResponse({"status": "error", "message": "Your cart is empty."}, status=400)

            # 1. Final Stock Check and Reservation
            for item in cart_items:
                merch = item.merchandise
                # Lock the Merchandise row for the transaction
                merch_to_update = Merchandise.objects.select_for_update().get(pk=merch.pk)
                
                if item.quantity > merch_to_update.stock:
                    # If stock runs out, raise an error to stop the transaction
                    raise ValueError(f"Insufficient stock for {merch.name}. Only {merch_to_update.stock} available.")
            
            # 2. Process Order and Update Stock
            # NOTE: You need to implement your Order/Transaction model here
            # new_order = Order.objects.create(user=request.user, total=..., status='pending')
            
            for item in cart_items:
                merch = item.merchandise
                # Decrease stock
                merch.stock -= item.quantity
                merch.save()
                
                # Link cart item to the new order (if applicable)
                # OrderItem.objects.create(order=new_order, merchandise=merch, quantity=item.quantity, price=item.merchandisePrice)


            # --- CRITICAL CHANGE FOR FORMALITY ---
            # Mark the current active cart as finalized (simulating order creation/payment)
            cart.status = 'paid' # Assuming your Cart model has a 'paid' or 'closed' status
            cart.save()
            
            # The next time the user tries to buy something, _get_user_cart will create a NEW cart.
            
            item_details = []
            total_price = 0
            for item in cart_items:
                item_details.append({
                    'name': item.merchandise.name,
                    'quantity': item.quantity,
                    # Assuming a CartItem method or property to calculate subtotal
                    'subtotal': item.subtotal, 
                    'price': item.merchandise.price,
                })
                total_price += item.subtotal

            return JsonResponse({
                "status": "success", 
                "message": "Checkout successful! Order created.",
                "order_id": str(cart.id), # Pass the ID of the completed cart back
                "created_at": cart.created_at.isoformat(), # Send the date as ISO string
                "total_price": total_price, # Assuming this method exists
                "items": item_details, # Send the list of ordered items
            }, status=200) # Use 200 OK for a successful API response

    except ValueError as ve:
        # Handled stock/validation errors
        return JsonResponse({"status": "error", "message": str(ve)}, status=400)
    except Exception as e:
        # Catch unexpected errors and roll back the transaction
        return JsonResponse({"status": "error", "message": f"An unexpected error occurred: {e}"}, status=500)