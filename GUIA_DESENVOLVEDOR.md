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
├── main.py                       ← ponto de entrada (`python main.py`)
├── requirements.txt              ← dependências (PySide6, numpy, matplotlib)
├── README.md                     ← descrição do projeto
├── GUIA_DESENVOLVEDOR.md         ← (este arquivo)
│
├── soloref/                      ← pacote principal
│   ├── __init__.py               ← versão do pacote
│   ├── __main__.py               ← permite `python -m soloref`
│   │
│   ├── core/                     ← MODELOS + CÁLCULOS (sem Qt)
│   │   ├── __init__.py           ← reexporta as classes principais
│   │   ├── models.py             ← dataclasses (Projeto, Solo, Geometria, …)
│   │   ├── persistence.py        ← salvar/carregar JSON
│   │   └── methods/              ← um arquivo por método
│   │       ├── __init__.py
│   │       ├── base.py           ← classe abstrata MetodoAnalise + Resultado
│   │       ├── coulomb.py
│   │       ├── rankine.py
│   │       ├── dois_blocos.py
│   │       ├── bishop.py         ← novo (placeholder)
│   │       └── geossintetico.py  ← novo (placeholder)
│   │
│   └── ui/                       ← INTERFACE (PySide6)
│       ├── __init__.py
│       ├── main_window.py        ← janela principal, menus, toolbar, MDI
│       └── dialogs/
│           ├── __init__.py
│           ├── entrada_dados.py    ← diálogo "Entrada de dados" (7 abas)
│           ├── esquema_widget.py   ← desenho do muro (vetorial, ao vivo)
│           ├── metodo_info.py      ← diálogo "Estabilidade interna"
│           └── quadro_resumo.py    ← tabela das últimas 8 situações
│
└── tests/
    └── test_models.py            ← smoke test do core
```

---

## 3. O que cada arquivo faz

### 3.1 Raiz do projeto

| Arquivo | Função | Quando mexer |
|---|---|---|
| `main.py` | Cria o `QApplication`, instancia a `MainWindow` e roda o `app.exec()`. É o ponto de entrada. | Quase nunca — só se quiser mudar nome da aplicação ou parâmetros globais do Qt. |
| `requirements.txt` | Lista as dependências instaláveis via `pip`. | Quando adicionar uma nova lib (ex.: `scipy` para otimização). |
| `README.md` | Descrição do projeto, instruções de instalação. | Quando quiser comunicar status do projeto a outros. |

### 3.2 `soloref/core/` — modelos e cálculos

| Arquivo | Função | Quando mexer |
|---|---|---|
| `models.py` | Define **todas as estruturas de dados** do projeto: `Identificacao`, `Geometria`, `FaceEstrutura`, `Solo`, `Sobrecarga` e `Projeto` (que agrega tudo). São `@dataclass` — Python já gera `__init__`, `__repr__`, comparação, etc. | Quando adicionar um novo campo de entrada (ex.: nível d'água), uma nova categoria de solo, ou um novo tipo de sobrecarga. **Atenção:** mudar aqui geralmente exige mudança correspondente em `entrada_dados.py` (UI) e `persistence.py` (carregar arquivos antigos). |
| `persistence.py` | Salva/carrega o `Projeto` em **JSON**. Usa `dataclasses.asdict()` para serializar. Formato legível, versionável em git, melhor que binário proprietário. | Se quiser mudar o formato do arquivo (ex.: YAML), versionar o schema, ou adicionar migração de versões antigas. |
| `__init__.py` | Reexporta as classes principais para que se possa fazer `from soloref.core import Projeto` sem precisar saber o caminho interno. | Quando criar um novo modelo importante. |

### 3.3 `soloref/core/methods/` — métodos de análise

| Arquivo | Função | Quando mexer |
|---|---|---|
| `base.py` | Define `MetodoAnalise` (classe abstrata com método `calcular(projeto) → Resultado`) e a dataclass `Resultado` (com `solicitacao_kN_m`, `inclinacao_cunha_g`, `fator_seguranca`, e um dict `extras` para dados específicos). | Se quiser mudar a interface comum a todos os métodos (ex.: adicionar um parâmetro de tolerância de iteração, ou um método `desenhar(painter)` para desenho específico de cada cunha). |
| `coulomb.py` | `MetodoCoulomb`. Hoje é placeholder: retorna `Resultado()` vazio. As **hipóteses** já estão escritas (mostradas na UI). | **Prioridade 1**: implementar o cálculo real do empuxo de Coulomb (caso simples primeiro, depois caso geral com δ ≠ 0). |
| `rankine.py` | `MetodoRankine`. Idem: placeholder com hipóteses. | **Prioridade 2**: implementar Ka = tan²(45−φ/2), Ea = ½γH²Ka − 2cH√Ka. |
| `dois_blocos.py` | `MetodoDoisBlocos`. Placeholder. | **Prioridade 3**: implementar busca pela cunha bilinear ótima (otimizar θ1, θ2 ou posição do ponto de inflexão). |
| `bishop.py` | `MetodoBishop` (NOVO). Placeholder. | Implementar Bishop simplificado com fatias e iteração de FS. |
| `geossintetico.py` | `MetodoGeossintetico` (NOVO). Placeholder. | Implementar dimensionamento de número de camadas, espaçamento Sv e comprimento de ancoragem Le. |
| `__init__.py` | Reexporta todas as classes de método. | Quando criar um novo método, adicionar import aqui. |

**Padrão para implementar um cálculo real**: ver seção 5.1 (Cookbook).

### 3.4 `soloref/ui/` — interface PySide6

#### `main_window.py`

A janela principal (`MainWindow`, herda de `QMainWindow`). Contém:

- **Menus**: Sistema, Dimensionamento, Relatórios, Janelas, Ajuda.
- **Toolbar** com os botões do programa original (ED, Coul, Rank, DB, Bish, Ref, Ext, Resu, Rela).
- **MDI Area** (`QMdiArea`) — mesma metáfora do programa original, sub-janelas internas.
- **Status bar** na base.
- Métodos `_novo`, `_abrir`, `_salvar`, `_entrada_dados`, `_mostrar_metodo`, `_abrir_resumo`, `_sobre`.

**Mexer aqui quando:**

- Quiser adicionar/remover um item de menu ou botão de toolbar.
- Quiser mudar como os diálogos são abertos (ex.: abrir o método sem passar pelo diálogo de hipóteses).
- Quiser mudar comportamento de salvar/abrir.

#### `dialogs/entrada_dados.py`

O **diálogo das 7 abas**. Cada aba é uma classe interna (`_AbaIdentificacao`, `_AbaGeometria`, `_AbaFace`, `_AbaSolo`, `_AbaSobrecarga`) com seu próprio formulário e um método `valores()` que devolve a dataclass correspondente.

A classe principal `EntradaDadosDialog` orquestra: monta as abas, conecta o esquema ilustrativo ao `valueChanged` dos campos relevantes (atualização ao vivo) e expõe `resultado()` para devolver o `Projeto` consolidado.

**Mexer aqui quando:**

- Adicionar um campo novo a uma aba (ex.: nível d'água em `_AbaSolo`).
- Adicionar uma aba nova (ex.: "Reforço" para parâmetros do geossintético): criar uma classe `_AbaReforco`, adicionar no `tabs.addTab(...)`, criar o método `valores()`.
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
| `test_models.py` | Smoke-test: cria um `Projeto` default e verifica os valores; testa o round-trip de salvar e carregar JSON. Roda sem precisar de Qt. |

**Mexer aqui:** sempre que implementar um método de cálculo, adicione um teste que confere o resultado contra um caso conhecido (ex.: para H=4, φ=30°, c=0, sem sobrecarga: Ea = 53,33 kN/m).

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
    [aqui entra a chamada real ao MetodoCoulomb().calcular(projeto)]
    [resultado vai para o QuadroResumoWidget]
```

A "[ ]" no fluxo acima é onde **falta a integração** entre UI e cálculos
— hoje a UI já está pronta, mas o `calcular()` é placeholder. Quando
implementar Coulomb, basta editar `MainWindow._mostrar_metodo` para
chamar o método real.

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
pip install pytest
pytest tests/ -v
```

Os testes em `tests/test_models.py` rodam **sem precisar de PySide6**, então funcionam em CI mesmo sem ambiente gráfico.

Quando começar a implementar os métodos, adicione um arquivo `tests/test_methods.py` com um teste por método, comparando contra valores conhecidos (ex.: o exemplo numérico do relatório teórico, Ea = 53,33 kN/m).

---

## Resumindo o "onde mexer"

| Quero mudar... | Vai em... |
|---|---|
| Cálculo de Coulomb | `core/methods/coulomb.py` |
| Cálculo de Rankine | `core/methods/rankine.py` |
| Cálculo de Dois Blocos | `core/methods/dois_blocos.py` |
| Adicionar Bishop | `core/methods/bishop.py` |
| Geossintéticos | `core/methods/geossintetico.py` |
| Campos do projeto (modelo de dados) | `core/models.py` |
| Como salvar/abrir arquivos | `core/persistence.py` |
| Janela principal, menus, toolbar | `ui/main_window.py` |
| Diálogo de Entrada de Dados (7 abas) | `ui/dialogs/entrada_dados.py` |
| Desenho do muro (esquema ilustrativo) | `ui/dialogs/esquema_widget.py` |
| Diálogo de hipóteses dos métodos | `ui/dialogs/metodo_info.py` |
| Tabela do Quadro Resumo | `ui/dialogs/quadro_resumo.py` |
| Ponto de entrada do app | `main.py` |
| Dependências do projeto | `requirements.txt` |
