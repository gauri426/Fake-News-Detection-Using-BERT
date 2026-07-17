from .models import *
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Q

def index(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')


def user_login(request):
    if request.method == "POST":
        identifier = request.POST.get("email")  # can be email or username
        password = request.POST.get("password")

        try:
            user = User.objects.get(
                Q(email=identifier) | Q(username=identifier),
                password=password
            )

            if user.is_banned:
                messages.error(request, "Your account is banned. You cannot log in.")
                return redirect('user_login')

            # ✅ Single session handling
            request.session['user_id'] = user.id
            request.session['username'] = user.username

            messages.success(request, "Login successful.")
            return redirect('user_home')

        except User.DoesNotExist:
            messages.error(request, "Invalid credentials.")
            return redirect('user_login')

    return render(request, "login.html")


def user_registration(request):
    if request.method == "POST":
        username = request.POST.get('username')
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')


        # Check if user with email or phone is already banned
        if User.objects.filter(email=email, is_banned=True).exists():
            messages.error(request, "You are banned from registering.")
            return redirect('user_registration')

        if User.objects.filter(username=username).exists():
            messages.warning(request, 'Username is already exists')
            return redirect('user_registration')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('user_registration')

        # Check if passwords match
        if password != confirm_password:
            messages.error(request, "Both passwords did not match.")
            return redirect('user_registration')

        # Create a new user
        user = User(
            username=username,
            name=name,
            email=email,
            password=password
        )
        user.save()

        messages.success(request, "Registration successful. Please log in.")
        return redirect('user_login')

    return render(request, "register.html")






def user_logout(request):
    request.session.flush()
    messages.success(request, "Logged out successfully.")
    return redirect('home')




from django.core.mail import send_mail
from django.conf import settings
import random
import time


# Store OTP and time per email
otp_storage = {}  # { email: {"otp": 123456, "time": 1234567890.0} }

def send_otp(request, email):
    otp = random.randint(100000, 999999)

    otp_storage[email] = {
        "otp": otp,
        "time": time.time()
    }

    request.session['otp_email'] = email

    subject = "Your OTP for Login"
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]


    # ✅ HTML Template
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', sans-serif;
                background-color: #f4f6f8;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 500px;
                margin: 40px auto;
                background: #ffffff;
                border-radius: 12px;
                padding: 30px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                text-align: center;
            }}
            .title {{
                font-size: 22px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }}
            .subtitle {{
                color: #555;
                font-size: 14px;
                margin-bottom: 25px;
            }}
            .otp-box {{
                font-size: 34px;
                font-weight: bold;
                color: white;
                background: linear-gradient(135deg, #667eea, #764ba2);
                padding: 15px 25px;
                border-radius: 10px;
                display: inline-block;
                letter-spacing: 5px;
                margin-bottom: 20px;
            }}
            .note {{
                font-size: 13px;
                color: #888;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="title">🔐 Fake News Detection</div>
            <div class="subtitle">
                Use the OTP below to securely log in
            </div>

            <div class="otp-box">{otp}</div>

            <div class="subtitle">
                This OTP is valid for <b>10 minutes</b><br>
                Do not share it with anyone
            </div>

            <div class="note">
                If you didn't request this, please ignore this email.
            </div>
        </div>
    </body>
    </html>
    """

    # ✅ Send Email
    email_message = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    email_message.attach_alternative(html_content, "text/html")
    email_message.send()

    print("OTP Storage:", otp_storage)

def otp_login_home(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        if not email:
            messages.error(request, "Email is required")
            return redirect('otp_login')

        check_user_email_exist = User.objects.filter(email=email).exists()
        if check_user_email_exist:
            send_otp(request, email)
            messages.success(request, f"OTP sent successfully to {email}")
            return redirect('verify_otp')
        else:
            messages.error(request, "Email is not registered")
            return redirect('otp_login')

    return render(request, 'OTP/otp_login_home.html')


def verify_otp(request):
    if request.method == "POST":
        otp = request.POST.get("otp")
        email = request.session.get("otp_email")
        current_time = time.time()

        if not otp:
            messages.error(request, "OTP is required")
            return redirect('verify_otp')

        if not email or email not in otp_storage:
            messages.error(request, "No OTP found. Please request again.")
            return redirect('otp_login_home')

        stored_otp = otp_storage[email]["otp"]
        otp_time = otp_storage[email]["time"]

        # Check if OTP expired (10 minutes)
        if current_time - otp_time > 600:
            del otp_storage[email]
            messages.error(request, "OTP has expired. Please request a new one.")
            return redirect('otp_login')

        # Check if OTP matches
        if int(otp) == stored_otp:
            user = User.objects.filter(email=email).first()
            request.session['user_id'] = user.id

            # Cleanup after success
            del otp_storage[email]
            del request.session['otp_email']

            messages.success(request, "Logged in Successfully")
            return redirect('user_home')

        messages.error(request, "Invalid OTP")
        return redirect('verify_otp')

    return render(request, 'OTP/verify_otp.html')


def resend_otp(request):
    email = request.session.get("otp_email")

    if not email:
        messages.error(request, "No email found. Please login again.")
        return redirect('otp_login')

    # Generate new OTP
    otp = random.randint(100000, 999999)
    otp_storage[email] = {
        "otp": otp,
        "time": time.time()
    }

    subject = "Your OTP for Login (Resent)"
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]


    # ✅ HTML Template (Resend version)
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', sans-serif;
                background-color: #f4f6f8;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 500px;
                margin: 40px auto;
                background: #ffffff;
                border-radius: 12px;
                padding: 30px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                text-align: center;
            }}
            .title {{
                font-size: 22px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }}
            .badge {{
                display: inline-block;
                background: #ff9800;
                color: white;
                padding: 5px 12px;
                border-radius: 20px;
                font-size: 12px;
                margin-bottom: 15px;
            }}
            .subtitle {{
                color: #555;
                font-size: 14px;
                margin-bottom: 25px;
            }}
            .otp-box {{
                font-size: 34px;
                font-weight: bold;
                color: white;
                background: linear-gradient(135deg, #ff758c, #ff7eb3);
                padding: 15px 25px;
                border-radius: 10px;
                display: inline-block;
                letter-spacing: 5px;
                margin-bottom: 20px;
            }}
            .note {{
                font-size: 13px;
                color: #888;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="title">🔐 Fake News Detection</div>

            <div class="badge">OTP Resent</div>

            <div class="subtitle">
                Your previous OTP expired or was requested again.
            </div>

            <div class="otp-box">{otp}</div>

            <div class="subtitle">
                This OTP is valid for <b>10 minutes</b><br>
                Do not share it with anyone
            </div>

            <div class="note">
                If you didn't request this, please secure your account.
            </div>
        </div>
    </body>
    </html>
    """

    # ✅ Send Email
    email_message = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    email_message.attach_alternative(html_content, "text/html")
    email_message.send()

    messages.success(request, f"New OTP has been sent to {email}")
    return redirect('verify_otp')


def userhome(request):
    return render(request, 'user_home.html')




# ========================================
# detection function
# ========================================

# your_app/utils.py
# we can also create seprate file for this but we are using it in same file

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_PATH = "bert_fake_news_model"

# Load tokenizer and model
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)

# Device setup
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()


def predict_news(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)

    # Move to device
    inputs = {key: val.to(device) for key, val in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

    pred = torch.argmax(outputs.logits, dim=1).item()

    return "Real" if pred == 1 else "Fake"

def detect(request):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect('user_login')

    if request.method == "POST":

        text = request.POST.get('news_text')

        if not text:
            messages.error(request, "Please enter news text")
            return redirect('detect')

        # ✅ BERT prediction
        result = predict_news(text)

        # ✅ Get user object (IMPORTANT FIX)
        user = User.objects.get(id=user_id)

        # ✅ Save to DB
        NewsHistory.objects.create(
            user=user,
            news_text=text,
            result=result
        )

        # ✅ Pass result to result page
        return render(request, "result.html", {
            "text": text,
            "result": result
        })

    return render(request, "detect.html")


from django.core.paginator import Paginator

def history(request):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect('user_login')

    user_history = NewsHistory.objects.filter(
        user_id=user_id
    ).order_by('-timestamp')

    # ✅ Pagination (10 per page)
    paginator = Paginator(user_history, 10)
    page_number = request.GET.get('page')
    history_page = paginator.get_page(page_number)

    context = {
        "history": history_page
    }

    return render(request, "history.html", context)

#
def admin_login(request):
    if request.method == 'POST':
        admin_username = request.POST.get('admin_username')
        password = request.POST.get('password')

        # Check credentials
        admin_obj = AdminData.objects.filter(admin_username = admin_username, password = password).first()
        if not admin_obj:
            admin_obj = AdminData.objects.filter(admin_email = admin_username, password = password).first()

        if admin_obj:
            request.session['admin_username'] = admin_obj.admin_username  # store username in session
            messages.success(request, "Successfully logged in")
            return redirect('admin_home')
        else:
            messages.error(request, "Invalid Username or Password...!")
            return redirect('admin_login')

    return render(request, 'admin_login.html')



def admin_registration(request):
    if request.method == 'POST':
        admin_username = request.POST['admin_username']
        email = request.POST['email']
        pass1 = request.POST['password']
        pass2 = request.POST['confirm_password']

        if pass1 != pass2 :
            messages.warning(request, 'Both password are not matched' )
            return redirect('admin_registration')

        if AdminData.objects.filter(admin_username=admin_username).exists():
            messages.warning(request, 'Admin username is already exists')
            return redirect('admin_registration')
        else:
            AdminData(admin_username=admin_username, admin_email=email, password=pass1).save()
            messages.success(request, 'The admin ' + request.POST['admin_username'] + " is saved successfully..!")
            return redirect('admin_login')
    else:
        return render(request, 'admin_registration.html')



def admin_logout(request):
    request.session.flush()
    messages.success(request, "Logged out successfully.")
    return redirect('home')




def admin_home(request):

    total_users = User.objects.count()
    total_predictions = NewsHistory.objects.count()
    fake_news = NewsHistory.objects.filter(result="Fake").count()

    context = {
        "total_users": total_users,
        "total_predictions": total_predictions,
        "fake_news": fake_news
    }

    return render(request,"admin_dir/admin_home.html",context)

def user_contact(request):
    if request.method == 'POST':
        names = request.POST['names']
        email = request.POST['email']
        phone = request.POST['phone']
        desc = request.POST['desc']
        contacts = Contact(names=names, email=email, phone=phone, desc=desc)
        contacts.save()
        return redirect('contact')
    else:
        return render(request, 'contact.html')


def user_about(request):
    return render(request, 'about.html')


def view_user(request):
    form = User.objects.all()
    return render(request, 'admin_dir/view_user.html', {'forms': form})


def view_contact(request):
    form = Contact.objects.all()
    return render(request, 'admin_dir/view_contact.html', {'forms': form})



from django.core.paginator import Paginator

def news_history(request):

    selected_date = request.GET.get('date')
    result_filter = request.GET.get('result')  # 👈 new filter

    history_list = NewsHistory.objects.all().order_by('-timestamp')

    # ✅ Filter by date
    if selected_date:
        history_list = history_list.filter(timestamp__date=selected_date)

    # ✅ Filter by result (Real / Fake)
    if result_filter in ["Real", "Fake"]:
        history_list = history_list.filter(result=result_filter)

    # ✅ Pagination (10 entries)
    paginator = Paginator(history_list, 10)
    page_number = request.GET.get('page')
    history = paginator.get_page(page_number)

    context = {
        "history": history,
        "selected_date": selected_date,
        "result_filter": result_filter
    }

    return render(request, "admin_dir/news_history.html", context)



from django.db.models import Count
from django.db.models.functions import TruncDate
from django.shortcuts import render
from .models import NewsHistory, User


def view_statistics(request):

    total_users = User.objects.count()
    total_news = NewsHistory.objects.count()

    fake_news = NewsHistory.objects.filter(result="Fake").count()
    real_news = NewsHistory.objects.filter(result="Real").count()

    # daily predictions
    daily_data = (
        NewsHistory.objects
        .annotate(date=TruncDate('timestamp'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    dates = [str(d['date']) for d in daily_data]
    counts = [d['count'] for d in daily_data]

    context = {
        "total_users": total_users,
        "total_news": total_news,
        "fake_news": fake_news,
        "real_news": real_news,
        "dates": dates,
        "counts": counts
    }

    return render(request,"admin_dir/statistics.html",context)

def delete_user(request, user_id):
    user = User.objects.filter(id=user_id).first()
    if user:
        user.delete()
        messages.success(request, "User Deleted Successfully")
        return redirect('view_user')  # Redirect to a list of reviews or another page


def ban_user(request,user_id):
    user = User.objects.get(id=user_id)

    user.is_banned = True
    user.save()
    return redirect(view_user)

def unban_user(request,user_id):
    user = User.objects.get(id=user_id)

    user.is_banned = False
    user.save()
    return redirect(view_user)

def logout(request):
    messages.success(request, "successfully logout..!")
    return redirect('index')