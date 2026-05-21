from django.urls import path

from . import views

app_name = "chatbot"

urlpatterns = [
    path("", views.chat_page, name="chat_page"),
    path("message/", views.chatbot_message, name="message"),
]
