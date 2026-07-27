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
│   │       ├── base.py           ← classe abstrata MetodoAnalise + Resultado
│   │       ├── coulomb.py        ← fórmula fechada + busca de cunha (trial wedge)
│   │       ├── rankine.py        ← fórmula fechada (horizontal e talude)
│   │       ├── dois_blocos.py    ← cunha bilinear, busca numérica (sem fórmula fechada)
│   │       ├── bishop.py         ← fatias + iteração de FS, busca do círculo crítico
│   │       └── geossintetico.py  ← dimensionamento de camadas (equilíbrio-limite/tieback)
│   │
│   └── ui/                       ← INTERFACE (PySide6)
│       ├── __init__.py
│       ├── main_window.py        ← janela principal, menus, toolbar, MDI — chama os métodos de verdade
│       └── dialogs/
│           ├── __init__.py
│           ├── entrada_dados.py    ← diálogo "Entrada de dados" (8 abas)
│           ├── esquema_widget.py   ← desenho do muro (vetorial, ao vivo)
│           ├── metodo_info.py      ← diálogo "Estabilidade interna"
│           └── quadro_resumo.py    ← tabela das últimas 8 situações
│
└── tests/
    ├── __init__.py
    ├── casos_literatura.py            ← dataset de casos de validação (fonte de verdade)
    ├── casos_referencia_original.csv  ← conferência opcional com o programa original (vazio por padrão)
    ├── test_models.py                 ← smoke test do core
    └── test_{rankine,coulomb,dois_blocos,bishop,geossintetico,degeneracia}.py
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
| `models.py` | Define **todas as estruturas de dados** do projeto: `Identificacao`, `Geometria`, `FaceEstrutura`, `Solo`, `Sobrecarga`, `Reforco` (parâmetros do geossintético) e `Projeto` (que agrega tudo). São `@dataclass` — Python já gera `__init__`, `__repr__`, comparação, etc. | Quando adicionar um novo campo de entrada (ex.: nível d'água), uma nova categoria de solo, ou um novo tipo de sobrecarga. **Atenção:** mudar aqui geralmente exige mudança correspondente em `entrada_dados.py` (UI) e `persistence.py` (carregar arquivos antigos). |
| `persistence.py` | Salva/carrega o `Projeto` em **JSON**. Usa `dataclasses.asdict()` para serializar. Formato legível, versionável em git, melhor que binário proprietário. `carregar()` usa `data.get(secao, {})` com fallback pros defaults da dataclass, para não quebrar ao abrir arquivos salvos antes de um campo/seção novo existir. | Se quiser mudar o formato do arquivo (ex.: YAML), versionar o schema, ou adicionar migração de versões antigas. **Sempre** que adicionar uma seção nova em `models.py`, adicionar aqui também (com o fallback), senão `carregar()` quebra em arquivos antigos. |
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
| `__init__.py` | Reexporta todas as classes de método. | Quando criar um novo método, adicionar import aqui. |

**Padrão para implementar um cálculo real**: ver seção 5.1 (Cookbook) — o exemplo ali
já é essencialmente o que está em `coulomb.py`/`rankine.py` de verdade hoje.

### 3.4 `soloref/ui/` — interface PySide6

#### `main_window.py`

A janela principal (`MainWindow`, herda de `QMainWindow`). Contém:

- **Menus**: Sistema, Dimensionamento, Relatórios, Janelas, Ajuda.
- **Toolbar** com os botões do programa original (ED, Coul, Rank, DB, Bish, Ref, Ext, Resu, Rela).
- **MDI Area** (`QMdiArea`) — mesma metáfora do programa original, sub-janelas internas.
- **Status bar** na base.
- Métodos `_novo`, `_abrir`, `_salvar`, `_entrada_dados`, `_mostrar_metodo`, `_abrir_resumo`, `_sobre`.
- `_mostrar_metodo(aba)` **já chama o método real** (`_METODOS_POR_ABA[aba]().calcular(projeto)`), dentro de `try/except` (erro vira mensagem na status bar, não crash), loga entrada+resultado em `logs/soloref_app.log`, e passa o resultado pro Quadro Resumo via `_CHAVES_RESUMO` (só Coulomb/Rankine/Dois Blocos têm linha própria hoje — Bishop e Geossintético ainda não).

**Mexer aqui quando:**

- Quiser adicionar/remover um item de menu ou botão de toolbar.
- Quiser mudar como os diálogos são abertos (ex.: abrir o método sem passar pelo diálogo de hipóteses).
- Quiser mudar comportamento de salvar/abrir.
- Quiser dar ao Bishop/Geossintético uma linha própria no Quadro Resumo (hoje `_CHAVES_RESUMO` só mapeia solicitação+cunha; Bishop usa `fator_seguranca` e Geossintético usa `extras["n_camadas"]`, então a status bar mostra "solicitação=0" pra eles — cosmético, não um bug de cálculo).

#### `dialogs/entrada_dados.py`

O **diálogo das 8 abas**. Cada aba é uma classe interna (`_AbaIdentificacao`,
`_AbaGeometria`, `_AbaFace`, `_AbaSolo`, `_AbaSobrecarga`, `_AbaReforco`) com seu
próprio formulário e um método `valores()` que devolve a dataclass correspondente.
`_AbaReforco` (parâmetros do geossintético — Tult, RFcr, RFid, RFd, Ci, FS) é o
exemplo real de "adicionar uma aba nova" que o cookbook da seção 5.2 descreve.

A classe principal `EntradaDadosDialog` orquestra: monta as abas, conecta o esquema ilustrativo ao `valueChanged` dos campos relevantes (atualização ao vivo) e expõe `resultado()` para devolver o `Projeto` consolidado.

**Mexer aqui quando:**

- Adicionar um campo novo a uma aba (ex.: nível d'água em `_AbaSolo`).
- Adicionar uma aba nova: seguir o padrão de `_AbaReforco` — criar a classe, adicionar no `tabs.addTab(...)`, criar o método `valores()`, e incluir no `resultado()` do diálogo.
- Mudar validação de campos (ex.: bloquear φ > 60°): ajustar os `QDoubleSpinBox` correspondentes.
- Mudar layout (ordem das abas, cores, posição dos botões).

#### `dialogs/esquema_widget.py`

O **desenho do muro** que aparece à direita em todas as abas. É um `QWidget` que sobrescreve `paintEvent` e usa `QPainter` para desenhar:

- A fundação (faixa marrom),
- O corpo do muro (polígono que respeita H, β, B, βe, i, Ht),
- A linha tracejada da cunha de ruptura (ilustrativa),
- As setinhas da sobrecarga uniforme q,
- A seta vermelha do trem-tipo P,
- As cotas H, Ht, B e os ângulos β, βe.

A escala se adapta ao tamanho da janela e aos valores de H, B, Ht. Toda vez que o usuário mexe em um spinbox, `EntradaDadosDialog` chama `esquema.atualizar(projeto)` e o widget se redesenha.

**Mexer aqui quando:**

- Mudar a aparência do desenho (cores, espessura de linha, fontes).
- Adicionar elementos novos (ex.: representação visual do nível d'água, das camadas de geossintético).
- Mudar a representação da cunha conforme o método selecionado.

#### `dialogs/metodo_info.py`

O diálogo **"Estabilidade interna - Geometria e hipóteses"**, com uma aba para cada método (Coulomb, Rankine, Dois Blocos, Bishop, Geossintéticos). Cada aba mostra:

- A figura da cunha do método (`_FiguraCunha`, desenhada com `QPainter`).
- Uma descrição curta do método.
- O texto das hipóteses (lido da própria classe do método via `metodo.hipoteses`).
- Botões Continuar / Fechar / Apoio.

**Mexer aqui quando:**

- Mudar a figura da cunha de algum método (entrar em `_FiguraCunha.paintEvent` e ajustar o desenho).
- Adicionar uma nova aba para um novo método.
- Mudar o texto de descrição de um método.

#### `dialogs/quadro_resumo.py`

A tabela do **Quadro Resumo**, com 23 linhas (situação, geometria, parâmetros do solo, sobrecargas, resultados de cada método) e até 8 colunas (últimas situações analisadas). É um `QWidget` com um `QTableWidget` dentro.

O método `adicionar_situacao(projeto, resultados)` adiciona uma nova coluna; quando completar 8, a mais antiga sai (rolamento FIFO).

**Mexer aqui quando:**

- Adicionar/remover linhas (ex.: quando implementar Bishop, adicionar linha "FS Bishop").
- Mudar a quantidade de situações armazenadas (constante `N_SITUACOES`).
- Formatar valores de forma diferente (função `_fmt`).

### 3.5 `tests/`

| Arquivo | Função |
|---|---|
| `casos_literatura.py` | **Fonte única de verdade** dos casos de validação: dataclass `CasoLiteratura` (id, método, fonte, entradas, esperado, tolerância) + `monta_projeto()` (aplica os overrides sobre um `Projeto()` default) + `METODOS` (mapa string→classe). Usado tanto pelos `test_*.py` quanto por `validar.py`. |
| `casos_referencia_original.csv` | Conferência **opcional** com o programa original (PLANO_IMPLEMENTACAO.md §5). Mesmo schema de `CasoLiteratura`, achatado em CSV (`entradas_json`/`esperado_json`). Vazio por padrão (só cabeçalho); `validar.py` carrega automaticamente se tiver linhas, numa seção separada do relatório que não afeta a taxa de aprovação nem o código de saída. |
| `test_models.py` | Smoke-test do core: `Projeto` default e round-trip de salvar/carregar JSON. |
| `test_rankine.py`, `test_coulomb.py`, `test_dois_blocos.py`, `test_bishop.py`, `test_geossintetico.py` | Um arquivo por método, lendo os casos de `casos_literatura.py` (para Rankine/Coulomb, que têm fórmula fechada) ou com oráculos próprios — limites, monotonicidade, convergência — para os métodos sem fórmula fechada (Dois Blocos, Bishop). |
| `test_degeneracia.py` | Casos degenerados/limite de **todos** os métodos, num só lugar (ex.: Coulomb com θ=δ=i=0 tem que coincidir com Rankine). |

Todos rodam **sem precisar de PySide6** — a suíte inteira testa só `core/`.

**Mexer aqui:** sempre que implementar/alterar um método de cálculo, adicione o
caso em `casos_literatura.py` (se tiver fórmula fechada ou caso-limite
verificável) e um teste correspondente no `test_<metodo>.py`. Para métodos sem
fórmula fechada, prefira oráculos (limites, monotonicidade, convergência) a
comparar contra um número "estimado".

---

## 4. Fluxo de execução

```
python main.py
    │
    ▼
QApplication, MainWindow.show()
    │
    ▼
Usuário clica "ED" (Entrada de Dados)
    │
    ▼
MainWindow._entrada_dados()
    │
    ├─ Cria EntradaDadosDialog(projeto_atual)
    ├─ Diálogo monta as 7 abas com os valores atuais
    ├─ Usuário edita campos → esquema_widget redesenha ao vivo
    └─ Usuário clica OK
        │
        ▼
    EntradaDadosDialog.resultado()
        ├─ Coleta valores de cada aba (.valores())
        └─ Devolve Projeto consolidado
        │
        ▼
    MainWindow.projeto = novo_projeto
        │
        ▼
Usuário clica "Coul" (Coulomb)
    │
    ▼
MainWindow._mostrar_metodo(0)
    │
    ├─ Mostra MetodoInfoDialog com a aba Coulomb
    └─ Usuário clica Continuar
        │
        ▼
    metodo = MetodoCoulomb(); resultado = metodo.calcular(self.projeto)
    (try/except — erro vira mensagem na status bar, não crash)
        │
        ▼
    logger.info(entrada + resultado) → logs/soloref_app.log
        │
        ▼
    resultado vai para o QuadroResumoWidget.adicionar_situacao(...)
```

Essa integração já está feita para os 5 métodos (`_METODOS_POR_ABA` em
`main_window.py`). O que falta: dar a Bishop e Geossintético uma linha
própria no Quadro Resumo (hoje só aparecem na status bar, não na tabela —
ver observação na seção 3.4).

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

2. `soloref/ui/main_window.py` — em `_mostrar_metodo`, depois de `dlg.exec()`:
   ```python
   from ..core.methods import MetodoCoulomb, MetodoRankine, MetodoDoisBlocos
   metodos = [MetodoCoulomb, MetodoRankine, MetodoDoisBlocos]
   resultado = metodos[aba]().calcular(self.projeto)
   self._abrir_resumo(trazer_pra_frente=True)
   self._resumo_widget.adicionar_situacao(
       self.projeto,
       resultados={f"{metodos[aba].sigla.lower()}_solicit": resultado.solicitacao_kN_m,
                   f"{metodos[aba].sigla.lower()}_cunha": resultado.inclinacao_cunha_g}
   )
   ```

3. `tests/test_methods.py` (criar):
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

### 5.3 ...adicionar um botão novo na toolbar

Em `main_window.py`:

1. Criar a `QAction` em `_montar_actions`.
2. Adicionar no menu apropriado em `_montar_menus`.
3. Adicionar no toolbar em `_montar_toolbar` com `add("Sigla", self.act_xxx)`.

### 5.4 ...mudar a aparência do esquema ilustrativo

Tudo está em `dialogs/esquema_widget.py`, no método `paintEvent`. As
cores são strings hex (`"#d4c8a8"` para o solo do muro, `"#a89878"`
para a fundação, etc.). Para adicionar um elemento novo (ex.: linhas
horizontais para representar camadas de geossintético), basta acrescentar
chamadas de `p.drawLine(...)` antes do `p.end()`.

### 5.5 ...mudar o formato do arquivo salvo

Está tudo em `persistence.py`. Funções `salvar(projeto, caminho)` e
`carregar(caminho)`. Se quiser:

- **Versionar**: adicionar `"_schema_version": 1` ao dict salvo e checar ao carregar.
- **Trocar para YAML**: substituir `import json` por `import yaml` e ajustar `dump`/`load`.
- **Compactar**: empacotar em `.zip` ou usar `gzip.open`.

### 5.6 ...adicionar um novo método de análise

Exemplo: implementar Spencer (mais geral que Bishop).

1. Criar `soloref/core/methods/spencer.py` herdando de `MetodoAnalise`.
2. Importar em `methods/__init__.py`.
3. Em `dialogs/metodo_info.py`, adicionar uma nova aba no `MetodoInfoDialog`.
4. Em `main_window.py`, criar a `QAction`, adicionar ao menu e ao toolbar.

A separação entre core e UI faz com que **adicionar um método novo nunca exija mexer em código de outro método**.

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

Toda a suíte roda **sem precisar de PySide6** (só `core/` é testado), então funciona
em CI mesmo sem ambiente gráfico.

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
| Campos do projeto (modelo de dados) | `core/models.py` |
| Como salvar/abrir arquivos | `core/persistence.py` |
| Janela principal, menus, toolbar, integração com cálculo | `ui/main_window.py` |
| Diálogo de Entrada de Dados (8 abas) | `ui/dialogs/entrada_dados.py` |
| Desenho do muro (esquema ilustrativo) | `ui/dialogs/esquema_widget.py` |
| Diálogo de hipóteses dos métodos | `ui/dialogs/metodo_info.py` |
| Tabela do Quadro Resumo | `ui/dialogs/quadro_resumo.py` |
| Dataset de casos de validação | `tests/casos_literatura.py` |
| Conferência com o programa original | `tests/casos_referencia_original.csv` |
| Runner de validação ("teste completo") | `validar.py` |
| Ponto de entrada do app | `main.py` |
| Dependências do projeto | `requirements.txt` |
