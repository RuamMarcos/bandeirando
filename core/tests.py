import json
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Pais, Partida, Perfil, ProgressoPais


class PaisesTests(TestCase):
    def test_195_paises_com_bandeira(self):
        from pathlib import Path
        self.assertEqual(Pais.objects.count(), 195)
        pasta = Path(__file__).parent / "static" / "core" / "flags"
        for pais in Pais.objects.all():
            self.assertTrue((pasta / f"{pais.codigo}.svg").exists(), pais.codigo)


class FluxoTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("ana", password="senha-forte-123")
        self.client.login(username="ana", password="senha-forte-123")

    def post(self, nome, dados):
        return self.client.post(reverse(nome), json.dumps(dados), content_type="application/json")

    def jogar(self, acertar=True, continente="", quantidade=5):
        self.assertEqual(self.post("api_iniciar", {"continente": continente, "quantidade": quantidade}).status_code, 200)
        resultados = []
        while True:
            pergunta = self.client.get(reverse("api_pergunta")).json()
            self.assertEqual(len(pergunta["opcoes"]), 4)
            self.assertEqual(len({o["id"] for o in pergunta["opcoes"]}), 4)
            sessao = self.client.session["quiz"]["atual"]
            escolha = sessao["pais"] if acertar else next(i for i in sessao["opcoes"] if i != sessao["pais"])
            r = self.post("api_responder", {"opcao": escolha}).json()
            resultados.append(r)
            if r["finalizado"]:
                return resultados

    def test_paginas_abrem(self):
        for nome in ["home", "aprender", "quiz", "painel", "ranking", "perfil", "senha", "login", "cadastro"]:
            resposta = self.client.get(reverse(nome))
            self.assertIn(resposta.status_code, (200, 302), nome)
        self.assertContains(self.client.get(reverse("aprender")), "Brasil")

    def test_quiz_exige_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("quiz")).status_code, 302)
        self.assertEqual(self.post("api_iniciar", {}).status_code, 302)

    def test_partida_perfeita_pontua_e_conta_streak(self):
        resultados = self.jogar(acertar=True, quantidade=5)
        ultimo = resultados[-1]
        self.assertEqual(ultimo["resumo"]["acertos"], 5)
        self.assertEqual(ultimo["resumo"]["percentual"], 100)
        self.assertGreaterEqual(ultimo["resumo"]["pontos"], 5 * 10 + (0 + 1 + 2 + 3 + 4))
        perfil = Perfil.objects.get(usuario=self.usuario)
        self.assertEqual(perfil.pontos, ultimo["resumo"]["pontos"])
        self.assertEqual(perfil.sequencia_dias, 1)
        self.assertEqual(perfil.melhor_sequencia_acertos, 5)
        self.assertTrue(Partida.objects.get().finalizada)
        self.assertNotIn("quiz", self.client.session)

    def test_erros_zeram_sequencia_e_nao_pontuam(self):
        resultados = self.jogar(acertar=False, quantidade=5)
        self.assertTrue(all(not r["correto"] and r["ganhos"] == 0 for r in resultados))
        self.assertEqual(Perfil.objects.get().pontos, 0)
        self.assertEqual(ProgressoPais.objects.filter(erros=1).count(), 5)

    def test_filtro_de_continente_e_distratores(self):
        self.post("api_iniciar", {"continente": "oceania", "quantidade": 10})
        for _ in range(10):
            pergunta = self.client.get(reverse("api_pergunta")).json()
            sessao = self.client.session["quiz"]["atual"]
            for pais in Pais.objects.filter(pk__in=sessao["opcoes"]):
                self.assertEqual(pais.continente, "oceania")
            self.post("api_responder", {"opcao": sessao["pais"]})

    def test_resposta_invalida_e_duplicada(self):
        self.post("api_iniciar", {"quantidade": 5})
        self.client.get(reverse("api_pergunta"))
        self.assertEqual(self.post("api_responder", {"opcao": 999999}).status_code, 400)
        certo = self.client.session["quiz"]["atual"]["pais"]
        self.assertEqual(self.post("api_responder", {"opcao": certo}).status_code, 200)
        self.assertEqual(self.post("api_responder", {"opcao": certo}).status_code, 400)

    def test_pais_aprendido(self):
        pais = Pais.objects.get(codigo="br")
        p = ProgressoPais.objects.create(usuario=self.usuario, pais=pais, acertos=2, erros=0)
        self.assertFalse(p.aprendido)
        p.acertos = 3
        self.assertTrue(p.aprendido)
        p.erros = 2  # 60%
        self.assertFalse(p.aprendido)

    def test_streak_diario(self):
        perfil = Perfil.objects.create(usuario=self.usuario)
        hoje = timezone.localdate()
        perfil.ultimo_dia = hoje - timedelta(days=1)
        perfil.sequencia_dias = 4
        perfil.registrar_dia()
        self.assertEqual(perfil.sequencia_dias, 5)
        perfil.registrar_dia()  # mesmo dia: não muda
        self.assertEqual(perfil.sequencia_dias, 5)
        perfil.ultimo_dia = hoje - timedelta(days=3)
        self.assertEqual(perfil.streak, 0)
        perfil.registrar_dia()
        self.assertEqual(perfil.sequencia_dias, 1)

    def test_painel_perfil_ranking_com_dados(self):
        self.jogar(acertar=True, quantidade=10)
        self.jogar(acertar=False, quantidade=5)
        painel = self.client.get(reverse("painel"))
        self.assertEqual(painel.status_code, 200)
        self.assertContains(painel, "Bandeiras que precisam de reforço")
        self.assertTrue(painel.context["mais_acertos"] and painel.context["reforco"])
        self.assertEqual(len(painel.context["semana"]), 7)
        self.assertTrue(painel.context["semana"][-1]["ativo"])
        self.assertContains(self.client.get(reverse("ranking")), "ana")
        resp = self.client.post(reverse("perfil"), {"first_name": "Ana", "last_name": "Lima", "email": "a@b.com", "avatar": "🐼"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Perfil.objects.get().avatar, "🐼")

    def test_cadastro_login_logout(self):
        self.client.logout()
        resp = self.client.post(reverse("cadastro"), {"username": "bia", "email": "", "password1": "Zq9!tR7vK2", "password2": "Zq9!tR7vK2"})
        self.assertRedirects(resp, reverse("quiz"))
        self.assertTrue(Perfil.objects.filter(usuario__username="bia").exists())
        self.assertEqual(self.client.post(reverse("logout")).status_code, 302)


class AjustesTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("leo", password="senha-forte-123")
        self.client.login(username="leo", password="senha-forte-123")

    def test_regiao_pequena_repete_para_completar_a_partida(self):
        resp = self.client.post(reverse("api_iniciar"), json.dumps({"continente": "america-sul", "quantidade": 30}),
                                content_type="application/json")
        self.assertEqual(resp.json()["total"], 30)
        ids = self.client.session["quiz"]["ids"]
        self.assertEqual(len(ids), 30)
        self.assertEqual(len(set(ids)), 12)
        self.assertTrue(all(a != b for a, b in zip(ids, ids[1:])))  # nunca o mesmo país em seguida
        # cada rodada de 12 usa todos os países antes de repetir
        self.assertEqual(len(set(ids[:12])), 12)

    def test_foco_nos_erros_tambem_repete(self):
        resp = self.client.post(reverse("api_iniciar"),
                                json.dumps({"continente": "oceania", "quantidade": 30, "foco": True}),
                                content_type="application/json")
        self.assertEqual(resp.json()["total"], 30)

    def test_header_logado(self):
        html = self.client.get(reverse("aprender")).content.decode()
        self.assertIn(f'class="marca" href="{reverse("aprender")}"', html)
        self.assertNotIn(reverse("painel"), html)
        self.assertContains(self.client.get(reverse("perfil")), reverse("painel"))
        self.assertContains(self.client.get(reverse("aprender")), 'id="modo-slide"')
        self.client.logout()
        self.assertIn(f'class="marca" href="{reverse("home")}"', self.client.get(reverse("home")).content.decode())


class SobrevivenciaTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("sam", password="senha-forte-123")
        self.client.login(username="sam", password="senha-forte-123")

    def post(self, nome, dados):
        return self.client.post(reverse(nome), json.dumps(dados), content_type="application/json")

    def iniciar(self, **extra):
        r = self.post("api_iniciar", {"modo": "sobrevivencia", **extra})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["modo"], "sobrevivencia")

    def jogada(self, acertar):
        pergunta = self.client.get(reverse("api_pergunta")).json()
        atual = self.client.session["quiz"]["atual"]
        escolha = atual["pais"] if acertar else next(i for i in atual["opcoes"] if i != atual["pais"])
        return pergunta, self.post("api_responder", {"opcao": escolha}).json()

    def test_tres_erros_encerram(self):
        self.iniciar()
        for esperado in (2, 1):
            _, r = self.jogada(False)
            self.assertFalse(r["finalizado"])
            self.assertEqual(r["vidas"], esperado)
        _, r = self.jogada(False)
        self.assertTrue(r["finalizado"])
        self.assertEqual(r["motivo"], "vidas")
        self.assertTrue(Partida.objects.get().finalizada)
        self.assertNotIn("quiz", self.client.session)

    def test_recorde(self):
        self.iniciar()
        for _ in range(6):
            _, r = self.jogada(True)
            self.assertIn("proxima_bandeira", r)
        for _ in range(3):
            _, r = self.jogada(False)
        self.assertTrue(r["finalizado"])
        self.assertEqual(r["resumo"]["acertos"], 6)
        self.assertTrue(r["resumo"]["novo_recorde"])
        self.assertEqual(Perfil.objects.get().recorde_sobrevivencia, 6)
        self.iniciar()
        for _ in range(2):
            self.jogada(True)
        for _ in range(3):
            _, r = self.jogada(False)
        self.assertFalse(r["resumo"]["novo_recorde"])
        self.assertEqual(Perfil.objects.get().recorde_sobrevivencia, 6)

    def test_tempo_esgotado_perde(self):
        self.iniciar()
        pergunta = self.client.get(reverse("api_pergunta")).json()
        self.assertEqual(pergunta["tempo"], 10)
        self.assertEqual(self.post("api_responder", {"opcao": None}).status_code, 400)  # ainda há tempo
        sessao = self.client.session
        sessao["quiz"]["atual"]["inicio"] -= 100
        sessao.save()
        r = self.post("api_responder", {"opcao": None}).json()
        self.assertTrue(r["timeout"] and r["finalizado"])
        self.assertEqual(r["motivo"], "tempo")
        self.assertEqual(ProgressoPais.objects.get().erros, 1)

    def test_resposta_tardia_conta_como_tempo_esgotado(self):
        self.iniciar()
        self.client.get(reverse("api_pergunta"))
        sessao = self.client.session
        sessao["quiz"]["atual"]["inicio"] -= 100
        sessao.save()
        escolha = self.client.session["quiz"]["atual"]["pais"]
        r = self.post("api_responder", {"opcao": escolha}).json()
        self.assertTrue(r["timeout"] and not r["correto"] and r["finalizado"])

    def test_sem_fim_e_tempo_diminui(self):
        self.iniciar(continente="america-sul")  # 12 países: a fila precisa se estender
        tempos = []
        for _ in range(40):
            pergunta, r = self.jogada(True)
            tempos.append(pergunta["tempo"])
            self.assertFalse(r["finalizado"])
        self.assertEqual(tempos[0], 10)
        self.assertEqual(tempos[5], 9)
        self.assertEqual(tempos[-1], 4)  # mínimo
        self.assertEqual(Partida.objects.get().total, 0)

    def test_classico_continua_igual(self):
        self.post("api_iniciar", {"quantidade": 5})
        pergunta = self.client.get(reverse("api_pergunta")).json()
        self.assertEqual((pergunta["modo"], pergunta["tempo"], pergunta["total"]), ("classico", None, 5))
        self.assertEqual(self.post("api_responder", {"opcao": None}).status_code, 400)


class ModalidadesTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("lia", password="senha-forte-123")
        self.client.login(username="lia", password="senha-forte-123")

    def post(self, nome, dados):
        return self.client.post(reverse(nome), json.dumps(dados), content_type="application/json")

    def jogar_uma(self, tipo):
        self.assertEqual(self.post("api_iniciar", {"tipo": tipo, "quantidade": 5}).json()["tipo"], tipo)
        pergunta = self.client.get(reverse("api_pergunta")).json()
        atual = self.client.session["quiz"]["atual"]
        r = self.post("api_responder", {"opcao": atual["pais"]}).json()
        return pergunta, r

    def test_capitais_unicas_e_mapa_cobre_todos_os_paises(self):
        from pathlib import Path
        self.assertEqual(len(set(Pais.objects.values_list("capital", flat=True))), 195)
        dados = json.loads((Path(__file__).parent / "static" / "core" / "data" / "mundo.json").read_text())
        self.assertEqual(set(dados["vistas"]), set(Pais.objects.values_list("codigo", flat=True)))

    def test_quiz_capital(self):
        pergunta, r = self.jogar_uma("capital")
        self.assertEqual(pergunta["tipo"], "capital")
        self.assertTrue(pergunta["nome"] and pergunta["bandeira"] and pergunta["codigo"] is None)
        self.assertEqual(len({o["capital"] for o in pergunta["opcoes"]}), 4)
        self.assertTrue(r["correto"])
        self.assertEqual(ProgressoPais.objects.get().tipo, "capital")

    def test_quiz_mapa_e_mapa_bandeira_contam_como_mapa(self):
        for tipo in ("mapa", "mapa-bandeira"):
            pergunta, r = self.jogar_uma(tipo)
            self.assertTrue(pergunta["codigo"] and pergunta["bandeira"] is None and pergunta["nome"] is None)
            self.assertTrue(r["correto"])
        self.assertEqual(set(ProgressoPais.objects.values_list("tipo", flat=True)), {"mapa"})
        self.assertEqual(Partida.objects.filter(tipo="mapa-bandeira").count(), 1)

    def test_progresso_separado_por_modalidade(self):
        pais = Pais.objects.get(codigo="br")
        for tipo in ("bandeira", "mapa", "capital"):
            ProgressoPais.objects.create(usuario=self.usuario, pais=pais, tipo=tipo, acertos=3)
        self.assertEqual(ProgressoPais.objects.filter(pais=pais).count(), 3)
        for tipo, rotulo in (("bandeira", "Bandeiras"), ("mapa", "Mapas"), ("capital", "Capitais")):
            resp = self.client.get(reverse("painel") + f"?tipo={tipo}")
            self.assertEqual(resp.context["rotulo_tipo"], rotulo)
            self.assertEqual(resp.context["aprendidos"], 1)
        self.assertEqual([d["aprendidos"] for d in resp.context["dominio"]], [1, 1, 1])

    def test_tipo_invalido_vira_bandeira(self):
        self.assertEqual(self.post("api_iniciar", {"tipo": "xyz"}).json()["tipo"], "bandeira")
        self.assertContains(self.client.get(reverse("quiz") + "?tipo=capital&foco=1"), 'id="t-capital" value="capital" checked')
