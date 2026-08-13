# Prompt para o Claude Code — leva de ajustes de UI e limpeza

Cole **chunk por chunk**, na ordem, rodando `pytest -q` e (quando envolver
cálculo) `python validar.py` ao fim de cada um. Commit por chunk.

## Contexto e regras

```
Você vai aplicar uma série de correções de interface e limpeza no SoloRef
(PySide6). Leia MANUAL_SOLOREF.md e GUIA_DESENVOLVEDOR.md antes.

Arquitetura: core/ (Python puro, cálculos) × ui/ (PySide6, janela de 3 painéis).
Módulos-chave: ui/panels.py (PainelDados = abas; PainelResultados = cartões),
ui/main_window.py (navbar, métodos), ui/relevancia.py (quais abas cada método
usa), ui/dialogs/entrada_dados.py (widgets _Aba*), ui/dialogs/esquema_widget.py
(desenho do muro), core/models.py (dataclasses).

REGRAS:
1. NÃO altere as fórmulas dos métodos. `python validar.py` deve continuar 100%
   verde. `pytest` não pode regredir; ATUALIZE os testes afetados.
2. Um chunk por vez; rode os testes ao fim de cada um.
3. Onde remover um campo do modelo, garanta que carregar() JSON antigo (com o
   campo) não quebre — ignore chaves desconhecidas.
```

---

### Chunk 1 — Remover as abas "Face" e "Identificação" (UI + modelo)

```
Remova por completo as abas Face e Identificação — elas não entram em nenhum
cálculo e a identificação é redundante com o Salvar.

core/models.py: remova as dataclasses FaceEstrutura e Identificacao e os campos
`face` e `identificacao` de Projeto.
core/persistence.py: ao carregar, IGNORE chaves desconhecidas do JSON (ex.:
projetos antigos com "face"/"identificacao") — filtre por campos existentes de
cada dataclass antes de reconstruir, para não quebrar arquivos salvos antigos.
ui/panels.py: remova aba_face, aba_identif, suas entradas em _ABAS_ORDENADAS, a
chamada _marcar_reservada(self.aba_face), as entradas correspondentes no laço de
ajuda "?" e no _ligar_live_update (sinais de identificação).
ui/dialogs/entrada_dados.py: remova as classes _AbaFace e _AbaIdentificacao e o
uso delas em EntradaDadosDialog (se ainda existir), e o `face=`/`identificacao=`
em resultado().
ui/relevancia.py: remova ABA_FACE e ABA_IDENTIFICACAO (e de ABAS_RESERVADAS).
ui/dialogs/quadro_resumo.py: se alguma linha usa identificação/face, remova.
tests: atualize test_models.py e qualquer caso em tests/ que referencie face/
identificação; adicione um teste de que carregar um JSON com chave "face" antiga
NÃO quebra (é ignorada).

Aceite: pytest e validar.py verdes; app abre com 6 abas (Geometria, Solo aterro,
Solo encosta, Solo fundação, Sobrecarga, Reforço).
```

---

### Chunk 2 — Bishop e sobrecarga: corrigir o destaque (o cálculo já está certo)

```
IMPORTANTE: o Bishop JÁ considera a sobrecarga q no cálculo (core/methods/
bishop.py passa q e o FS muda com q — confirmado: FS cai de 1,77 para 1,15 com
q=0→100 kPa). O problema é só o destaque: ui/relevancia.py lista "Bish" sem a
aba Sobrecarga, então ela aparece atenuada, dando a impressão de que é ignorada.

Correção: em ui/relevancia.py, inclua ABA_SOBRECARGA (campo "q") no mapa do
"Bish". Atualize o texto de ajuda "?" da aba (em ui/panels.py, dict _AJUDA) e o
manual para dizer que Bishop usa q. Amplie test_relevancia.py para checar que
"Bish" inclui sobrecarga.

(Refinamento OPCIONAL, se quiser: aplicar q só sobre a crista horizontal do
talude, não sobre as fatias da face inclinada — mas isso muda números; se fizer,
ajuste os testes/validar. Se não, deixe como está, que já é conservador.)

Aceite: com Bishop ativo, a aba Sobrecarga fica destacada; testes verdes.
```

---

### Chunk 3 — Corrigir o bug do "recalcular"/"registrar" na Estabilidade externa

```
Bug: a Estabilidade externa não altera `_metodo_atual` (que continua sendo o
último método de cunha). Os botões "Calcular/recalcular" e "Registrar no quadro"
do PainelResultados estão ligados a _calcular(self._metodo_atual) e
_mostrar_metodo(self._metodo_atual) — que recalculam o método de CUNHA, não a
externa. Por isso, ao recalcular vendo a externa, ela "volta" para a Rankine.

Correção em ui/main_window.py: rastreie o modo/análise ativo (ex.: um atributo
self._analise_atual que guarda ou o índice do método de cunha ou um marcador de
"externa", ou uma callable de "recalcular o que está na tela"). Faça o botão
Calcular recalcular a ANÁLISE ATUAL (incluindo a externa) e o botão Registrar
gravar a análise atual no Quadro Resumo (para a externa, usar
resultado_para_resumo(MetodoEstabilidadeExterna, ...), que já existe).
Atualize _selecionar_metodo / _calcular_externa para setar esse estado.

Aceite: selecionar Estabilidade externa, clicar Calcular → continua na externa;
Registrar → grava os 3 FS da externa no quadro. Métodos de cunha seguem normais.
```

---

### Chunk 4 — Esquema ilustrativo: B proporcional + rótulo do i + arcos dos ângulos

```
Em ui/dialogs/esquema_widget.py:

(a) B proporcional: hoje a escala usa uma largura aproximada (ex.: B*2.2), o que
faz o desenho reescalar sem B "crescer" de forma proporcional. Troque por
FIT-TO-CONTENT: calcule a caixa delimitadora (bounding box) REAL de todos os
pontos do muro em coordenadas de mundo (incluindo x_face + B + x_enc na
horizontal e H + Ht na vertical), e aplique uma ÚNICA escala uniforme que faça
essa caixa caber no painel com margens. Assim B, H e Ht ficam em proporção
correta entre si e o desenho continua cabendo no quadro.

(b) Rótulo do i: desenhe o rótulo "i" junto ao talude do topo quando i ≠ 0
(hoje o topo inclina, mas não há legenda). Mantenha "Ht" já condicional a Ht>0.

(c) Arcos dos ângulos: para cada ângulo mostrado (β na face, βe na encosta, i no
topo), desenhe um pequeno ARCO (QPainter.drawArc / QPainterPath.arcTo) indicando
a região do ângulo, além da letra. Só desenhe o arco de i quando i≠0.

Aceite: mudar B muda visivelmente a largura do muro (mantendo tudo dentro do
quadro); i e Ht aparecem rotulados quando ≠0; β, βe e i têm arco. (Sem teste
numérico — confira visualmente e não quebre pytest/validar.)
```

---

### Chunk 5 — Polimento visual

```
(a) Remover o vermelho do B: em ui/dialogs/entrada_dados.py, no _AbaGeometria, o
rótulo de B usa cor vermelha (#b00). Remova o setStyleSheet vermelho e deixe o
rótulo normal, com o símbolo — algo como "Largura do aterro, B (m)".

(b) Cor de destaque adaptável a tema claro/escuro: em ui/panels.py, o
_COR_RELEVANTE é um azul fixo (#0b3d91) que não se adapta ao modo escuro. Troque
por uma cor derivada da PALETA do sistema (ex.: self.palette().color(
QPalette.Highlight) ou QPalette.Link), que funciona em claro e escuro, E reforce
o destaque com NEGRITO na aba relevante (não depender só de cor — acessibilidade).
As abas não relevantes voltam à cor padrão do tema (sem cor fixa).

(c) Retirar "(novo)" do Bishop: em ui/main_window.py, o rótulo da ação é
"Método de &Bishop (novo)" — troque para "Método de &Bishop". Se houver "(novo)"
em outros rótulos (ex.: em metodo_info.py), remova também.

(d) Remover o botão "Hipóteses / figura": em ui/panels.py (PainelResultados),
remova o botão btn_hip e o sinal verHipoteses; em ui/main_window.py remova a
conexão e o método _ver_hipoteses (e o import de MetodoInfoDialog se ficar sem
uso). MANTENHA a área de texto "Hipóteses do método" no painel de resultados (que
mostra metodo.hipoteses) — é ela que passa a cumprir esse papel. Garanta que as
hipoteses de cada método estejam completas e claras (revise as tuplas
`hipoteses` em core/methods/*.py se necessário).

Aceite: B sem vermelho; destaque de aba legível em tema claro e escuro (com
negrito); sem "(novo)"; sem botão Hipóteses/figura, mas o texto de hipóteses
continua no painel. pytest/validar verdes.
```

---

### Chunk 6 — Verificação e documentação

```
1. Rode `pytest -q` e `python validar.py` — tudo verde.
2. Rode o app: confira as 6 abas, o destaque de aba (claro/escuro), o esquema
   (B proporcional, i/Ht rotulados, arcos), a estabilidade externa (recalcular/
   registrar), Bishop com sobrecarga (aba destacada e FS mudando com q).
3. Atualize MANUAL_SOLOREF.md e GUIA_DESENVOLVEDOR.md: remoção das abas Face e
   Identificação; Bishop usa sobrecarga; botão Hipóteses/figura removido (as
   hipóteses ficam no painel de resultados); ajustes do esquema. NÃO preencha a
   Parte III.
```

---

### Ordem e dependências

O Chunk 1 (remoção de campos do modelo) é o mais delicado — faça primeiro, com
os testes verdes, porque mexe em persistência. Os demais são independentes entre
si. Um commit por chunk; se algo regredir, `validar.py`/`pytest` acusam na hora.
```
