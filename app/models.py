from django.db import models

# Create your models here.


class User(models.Model):
    username = models.CharField(max_length=80, unique=True)
    name = models.CharField(max_length=89)
    email = models.EmailField(max_length=90, unique=True)
    password = models.CharField(max_length=90)
    is_banned = models.BooleanField(default=False)

    def __str__(self):
        return self.Username


class Contact(models.Model):
    names = models.CharField(max_length=30)
    email = models.EmailField(max_length=50, null='True')
    phone = models.CharField(max_length=10, null='True')
    desc = models.TextField(null='True')
    # var = models.TextField(null='True')
    # var2 = models.TextField(null='True')


class AdminData(models.Model):
    admin_username = models.CharField(max_length=80, unique=True)
    admin_email = models.EmailField(max_length=90, unique=True)
    password = models.CharField(max_length=90)


class NewsHistory(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    news_text = models.TextField()
    result = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)