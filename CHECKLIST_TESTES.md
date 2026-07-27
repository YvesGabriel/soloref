# Checklist de testes — SoloRef

Percorra este documento para conferir se o programa está funcionando como deveria.
Cada item tem uma caixa `[ ]` que você marca como `[x]` ao verificar. O que aparece
**em negrito** é o comportamento esperado; se der diferente, é bug.

Legenda: 🟢 = teste rápido (segundos), 🟡 = teste com atenção, 🔴 = teste que
exige comparar com o programa original.

---

## 1. Preparação e boot 🟢

- [ ] `python --version` retorna 3.10 ou superior.
- [ ] `pip install -r requirements.txt` termina **sem erro** e instala PySide6, numpy, matplotlib.
- [ ] `python -c "from soloref.core import Projeto; print(Projeto())"` roda **sem erro** e imprime a dataclass com os defaults (H=4.0, γ=20.0, φ=30.0, etc.). Isso confirma que o `core/` sozinho está saudável.
- [ ] `python main.py` abre uma janela **sem crash no console**.

---

## 2. Janela principal 🟢

Após o boot:

- [ ] Título da janela: **"SoloRef - Dimensionamento de Estruturas de Solo Reforçado"**.
- [ ] Menu bar mostra 5 menus na ordem: **Sistema · Dimensionamento · Relatórios · Janelas · Ajuda**.
- [ ] Toolbar tem 9 botões, nessa ordem: **ED · Coul · Rank · DB · Bish · Ref · Ext · Resu · Rela**.
- [ ] Status bar (na base) mostra "**Situação ainda indeterminada**".
- [ ] Área central (MDI) começa vazia.

---

## 3. Menu Sistema 🟢

- [ ] **Sistema > Novo** (ou `Ctrl+N`): status bar muda para "Novo projeto", MDI limpa.
- [ ] **Sistema > Salvar como…**: abre file dialog; após salvar em `teste.json`, o arquivo existe no disco e o status bar mostra "Salvo: teste.json".
- [ ] Abra `teste.json` em um editor de texto: deve ser **JSON legível** com chaves `identificacao`, `geometria`, `face`, `solo_aterro`, etc.
- [ ] **Sistema > Abrir** e escolher `teste.json`: status bar mostra "Carregado: teste.json".
- [ ] **Sistema > Sair** fecha o programa limpo (sem crash).

---

## 4. Menu Ajuda 🟢

- [ ] **Ajuda > Sobre…**: abre caixa mostrando "SoloRef (reimplementação)", nome do aluno e do orientador, "Python + PySide6".

---

## 5. Diálogo Entrada de Dados 🟡

Clique em **ED** (toolbar) ou **Dimensionamento > Entrada de dados**.

### 5.1 Estrutura do diálogo

- [ ] Título da janela: "**Entrada de dados**".
- [ ] Aparecem **8 abas** na ordem: Solo de aterro · Solo de encosta · Solo de fundação · Geometria da estrutura · Face da estrutura · Sobrecarga · Reforço (geossintético) · Identificação do projeto.
- [ ] À direita há um painel **"Esquema ilustrativo"** com um desenho do muro.
- [ ] Na base direita há os botões **OK** e **Cancelar**.
- [ ] Na base do diálogo, uma linha de status mostra "Dimensiona a estrutura."

### 5.2 Aba Solo de aterro (padrão)

- [ ] 4 campos com valores padrão: **γ = 20** kN/m³, **c = 0** kN/m², **φ = 30°**, **φb = 30°**.
- [ ] Todos os campos aceitam edição (spinbox com setinhas).
- [ ] Aparece o link vermelho "**-> Discussão sobre parâmetros do solo**".

### 5.3 Aba Solo de encosta

- [ ] 3 campos (**sem** o φb entre blocos).
- [ ] Aparece observação vermelha: "**Obs. Os parâmetros do solo de encosta não são necessários no dimensionamento.**"

### 5.4 Aba Solo de fundação

- [ ] 3 campos com padrão: **γ = 20, c = 15, φ = 30**.

### 5.5 Aba Geometria da estrutura

- [ ] 6 campos com padrão: **H = 4**, **β = 90°**, **B = 5**, **βe = 90°**, **i = 0°**, **Ht = 0**.
- [ ] O rótulo de **B** aparece em **vermelho** (destaque do original).

### 5.6 Aba Face da estrutura

- [ ] Checkbox "O projeto considera blocos de face" **desmarcado**.
- [ ] Os 3 campos (altura, largura, recuo) começam **desabilitados**.
- [ ] Marcar o checkbox → os 3 campos ficam **habilitados**.
- [ ] Desmarcar → voltam a ficar desabilitados.
- [ ] Aparece observação vermelha sobre "blocos de face não são considerados elementos de contenção".

### 5.7 Aba Sobrecarga

- [ ] Campo **q** (sobrecarga uniforme) em vermelho.
- [ ] Grupo "**Trem-tipo (sobrecarga linear)**" com P, xo, e.

### 5.7b Aba Reforço (geossintético)

- [ ] 6 campos com padrão: **Tult = 40** kN/m, **RFcr = 2,0**, **RFid = 1,1**, **RFd = 1,1**, **Ci = 0,8**, **FS = 1,5**.
- [ ] Aparece observação vermelha sobre os valores default serem "ordens de grandeza típicas" (não uma especificação de produto).

### 5.8 Aba Identificação do projeto

- [ ] Campos "Identificação do projeto" e "Empresa" editáveis.
- [ ] Campo "Número do dimensionamento" **desabilitado** (só leitura).

### 5.9 Esquema ilustrativo — atualização ao vivo 🟡

Este é o mais divertido de testar. Volte para a aba **Geometria** e vá mudando os valores devagar; olhe o painel do esquema à direita:

- [ ] Aumentar **H** de 4 para 8: muro fica **mais alto**.
- [ ] Diminuir **β** de 90° para 60°: face fica **inclinada para a direita**.
- [ ] Aumentar **B** de 5 para 10: aterro fica **mais largo**.
- [ ] Aumentar **Ht** de 0 para 3: aparece o **talude de topo**.
- [ ] Mudar **i** de 0° para 15°: topo fica **inclinado para cima**.
- [ ] Aba **Sobrecarga**: aumentar **q** para 20 kN/m² → as **setinhas verticais** ficam mais visíveis (o desenho sempre mostra as setinhas de q, então o efeito é visual: setinhas maiores).
- [ ] Mudar **xo** de 0 para 3: a **seta vermelha** da carga linear P muda de posição no topo.
- [ ] Todos os testes acima devem redesenhar o esquema **sem travar** nem piscar.

### 5.10 OK / Cancelar

- [ ] Mude H para 10, clique **Cancelar**, reabra ED. **H deve estar em 4** de novo (não persistiu).
- [ ] Mude H para 10, clique **OK**, reabra ED. **H deve estar em 10** (persistiu).

---

## 6. Diálogos de Métodos 🟡

### 6.1 Coulomb (Coul)

- [ ] Clique **Coul** na toolbar → abre diálogo **"Estabilidade interna - Geometria e hipóteses"**.
- [ ] A aba ativa é **"Método de Coulomb"**.
- [ ] Há uma **figura** ilustrando a cunha de Coulomb (parede vertical, cunha plana, forças W, N, R, Tf+Tc, E).
- [ ] Abaixo da figura, um texto descritivo.
- [ ] Caixa **"Hipóteses do método"** com 4 bullets começando por "Método de cálculo por equilíbrio limite…".
- [ ] Checkbox "Não mostrar esta tela no dimensionamento".
- [ ] Botões **Continuar · Fechar · Apoio**.
- [ ] Clique **Continuar**: roda `MetodoCoulomb().calcular(...)` de verdade, registra a situação no Quadro Resumo (com solicitação e cunha **reais**, não mais placeholder) e volta para a MDI.
- [ ] Status bar mostra algo como "**Método de Coulomb: solicitação=X kN/m, cunha=Y°**" (com os defaults do projeto: X≈47,5, Y≈54,3 — depende do δ do solo de aterro).
- [ ] `logs/soloref_app.log` ganha uma linha nova com a entrada completa e o `Resultado`.

### 6.2 Rankine (Rank)

- [ ] Clique **Rank** → mesmo diálogo, aba ativa "**Método de Rankine**".
- [ ] Figura mostra cunha de Rankine com **camadas horizontais tracejadas** (representando reforço).
- [ ] Hipóteses começam por "Considera o estado de tensões ativas…".

### 6.3 Dois Blocos (DB)

- [ ] Aba ativa "**Método dos Dois Blocos**".
- [ ] Figura mostra **cunha bilinear** com W1, W2, θ2, d1, d2.
- [ ] Hipóteses citam "cunha de ruptura bilinear".

### 6.4 Bishop (Bish) — extensão

- [ ] Aba ativa "**Método de Bishop (novo)**".
- [ ] Marcada como (NOVO) no título da aba.
- [ ] Hipóteses citam "superfície de ruptura circular dividida em fatias".
- [ ] Clique **Continuar**: roda `MetodoBishop().calcular(...)` de verdade (busca do círculo crítico) e loga em `logs/soloref_app.log`. **Conhecido/cosmético**: a status bar mostra "solicitação=0 kN/m, cunha=0°" mesmo com o FS calculado corretamente — Bishop não usa esses dois campos, usa `fator_seguranca` (não exibido na status bar ainda). Bishop também ainda não tem linha própria no Quadro Resumo.

### 6.5 Reforço (Ref) — extensão

- [ ] Aba ativa "**Reforço com geossintéticos (novo)**".
- [ ] Hipóteses citam "número de camadas" e "fator de segurança alvo".
- [ ] Clique **Continuar**: roda `MetodoGeossintetico().calcular(...)` de verdade (nº de camadas, Sv, La, Le) e loga. Mesma ressalva cosmética do Bishop: status bar mostra "solicitação=0"; sem linha própria no Quadro Resumo ainda.

### 6.6 Ext e Rela

- [ ] **Ext** e **Rela** exibem "Esta funcionalidade será implementada nas próximas etapas do projeto" (ainda não implementados).

---

## 7. Quadro Resumo 🟡

Clique em **Resu** ou faça vários **Coul/Rank/DB**.

- [ ] Quadro Resumo abre como uma **sub-janela dentro da MDI area**.
- [ ] Título: "Quadro comparativo da análise da estabilidade interna nas últimas oito situações consideradas".
- [ ] A tabela tem **23 linhas** com os rótulos corretos (situação, altura, inclinação da face, …, 2ª inclinação da cunha).
- [ ] A tabela tem **8 colunas** de dados (números 1 a 8), além da coluna dos rótulos.
- [ ] Registrar 1 situação preenche apenas a coluna 1. As demais mostram **—** (célula vazia).
- [ ] Registrar 9 situações: a mais antiga é **descartada**, a mais nova entra na última coluna (comportamento FIFO).
- [ ] Rodar **Coul**, depois **Rank**, depois **DB**: os valores "solicit., Mét. Coulomb/Rankine/Dois Blocos" e as respectivas cunhas aparecem com **números reais** (não mais placeholder). As linhas de Dois Blocos (ponto de inflexão, 1ª/2ª inclinação da cunha) continuam em **—**: só a solicitação e a 1ª cunha estão ligadas ao Quadro Resumo hoje.
- [ ] Rodar **Bish** ou **Ref**: essas linhas continuam em **—** no Quadro Resumo — os dois métodos calculam de verdade (conferir no `logs/soloref_app.log` ou na status bar), mas ainda não têm linha própria na tabela (pendência conhecida, ver GUIA_DESENVOLVEDOR.md §3.4).

---

## 8. Menu Janelas 🟢

Com o Quadro Resumo aberto:

- [ ] **Janelas > Organizar em cascata** — sub-janela vai para posição em cascata.
- [ ] **Janelas > Organizar lado a lado** — sub-janela ocupa o espaço.
- [ ] **Janelas > Fechar tudo** — sub-janela fecha.

---

## 9. Persistência (round trip) 🟡

- [ ] **Novo** → abrir ED → mudar H para 6, φ do aterro para 33°, coesão do aterro para 5, nome do projeto para "Teste 1" → **OK**.
- [ ] **Salvar como** `caso_1.json`.
- [ ] Feche o programa completamente.
- [ ] Abra o programa de novo → **Abrir** → `caso_1.json`.
- [ ] Abra ED → **os valores devem estar exatamente como salvou** (H=6, φ=33, c=5, projeto = "Teste 1").
- [ ] Abra `caso_1.json` num editor de texto para conferir se está bonito e legível (JSON indentado com nomes claros).

---

## 10. Testes automatizados do core 🟢

Rode no terminal:

```bash
pip install pytest
pytest tests/ -v
```

- [ ] `test_projeto_default` passa (valores padrão corretos).
- [ ] `test_round_trip` passa (salvar/carregar não perde informação).

Estes rodam **sem PySide6**, então funcionam em qualquer ambiente (CI, servidor, etc.).

---

## 11. Comparação com o programa original 🔴

Coloque o print original e a versão nova lado a lado:

- [ ] Ordem dos menus é a mesma (**Sistema, Dimensionamento, Relatórios, Janelas, Ajuda**).
- [ ] Ordem dos botões da toolbar é a mesma (ignorando o novo botão **Bish** que é extensão).
- [ ] Ordem das abas do diálogo de Entrada de Dados corresponde à original.
- [ ] Os rótulos em vermelho no original também estão em vermelho na versão nova.
- [ ] O diálogo dos métodos tem a mesma disposição (Geometria em cima, descrição no meio, hipóteses embaixo, botões na base).
- [ ] O Quadro Resumo tem as mesmas 23 linhas e 8 colunas do original.

---

## 12. Robustez e casos-limite 🟡

- [ ] Abrir ED, apagar tudo do campo H (deixar em 0), OK. O programa **não deve travar**. Rodar qualquer método (Coul/Rank/DB/Bish/Ref) com H=0: os 5 lançam `ValueError` internamente (geometria degenerada), capturado por `_mostrar_metodo` e mostrado como mensagem de erro na status bar — não deve fechar o programa nem poluir o Quadro Resumo com números sem sentido.
- [ ] Digitar `-5` em γ (peso específico): idealmente o spinbox **não permite** valor negativo em campos que não fazem sentido negativo. Se aceitar, é um bug de validação a corrigir.
- [ ] φ = 90° (impossível fisicamente): idealmente barrado (cap. em 60°). Se aceitar, é um bug de validação.
- [ ] Salvar por cima de um arquivo aberto em outro programa: mensagem de erro amigável, não crash.
- [ ] Cancelar o file dialog de Abrir sem escolher arquivo: nada acontece (**sem crash**).

---

## 13. Interface — pequenas coisas visuais 🟢

- [ ] Redimensionar a janela principal: menus, toolbar e MDI se ajustam bem.
- [ ] Redimensionar o diálogo Entrada de Dados: abas continuam legíveis, esquema se adapta.
- [ ] Redimensionar o Quadro Resumo: colunas se ajustam (as com número usam **stretch**, a com rótulos usa **resize to contents**).
- [ ] Fechar sub-janelas com o X funciona sem crash.

---

## 14. Testes de cálculo 🟢 (automatizados) / 🔴 (benchmarks pendentes)

Os 5 métodos estão implementados e os casos abaixo já são **testes automatizados**
(não precisam mais de verificação manual): `pytest tests/ -v` roda todos, e
`python validar.py` gera `RELATORIO_VALIDACAO.md` com a mesma conferência num
formato legível. Rode os dois e confira:

- [ ] `pytest tests/ -v` — **todos os testes passam**.
- [ ] `python validar.py` termina com `EXIT: 0` e imprime "9/9 campos aprovados".
- [ ] `RELATORIO_VALIDACAO.md` mostra **Taxa de aprovação geral: 9/9 (100.0%)**.

Os valores de referência (dataset em `tests/casos_literatura.py`, seção 4.1 do
`PLANO_IMPLEMENTACAO.md`) — **substituem** os números da apostila que estavam
antes aqui, que não foram conferidos contra as convenções desta reimplementação:

| id | método | caso | esperado |
|---|---|---|---|
| RANK-01 | Rankine | H=4, γ=20, φ=30°, c=0 | Ea=53,333 kN/m; cunha=60° |
| RANK-02 | Rankine | H=6, γ=17,5, φ=20°, c=10 | Ea=70,417 kN/m; z0=1,632 m |
| RANK-03 | Rankine (talude) | i=10°, φ=30° | Ka=0,34952 |
| COUL-01 | Coulomb (degenerado) | θ=0, δ=0, i=0, φ=30° | Ka=0,33333 (= Rankine) |
| COUL-02 | Coulomb | δ=15°, θ=0, i=0, φ=30° | Ka=0,30142 |
| BISH-01 | Bishop (talude infinito) | c=0, φ=30°, β=20° | FS=1,5863 |
| GEO-01 | Geossintético (consistência) | H=4, γ=20, φ=30°, c=0 | ΣTmax ≈ Ea_Rankine (53,333) |

**Pendências** (não fabricar números — pedir a referência exata antes de preencher):

- [ ] Benchmark de exemplo resolvido de livro (Das ou Craig) para Bishop — ver TODO no topo de `tests/test_bishop.py`.
- [ ] Benchmark de exemplo resolvido FHWA/livro para Geossintéticos — ver TODO no topo de `tests/test_geossintetico.py`.
- [ ] Casos em `tests/casos_referencia_original.csv` (conferência com o programa antigo) — vazio por padrão, ver PLANO_IMPLEMENTACAO.md §5.

Verificação manual complementar (rápida, opcional já que o automatizado cobre o cálculo em si):

- [ ] Na UI, com os defaults do projeto, rodar **Rank**: Quadro Resumo mostra solicitação≈53,33 kN/m, cunha=60°.
- [ ] Rodar **Coul** com os defaults (δ=30° padrão do solo de aterro): solicitação≈47,5 kN/m — **menor** que Rankine, por causa do atrito muro-solo.

---

## 15. Fluxo completo — teste de aceitação 🟡

Simule um projeto real do começo ao fim:

- [ ] Abrir o programa (janela vazia).
- [ ] Preencher a Entrada de Dados com um caso realista (H=6, β=80°, c=5, φ=32°, q=15).
- [ ] Rodar Coulomb → registra no Quadro Resumo.
- [ ] Rodar Rankine → segunda coluna preenchida.
- [ ] Rodar Dois Blocos → terceira coluna preenchida.
- [ ] Salvar como `projeto_final.json`.
- [ ] Fechar e reabrir o programa.
- [ ] Abrir `projeto_final.json`.
- [ ] Verificar que os valores voltaram (mas o Quadro Resumo começa vazio — decisão de projeto: pode ficar assim ou salvar as situações junto; anote como decisão).

---

## Como registrar problemas

Se algo falhar, anote em uma issue no repositório (ou num arquivo `BUGS.md`)
com:

1. Passo a passo que reproduz o problema.
2. O que era esperado.
3. O que aconteceu.
4. Print/screenshot, se possível.
5. Mensagem de erro do console (se houver).

---

## Ordem sugerida de execução

Para o primeiro run:

1. Seção **1** (preparação) — 2 minutos.
2. Seção **2** (janela principal) — 1 minuto.
3. Seção **10** (testes do core) — 30 segundos.
4. Seção **5** (Entrada de Dados, com atenção ao 5.9) — 5 minutos.
5. Seções **6** e **7** (métodos e Quadro Resumo) — 3 minutos.
6. Seção **9** (round trip) — 2 minutos.
7. Seção **11** (comparação com original) — 5 minutos, opcional na primeira rodada.

**Total: ~15-20 minutos para uma bateria completa.**

Depois, à medida que você for implementando cálculos, vá acrescentando testes
na seção 14 (e transformando em `pytest` de verdade).
