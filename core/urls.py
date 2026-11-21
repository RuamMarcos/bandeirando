from django.contrib.auth import views as auth_views
from django.urls import path
from django.urls import reverse_lazy

from . import views
from .forms import LoginForm, SenhaForm

urlpatterns = [
    path("", views.home, name="home"),
    path("aprender/", views.aprender, name="aprender"),
    path("quiz/", views.quiz, name="quiz"),
    path("quiz/api/iniciar/", views.api_iniciar, name="api_iniciar"),
    path("quiz/api/pergunta/", views.api_pergunta, name="api_pergunta"),
    path("quiz/api/responder/", views.api_responder, name="api_responder"),
    path("painel/", views.painel, name="painel"),
    path("ranking/", views.ranking, name="ranking"),
    path("perfil/", views.perfil, name="perfil"),
    path(
        "perfil/senha/",
        views.SenhaView.as_view(template_name="registration/senha.html", form_class=SenhaForm,
                                success_url=reverse_lazy("perfil")),
        name="senha",
    ),
    path("entrar/", auth_views.LoginView.as_view(authentication_form=LoginForm), name="login"),
    path("sair/", auth_views.LogoutView.as_view(), name="logout"),
    path("cadastro/", views.cadastro, name="cadastro"),
]
