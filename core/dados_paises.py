"""Países atuais (193 membros da ONU + Vaticano + Palestina) com capital e região."""

_DADOS = {
    "africa": """
dz|Argélia|Argel
ao|Angola|Luanda
bj|Benim|Porto Novo
bw|Botsuana|Gaborone
bf|Burquina Fasso|Uagadugu
bi|Burundi|Gitega
cv|Cabo Verde|Praia
cm|Camarões|Iaundé
cf|República Centro-Africana|Bangui
td|Chade|N'Djamena
km|Comores|Moroni
cg|Congo|Brazavile
cd|República Democrática do Congo|Kinshasa
ci|Costa do Marfim|Iamussucro
dj|Djibuti|Djibuti
eg|Egito|Cairo
gq|Guiné Equatorial|Malabo
er|Eritreia|Asmara
sz|Essuatíni|Mbabane
et|Etiópia|Adis Abeba
ga|Gabão|Libreville
gm|Gâmbia|Banjul
gh|Gana|Acra
gn|Guiné|Conacri
gw|Guiné-Bissau|Bissau
ke|Quênia|Nairóbi
ls|Lesoto|Maseru
lr|Libéria|Monróvia
ly|Líbia|Trípoli
mg|Madagascar|Antananarivo
mw|Malawi|Lilongue
ml|Mali|Bamaco
ma|Marrocos|Rabat
mr|Mauritânia|Nouakchott
mu|Maurício|Port Louis
mz|Moçambique|Maputo
na|Namíbia|Windhoek
ne|Níger|Niamei
ng|Nigéria|Abuja
rw|Ruanda|Kigali
st|São Tomé e Príncipe|São Tomé
sn|Senegal|Dacar
sc|Seicheles|Vitória
sl|Serra Leoa|Freetown
so|Somália|Mogadíscio
za|África do Sul|Pretória
ss|Sudão do Sul|Juba
sd|Sudão|Cartum
tz|Tanzânia|Dodoma
tg|Togo|Lomé
tn|Tunísia|Túnis
ug|Uganda|Kampala
zm|Zâmbia|Lusaka
zw|Zimbábue|Harare
""",
    "america-norte": """
ag|Antígua e Barbuda|Saint John's
bs|Bahamas|Nassau
bb|Barbados|Bridgetown
bz|Belize|Belmopan
ca|Canadá|Ottawa
cr|Costa Rica|San José
cu|Cuba|Havana
dm|Dominica|Roseau
sv|El Salvador|San Salvador
us|Estados Unidos|Washington, D.C.
gd|Granada|Saint George's
gt|Guatemala|Cidade da Guatemala
ht|Haiti|Porto Príncipe
hn|Honduras|Tegucigalpa
jm|Jamaica|Kingston
mx|México|Cidade do México
ni|Nicarágua|Manágua
pa|Panamá|Cidade do Panamá
do|República Dominicana|Santo Domingo
kn|São Cristóvão e Névis|Basseterre
lc|Santa Lúcia|Castries
vc|São Vicente e Granadinas|Kingstown
tt|Trinidad e Tobago|Port of Spain
""",
    "america-sul": """
ar|Argentina|Buenos Aires
bo|Bolívia|Sucre
br|Brasil|Brasília
cl|Chile|Santiago
co|Colômbia|Bogotá
ec|Equador|Quito
gy|Guiana|Georgetown
py|Paraguai|Assunção
pe|Peru|Lima
sr|Suriname|Paramaribo
uy|Uruguai|Montevidéu
ve|Venezuela|Caracas
""",
    "asia": """
af|Afeganistão|Cabul
sa|Arábia Saudita|Riade
am|Armênia|Erevan
az|Azerbaijão|Baku
bh|Bahrein|Manama
bd|Bangladesh|Daca
bt|Butão|Timbu
bn|Brunei|Bandar Seri Begawan
kh|Camboja|Phnom Penh
kz|Cazaquistão|Astana
qa|Catar|Doha
cn|China|Pequim
sg|Singapura|Singapura
kp|Coreia do Norte|Pyongyang
kr|Coreia do Sul|Seul
ae|Emirados Árabes Unidos|Abu Dhabi
ph|Filipinas|Manila
ge|Geórgia|Tbilisi
ye|Iêmen|Sanaa
in|Índia|Nova Délhi
id|Indonésia|Jacarta
ir|Irã|Teerã
iq|Iraque|Bagdá
il|Israel|Jerusalém
jp|Japão|Tóquio
jo|Jordânia|Amã
kw|Kuwait|Cidade do Kuwait
la|Laos|Vienciana
lb|Líbano|Beirute
my|Malásia|Kuala Lumpur
mv|Maldivas|Malé
mn|Mongólia|Ulan Bator
mm|Mianmar|Naypyidaw
np|Nepal|Catmandu
om|Omã|Mascate
pk|Paquistão|Islamabad
ps|Palestina|Ramala
kg|Quirguistão|Bisqueque
sy|Síria|Damasco
lk|Sri Lanka|Sri Jayawardenapura Kotte
tj|Tadjiquistão|Duchambe
th|Tailândia|Bangcoc
tl|Timor-Leste|Díli
tm|Turcomenistão|Asgabate
tr|Turquia|Ancara
uz|Uzbequistão|Tasquente
vn|Vietnã|Hanói
""",
    "europa": """
al|Albânia|Tirana
de|Alemanha|Berlim
ad|Andorra|Andorra a Velha
at|Áustria|Viena
by|Bielorrússia|Minsk
be|Bélgica|Bruxelas
ba|Bósnia e Herzegovina|Saraievo
bg|Bulgária|Sófia
hr|Croácia|Zagreb
cy|Chipre|Nicósia
dk|Dinamarca|Copenhague
sk|Eslováquia|Bratislava
si|Eslovênia|Liubliana
es|Espanha|Madri
ee|Estônia|Tallinn
fi|Finlândia|Helsinque
fr|França|Paris
gr|Grécia|Atenas
hu|Hungria|Budapeste
ie|Irlanda|Dublin
is|Islândia|Reykjavik
it|Itália|Roma
lv|Letônia|Riga
li|Liechtenstein|Vaduz
lt|Lituânia|Vilnius
lu|Luxemburgo|Luxemburgo
mk|Macedônia do Norte|Escópia
mt|Malta|Valeta
md|Moldávia|Chisinau
mc|Mônaco|Mônaco
me|Montenegro|Podgorica
no|Noruega|Oslo
nl|Países Baixos|Amsterdã
pl|Polônia|Varsóvia
pt|Portugal|Lisboa
gb|Reino Unido|Londres
cz|Tchéquia|Praga
ro|Romênia|Bucareste
ru|Rússia|Moscou
sm|San Marino|San Marino
rs|Sérvia|Belgrado
se|Suécia|Estocolmo
ch|Suíça|Berna
ua|Ucrânia|Kiev
va|Vaticano|Cidade do Vaticano
""",
    "oceania": """
au|Austrália|Camberra
fj|Fiji|Suva
ki|Kiribati|Tarawa Sul
mh|Ilhas Marshall|Majuro
sb|Ilhas Salomão|Honiara
fm|Micronésia|Palikir
nr|Nauru|Yaren
nz|Nova Zelândia|Wellington
pw|Palau|Ngerulmud
pg|Papua-Nova Guiné|Port Moresby
ws|Samoa|Apia
to|Tonga|Nuku'alofa
tv|Tuvalu|Funafuti
vu|Vanuatu|Port Vila
""",
}

# (codigo ISO, nome, capital, continente)
PAISES = [
    (cod, nome, capital, continente)
    for continente, bloco in _DADOS.items()
    for linha in bloco.strip().splitlines()
    for cod, nome, capital in [linha.split("|")]
]
