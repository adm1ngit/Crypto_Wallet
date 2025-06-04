from django.urls import path
from .views import SendTransaction, ConvertUzsToEth

urlpatterns = [
    path('send/', SendTransaction.as_view()),
    path('convert/', ConvertUzsToEth.as_view()),
]
