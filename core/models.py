from django.conf import settings
from django.db import models
from django.templatetags.static import static
from django.utils import timezone

from .utils import normalizar

CONTINENTES = [
    ("africa", "África"),
    ("america-norte", "América do Norte e Central"),
    ("america-sul", "América do Sul"),
    ("asia", "Ásia"),
    ("europa", "Europa"),
    ("oceania", "Oceania"),
]
ROTULO_CONTINENTE = dict(CONTINENTES)
EMOJI_CONTINENTE = {
    "africa": "🌍", "america-norte": "🌎", "america-sul": "🌎",
    "asia": "🌏", "europa": "🌍", "oceania": "🌏",
}

AVATARES = ["🦊", "🐼", "🦁", "🐯", "🐸", "🐙", "🦉", "🐧", "🐨", "🦄", "🐳", "🦋"]

NIVEIS = [
    (0, "Iniciante"),
    (150, "Explorador"),
    (500, "Viajante"),
    (1200, "Navegador"),
    (2500, "Cartógrafo"),
    (5000, "Diplomata"),
    (10000, "Mestre das Bandeiras"),
]

# Um país conta como "aprendido" com 3+ acertos e 70%+ de aproveitamento.
# Modalidades de treino. "mapa-bandeira" (mapa -> escolher a bandeira) conta no progresso de mapas.
TIPOS = [("bandeira", "Bandeiras"), ("mapa", "Mapas"), ("capital", "Capitais")]
ROTULO_TIPO = dict(TIPOS)
TIPOS_QUIZ = {"bandeira": "bandeira", "mapa": "mapa", "mapa-bandeira": "mapa", "capital": "capital"}

MIN_ACERTOS_APRENDIDO = 3
MIN_TAXA_APRENDIDO = 70


class Pais(models.Model):
    codigo = models.CharField("código ISO", max_length=2, unique=True)
    nome = models.CharField(max_length=80)
    capital = models.CharField(max_length=80)
    continente = models.CharField(max_length=20, choices=CONTINENTES)

    class Meta:
        ordering = ["nome"]
        verbose_name = "país"
        verbose_name_plural = "países"

    def __str__(self):
        return self.nome

    @property
    def bandeira_url(self):
        return static(f"core/flags/{self.codigo}.svg")

    @property
    def rotulo_continente(self):
        return ROTULO_CONTINENTE.get(self.continente, "")

    @classmethod
    def ordenados(cls, **filtros):
        """Lista em ordem alfabética, ignorando acentos."""
        return sorted(cls.objects.filter(**filtros), key=lambda p: normalizar(p.nome))


class Perfil(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil")
    avatar = models.CharField(max_length=8, default=AVATARES[0])
    pontos = models.PositiveIntegerField(default=0)
    acertos = models.PositiveIntegerField(default=0)
    erros = models.PositiveIntegerField(default=0)
    sequencia_dias = models.PositiveIntegerField(default=0)
    melhor_sequencia_dias = models.PositiveIntegerField(default=0)
    melhor_sequencia_acertos = models.PositiveIntegerField(default=0)
    recorde_sobrevivencia = models.PositiveIntegerField(default=0)
    ultimo_dia = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Perfil de {self.usuario}"

    @property
    def streak(self):
        """Sequência de dias ativa (zera se o usuário ficou um dia inteiro sem treinar)."""
        if self.ultimo_dia and (timezone.localdate() - self.ultimo_dia).days <= 1:
            return self.sequencia_dias
        return 0

    @property
    def praticou_hoje(self):
        return self.ultimo_dia == timezone.localdate()

    @property
    def taxa_acerto(self):
        total = self.acertos + self.erros
        return round(self.acertos * 100 / total) if total else 0

    @property
    def nivel(self):
        atual = max(i for i, (minimo, _) in enumerate(NIVEIS) if self.pontos >= minimo)
        minimo, titulo = NIVEIS[atual]
        if atual + 1 < len(NIVEIS):
            prox_minimo, prox_titulo = NIVEIS[atual + 1]
            percentual = int((self.pontos - minimo) * 100 / (prox_minimo - minimo))
            faltam = prox_minimo - self.pontos
        else:
            prox_titulo, percentual, faltam = None, 100, 0
        return {"numero": atual + 1, "titulo": titulo, "proximo": prox_titulo,
                "percentual": percentual, "faltam": faltam}

    def registrar_dia(self):
        """Atualiza o streak diário na primeira resposta do dia."""
        hoje = timezone.localdate()
        if self.ultimo_dia == hoje:
            return
        if self.ultimo_dia and (hoje - self.ultimo_dia).days == 1:
            self.sequencia_dias += 1
        else:
            self.sequencia_dias = 1
        self.ultimo_dia = hoje
        self.melhor_sequencia_dias = max(self.melhor_sequencia_dias, self.sequencia_dias)


class ProgressoPais(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="progresso")
    pais = models.ForeignKey(Pais, on_delete=models.CASCADE, related_name="progresso")
    tipo = models.CharField(max_length=10, choices=TIPOS, default="bandeira")
    acertos = models.PositiveIntegerField(default=0)
    erros = models.PositiveIntegerField(default=0)
    ultima_resposta = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("usuario", "pais", "tipo")]
        verbose_name = "progresso por país"
        verbose_name_plural = "progresso por país"

    def __str__(self):
        return f"{self.usuario} · {self.pais}"

    @property
    def total(self):
        return self.acertos + self.erros

    @property
    def taxa(self):
        return round(self.acertos * 100 / self.total) if self.total else 0

    @property
    def aprendido(self):
        return self.acertos >= MIN_ACERTOS_APRENDIDO and self.acertos * 100 >= MIN_TAXA_APRENDIDO * self.total


class Partida(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="partidas")
    continente = models.CharField(max_length=20, blank=True)  # vazio = todos
    modo = models.CharField(max_length=14, default="classico")  # classico | sobrevivencia
    tipo = models.CharField(max_length=14, default="bandeira")  # bandeira | mapa | mapa-bandeira | capital
    total = models.PositiveSmallIntegerField()
    respondidas = models.PositiveSmallIntegerField(default=0)
    acertos = models.PositiveSmallIntegerField(default=0)
    pontos = models.PositiveIntegerField(default=0)
    melhor_sequencia = models.PositiveSmallIntegerField(default=0)
    finalizada = models.BooleanField(default=False)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criada_em"]

    def __str__(self):
        return f"Partida #{self.pk} de {self.usuario}"

    @property
    def sobrevivencia(self):
        return self.modo == "sobrevivencia"

    @property
    def rotulo_continente(self):
        return ROTULO_CONTINENTE.get(self.continente, "Mundo todo")
