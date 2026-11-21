from .services import obter_perfil


def perfil_atual(request):
    """Disponibiliza o perfil (pontos e streak) para a barra de navegação."""
    if request.user.is_authenticated:
        return {"perfil_atual": obter_perfil(request.user)}
    return {}
