# Guia do desenvolvedor — SoloRef

Este guia descreve, arquivo por arquivo, o que existe no projeto e
**onde mexer** para alterar cada coisa. Use o sumário como atalho.

---

## Sumário

- [1. Visão geral da arquitetura](#1-visão-geral-da-arquitetura)
- [2. Estrutura de pastas](#2-estrutura-de-pastas)
- [3. O que cada arquivo faz](#3-o-que-cada-arquivo-faz)
  - [3.1 Raiz do projeto](#31-raiz-do-projeto)
  - [3.2 `soloref/core/` — modelos e cálculos](#32-soloref-core--modelos-e-cálculos)
  - [3.3 `soloref/core/methods/` — métodos de análise](#33-soloref-core-methods--métodos-de-análise)
  - [3.4 `soloref/ui/` — interface PySide6](#34-soloref-ui--interface-pyside6)
  - [3.5 `tests/`](#35-tests)
- [4. Fluxo de execução](#4-fluxo-de-execução)
- [5. Cookbook — onde mexer para...](#5-cookbook--onde-mexer-para)
- [6. Convenções de código](#6-convenções-de-código)
- [7. Como rodar os testes](#7-como-rodar-os-testes)

---

## 1. Visão geral da arquitetura

O projeto está dividido em **duas camadas** bem separadas:

```
┌───────────────────────────────┐
│   soloref/ui/   (PySide6)     │  ← janelas, diálogos, desenho
└────────────┬──────────────────┘
             │ usa
             ▼
┌───────────────────────────────┐
│   soloref/core/ (Python puro) │  ← modelos + cálculos + persistência
└───────────────────────────────┘
```

**Por que essa separação importa:**

- A camada `core/` **não importa nada do PySide6**. Você consegue rodar
  os cálculos em script, em testes automatizados, em uma futura
  interface web ou em linha de comando, sem mexer em uma linha sequer.
- A camada `ui/` só sabe **mostrar** os dados e disparar os cálculos.
  Se você decidir trocar PySide6 por outra biblioteca (Tkinter, Web,
  etc.), todo o `core/` é reaproveitado.
- Para testar um método novo, você só precisa de `pytest` — não precisa
  abrir janela nenhuma.

---

## 2. Estrutura de pastas

```
SoloRef/
├── main.py                       ← ponto de entrada (`python main.py`); também configura logging
├── validar.py                    ← runner de validação ("teste completo") — python validar.py
├── requirements.txt              ← dependências (PySide6, numpy, matplotlib, scipy, pytest)
├── README.md                     ← descrição do projeto
├── GUIA_DESENVOLVEDOR.md         ← (este arquivo)
├── PLANO_IMPLEMENTACAO.md        ← fórmulas, decisões de modelagem e status de cada método
├── RELATORIO_VALIDACAO.md        ← gerado por validar.py (não editar à mão)
│
├── soloref/                      ← pacote principal
│   ├── __init__.py               ← versão do pacote
│   ├── __main__.py               ← permite `python -m soloref`
│   │
│   ├── core/                     ← MODELOS + CÁLCULOS (sem Qt)
│   │   ├── __init__.py           ← reexporta as classes principais
│   │   ├── models.py             ← dataclasses (Projeto, Solo, Geometria, Reforco, …)
│   │   ├── persistence.py        ← salvar/carregar JSON
│   │   └── methods/              ← um arquivo por método, todos implementados
│   │       ├── __init__.py
│   │       ├── base.py           ← classe abstrata MetodoAnalise + Resultado + avisos()
│   │       ├── coulomb.py        ← fórmula fechada + busca de cunha (trial wedge)
│   │       ├── rankine.py        ← fórmula fechada (horizontal e talude)
│   │       ├── dois_blocos.py    ← cunha bilinear, busca numérica (sem fórmula fechada)
│   │       ├── bishop.py         ← fatias + iteração de FS, busca do círculo crítico
│   │       ├── geossintetico.py  ← dimensionamento de camadas (equilíbrio-limite/tieback)
│   │       └── estabilidade_externa.py  ← bloco rígido: deslizamento/tombamento/capacidade (Vésic)
│   │
│   └── ui/                       ← INTERFACE (PySide6) — janela única de 3 painéis
│       ├── __init__.py
│       ├── main_window.py        ← janela, navbar única, cálculo (c/ cache), log
│       ├── panels.py             ← PainelDados (6 abas) e PainelResultados (cartões)
│       ├── relevancia.py         ← SEM Qt: quais abas cada método consome
│       ├── interpretacao.py      ← SEM Qt: cartões + selos de julgamento
│       ├── resumo_map.py         ← SEM Qt: Resultado -> linhas do Quadro Resumo
│       ├── estado_projeto.py     ← SEM Qt: "há alterações não salvas?"
│       ├── cache_resultados.py   ← SEM Qt: cache de Resultado por método
│       ├── geometria_segura.py   ← SEM Qt: divisão segura por tangente (esquema)
│       └── dialogs/
│           ├── __init__.py
│           ├── entrada_dados.py    ← as classes `_Aba*` (reaproveitadas por panels.py);
│           │                         `EntradaDadosDialog` é resíduo da versão MDI, não usado
│           ├── esquema_widget.py   ← desenho do muro + superfície crítica do método ativo
│           ├── metodo_info.py      ← diálogo "Hipóteses / figura" — resíduo, não usado
│           │                         (botão removido; hipóteses aparecem em panels.py)
│           └── quadro_resumo.py    ← tabela das últimas 8 situações (27 linhas)
│
└── tests/
    ├── __init__.py
    ├── casos_literatura.py            ← dataset de casos de validação (fonte de verdade)
    ├── casos_referencia_original.csv  ← conferência opcional com o programa original (vazio por padrão)
    ├── test_models.py                 ← smoke test do core
    ├── test_{rankine,coulomb,dois_blocos,bishop,geossintetico,degeneracia}.py
    ├── test_validade.py               ← MetodoAnalise.avisos() de cada método
    └── test_{relevancia,interpretacao,resumo_map,estado_projeto,cache_resultados}.py
                                        ← lógica de ui/ sem Qt (mesmo padrão do core)
```

---

## 3. O que cada arquivo faz

### 3.1 Raiz do projeto

| Arquivo | Função | Quando mexer |
|---|---|---|
| `main.py` | Cria o `QApplication`, configura logging (`logs/soloref_app.log`), instancia a `MainWindow` e roda o `app.exec()`. É o ponto de entrada. | Quase nunca — só se quiser mudar nome da aplicação, parâmetros globais do Qt, ou o formato do log. |
| `validar.py` | Runner de validação: roda todos os casos de `tests/casos_literatura.py` (+ `tests/casos_referencia_original.csv` se tiver linhas), compara com o esperado e gera `RELATORIO_VALIDACAO.md` + log em `logs/`. | Quando adicionar um caso novo ao dataset e quiser ver o relatório atualizado; raramente precisa mexer na lógica do runner em si. |
| `requirements.txt` | Lista as dependências instaláveis via `pip` (PySide6, numpy, matplotlib, scipy, pytest). | Quando adicionar uma nova lib. |
| `README.md` | Descrição do projeto, instruções de instalação e de como rodar os testes/validação. | Quando quiser comunicar status do projeto a outros. |

### 3.2 `soloref/core/` — modelos e cálculos

| Arquivo | Função | Quando mexer |
|---|---|---|
| `models.py` | Define **todas as estruturas de dados** do projeto: `Geometria`, `Solo`, `Sobrecarga`, `Reforco` (parâmetros do geossintético) e `Projeto` (que agrega tudo). São `@dataclass` — Python já gera `__init__`, `__repr__`, comparação, etc. `Identificacao` e `FaceEstrutura` existiram aqui, mas foram removidas (nenhum método as lia). | Quando adicionar um novo campo de entrada (ex.: nível d'água), uma nova categoria de solo, ou um novo tipo de sobrecarga. **Atenção:** mudar aqui geralmente exige mudança correspondente em `entrada_dados.py` (UI) e `persistence.py` (carregar arquivos antigos — ver `_filtra_campos`, que ignora seções/campos desconhecidos ao carregar). |
| `persistence.py` | Salva/carrega o `Projeto` em **JSON**. Usa `dataclasses.asdict()` para serializar. Formato legível, versionável em git, melhor que binário proprietário. `carregar()` usa `data.get(secao, {})` (seção ausente vira `{}`, os defaults da dataclass cobrem o resto) **e** `_filtra_campos(cls, dados)` (mantém só as chaves de `dados` que batem com `dataclasses.fields(cls)`) antes de reconstruir cada seção — então tanto uma seção inteira quanto um campo específico que saíram de uma dataclass (ex.: as extintas `face`/`identificacao`) são ignorados, em vez de quebrar com `TypeError`/`KeyError` ao abrir um arquivo antigo. | Se quiser mudar o formato do arquivo (ex.: YAML), versionar o schema, ou adicionar migração de versões antigas. **Sempre** que adicionar uma seção nova em `models.py`, adicionar aqui também (em `carregar()`), senão ela nunca é lida de volta — remover uma seção não exige nada aqui, `_filtra_campos` cuida sozinho. |
| `__init__.py` | Reexporta as classes principais para que se possa fazer `from soloref.core import Projeto` sem precisar saber o caminho interno. | Quando criar um novo modelo importante. |

### 3.3 `soloref/core/methods/` — métodos de análise

| Arquivo | Função | Quando mexer |
|---|---|---|
| `base.py` | Define `MetodoAnalise` (classe abstrata com método `calcular(projeto) → Resultado`) e a dataclass `Resultado` (com `solicitacao_kN_m`, `inclinacao_cunha_g`, `fator_seguranca`, e um dict `extras` para dados específicos). | Se quiser mudar a interface comum a todos os métodos (ex.: adicionar um parâmetro de tolerância de iteração, ou um método `desenhar(painter)` para desenho específico de cada cunha). |
| `coulomb.py` | `MetodoCoulomb` — **implementado**. Ka geral fechado (θ=90−β, δ, i) + `Ea = ½γH²Ka + KaqH`. Além disso, uma busca de cunha independente (trial wedge/Culmann, via equilíbrio de forças da cunha tentativa) que serve de conferência cruzada — o Ea da busca é comparado ao da fórmula fechada nos testes. | Ajustar a convenção de sobrecarga, adicionar coesão à fórmula geral, ou revisar a faixa de validade (70°≤β≤90°). |
| `rankine.py` | `MetodoRankine` — **implementado**. `Ka=(1-senφ)/(1+senφ)` (horizontal) ou forma de talude (i≠0, c=0); `Ea`, cunha (45+φ/2) e `z0` (trinca de tração, com coesão). | Estender para retroaterro inclinado **com** coesão (hoje só a forma sem coesão está implementada para i≠0). |
| `dois_blocos.py` | `MetodoDoisBlocos` — **implementado**, sem fórmula fechada. Cunha bilinear tipo "two-part wedge": interface vertical entre os dois blocos, força de interação horizontal (simplificação documentada no módulo). Busca da superfície crítica por grade + `scipy.optimize`. | Ver a limitação documentada no topo do arquivo (δ próximo de φ fica ~10-15% acima de Coulomb, não os ~1-3% típicos) antes de mexer na busca. |
| `bishop.py` | `MetodoBishop` — **implementado**. Fatias sobre um círculo restrito a passar pelo pé do talude ("toe circle" — reduz a busca a 2 parâmetros, centro (xc,yc)); FS por iteração de ponto fixo (`mα`); busca do círculo crítico por grade + refino. Reaproveita `inclinacao_face_beta_g` como ângulo do talude (não da parede) — ver ressalva no docstring. | Generalizar para círculos que não passam pelo pé, ou separar o campo de ângulo do talude do campo de ângulo da parede em `models.py`. |
| `geossintetico.py` | `MetodoGeossintetico` — **implementado**. Equilíbrio-limite/tieback estilo FHWA GEC-011: `σv`, `σh=Ka·σv`, `Tadm` com os 3 fatores de redução, `La`/`Le`. Espaçamento uniforme dimensionado pela condição mais crítica (base do maciço); profundidade de cada camada é o **ponto médio** da zona tributária (não o topo) — é isso que faz `ΣTmax` reproduzir Rankine quase exatamente, ver docstring do módulo. | Implementar espaçamento variável por camada (método FHWA completo, hoje simplificado para uniforme), ou compor com Coulomb/Dois Blocos em vez de só Rankine. |
| `estabilidade_externa.py` | `MetodoEstabilidadeExterna` — **implementado**. Trata o maciço reforçado como bloco rígido: deslizamento (`Fr=(N+Pav)·tanφ_base+c_base·B`), tombamento (`M_estab/M_tomb`, excentricidade `e`) e capacidade de carga (Vésic, `B'=B-2e`, fatores `Nc/Nq/Nγ` numa função pura `fatores_vesic`). O empuxo motor **reaproveita `MetodoRankine.calcular()`** sobre um `Projeto` temporário com `solo_aterro=solo_encosta` — não duplica Ka. Único método cujo construtor aceita argumento (`fonte_phi_base="fundacao"` ou `"aterro"`) — necessário pro benchmark EXT-REF-01 (Wesley). | Mudar a fonte de φ_base/c_base, generalizar a capacidade de carga (hoje só sapata corrida), ou expor `fonte_phi_base` na UI (hoje só configurável instanciando a classe direto, ex. em testes). |
| `__init__.py` | Reexporta todas as classes de método. | Quando criar um novo método, adicionar import aqui. |

**Padrão para implementar um cálculo real**: ver seção 5.1 (Cookbook) — o exemplo ali
já é essencialmente o que está em `coulomb.py`/`rankine.py` de verdade hoje.

### 3.4 `soloref/ui/` — interface PySide6

A UI é uma janela única de três painéis (`main_window.py` + `panels.py`), não
mais a metáfora MDI original. Boa parte da lógica de decisão (não de desenho)
foi tirada dos widgets e colocada em módulos **sem import de Qt** —
`relevancia.py`, `interpretacao.py`, `resumo_map.py`, `estado_projeto.py`,
`cache_resultados.py` — seguindo a mesma regra de `core/`: se dá pra testar
sem abrir janela, não deveria precisar de Qt para existir. Widgets só chamam
essas funções e desenham o resultado.

#### `main_window.py`

A janela principal (`MainWindow`, herda de `QMainWindow`). Contém:

- **Menus**: Sistema, Dimensionamento, Relatórios, Janelas, Ajuda.
- **Navbar única** (`QToolBar`, espelhada no menu Dimensionamento), nomes
  completos: Entrada de dados · os cinco métodos (como `QAction` checkáveis
  num `QActionGroup` — funcionam como abas exclusivas) · Comparar métodos ·
  Estabilidade externa · Quadro Resumo · Relatórios.
- Três painéis no centro (`PainelDados` | `EsquemaWidget` | `PainelResultados`,
  num `QSplitter`) e o `QuadroResumoWidget` como `QDockWidget` na base.
- **Status bar** na base.
- `_calcular_metodo(metodo, cache_idx)`: o núcleo comum a **todos** os
  métodos — os 5 de cunha e a Estabilidade Externa. Roda via
  `_calcular_com_cache` (cache por método — ver `cache_resultados.py`
  abaixo), atualiza esquema + painel de resultados, mostra o primeiro
  `metodo.avisos(projeto)` na status bar (ou o resumo do resultado, se
  não houver aviso). Não mexe no Quadro Resumo.
- `_calcular(aba)`: wrapper fino de `_calcular_metodo` para um dos 5
  métodos de cunha, pelo índice `aba` (0..4, mesmo índice do cache).
- `_calcular_externa()`: idem, para `MetodoEstabilidadeExterna` — cache
  num índice dedicado (`_IDX_EXT = 5`), fora do grupo exclusivo da navbar
  (não é uma "aba" de cunha, é uma verificação à parte). Marca
  `_analise_atual = _ANALISE_EXT`.
- `_selecionar_metodo(aba)`: troca de método de cunha na navbar —
  recalcula (ou usa o cache) e mostra, **sem** registrar no Quadro Resumo;
  marca `_analise_atual = aba`.
- `_analise_atual` (`int` 0..4 ou o marcador `_ANALISE_EXT`): qual análise
  está exibida no painel de resultados agora — é o que os botões
  "Calcular"/"Registrar no quadro" do `PainelResultados` (`_recalcular_atual`/
  `_registrar_atual`) usam para agir sobre a análise certa, em vez de
  sempre voltar para o último método de cunha (bug corrigido: antes esses
  botões estavam ligados a um atributo — `_metodo_atual`, hoje removido —
  que a Estabilidade Externa nunca atualizava; "Calcular" com a Ext na
  tela recalculava Rankine).
- `_mostrar_metodo(aba)`: o botão "Registrar no quadro" para um método de
  cunha — recalcula/mostra **e** registra uma situação. `_registrar_externa()`
  é o equivalente para a Estabilidade Externa (usa
  `resumo_map.resultado_para_resumo(MetodoEstabilidadeExterna, resultado)`).
  `_recalcular_atual()`/`_registrar_atual()` despacham para um dos dois
  conforme `_analise_atual`.
- `_comparar_metodos()`: roda os 5 métodos de cunha **+ a Estabilidade
  Externa** (6 ao todo) de uma vez, reaproveitando o cache do que já
  estiver calculado, e registra tudo numa única coluna consolidada.
  Métodos fora da faixa de validade (`avisos()`) não são pulados — continuam
  rodando, só entram na lista "fora de faixa" da mensagem final.
- `_atualizar_titulo()` / `_confirmar_descarte()`: alterações não salvas (usa
  `estado_projeto.projeto_sujo`) — ver `estado_projeto.py` abaixo.

**Mexer aqui quando:**

- Quiser adicionar/remover um item de menu ou ação da navbar.
- Quiser mudar o fluxo de cálculo/cache/comparação.
- Quiser mudar comportamento de salvar/abrir/novo ou a proteção contra perda
  de dados.

#### `panels.py`

`PainelDados`: as seis abas de entrada (reaproveita as classes `_Aba*` de
`dialogs/entrada_dados.py`), sempre visíveis, emitindo `dadosAlterados` a
**qualquer** edição — não só geometria/sobrecarga, precisa cobrir tudo para o
rastreamento de alterações não salvas funcionar direito. Também:

- `destacar_metodo(sigla)`: realça as abas relevantes para o método ativo
  (`relevancia.abas_relevantes`) — inclui "Ext" — com **negrito** +
  `self.palette().color(QPalette.Link)` (cor de link do tema: se adapta
  sozinha a claro/escuro, ao contrário de um hex fixo) via
  `_TabBarComNegrito`, uma `QTabBar` customizada só pra permitir negritar
  tabs por índice (API que o `QTabBar` padrão não tem — `QStyleOptionTab`
  não carrega fonte, então o `paintEvent` troca a fonte do `QStylePainter`
  tab a tab antes de `drawControl`). As abas não relevantes voltam à cor e
  ao peso padrão do tema — nenhuma cor fixa também para "não relevante".
- `relevancia.ABAS_RESERVADAS` está vazia hoje (nenhuma aba sobrou
  reservada desde que Face/Identificação foram removidas do modelo).

`PainelResultados`: cartões de resultado (via `interpretacao.cartoes_resultado`,
já com selos de julgamento), banner de avisos (`metodo.avisos(projeto)`), a
caixa "Hipóteses do método" (texto de `metodo.hipoteses`, sempre visível — é
o que hoje cumpre o papel do antigo botão "Hipóteses / figura", removido) e os
botões **Recalcular** (renomeado de "Calcular" — só recalcula o método ativo;
trocar de método na navbar já recalcula sozinho, ver docstring da classe para
a decisão completa) e **Registrar no quadro**.

**Mexer aqui quando:**

- Adicionar um campo novo a uma aba (mexe em `dialogs/entrada_dados.py`, mas
  pode precisar conectar o novo widget em `PainelDados._ligar_live_update`).
- Adicionar uma aba nova: seguir o padrão de `_AbaReforco` (`entrada_dados.py`)
  e registrar em `PainelDados._construir`/`resultado()` e em `relevancia.py`.
- Mudar quais abas cada método destaca, ou o texto/estilo dos cartões de
  resultado — isso é lógica e vai em `relevancia.py`/`interpretacao.py`, não
  aqui; `panels.py` só monta os widgets a partir do que essas funções devolvem.

#### `relevancia.py`, `interpretacao.py`, `resumo_map.py` (sem Qt)

- `relevancia.py`: mapa sigla-do-método → abas/campos que ele usa
  (`abas_relevantes`, `campos_relevantes`) e `ABAS_RESERVADAS`. Fonte de
  verdade para o destaque de abas em `PainelDados` — e para saber quais abas
  ainda não alimentam nenhum cálculo.
- `interpretacao.py`: `Cartao` (rótulo/valor/selo) e `cartoes_resultado(sigla,
  resultado, projeto, referencia)` — decide os selos ADEQUADO/INSUFICIENTE
  (Bishop, FS vs. `projeto.reforco.fs_alvo`; Estabilidade Externa, os três FS
  vs. `MetodoEstabilidadeExterna.FS_ALVO_*` — os alvos não são duplicados
  aqui, vêm direto da classe do método), OK/ALERTA (Geossintético,
  dimensionamento fechou ou não; Estabilidade Externa, excentricidade vs.
  B/6), o cartão de ponto de aplicação (H/3) e a comparação percentual com
  Rankine (Coulomb/Dois Blocos).
- `resumo_map.py`: `resultado_para_resumo(metodo_cls, resultado)` — o
  `Resultado` de um método vira o dict de chaves que `QuadroResumoWidget`
  espera (`coulomb_solicit`, `bishop_fs`, `n_camadas`, `ext_fs_desl`/
  `ext_fs_tomb`/`ext_fs_cap`, etc.); preserva as chaves da versão MDI
  original.

**Mexer aqui quando:**

- Um método novo precisar de uma linha no Quadro Resumo → `resumo_map.py`.
- Mudar a faixa de abas que um método usa, ou os campos citados no tooltip →
  `relevancia.py`.
- Mudar a regra de "adequado"/o texto de um cartão → `interpretacao.py`.
- Todos são testáveis direto com `pytest`, sem Qt.

#### `estado_projeto.py`, `cache_resultados.py` (sem Qt)

- `estado_projeto.projeto_sujo(atual, referencia) -> bool`: compara dois
  `Projeto` por valor (dataclasses geram `__eq__` recursivo). `MainWindow`
  guarda `_projeto_salvo` (o último salvo/carregado) e chama isso sempre que
  precisa saber se há alterações pendentes — título com `"*"`,
  `_confirmar_descarte` antes de Novo/Abrir/fechar.
- `cache_resultados.CacheResultados`: um slot de `Resultado` por índice de
  método (`obter`/`guardar`/`invalidar`), comparando o `Projeto` por valor
  (`dataclasses.asdict`) — não por identidade, já que `PainelDados.resultado()`
  sempre devolve uma instância nova. `MainWindow._dados_alterados` chama
  `invalidar()` a cada edição; `_calcular_com_cache` consulta antes de rodar
  `metodo.calcular` (Dois Blocos/Bishop otimizam e podem demorar — só em cache
  miss é que mostram "Calculando..." + cursor de ocupado). Índices 0-4 são os
  métodos de cunha (`_METODOS_POR_ABA`), `_IDX_EXT=5` é a Estabilidade Externa.

**Mexer aqui quando:**

- Mudar o que conta como "alterações não salvas" — o que muda é o que
  `MainWindow` compara, `estado_projeto.py` continua igual.
- Mudar a política de cache (ex.: cachear por sigla em vez de índice, ou
  invalidar por método em vez de tudo de uma vez) → `cache_resultados.py`.

#### `dialogs/entrada_dados.py`

As classes **`_Aba*`** (`_AbaGeometria`, `_AbaSolo`, `_AbaSobrecarga`,
`_AbaReforco`) — cada uma com seu formulário e um método `valores()` que
devolve a dataclass correspondente. São o que `panels.PainelDados` monta como
as seis abas do painel de dados (`_AbaSolo` é reaproveitada três vezes:
aterro, encosta, fundação). `_AbaReforco` (Tult, RFcr, RFid, RFd, Ci, FS) é o
exemplo real de "adicionar uma aba nova" que o cookbook da seção 5.2 descreve.
`_AbaFace` e `_AbaIdentificacao` existiram aqui, mas foram removidas junto com
as dataclasses `FaceEstrutura`/`Identificacao` (`core/models.py`) e os campos
`face`/`identificacao` de `Projeto` — nenhum método as lia, e a identificação
do projeto é redundante com o próprio arquivo salvo.

`_AbaSolo.__init__` aceita `com_atrito_blocos: bool` (mostra ou não o spinbox
de ângulo de atrito entre blocos) e, desde a Estabilidade Externa,
`rotulo_atrito_blocos`/`default_atrito_blocos` — permitem reaproveitar o mesmo
spinbox com outro rótulo/valor padrão. `panels.py` usa isso para a aba de solo
de encosta: `com_atrito_blocos=True, rotulo_atrito_blocos="Atrito solo-muro do
retido, δ_ret (graus)", default_atrito_blocos=0.0` — o campo vira `δ_ret`, não
mais o atrito entre blocos, e alimenta `solo_encosta.angulo_atrito_blocos_g`
que `MetodoEstabilidadeExterna` lê para o empuxo do solo retido.

A classe `EntradaDadosDialog`, no mesmo arquivo, é resíduo da versão MDI (o
diálogo modal de Entrada de Dados) — **não é mais instanciada em lugar
nenhum**; a UI atual usa as abas `_Aba*` diretamente em `panels.py`. Não foi
removida porque remover código morto não fazia parte de nenhuma tarefa; se for
mexer numa aba, edite a classe `_Aba*`, não `EntradaDadosDialog`.

**Mexer aqui quando:**

- Adicionar um campo novo a uma aba (ex.: nível d'água em `_AbaSolo`).
- Adicionar uma aba nova: seguir o padrão de `_AbaReforco` — criar a classe,
  registrar em `panels.PainelDados` (`_construir`, `resultado()`, e a tabela
  `_ABAS_ORDENADAS`) e em `relevancia.py`.
- Mudar validação de campos (ex.: bloquear φ > 60°): ajustar os
  `QDoubleSpinBox` correspondentes.

#### `dialogs/esquema_widget.py`

O **desenho do muro**, no painel central da janela principal. É um `QWidget`
que sobrescreve `paintEvent` e usa `QPainter` para desenhar:

- A fundação (faixa marrom) e o corpo do muro (polígono que respeita H, β, B,
  βe, i, Ht) — transformação mundo→tela (`_transformacao`/`_w2s`) com origem
  no pé do muro, reaproveitada tanto pelo polígono quanto pelos overlays.
  `_transformacao` é **fit-to-content**: `_bbox_mundo()` calcula a caixa
  delimitadora real dos quatro pontos-chave (pé, topo da face, topo do
  talude, pé da encosta) em metros, e uma única escala uniforme (mínimo dos
  dois eixos) faz essa caixa caber na área disponível — descontadas margens
  fixas em pixels reservadas pras cotas/setas/legendas ao redor — e fica
  centralizada. Isso substituiu uma heurística antiga (`B * 2.2` fixo) em
  que B não crescia de forma proporcional ao editar o campo.
- **A superfície crítica do método ativo**, por cima do muro, quando há um
  resultado (`mostrar_resultado(sigla, resultado)` / `limpar_resultado()`):
  reta da cunha (Rankine/Coulomb, a partir de `inclinacao_cunha_g`), bilinear
  (Dois Blocos, `cunha1_g`/`cunha2_g`/`xp_m`/`inflexao_m`), círculo crítico
  (Bishop, `xc_m`/`yc_m`/`R_m`) ou as camadas de reforço (Geossintético,
  `extras["camadas"]`) — cada um com cor e rótulo próprios. Sem resultado (ou
  faltando algum dado), cai no traço tracejado genérico de antes — nunca
  lança exceção, é só desenho ilustrativo.
- As setinhas da sobrecarga uniforme q, a seta vermelha do trem-tipo P, as
  cotas H, B (sempre) e Ht/i (só quando ≠ 0 — um talude de topo é opcional),
  e os ângulos β, βe e i, cada um com a letra **e** um pequeno arco
  (`_arco_angulo`, via `QPainterPath.arcTo`) indicando a região do ângulo —
  raio limitado a 18px e a 45% da aresta adjacente mais curta, e pontos
  coincidentes (ex.: Ht=0 com βe=90°) são ignorados por não terem direção
  definida.

`MainWindow._calcular` chama `mostrar_resultado` depois de um cálculo
bem-sucedido; `_dados_alterados` chama `limpar_resultado()` (dado mudou sem
recalcular → a cunha desenhada ficaria desatualizada).

**Mexer aqui quando:**

- Mudar a aparência do desenho (cores, espessura de linha, fontes) — inclusive
  `_COR_OVERLAY` para as cores por método.
- Adicionar um overlay novo (ex.: nível d'água): seguir o padrão dos
  `_overlay_*` — um método que desenha em coordenadas de mundo via `_w2s` e
  devolve `True`/`False` (desenhou ou não).
- Mudar as margens fixas reservadas ao redor do muro (cotas, setas, legendas):
  `_PAD_ESQUERDA`/`_PAD_DIREITA`/`_PAD_TOPO`/`_PAD_BASE`, no topo da classe.
- Mudar a representação da cunha/círculo/camadas conforme o método.

#### `dialogs/metodo_info.py`

**Resíduo — não é mais instanciado em lugar nenhum.** Era o diálogo
"Hipóteses / figura" (aberto por um botão no painel de resultados), com uma
aba por método (Coulomb, Rankine, Dois Blocos, Bishop, Geossintéticos) — cada
uma com a figura da cunha (`_FiguraCunha`, `QPainter`), uma descrição curta e
o texto de `metodo.hipoteses`. O botão foi removido (o texto de hipóteses
agora aparece direto na caixa "Hipóteses do método" do painel de resultados,
sem precisar de diálogo nem de figura à parte) e `MainWindow._ver_hipoteses`/
o import de `MetodoInfoDialog` saíram de `main_window.py` junto. Mesmo
tratamento dado a `EntradaDadosDialog` em `entrada_dados.py`: não foi
removido porque limpar código morto não fazia parte de nenhuma tarefa; se for
mexer em hipóteses/descrição de método, edite a tupla `hipoteses` da classe
em `core/methods/*.py`, não este arquivo.

#### `dialogs/quadro_resumo.py`

A tabela do **Quadro Resumo**, com 27 linhas (situação, geometria, parâmetros
do solo, sobrecargas, resultados de cada método — inclusive `"FS, Mét.
Bishop"` e as três linhas de Estabilidade Externa, `ext_fs_desl`/
`ext_fs_tomb`/`ext_fs_cap`) e até 8 colunas (últimas situações analisadas). É
um `QWidget` com um `QTableWidget` dentro.

O método `adicionar_situacao(projeto, resultados)` adiciona uma nova coluna
(vem de `resumo_map.resultado_para_resumo`, um método por vez, ou já
consolidado com os 6 métodos — 5 de cunha + Estabilidade Externa — no caso de
`MainWindow._comparar_metodos`);
quando completar 8, a mais antiga sai (rolamento FIFO). `limpar()` esvazia
tudo (usado no "Novo").

**Mexer aqui quando:**

- Adicionar/remover linhas: acrescentar em `LINHAS` **e** popular a posição
  correspondente em `_preencher_coluna` (mantendo os dois na mesma ordem) — e
  adicionar a chave nova em `resumo_map.py`.
- Mudar a quantidade de situações armazenadas (constante `N_SITUACOES`).
- Formatar valores de forma diferente (função `_fmt` — usa `"—"` para `None`,
  não um valor-placeholder tipo `10`; isso já foi um bug real aqui, não
  repetir).

### 3.5 `tests/`

| Arquivo | Função |
|---|---|
| `casos_literatura.py` | **Fonte única de verdade** dos casos de validação: dataclass `CasoLiteratura` (id, método, fonte, entradas, esperado, tolerância) + `monta_projeto()` (aplica os overrides sobre um `Projeto()` default) + `METODOS` (mapa string→classe). Usado tanto pelos `test_*.py` quanto por `validar.py`. |
| `casos_referencia_original.csv` | Conferência **opcional** com o programa original (PLANO_IMPLEMENTACAO.md §5). Mesmo schema de `CasoLiteratura`, achatado em CSV (`entradas_json`/`esperado_json`). Vazio por padrão (só cabeçalho); `validar.py` carrega automaticamente se tiver linhas, numa seção separada do relatório que não afeta a taxa de aprovação nem o código de saída. |
| `test_models.py` | Smoke-test do core: `Projeto` default e round-trip de salvar/carregar JSON. |
| `test_rankine.py`, `test_coulomb.py`, `test_dois_blocos.py`, `test_bishop.py`, `test_geossintetico.py`, `test_estabilidade_externa.py` | Um arquivo por método, lendo os casos de `casos_literatura.py` (Rankine/Coulomb/Estabilidade Externa têm fórmula fechada) ou com oráculos próprios — limites, monotonicidade, convergência — para os métodos sem fórmula fechada (Dois Blocos, Bishop). `test_estabilidade_externa.py` cobre deslizamento/tombamento/capacidade de carga, os fatores de Vésic e a reutilização do `MetodoRankine` para o empuxo motor. |
| `test_degeneracia.py` | Casos degenerados/limite de **todos** os métodos, num só lugar (ex.: Coulomb com θ=δ=i=0 tem que coincidir com Rankine). |
| `test_validade.py` | `MetodoAnalise.avisos(projeto)` de cada método — presença/ausência de aviso por faixa de β, não o texto exato. |
| `test_relevancia.py`, `test_interpretacao.py`, `test_resumo_map.py`, `test_estado_projeto.py`, `test_cache_resultados.py` | Lógica de `ui/*.py` que não depende de Qt (destaque de abas, selos/cartões de julgamento, mapeamento pro Quadro Resumo, alterações não salvas, cache de resultados) — mesmo padrão dos testes de `core/`: `Resultado`/`Projeto` construídos à mão, sem rodar `calcular()` nem abrir janela. |
| `test_geometria_segura.py` | `ui/geometria_segura.py::cotg_segura` — divisão de tangente segura perto de singularidades (β/βe = 0°, 90°), usada por `esquema_widget.py` pra não estourar `ZeroDivisionError`. |

Todos rodam **sem precisar de PySide6** — mesmo os de `ui/*.py` acima, que
testam só os módulos sem Qt daquela camada (a suíte não abre nenhuma janela).

**Mexer aqui:** sempre que implementar/alterar um método de cálculo, adicione o
caso em `casos_literatura.py` (se tiver fórmula fechada ou caso-limite
verificável) e um teste correspondente no `test_<metodo>.py`. Para métodos sem
fórmula fechada, prefira oráculos (limites, monotonicidade, convergência) a
comparar contra um número "estimado". Ao adicionar lógica nova em `ui/` que
não seja desenho puro (Qt), coloque-a num módulo sem import de Qt e escreva um
teste — é o padrão que `relevancia.py`/`interpretacao.py`/`resumo_map.py`/
`estado_projeto.py`/`cache_resultados.py` seguem.

---

## 4. Fluxo de execução

```
python main.py
    │
    ▼
QApplication, MainWindow.show()
    │
    ├─ PainelDados montado com Projeto() default
    └─ _calcular(1)  # Rankine, feedback imediato
        │
        ▼
Usuário edita um campo (qualquer aba)
    │
    ▼
PainelDados.dadosAlterados  (sinal — TODOS os campos estão conectados)
    │
    ▼
MainWindow._dados_alterados()
    ├─ self.projeto = painel_dados.resultado()   # Projeto novo, consolidado
    ├─ esquema.atualizar(projeto) + limpar_resultado()  # cunha desenhada some
    ├─ cache.invalidar()               # qualquer método pode ter sido afetado
    └─ _atualizar_titulo()             # "*" acende se projeto ≠ _projeto_salvo
        │
        ▼
Usuário clica "Coulomb" na navbar
    │
    ▼
MainWindow._selecionar_metodo(0) → _calcular(0)
    │
    ├─ projeto = painel_dados.resultado()
    ├─ painel_dados.destacar_metodo("Coul")     # abas relevantes em destaque
    ├─ _calcular_com_cache(0, metodo, projeto)
    │      ├─ cache HIT  → devolve na hora (troca de aba instantânea)
    │      └─ cache MISS → "Calculando..." + WaitCursor (só p/ DB/Bishop) →
    │                      metodo.calcular(projeto) → guarda no cache
    ├─ esquema.mostrar_resultado("Coul", resultado)   # desenha a cunha real
    ├─ referencia = _calcular_com_cache(1, MetodoRankine(), projeto)  # p/ comparação
    ├─ painel_resultados.mostrar(metodo, resultado, projeto, referencia)
    │      └─ interpretacao.cartoes_resultado(...) monta cartões + selos;
    │         banner de metodo.avisos(projeto), se houver
    ├─ logger.info(entrada + resultado) → logs/soloref_app.log
    └─ status bar: primeiro aviso, OU resumo do resultado
        │
        ▼
Usuário clica "Registrar no quadro" no painel de resultados (ou "Comparar métodos" na navbar)
    │
    ▼
MainWindow._registrar_atual()                    OU     _comparar_metodos()
    │
    ├─ _analise_atual é um índice 0..4          [6 métodos — 5 de cunha +
    │  → _mostrar_metodo(aba): recalcula/         Estabilidade Externa
    │    mostra + resultado_para_resumo(...)       numa só coluna
    │                                               consolidada, reapro-
    ├─ _analise_atual é _ANALISE_EXT               veitando o cache do
    │  → _registrar_externa(): recalcula/mostra +  que já estiver
    │    resultado_para_resumo(MetodoEstabili-      calculado]
    │    dadeExterna, resultado)
    │
    └─ _abrir_resumo() + quadro.adicionar_situacao(projeto, resultados)

Usuário clica "Estabilidade externa" na navbar (act_ext)
    │
    ▼
MainWindow._calcular_externa()
    ├─ self._analise_atual = _ANALISE_EXT   # "Calcular"/"Registrar" do painel de
    │                                       # resultados passam a agir sobre a Ext
    ├─ metodo = MetodoEstabilidadeExterna()
    └─ _calcular_metodo(metodo, _IDX_EXT)   # mesmo caminho de cache/esquema/painel/log,
                                             # mas fora do grupo exclusivo da navbar

Usuário clica "Calcular"/"Recalcular" no painel de resultados
    │
    ▼
MainWindow._recalcular_atual()
    ├─ _analise_atual é um índice 0..4  → _calcular(aba)
    └─ _analise_atual é _ANALISE_EXT    → _calcular_externa()
```

Essa integração de "Registrar no quadro" está feita para os 5 métodos de
cunha (`_METODOS_POR_ABA` em `main_window.py`), inclusive Bishop
(`bishop_fs`) e Geossintético (`n_camadas`) — ambos com linha própria no
Quadro Resumo — e, desde a correção do bug acima, também para a
Estabilidade Externa via `_registrar_externa`. "Comparar métodos"
continua sendo o único jeito de registrar os 6 numa única coluna
consolidada de uma vez.

---

## 5. Cookbook — onde mexer para...

### 5.1 ...implementar de verdade um método de cálculo

Exemplo: implementar Coulomb para o caso simples (parede vertical, sem
atrito solo-muro, sem coesão).

**Arquivos a editar:**

1. `soloref/core/methods/coulomb.py`
   ```python
   import math

   class MetodoCoulomb(MetodoAnalise):
       # ... (já existe)
       def calcular(self, projeto):
           g = projeto.geometria
           s = projeto.solo_aterro
           sob = projeto.sobrecarga
           phi = math.radians(s.angulo_atrito_g)
           Ka = math.tan(math.pi/4 - phi/2)**2
           Ea = 0.5 * s.peso_especifico_kN_m3 * g.altura_H_m**2 * Ka \
                + sob.uniforme_q_kN_m2 * g.altura_H_m * Ka
           return Resultado(
               metodo=self.nome,
               solicitacao_kN_m=Ea,
               inclinacao_cunha_g=45.0 + s.angulo_atrito_g/2,
               extras={"Ka": Ka},
           )
   ```

Como os cinco métodos já estão implementados de verdade, isso é só o padrão a
seguir para um método novo (seção 5.6). `_METODOS_POR_ABA`, em
`main_window.py`, já mapeia índice → classe; `MainWindow._calcular` chama
`metodo.calcular(projeto)` (com cache — `_calcular_com_cache`) e passa o
`Resultado` para `panels.PainelResultados.mostrar`, que usa
`interpretacao.cartoes_resultado` para montar os cartões. Nada disso precisa
mudar por método — só `resumo_map.resultado_para_resumo` (chave nova no
Quadro Resumo) e, se fizer sentido, `interpretacao.py` (um cartão/selo
específico, como o ADEQUADO/INSUFICIENTE do Bishop).

3. `tests/test_coulomb.py` (segue o padrão dos outros métodos — ver seção 3.5):
   ```python
   from soloref.core import Projeto
   from soloref.core.methods import MetodoCoulomb

   def test_coulomb_caso_padrao():
       r = MetodoCoulomb().calcular(Projeto())
       assert abs(r.solicitacao_kN_m - 53.33) < 0.1
       assert abs(r.inclinacao_cunha_g - 60.0) < 0.1
   ```

### 5.2 ...adicionar um campo de entrada novo

Exemplo: adicionar **nível d'água** ao solo de aterro.

1. **`models.py`** — adicionar campo na dataclass `Solo`:
   ```python
   @dataclass
   class Solo:
       # ... campos existentes
       nivel_dagua_m: Optional[float] = None
   ```

2. **`entrada_dados.py`** — em `_AbaSolo.__init__`, adicionar o spinbox:
   ```python
   self.nivel_dagua = _spin(0, minimum=0)
   form.addRow("Nível d'água (m)", self.nivel_dagua)
   ```
   E em `valores()`, incluir `nivel_dagua_m=self.nivel_dagua.value()`.

3. **`persistence.py`** — não precisa mudar (dataclasses + json cuidam sozinhos).

4. **Cálculos** que usem o campo (ex.: `coulomb.py`) — passar a considerar a poropressão.

5. **`quadro_resumo.py`** — se quiser exibir o NA na tabela, adicionar uma linha em `LINHAS` e popular em `_preencher_coluna`.

### 5.3 ...adicionar um botão novo na navbar

Em `main_window.py` (a navbar é uma `QToolBar` só, com nomes completos — não
há mais o wrapper de sigla curta da versão MDI):

1. Criar a `QAction` em `_montar_actions`, com o nome completo (ex.:
   `QAction("&Relatório em PDF", self)`).
2. Adicionar no menu apropriado em `_montar_menus`.
3. Adicionar na toolbar em `_montar_toolbar` com `tb.addAction(self.act_xxx)`
   (a mesma `QAction` do menu — texto e atalho ficam automaticamente
   sincronizados entre os dois).

### 5.4 ...mudar a aparência do esquema ilustrativo

O muro em si está em `dialogs/esquema_widget.py`, no método `paintEvent`. As
cores são strings hex (`"#d4c8a8"` para o solo do muro, `"#a89878"` para a
fundação, etc.). Para adicionar um elemento novo ao muro, acrescente chamadas
de `p.drawLine(...)`/`p.drawPolygon(...)` antes do `p.end()`, usando
`self._w2s(x_m, y_m, *transf)` para converter coordenadas de mundo (metros,
origem no pé do muro) em coordenadas de tela.

A **superfície crítica do método ativo** (cunha/círculo/camadas) é desenhada
à parte, pelos métodos `_overlay_*` (`_desenhar_overlay_resultado` decide qual
chamar, por `sigla`) — para mudar como um método específico é ilustrado, mexa
no `_overlay_*` dele, não no `paintEvent` principal.

### 5.5 ...mudar o formato do arquivo salvo

Está tudo em `persistence.py`. Funções `salvar(projeto, caminho)` e
`carregar(caminho)`. Se quiser:

- **Versionar**: adicionar `"_schema_version": 1` ao dict salvo e checar ao carregar.
- **Trocar para YAML**: substituir `import json` por `import yaml` e ajustar `dump`/`load`.
- **Compactar**: empacotar em `.zip` ou usar `gzip.open`.

### 5.6 ...adicionar um novo método de análise

Exemplo: implementar Spencer (mais geral que Bishop).

1. Criar `soloref/core/methods/spencer.py` herdando de `MetodoAnalise` —
   implemente `calcular`, preencha a tupla `hipoteses` (aparece sozinha na
   caixa "Hipóteses do método" do painel de resultados, sem UI adicional) e,
   se fizer sentido, `avisos(projeto)` (faixa de validade — ver seção 15 do
   manual/`test_validade.py`).
2. Importar em `methods/__init__.py`.
3. Em `main_window.py`: criar a `QAction` (checkável, no `grupo_metodos`),
   adicionar ao menu e à navbar, e um índice em `_METODOS_POR_ABA`.
4. Em `ui/relevancia.py`: adicionar a sigla ao mapa `_RELEVANCIA` (quais
   abas/campos o método usa) — sem isso, nenhuma aba se destaca quando ele
   está ativo.
5. Em `ui/resumo_map.py`: um `if metodo_cls is MetodoSpencer: return {...}`
   para a linha dele no Quadro Resumo (e a linha correspondente em
   `dialogs/quadro_resumo.py::LINHAS`).
6. Opcional: um `_overlay_spencer` em `dialogs/esquema_widget.py` para
   desenhar a superfície crítica dele (seção 5.4), e um caso em
   `interpretacao.cartoes_resultado` se o resultado pedir um cartão/selo
   específico (seção 3.4).

A separação entre core e UI faz com que **o cálculo em si nunca exija mexer em
código de outro método**; os passos 3–6 são só "plugar" o método novo nos
módulos de UI que precisam saber que ele existe.

Há um precedente real que foge um pouco do padrão acima:
`MetodoEstabilidadeExterna` (`core/methods/estabilidade_externa.py`) reaproveita
`MetodoRankine.calcular()` para o empuxo motor em vez de reimplementar Ka, e é
o único método cujo construtor aceita um argumento (`fonte_phi_base="fundacao"
| "aterro"` — de qual solo vem o φ da base do bloco). Por não ser um método de
cunha, ele não entra em `_METODOS_POR_ABA`: tem sua própria `QAction`
(`act_ext` → `MainWindow._calcular_externa`) fora do `grupo_metodos` exclusivo
da navbar. Ganha coluna no Quadro Resumo tanto via `_comparar_metodos` (junto
com os 5 de cunha) quanto individualmente pelo botão "Registrar no quadro" do
painel de resultados, que despacha para `_registrar_externa` quando
`_analise_atual` é a Estabilidade Externa (seção 4).

### 5.7 ...mudar o número de situações armazenadas no Quadro Resumo

`dialogs/quadro_resumo.py`, constante `N_SITUACOES = 8` no topo do arquivo.

### 5.8 ...mudar o idioma da interface

Hoje tudo está hardcoded em português. Para internacionalizar:

1. Envolver strings com `self.tr("...")` (Qt já tem suporte).
2. Gerar arquivos `.ts` com `pyside6-lupdate`.
3. Traduzir e compilar com `pyside6-lrelease`.
4. Carregar `QTranslator` no `main.py`.

---

## 6. Convenções de código

- **Nomes de campos em português** quando se referem a grandezas físicas (ex.: `peso_especifico_kN_m3`) — assim o código fica mais próximo da literatura.
- **Unidades no nome do campo** sempre que houver risco de confusão.
- **`core/` é Python puro**: não importa Qt, não usa widgets. Se você se pegar fazendo `from PySide6...` dentro de `core/`, está no lugar errado.
- **Métodos que começam com `_`** são privados (não usar de fora da classe).
- **Type hints sempre que possível**, em especial em funções públicas.
- **Docstrings** em português, curtas, no topo de cada módulo e em métodos públicos.

---

## 7. Como rodar os testes

```bash
pip install -r requirements.txt   # já inclui pytest e scipy
pytest tests/ -v                  # suíte pytest — rápida, um arquivo por método
python validar.py                 # runner de validação — gera RELATORIO_VALIDACAO.md
```

Toda a suíte roda **sem precisar de PySide6** — `core/` inteiro, mais os
módulos de `ui/*.py` que não importam Qt (`relevancia.py`, `interpretacao.py`,
`resumo_map.py`, `estado_projeto.py`, `cache_resultados.py`,
`geometria_segura.py`) — então funciona em CI mesmo sem ambiente gráfico. Só os
widgets (`main_window.py`, `panels.py`, `dialogs/*.py`) exigem Qt, e não têm
teste automatizado hoje — a verificação deles é visual (rodar o app).

`validar.py` é o "teste completo do programa": percorre `tests/casos_literatura.py`,
calcula o erro relativo de cada caso, grava um log estruturado em
`logs/validacao_<timestamp>.log` e sai com código ≠ 0 se algo não bater dentro da
tolerância. Também carrega `tests/casos_referencia_original.csv` se ele tiver
linhas (conferência opcional com o programa original — não afeta o código de
saída). No estado atual do projeto, ambos os comandos devem terminar 100% verdes.

---

## Resumindo o "onde mexer"

| Quero mudar... | Vai em... |
|---|---|
| Cálculo de Coulomb | `core/methods/coulomb.py` |
| Cálculo de Rankine | `core/methods/rankine.py` |
| Cálculo de Dois Blocos | `core/methods/dois_blocos.py` |
| Cálculo de Bishop | `core/methods/bishop.py` |
| Geossintéticos | `core/methods/geossintetico.py` |
| Cálculo de Estabilidade Externa (deslizamento, tombamento, capacidade de carga/Vésic) | `core/methods/estabilidade_externa.py` |
| Avisos de aplicabilidade de um método (faixa de β, etc.) | `core/methods/base.py` (`avisos`) + o método específico |
| Campos do projeto (modelo de dados) | `core/models.py` |
| Como salvar/abrir arquivos | `core/persistence.py` |
| Janela principal, menus, navbar, cálculo (com cache), comparar métodos | `ui/main_window.py` |
| Abas de entrada (painel de dados) e cartões de resultado (montagem) | `ui/panels.py` |
| Quais abas cada método destaca | `ui/relevancia.py` |
| Selos/cartões de julgamento (ADEQUADO, OK, comparação com Rankine, ...) | `ui/interpretacao.py` |
| Mapeamento Resultado → linhas do Quadro Resumo | `ui/resumo_map.py` |
| "Há alterações não salvas?" (título com `*`, confirmar descarte) | `ui/estado_projeto.py` |
| Cache de resultado por método | `ui/cache_resultados.py` |
| Divisão segura de tangente perto de singularidades (β/βe = 0°, 90°) | `ui/geometria_segura.py` |
| Classes `_Aba*` de entrada (campos de cada aba) | `ui/dialogs/entrada_dados.py` |
| Desenho do muro e da superfície crítica (esquema ilustrativo) | `ui/dialogs/esquema_widget.py` |
| Texto de hipóteses de um método | tupla `hipoteses` em `core/methods/<metodo>.py` |
| Tabela do Quadro Resumo (linhas, formatação) | `ui/dialogs/quadro_resumo.py` |
| Dataset de casos de validação | `tests/casos_literatura.py` |
| Conferência com o programa original | `tests/casos_referencia_original.csv` |
| Runner de validação ("teste completo") | `validar.py` |
| Ponto de entrada do app | `main.py` |
| Dependências do projeto | `requirements.txt` |
