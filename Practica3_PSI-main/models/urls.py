from django.urls import path
from models.models import myClassView

urlpatterns = [
    path('myclassView/', myClassView.as_view()),
]
