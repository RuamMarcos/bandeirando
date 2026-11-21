import random

from .models import Pais, Perfil, ProgressoPais


def obter_perfil(usuario):
    perfil, _ = Perfil.objects.get_or_create(usuario=usuario)
    return perfil


def _ordem_rodada(paises, progresso, focar_dificeis):
    """Ordem de uma rodada completa (todos os países da região, sem repetir)."""
    if not focar_dificeis:
        ordem = [p.id for p in paises]
        random.shuffle(ordem)
        return ordem
    chaves = []
    for pais in paises:
        prog = progresso.get(pais.id)
        if prog is None or prog.total == 0:
            peso = 3.0
        else:
            peso = 0.5 + 4 * (prog.erros / prog.total) + (1 if prog.acertos < 3 else 0)
        # amostragem ponderada sem reposição (Efraimidis-Spirakis): erros e inéditos vêm primeiro
        chaves.append((random.random() ** (1 / peso), pais.id))
    chaves.sort(reverse=True)
    return [pais_id for _, pais_id in chaves]


def _ordenar(paises, progresso, focar_dificeis):
    """Uma rodada com todos os países em ordem sorteada (ponderada pelos pontos fracos, se pedido)."""
    if not focar_dificeis:
        rodada = list(paises)
        random.shuffle(rodada)
        return [p.id for p in rodada]
    chaves = []
    for pais in paises:
        prog = progresso.get(pais.id)
        if prog is None or prog.total == 0:
            peso = 3.0
        else:
            peso = 0.5 + 4 * (prog.erros / prog.total) + (1 if prog.acertos < 3 else 0)
        # amostragem ponderada sem reposição (Efraimidis-Spirakis)
        chaves.append((random.random() ** (1 / peso), pais.id))
    chaves.sort(reverse=True)
    return [pais_id for _, pais_id in chaves]


def montar_perguntas(usuario, continente, quantidade, focar_dificeis, tipo="bandeira"):
    """Sorteia os países da partida. Se a região tem menos países que a partida, as rodadas se repetem
    (sem repetir o mesmo país duas vezes seguidas)."""
    paises = list(Pais.objects.filter(continente=continente)) if continente else list(Pais.objects.all())
    if not paises:
        return []
    progresso = {}
    if focar_dificeis:
        progresso = {p.pais_id: p for p in ProgressoPais.objects.filter(usuario=usuario, tipo=tipo)}
    ids = []
    while len(ids) < quantidade:
        rodada = _ordenar(paises, progresso, focar_dificeis)
        if ids and len(rodada) > 1 and rodada[0] == ids[-1]:
            rodada[0], rodada[1] = rodada[1], rodada[0]
        ids += rodada[: quantidade - len(ids)]
    return ids


def gerar_opcoes(pais, continente_restrito):
    """Retorna os ids das 4 alternativas (1 certa + 3 erradas), embaralhados."""
    outros = list(Pais.objects.exclude(pk=pais.pk))
    mesmos = [p for p in outros if p.continente == pais.continente]
    qtd_mesmo = min(3 if continente_restrito else 2, len(mesmos))
    erradas = random.sample(mesmos, qtd_mesmo)
    restantes = [p for p in outros if p not in erradas]
    erradas += random.sample(restantes, 3 - len(erradas))
    ids = [p.id for p in erradas] + [pais.id]
    random.shuffle(ids)
    return ids


def calcular_pontos(segundos, sequencia):
    """10 base + até 5 de rapidez (responder em <10s) + até 5 por sequência de acertos."""
    base = 10
    rapidez = max(0, 5 - int(segundos // 2))
    bonus_sequencia = min(sequencia - 1, 5)
    return base, rapidez, bonus_sequencia
