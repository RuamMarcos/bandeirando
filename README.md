# 1. Bandeirando

Site em Django para aprender e treinar as bandeiras dos 195 países atuais (193 da ONU + Vaticano + Palestina). Tudo em português - Brasil.

<img width="1000" height="600" alt="Untitled" src="https://github.com/user-attachments/assets/d81e6709-7ef4-4c15-923c-5c902413bcf3" />
<br>

# 2. Como roda a Aplicação

É necessário ter o python instalado na versão 3.11+.

#### No terminal:
```
python -m venv .venv
source .venv/bin/activate # Windows: .venv/Scripts/activate
ppip install -r requirements.txt
python manage.py migrate #vai criar o banco e carregar os 195 países
python manage.py runserver
```
Acesse a url no navegador: ```http://127.0.0.1:8000```, crie um login e poderá aproveitar os recursos!

Para acessar o admin:
```
python manage.py createsuperuser
```
e vá em /admin/

Para rodar os teste:
```
python manage.py test
```

# 3. Recursos

- *Aprender:* Todas as bandeiras com nome, capitale região. Busca, filtro por várias regiões ao mesmo tempo, modo slides (ótimo para detalhes), embalhar e detalhes em janela pop-up.
- *Quiz Clássico:* 4 alternativas, agrupar por continente, com 10|20|30 perguntas e  opção de priorizar pontos fracos.
- *Quiz sobrevivência>* Desafio cronometrado, com três vidas tolerantes a erro. Guarda o seu recorde.
- *Pontuação:* +10 por acerto, +5 de rapidez (menos de 10s) e até +5 por combo.
- *Streak:* Sistema de ofensiva, acumula por dias seguidos. (zera se ficar um dia inteiro sem jogar, sistema que incentiva a consistência).
- *País aprendido:* Um país é considerado aprendido se tiver 3 ou mais acertos com 70% ou mais de aproveitamento. 
- *Painel:* Painel presente no perfil do usuário, com pontos, streak, países aprendidos, aproveitamento, gráfico dos últimos 14 dias, semana ativa, países que mais acerta, países que precisa de reforço, progresso por região, recorde de sobrevivência e últimas partidas.
- *Elementos Básicos:* Login; Perfil; Cadastro e Logout; Tema Claro e Escuro; Layout responsivo.



---

Espero que aprenda e divirta-se com minha aplicação!! 
