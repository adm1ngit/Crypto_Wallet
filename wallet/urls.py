from django.urls import path
from .views import SendTransaction, ConvertUzsToEth, BuyCrypto

urlpatterns = [
    path('send/', SendTransaction.as_view()),
    path('convert/', ConvertUzsToEth.as_view()),
    path('buy/', BuyCrypto.as_view()),
]
