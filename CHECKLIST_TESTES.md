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
- [ ] Aparecem **7 abas** na ordem: Solo de aterro · Solo de encosta · Solo de fundação · Geometria da estrutura · Face da estrutura · Sobrecarga · Identificação do projeto.
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
- [ ] Clique **Continuar**: registra situação no Quadro Resumo e volta para a MDI.
- [ ] Status bar mostra "Situação registrada (aba 0)".

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

### 6.5 Reforço (Ref) — extensão

- [ ] Aba ativa "**Reforço com geossintéticos (novo)**".
- [ ] Hipóteses citam "número de camadas" e "fator de segurança alvo".

### 6.6 Ext e Rela

- [ ] **Ext** e **Rela** exibem "Esta funcionalidade será implementada nas próximas etapas do projeto" (ainda não implementados).

---

## 7. Quadro Resumo 🟡

Clique em **Resu** ou faça vários **Coul/Rank/DB**.

- [ ] Quadro Resumo abre como uma **sub-janela dentro da MDI area**.
- [ ] Título: "Quadro comparativo da análise da estabilidade interna nas últimas oito situações consideradas".
- [ ] A tabela tem **23 linhas** com os rótulos corretos (situação, altura, inclinação da face, …, 2ª inclinação da cunha).
- [ ] A tabela tem **8 colunas** de dados (números 1 a 8), além da coluna dos rótulos.
- [ ] Registrar 1 situação preenche apenas a coluna 1. As demais mostram **$$$$$$$$$$** (placeholder).
- [ ] Registrar 9 situações: a mais antiga é **descartada**, a mais nova entra na última coluna (comportamento FIFO).
- [ ] Os valores "solicit. Coulomb" etc. aparecem como **$$$$$$$$$$** porque os métodos ainda são placeholders — isso é **esperado nesta fase**.

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

- [ ] Abrir ED, apagar tudo do campo H (deixar em 0), OK. O programa **não deve travar**. Ao chamar Coulomb (quando estiver implementado), deve tratar a divisão por zero.
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

## 14. Testes de cálculo (só depois que os métodos estiverem implementados) 🔴

Quando você começar a implementar Coulomb (Cap. 6 da apostila), estes viram os
testes de aceitação. Compare o resultado do software com os exercícios resolvidos
da apostila:

- [ ] **Caso default do SoloRef** (H=4, γ=20, φ=30°, c=0, parede vertical, sem sobrecarga): Coulomb deve dar **Ea = 53,33 kN/m** e θ = 60°.
- [ ] **Rankine mesmo caso**: idêntico a Coulomb (Ea = 53,33; θ = 60°).
- [ ] **Rankine com c = 10**: Ea = 17,13 kN/m; zt = 1,73 m.
- [ ] **Coulomb com δ = 20°**: Ka = 0,297; Ea = 47,5 kN/m.
- [ ] **Rankine com terreno inclinado i = 15°**: Ka = 0,373; Ea = 59,7 kN/m.
- [ ] **Bishop com 3 fatias (exercício 8.1 da apostila)**: FS = 1,39 (não parar na primeira iteração).
- [ ] **Geossintético caso default**: Tadm = 18 kN/m; N = 9 camadas; Sv = 0,44 m.

Recomendo transformar cada um desses em um teste em `tests/test_methods.py`.

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
