# finance/views.py
from dotenv import load_dotenv
load_dotenv()

from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from datetime import date
from .models import Users, FixedDeposit, Stocks
from django.contrib.auth import login, logout
from decimal import Decimal
from openai import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnableLambda
from langchain.schema.output_parser import StrOutputParser
import os

# AI 分析模型初始化（用 LangChain）
chat_model = ChatOpenAI(api_key=os.environ.get("OPENAI_API_KEY"), temperature=0.5)

prompt_template = PromptTemplate.from_template("""
你是一位台灣的專業投資分析師。以下是使用者的持股資訊：
- 股票代號：{symbol}
- 名稱：{name}
- 張數：{shares}
- 總成本：{cost} 元

請用繁體中文回答：
1. 是否建議現在賣出？（是/否）
2. 請簡短說明理由
""")
# 手動登入
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        try:
            user = Users.objects.get(username=username, password=password)
            request.session['user_id'] = user.id
            return redirect('dashboard')
        except Users.DoesNotExist:
            messages.error(request, '帳號或密碼錯誤')
    return render(request, 'finance/login.html')

ai_chain = prompt_template | RunnableLambda(lambda x: chat_model.invoke(x)) | StrOutputParser()

# 手動註冊
def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        if Users.objects.filter(username=username).exists():
            messages.error(request, '使用者名稱已存在')
        else:
            Users.objects.create(username=username, password=password, email=email, account_balance=0.0)
            messages.success(request, '註冊成功，請登入')
            return redirect('login')
    return render(request, 'finance/register.html')

def logout_view(request):
    request.session.flush()
    return redirect('login')

def get_current_user(request):
    user_id = request.session.get('user_id')
    if user_id:
        try:
            return Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            return None
    return None

def dashboard(request):
    user = get_current_user(request)
    if not user:
        return redirect('login')

    fixed_deposits = FixedDeposit.objects.filter(user=user)
    stocks = Stocks.objects.filter(user=user)

    for fd in fixed_deposits:
        if not fd.matured and fd.end_date <= date.today():
            interest = fd.amount * (fd.interest_rate / 100)
            user.account_balance += fd.amount + interest
            fd.matured = True
            fd.save()
            user.save()

    total_fixed = sum(fd.amount for fd in fixed_deposits if not fd.matured)
    total_stock = sum(stock.total_cost for stock in stocks)
    total_asset = user.account_balance + total_fixed + total_stock

    return render(request, 'finance/dashboard.html', {
        'user': user,
        'fixed_deposits': fixed_deposits,
        'stocks': stocks,
        'total_fixed': total_fixed,
        'total_stock': total_stock,
        'total_asset': total_asset,
    })
def deposit(request):
    user = get_current_user(request)
    if not user:
        return redirect('login')

    if request.method == 'POST':
        amount = request.POST.get('amount')
        if amount:
            try:
                amount_decimal = Decimal(amount)
                user.account_balance += amount_decimal
                user.save()
                messages.success(request, f"成功存入 NT${amount_decimal}")
            except:
                messages.error(request, "請輸入正確的金額格式")
        return redirect('dashboard')

    return render(request, 'finance/deposit.html')

def withdraw(request):
    user = get_current_user(request)
    if not user:
        return redirect('login')

    if request.method == 'POST':
        amount = request.POST.get('amount')
        if amount:
            try:
                amount_decimal = Decimal(amount)
                if amount_decimal > user.account_balance:
                    messages.error(request, "餘額不足，無法提款")
                else:
                    user.account_balance -= amount_decimal
                    user.save()
                    messages.success(request, f"成功提款 NT${amount_decimal}")
            except:
                messages.error(request, "請輸入正確的金額格式")
        return redirect('dashboard')

    return render(request, 'finance/withdraw.html')
 

def add_fixed_deposit(request):
    user = get_current_user(request)
    if not user:
        return redirect('login')

    if request.method == 'POST':
        amount = request.POST['amount']
        interest_rate = request.POST['interest_rate']
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']

        FixedDeposit.objects.create(
            user=user,
            amount=amount,
            interest_rate=interest_rate,
            start_date=start_date,
            end_date=end_date
        )
        return redirect('dashboard')

    return render(request, 'finance/add_fixed_deposit.html')

def add_stock(request):
    user = get_current_user(request)
    if not user:
        return redirect('login')

    if request.method == 'POST':
        symbol = request.POST['stock_symbol']
        name = request.POST['stock_name']
        shares = int(request.POST['shares'])
        total_cost = float(request.POST['total_cost'])

        Stocks.objects.create(
            user=user,
            stock_symbol=symbol,
            stock_name=name,
            shares=shares,
            total_cost=total_cost
        )
        return redirect('dashboard')

    return render(request, 'finance/add_stock.html')

def sell_stock(request, stock_id):
    user = get_current_user(request)
    if not user:
        return redirect('login')

    stock = Stocks.objects.get(id=stock_id, user=user)
    if request.method == 'POST':
        sell_shares = int(request.POST['sell_shares'])
        sell_price = Decimal(request.POST['sell_price']) 
        if sell_shares <= stock.shares:
            unit_cost = stock.total_cost / stock.shares
            original_cost = unit_cost * sell_shares
            sale_amount = sell_price * sell_shares
            profit = sale_amount - original_cost  

            user.account_balance += profit
            stock.shares -= sell_shares
            stock.total_cost -= original_cost
            if stock.shares == 0:
                stock.delete()
            else:
                stock.save()
            user.save()
        return redirect('dashboard')

    return render(request, 'finance/sell_stock.html', {'stock': stock})

def analyze_stock(request, stock_id):
    user = get_current_user(request)
    if not user:
        return redirect('login')

    stock = Stocks.objects.get(id=stock_id, user=user)
    result = ai_chain.invoke({
        "symbol": stock.stock_symbol,
        "name": stock.stock_name,
        "shares": stock.shares,
        "cost": stock.total_cost
    })
    return render(request, 'finance/analysis_result.html', {
        'stock': stock,
        'analysis': result
    })
