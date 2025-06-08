from django.db import models

class Users(models.Model):
    username = models.CharField(unique=True, max_length=150)
    password = models.CharField(max_length=128)
    email = models.CharField(max_length=254, blank=True, null=True)
    account_balance = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'users'


class FixedDeposit(models.Model):
    user = models.ForeignKey(Users, on_delete=models.DO_NOTHING)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    matured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'fixed_deposit'


class Stocks(models.Model):
    user = models.ForeignKey(Users, on_delete=models.DO_NOTHING)
    stock_symbol = models.CharField(max_length=20)
    stock_name = models.CharField(max_length=100, blank=True, null=True)
    shares = models.IntegerField()
    total_cost = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'stocks'
