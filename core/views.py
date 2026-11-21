import json
import time
from collections import Counter
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .forms import CadastroForm, PerfilForm
from .models import (CONTINENTES, EMOJI_CONTINENTE, ROTULO_CONTINENTE, ROTULO_TIPO, TIPOS, TIPOS_QUIZ, Pais, Partida,
                     Perfil, ProgressoPais)
from .services import calcular_pontos, gerar_opcoes, montar_perguntas, obter_perfil
from .utils import normalizar


# ---------------------------------------------------------------- páginas públicas
def home(request):
    hero = ["br", "jp", "fr", "de", "ca", "za", "in", "mx", "au", "it", "eg", "ar"]
    return render(request, "home.html", {"total_paises": Pais.objects.count(), "hero_codigos": hero})


def aprender(request):
    progresso = {}
    if request.user.is_authenticated:
        progresso = {p.pais_id: p for p in ProgressoPais.objects.filter(usuario=request.user, tipo="bandeira")}
    paises = Pais.ordenados()
    for indice, pais in enumerate(paises):
        pais.ordem = indice
        prog = progresso.get(pais.id)
        pais.prog = prog
        pais.status = "" if prog is None else ("aprendido" if prog.aprendido else "visto")
    continentes = [{"chave": c, "rotulo": r, "emoji": EMOJI_CONTINENTE[c]} for c, r in CONTINENTES]
    return render(request, "aprender.html", {"paises": paises, "continentes": continentes})


def cadastro(request):
    if request.user.is_authenticated:
        return redirect("painel")
    form = CadastroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        usuario = form.save()
        obter_perfil(usuario)
        login(request, usuario)
        messages.success(request, f"Bem-vindo(a), {usuario.username}! Vamos começar pelo quiz?")
        return redirect("quiz")
    return render(request, "registration/cadastro.html", {"form": form})


# ---------------------------------------------------------------- quiz
VIDAS_INICIAIS = 3


def _limite_tempo(acertos):
    """Sobrevivência: 10 s por carta no início, caindo 1 s a cada 5 acertos (mínimo 4 s)."""
    return max(4, 10 - acertos // 5)


@login_required
def quiz(request):
    totais = Counter(Pais.objects.values_list("continente", flat=True))
    continentes = [
        {"chave": c, "rotulo": r, "emoji": EMOJI_CONTINENTE[c], "total": totais[c]} for c, r in CONTINENTES
    ]
    estado = request.session.get("quiz")
    contexto = {
        "continentes": continentes,
        "total_paises": sum(totais.values()),
        "foco_inicial": request.GET.get("foco") == "1",
        "tipo_inicial": request.GET.get("tipo") if request.GET.get("tipo") in TIPOS_QUIZ else "bandeira",
        "em_andamento": bool(estado),
        "respondidas": estado["indice"] if estado else 0,
        "total_partida": len(estado["ids"]) if estado else 0,
        "em_andamento_sobrevivencia": bool(estado) and estado.get("modo") == "sobrevivencia",
        "recorde": obter_perfil(request.user).recorde_sobrevivencia,
    }
    return render(request, "quiz.html", contexto)


def _erro(mensagem, status=400):
    return JsonResponse({"erro": mensagem}, status=status)


def _ler_json(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return None


def _estender_ids(usuario, estado):
    """Sobrevivência é sem fim: sorteia mais países quando a fila está acabando."""
    if estado.get("modo") != "sobrevivencia" or len(estado["ids"]) - estado["indice"] > 5:
        return
    novos = montar_perguntas(usuario, estado["continente"], 50, estado.get("foco", False))
    if novos and estado["ids"] and len(novos) > 1 and novos[0] == estado["ids"][-1]:
        novos[0], novos[1] = novos[1], novos[0]
    estado["ids"] = estado["ids"] + novos


@login_required
@require_POST
def api_iniciar(request):
    dados = _ler_json(request)
    if dados is None:
        return _erro("Requisição inválida.")
    continente = dados.get("continente", "")
    if continente not in ROTULO_CONTINENTE:
        continente = ""
    modo = "sobrevivencia" if dados.get("modo") == "sobrevivencia" else "classico"
    foco = bool(dados.get("foco"))
    tipo = dados.get("tipo") if dados.get("tipo") in TIPOS_QUIZ else "bandeira"
    try:
        quantidade = min(max(int(dados.get("quantidade", 10)), 5), 50)
    except (TypeError, ValueError):
        quantidade = 10
    ids = montar_perguntas(request.user, continente, 50 if modo == "sobrevivencia" else quantidade, foco, TIPOS_QUIZ[tipo])
    if not ids:
        return _erro("Não há países para esta região.")
    total = 0 if modo == "sobrevivencia" else len(ids)  # sobrevivência não tem total fixo
    partida = Partida.objects.create(usuario=request.user, continente=continente, modo=modo, tipo=tipo, total=total)
    request.session["quiz"] = {
        "partida": partida.id, "ids": ids, "indice": 0, "sequencia": 0, "continente": continente,
        "foco": foco, "modo": modo, "tipo": tipo, "vidas": VIDAS_INICIAIS, "atual": None,
    }
    return JsonResponse({"total": total, "modo": modo, "tipo": tipo})


@login_required
@require_GET
def api_pergunta(request):
    estado = request.session.get("quiz")
    if not estado:
        return _erro("Nenhuma partida em andamento. Comece uma nova.")
    _estender_ids(request.user, estado)
    if estado["indice"] >= len(estado["ids"]):
        return _erro("Nenhuma partida em andamento. Comece uma nova.")
    sobrev = estado.get("modo") == "sobrevivencia"
    tipo = estado.get("tipo", "bandeira")
    partida = Partida.objects.get(pk=estado["partida"])
    if not estado.get("atual"):
        pais = Pais.objects.get(pk=estado["ids"][estado["indice"]])
        estado["atual"] = {
            "pais": pais.id,
            "opcoes": gerar_opcoes(pais, bool(estado["continente"])),
            "inicio": time.time(),
            "limite": _limite_tempo(partida.acertos) if sobrev else None,
        }
    else:  # retomada (recarregou a página): o relógio recomeça
        estado["atual"]["inicio"] = time.time()
    request.session["quiz"] = estado
    atual = estado["atual"]
    pais = Pais.objects.get(pk=atual["pais"])
    paises = Pais.objects.in_bulk(atual["opcoes"])
    return JsonResponse({
        "indice": estado["indice"] + 1,
        "total": partida.total,
        "modo": estado.get("modo", "classico"),
        "vidas": estado.get("vidas", VIDAS_INICIAIS),
        "tempo": atual.get("limite"),
        "tipo": tipo,
        "codigo": pais.codigo if tipo in ("mapa", "mapa-bandeira") else None,
        "bandeira": pais.bandeira_url if tipo in ("bandeira", "capital") else None,
        "nome": pais.nome if tipo == "capital" else None,
        "opcoes": [{"id": i, "nome": paises[i].nome, "capital": paises[i].capital, "bandeira": paises[i].bandeira_url}
                   for i in atual["opcoes"]],
        "pontos": partida.pontos,
        "sequencia": estado["sequencia"],
    })


@login_required
@require_POST
def api_responder(request):
    estado = request.session.get("quiz")
    dados = _ler_json(request)
    if not estado or not estado.get("atual") or dados is None:
        return _erro("Nenhuma pergunta em andamento.")
    atual = estado["atual"]
    sobrev = estado.get("modo") == "sobrevivencia"
    segundos = max(0.0, time.time() - atual["inicio"])
    limite = atual.get("limite")
    opcao = dados.get("opcao")

    # Sobrevivência: opcao nula = o cronômetro da carta zerou no navegador.
    estourou = False
    if sobrev:
        if opcao is None:
            if segundos < limite - 0.7:
                return _erro("Ainda há tempo.")
            estourou = True
        elif segundos > limite + 2:
            estourou = True
    if not estourou:
        try:
            opcao = int(opcao)
        except (TypeError, ValueError):
            return _erro("Resposta inválida.")
        if opcao not in atual["opcoes"]:
            return _erro("Resposta inválida.")

    pais = Pais.objects.get(pk=atual["pais"])
    correto = not estourou and opcao == pais.id
    base = rapidez = bonus_seq = ganhos = 0
    fim, motivo, novo_recorde = False, "", False

    with transaction.atomic():
        perfil = obter_perfil(request.user)
        partida = Partida.objects.select_for_update().get(pk=estado["partida"], usuario=request.user)
        prog, _ = ProgressoPais.objects.get_or_create(usuario=request.user, pais=pais, tipo=TIPOS_QUIZ[estado.get("tipo", "bandeira")])
        era_aprendido = prog.aprendido

        if correto:
            estado["sequencia"] += 1
            base, rapidez, bonus_seq = calcular_pontos(segundos, estado["sequencia"])
            ganhos = base + rapidez + bonus_seq
            prog.acertos += 1
            perfil.acertos += 1
            partida.acertos += 1
        else:
            estado["sequencia"] = 0
            prog.erros += 1
            perfil.erros += 1
            if sobrev and not estourou:
                estado["vidas"] = estado.get("vidas", VIDAS_INICIAIS) - 1

        partida.respondidas += 1
        partida.pontos += ganhos
        partida.melhor_sequencia = max(partida.melhor_sequencia, estado["sequencia"])
        if sobrev:
            if estourou:
                fim, motivo = True, "tempo"
            elif estado["vidas"] <= 0:
                fim, motivo = True, "vidas"
        else:
            fim = estado["indice"] + 1 >= len(estado["ids"])
        partida.finalizada = fim
        partida.save()

        perfil.pontos += ganhos
        perfil.melhor_sequencia_acertos = max(perfil.melhor_sequencia_acertos, estado["sequencia"])
        if sobrev and fim and partida.acertos > perfil.recorde_sobrevivencia:
            perfil.recorde_sobrevivencia = partida.acertos
            novo_recorde = partida.acertos > 0
        perfil.registrar_dia()
        perfil.save()

        prog.ultima_resposta = timezone.now()
        prog.save()

    estado["indice"] += 1
    estado["atual"] = None
    resposta = {
        "correto": correto,
        "timeout": estourou,
        "correta_id": pais.id,
        "tipo": estado.get("tipo", "bandeira"),
        "bandeira": pais.bandeira_url,
        "nome": pais.nome,
        "capital": pais.capital,
        "continente": pais.rotulo_continente,
        "ganhos": ganhos,
        "detalhe": {"base": base, "rapidez": rapidez, "sequencia": bonus_seq},
        "pontos": partida.pontos,
        "sequencia": estado["sequencia"],
        "vidas": estado.get("vidas", VIDAS_INICIAIS),
        "novo_aprendido": prog.aprendido and not era_aprendido,
        "finalizado": fim,
        "motivo": motivo,
    }
    if fim:
        resposta["resumo"] = {
            "acertos": partida.acertos,
            "total": partida.total or partida.respondidas,
            "pontos": partida.pontos,
            "melhor_sequencia": partida.melhor_sequencia,
            "percentual": round(partida.acertos * 100 / max(partida.respondidas, 1)),
            "modo": estado.get("modo", "classico"),
            "motivo": motivo,
            "novo_recorde": novo_recorde,
            "recorde": perfil.recorde_sobrevivencia,
        }
        del request.session["quiz"]
    else:
        _estender_ids(request.user, estado)
        request.session["quiz"] = estado
        # o navegador já pré-carrega a próxima bandeira (transição mais rápida)
        resposta["proxima_bandeira"] = Pais.objects.get(pk=estado["ids"][estado["indice"]]).bandeira_url
        if estado.get("tipo", "bandeira") in ("mapa", "mapa-bandeira"):
            resposta["proxima_bandeira"] = None
    return JsonResponse(resposta)


# ---------------------------------------------------------------- painel, ranking, perfil
@login_required
def painel(request):
    usuario = request.user
    perfil = obter_perfil(usuario)
    tipo = request.GET.get("tipo") if request.GET.get("tipo") in ROTULO_TIPO else "bandeira"
    todos = list(ProgressoPais.objects.filter(usuario=usuario).select_related("pais"))
    progresso = [p for p in todos if p.tipo == tipo]
    total_paises = Pais.objects.count()
    aprendidos = [p for p in progresso if p.aprendido]
    dominio = []
    for chave, rotulo in TIPOS:
        n = sum(1 for p in todos if p.tipo == chave and p.aprendido)
        dominio.append({"chave": chave, "rotulo": rotulo, "aprendidos": n,
                        "pct": round(n * 100 / total_paises) if total_paises else 0})

    mais_acertos = sorted((p for p in progresso if p.acertos > 0),
                          key=lambda p: (-p.acertos, -p.taxa, normalizar(p.pais.nome)))[:8]
    reforco = sorted((p for p in progresso if p.erros > 0),
                     key=lambda p: (p.taxa, -p.erros, normalizar(p.pais.nome)))[:8]

    totais = Counter(Pais.objects.values_list("continente", flat=True))
    aprendidos_por = Counter(p.pais.continente for p in aprendidos)
    por_continente = [
        {"rotulo": rotulo, "emoji": EMOJI_CONTINENTE[chave], "aprendidos": aprendidos_por[chave],
         "total": totais[chave], "pct": round(aprendidos_por[chave] * 100 / totais[chave]) if totais[chave] else 0}
        for chave, rotulo in CONTINENTES
    ]

    # últimos 14 dias de atividade
    hoje = timezone.localdate()
    inicio = hoje - timedelta(days=13)
    partidas_recentes = Partida.objects.filter(usuario=usuario, respondidas__gt=0, criada_em__date__gte=inicio)
    pontos_dia = Counter()
    for partida in partidas_recentes:
        pontos_dia[timezone.localtime(partida.criada_em).date()] += partida.pontos
    dias = [inicio + timedelta(days=i) for i in range(14)]
    grafico = {
        "rotulos": [d.strftime("%d/%m") for d in dias],
        "pontos": [pontos_dia[d] for d in dias],
        "acertos": perfil.acertos,
        "erros": perfil.erros,
    }
    semana = [
        {"letra": "DSTQQSS"[(d.weekday() + 1) % 7], "ativo": pontos_dia.get(d, 0) > 0 or (
            perfil.ultimo_dia is not None and perfil.streak > 0
            and 0 <= (perfil.ultimo_dia - d).days < perfil.streak),
         "hoje": d == hoje}
        for d in dias[-7:]
    ]

    contexto = {
        "perfil": perfil,
        "tipo": tipo,
        "tipos": TIPOS,
        "rotulo_tipo": ROTULO_TIPO[tipo],
        "dominio": dominio,
        "total_paises": total_paises,
        "aprendidos": len(aprendidos),
        "pct_aprendidos": round(len(aprendidos) * 100 / total_paises) if total_paises else 0,
        "vistos": len(progresso),
        "nao_vistos": total_paises - len(progresso),
        "mais_acertos": mais_acertos,
        "reforco": reforco,
        "por_continente": por_continente,
        "semana": semana,
        "grafico": grafico,
        "partidas": Partida.objects.filter(usuario=usuario, respondidas__gt=0)[:6],
        "partidas_total": Partida.objects.filter(usuario=usuario, respondidas__gt=0).count(),
    }
    return render(request, "painel.html", contexto)


@login_required
def ranking(request):
    perfis = list(Perfil.objects.filter(pontos__gt=0).select_related("usuario")
                  .order_by("-pontos", "usuario__username")[:20])
    meu = obter_perfil(request.user)
    posicao = Perfil.objects.filter(pontos__gt=meu.pontos).count() + 1 if meu.pontos else None
    return render(request, "ranking.html", {"perfis": perfis, "meu_perfil": meu, "posicao": posicao})


@login_required
def perfil(request):
    meu = obter_perfil(request.user)
    inicial = {"first_name": request.user.first_name, "last_name": request.user.last_name,
               "email": request.user.email, "avatar": meu.avatar}
    form = PerfilForm(request.POST or None, initial=inicial)
    if request.method == "POST" and form.is_valid():
        dados = form.cleaned_data
        request.user.first_name = dados["first_name"]
        request.user.last_name = dados["last_name"]
        request.user.email = dados["email"]
        request.user.save()
        meu.avatar = dados["avatar"]
        meu.save()
        messages.success(request, "Perfil atualizado!")
        return redirect("perfil")
    contexto = {
        "form": form,
        "meu": meu,
        "partidas": Partida.objects.filter(usuario=request.user, respondidas__gt=0).count(),
        "aprendidos": sum(1 for p in ProgressoPais.objects.filter(usuario=request.user, tipo="bandeira") if p.aprendido),
        "total_paises": Pais.objects.count(),
    }
    return render(request, "perfil.html", contexto)


class SenhaView(PasswordChangeView):
    def form_valid(self, form):
        messages.success(self.request, "Senha alterada com sucesso!")
        return super().form_valid(form)
