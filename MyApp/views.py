from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import auth, messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from .models import Product, Order, OrderItem
import uuid


# -------------------------
# BASIC PAGES
# -------------------------

def index(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def menu(request):
    return render(request, 'menu.html')

def service(request):
    return render(request, 'service.html')

def team(request):
    return render(request, 'team.html')

def testimonial(request):
    return render(request, 'testimonial.html')


@login_required(login_url='login')
def order_success(request):
    return render(request, "order_success.html")


# -------------------------
# SHOP
# -------------------------

def shop(request):
    products = Product.objects.all()
    return render(request, "shop.html", {"products": products})


# -------------------------
# AUTH
# -------------------------

def login(request):
    next_url = request.GET.get("next", "/")

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = auth.authenticate(username=username, password=password)
        if user:
            auth.login(request, user)
            return redirect(request.POST.get("next", "/"))

        messages.error(request, "Invalid username or password!")
        return redirect(f'/login/?next={next_url}')

    return render(request, 'login.html', {"next": next_url})


def logout(request):
    auth.logout(request)
    return redirect('/')


def register(request):
    if request.method == 'POST':
        fn = request.POST['fname']
        ln = request.POST['lname']
        email = request.POST['email']
        username = request.POST['uname']
        p1 = request.POST['pass1']
        p2 = request.POST['pass2']

        if p1 != p2:
            messages.error(request, "Passwords do not match!")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return redirect('register')

        User.objects.create_user(
            first_name=fn,
            last_name=ln,
            email=email,
            username=username,
            password=p1
        )

        messages.success(request, "Account created successfully!")
        return redirect('login')

    return render(request, 'register.html')


# -------------------------
# CART (SESSION BASED)
# -------------------------

@login_required(login_url='login')
def add_to_cart(request, id):
    product = get_object_or_404(Product, id=id)
    quantity = int(request.POST.get('quantity', 1))

    if quantity < 1:
        messages.error(request, "Quantity must be at least 1.")
        return redirect('shop')

    cart = request.session.get('cart', {})

    if str(id) in cart:
        cart[str(id)]['quantity'] += quantity
    else:
        cart[str(id)] = {
            'price': str(product.price),
            'quantity': quantity
        }

    request.session['cart'] = cart
    messages.success(request, f"{product.name} added to cart.")
    return redirect('cart_detail')

@login_required(login_url='login')
def cart_detail(request):
    cart = request.session.get('cart', {})
    items = []
    total = Decimal('0.00')

    for pid, data in cart.items():
        product = get_object_or_404(Product, id=int(pid))  # ✅ FIX
        price = Decimal(data['price'])
        quantity = data['quantity']
        subtotal = price * quantity

        total += subtotal

        items.append({
            'product': product,
            'price': price,
            'quantity': quantity,
            'subtotal': subtotal
        })

    return render(request, 'cart/detail.html', {
        'items': items,
        'total': total
    })



@login_required(login_url='login')
def increase_quantity(request, id):
    cart = request.session.get('cart', {})
    id = str(id)

    if id in cart:
        cart[id]['quantity'] += 1

    request.session['cart'] = cart
    return redirect('cart_detail')


@login_required(login_url='login')
def decrease_quantity(request, id):
    cart = request.session.get('cart', {})
    id = str(id)

    if id in cart:
        if cart[id]['quantity'] > 1:
            cart[id]['quantity'] -= 1
        else:
            del cart[id]

    request.session['cart'] = cart
    return redirect('cart_detail')


@login_required(login_url='login')
def remove_from_cart(request, id):
    cart = request.session.get('cart', {})
    cart.pop(str(id), None)
    request.session['cart'] = cart
    return redirect('cart_detail')


@login_required(login_url='login')
def clear_cart(request):
    request.session['cart'] = {}
    return redirect('cart_detail')


# -------------------------
# CHECKOUT
# -------------------------

@login_required(login_url='login')
def checkout(request):
    cart = request.session.get('cart', {})

    if not cart:
        messages.error(request, "Your cart is empty!")
        return redirect('shop')

    items = []
    total = Decimal('0.00')

    for id, data in cart.items():
        product = get_object_or_404(Product, id=id)
        price = Decimal(data['price'])
        quantity = data['quantity']
        subtotal = price * quantity

        total += subtotal

        items.append({
            'product': product,
            'price': price,
            'quantity': quantity,
            'subtotal': subtotal
        })

    if request.method == "POST":
        order = Order.objects.create(
            user=request.user,
            order_id=f"ORD-{uuid.uuid4().hex[:6].upper()}",
            total_amount=total
        )

        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                price=item['price'],
                quantity=item['quantity']
            )

        request.session['cart'] = {}
        return render(request, "order_success.html", {"order_id": order.order_id})

    return render(request, "checkout.html", {
        "items": items,
        "total": total
    })


# -------------------------
# ORDERS
# -------------------------

@login_required(login_url='login')
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'my_orders.html', {'orders': orders})


@login_required(login_url='login')
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_detail.html', {'order': order})
