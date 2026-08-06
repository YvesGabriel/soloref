# Manual do SoloRef

**Dimensionamento de Estruturas de Solo Reforçado — guia de uso, teoria e documentação técnica**

Iniciação Científica — Yves Gabriel Queiroz de Sousa · Orientador: Prof. José Antonio Schiavon

---

Este documento tem dois públicos e, por isso, duas partes independentes:

- A **Parte I** é para quem vai **usar** o programa. Cada funcionalidade vem com
  uma introdução teórica curta (conceito + equações-chave) seguida do passo a
  passo no programa e do resultado aplicado a um **exemplo condutor** único, que
  atravessa o documento inteiro. A ideia é que você consiga aprender a teoria
  enquanto opera o programa.
- A **Parte II** é para quem vai **mexer no código**: arquitetura, bibliotecas,
  modelo de dados, padrão dos métodos, testes e validação.

A **Parte III** ("Próximos passos") está reservada e será preenchida depois.

> Convenção de unidades em todo o documento: comprimentos em metros (m), ângulos
> em graus (°), pesos específicos em kN/m³, tensões e coesão em kN/m² (= kPa) e
> esforços por metro linear de muro em kN/m.

---

## Sumário

**Parte I — Uso do programa com teoria**
1. Sobre o SoloRef
2. Conceitos fundamentais
3. Instalação e primeiros passos
4. A interface em cinco minutos
5. Entrada de dados (as sete abas)
6. O exemplo condutor
7. Os métodos de cálculo
   - 7.1 Rankine · 7.2 Coulomb · 7.3 Dois Blocos · 7.4 Bishop · 7.5 Geossintéticos
8. Quadro resumo e interpretação
9. Salvar e abrir projetos
10. Validação e confiabilidade

**Parte II — Documentação técnica do código**
11. Arquitetura geral
12. Estrutura de pastas
13. Bibliotecas e por que cada uma
14. Modelo de dados
15. Padrão dos métodos de cálculo
16. Persistência
17. Testes e validação automática
18. Como estender o programa

**Parte III — Próximos passos** *(a preencher)*

Referências

---

# Parte I — Uso do programa com teoria

## 1. Sobre o SoloRef

O SoloRef é um programa para **dimensionamento de estruturas de contenção em solo
reforçado** — muros e taludes íngremes cuja estabilidade é garantida por camadas
de reforço (por exemplo, geossintéticos) embutidas no aterro. Ele é a
reimplementação, em stack moderna e multiplataforma (Python + PySide6), de um
programa antigo escrito para Windows 16/32 bits que não roda mais nos sistemas
atuais.

Na prática, o programa responde a três perguntas de projeto: **qual o esforço que
o solo retido impõe à estrutura** (empuxo de terra), **qual a segurança do maciço
contra o escorregamento** (fator de segurança) e **quanto reforço é preciso** para
atingir a segurança desejada. Para isso reúne quatro métodos clássicos de análise
por cunha — Rankine, Coulomb, Dois Blocos e Bishop simplificado — mais um módulo
de dimensionamento de reforço com geossintéticos.

O programa cobre hoje a **estabilidade interna** da estrutura (o que acontece
dentro do maciço reforçado). As verificações de **estabilidade externa**
(deslizamento na base, tombamento e capacidade de carga da fundação) estão
previstas para uma etapa futura, registrada na Parte III.

## 2. Conceitos fundamentais

Antes dos métodos, vale fixar cinco ideias que aparecem o tempo todo.

**Empuxo de terra.** É a força que uma massa de solo exerce sobre a estrutura que
a contém. Quando o muro tende a se afastar do solo (o caso de projeto de um muro
de arrimo), o solo se distende e mobiliza sua resistência ao cisalhamento; a
força resultante é o **empuxo ativo** (Ea), o menor valor possível — e é o que se
usa para dimensionar a contenção. O empuxo cresce com o quadrado da altura, o que
explica por que muros altos exigem tanto reforço.

**Coeficiente de empuxo ativo (Ka).** É a razão entre a tensão horizontal e a
vertical no estado ativo. Quanto maior o ângulo de atrito do solo (φ), menor o Ka
e, portanto, menor o empuxo — solos mais "travados" empurram menos.

**Cunha de ruptura.** Os métodos de equilíbrio-limite assumem que, na iminência do
colapso, uma "fatia" de solo escorrega ao longo de uma superfície de ruptura. Se
essa superfície é uma reta, fala-se em **cunha plana** (Rankine, Coulomb); se são
duas retas, **cunha bilinear** (Dois Blocos); se é um arco de círculo, **cunha
circular** (Bishop). A inclinação/posição crítica dessa superfície é aquela que
solicita mais a estrutura, e é o que os métodos procuram.

**Fator de segurança (FS).** É a razão entre o que resiste e o que solicita. Um
FS = 1 significa colapso iminente; projetos de contenção costumam exigir FS entre
1,3 e 1,5. Rankine, Coulomb e Dois Blocos entregam o **esforço** (Ea) a ser
resistido pelo reforço; Bishop entrega diretamente o **FS** do talude.

**Estabilidade interna × externa.** Estabilidade interna pergunta se o maciço
reforçado não rompe por dentro (reforço insuficiente, arrancamento). Estabilidade
externa trata o maciço como um bloco e pergunta se ele desliza, tomba ou afunda.
O SoloRef, nesta versão, trata da interna.

## 3. Instalação e primeiros passos

O programa exige **Python 3.10 ou superior**. Com o Python instalado, no diretório
do projeto:

```bash
pip install -r requirements.txt
python main.py
```

O primeiro comando instala as dependências (PySide6 para a interface, NumPy e
SciPy para os cálculos numéricos). O segundo abre a janela principal. Se a janela
aparece com o título "SoloRef — Dimensionamento de Estruturas de Solo Reforçado",
está tudo certo.

## 4. A interface em cinco minutos

A janela principal é dividida em três painéis lado a lado — **Dados** (entrada,
à esquerda), **Esquema ilustrativo** (ao centro) e **Resultado** (à direita) —
mais o **Quadro Resumo**, um painel acoplável (dock) que abre na base. Não há
diálogos modais nem sub-janelas MDI: editar um dado, escolher um método e ver o
resultado acontece tudo na mesma tela, ao vivo.

No alto ficam os **menus** (Sistema, Dimensionamento, Relatórios, Janelas,
Ajuda) e uma **navbar única** (toolbar, com os mesmos itens do menu
Dimensionamento) com nomes completos, na ordem: **Entrada de dados**, os
**cinco métodos** (Coulomb, Rankine, Dois Blocos, Bishop, Reforço com
geossintéticos — funcionam como abas exclusivas: clicar troca o método ativo e
recalcula), **Comparar métodos**, **Estabilidade externa** (reservado),
**Quadro Resumo** e **Relatórios**. Na base, a barra de status informa o que o
programa está fazendo e mostra o resultado do último cálculo — ou o primeiro
aviso de aplicabilidade do método, quando houver (seção 7).

O **esquema ilustrativo**, ao centro, não é um desenho genérico: depois de
calcular um método, ele passa a desenhar por cima do muro a **superfície
crítica** que aquele método encontrou — a reta da cunha (Rankine/Coulomb), a
bilinear (Dois Blocos), o círculo crítico (Bishop) ou as camadas de reforço
(Geossintéticos) — com um rótulo curto (ex. "cunha 60,0°", "FS = 1,945").
Editar um dado sem recalcular volta ao traço genérico, para não deixar na tela
uma cunha desatualizada.

O fluxo típico é: entrar os dados (painel da esquerda, sempre visível), escolher
um método na navbar para ver o resultado no painel da direita, e **Registrar no
quadro** quando quiser guardar aquela situação para comparar depois. Para
comparar **todos** os métodos de uma vez — o propósito central do programa —
use **Comparar métodos**: roda os cinco para o projeto atual e registra tudo
numa única coluna do Quadro Resumo, sem precisar clicar método por método
(seção 8).

Trocar para um método já calculado com os mesmos dados é instantâneo: o
programa guarda o último resultado de cada método num cache e só recalcula se
algo mudou desde então. Dois Blocos e Bishop rodam uma otimização numérica e
podem levar um instante na primeira vez (ou depois de editar um dado) — nesse
caso a barra de status mostra "Calculando <método>…" e o cursor vira uma
ampulheta enquanto processa, para não parecer que o programa travou.

## 5. Entrada de dados (as oito abas)

O painel **Dados**, à esquerda da janela principal, tem oito abas sempre
visíveis — não é um diálogo separado: qualquer edição atualiza o esquema
ilustrativo ao vivo e, se mudar algo em relação ao que está salvo, acende o
"*" de alterações não salvas no título da janela (seção 9).

**As abas mudam de cor conforme o método ativo.** Cada método usa só um
subconjunto dos dados — Rankine, por exemplo, não olha para o atrito
solo-muro (δ), que só entra em Coulomb e Dois Blocos. Ao trocar de método na
navbar, as abas relevantes para ele ficam em destaque (azul, com uma dica
"Usa: ..." ao passar o mouse) e as demais ficam atenuadas (cinza) — uma forma
rápida de saber que campo vale a pena conferir antes de calcular.

**Três abas são reservadas.** "Solo de encosta", "Solo de fundação" e "Face"
levam o sufixo "(estab. externa)" no rótulo e mostram um aviso amarelo no
topo: nenhum dos cinco métodos hoje implementados lê esses campos — eles
estão reservados para a futura verificação de estabilidade externa
(deslizamento, tombamento, capacidade de carga). Os campos continuam lá,
editáveis e salvos no projeto, só não entram no cálculo ainda.

Os parâmetros, agrupados por aba:

| Aba | Parâmetro | Significado |
|---|---|---|
| Geometria | H | Altura da parte reforçada da estrutura (m). |
| | β | Inclinação da face, medida da horizontal (90° = parede vertical). |
| | B | Largura do aterro reforçado (m). |
| | βe | Inclinação da encosta a jusante. |
| | i | Inclinação do talude no topo do muro. |
| | Ht | Altura do talude de topo. |
| Solo de aterro | γ | Peso específico do solo reforçado (kN/m³). |
| | c | Coesão (kN/m²). |
| | φ | Ângulo de atrito interno (°) — o parâmetro mais influente. |
| | δ | Ângulo de atrito solo-muro (interface), usado por Coulomb e Dois Blocos. |
| Solo de encosta *(estab. externa)* | γ, c, φ | Idem, para o solo da encosta a jusante. |
| Solo de fundação *(estab. externa)* | γ, c, φ | Idem, para o solo de apoio. |
| Face *(estab. externa)* | blocos | Se a face usa blocos, com altura/largura/recuo. |
| Sobrecarga | q | Sobrecarga uniforme no topo (kN/m²). |
| | P, x₀, e | Carga linear (trem-tipo), posição e eixo. |
| Reforço | Tult | Resistência à tração última do geossintético (kN/m). |
| | RFcr, RFid, RFd | Fatores de redução — fluência, dano de instalação, degradação. |
| | Ci | Coeficiente de interação (arrancamento). |
| | FS | Fator de segurança de projeto do reforço — também usado para julgar o FS do Bishop (seção 7.4). |
| Identificação | textos | Nome do projeto, empresa, número do dimensionamento. |

Dica de aprendizado: altere φ e observe o esquema e, depois de calcular, o
empuxo. Ver o Ea cair quando φ sobe fixa a intuição de que solo mais resistente
empurra menos.

## 6. O exemplo condutor

Para tornar tudo concreto, todo o restante da Parte I usa **o mesmo muro** como
exemplo. Descreva-o na aba de entrada de dados assim:

- **Geometria:** H = 4,0 m; face vertical (β = 90°); topo horizontal (i = 0°).
- **Solo de aterro:** γ = 20 kN/m³; φ = 30°; c = 0; δ = 20° (atrito solo-muro,
  adotado como ⅔·φ, valor típico).
- **Sobrecarga:** q = 10 kN/m² uniforme no topo.

É um muro vertical de 4 m, aterro granular limpo (sem coesão), com uma sobrecarga
de 10 kPa simulando, por exemplo, tráfego ou uma laje sobre o aterro. Guardaremos
esse projeto e passaremos por todos os métodos com ele. Para o método de Bishop,
que pressupõe geometria mais abatida, usaremos um exemplo complementar (um talude),
apresentado na seção 7.4.

## 7. Os métodos de cálculo

Cada método abaixo segue a mesma receita: **a ideia**, **as equações-chave**,
**quando usar**, **como rodar no programa** e **o resultado no exemplo**.

### 7.1 Método de Rankine

**A ideia.** Rankine (1857) supõe que, no estado ativo, todo o maciço atrás de uma
parede vertical atinge simultaneamente a plastificação, com planos de ruptura
inclinados a 45° + φ/2 da horizontal. É o método mais simples e serve de
referência para todos os outros.

**Equações-chave.** Para parede vertical e retroaterro horizontal:

```
Ka = tan²(45° − φ/2) = (1 − sen φ) / (1 + sen φ)
Ea = ½·Ka·γ·H²  +  Ka·q·H  −  2·c·H·√Ka
inclinação da cunha = 45° + φ/2
```

O primeiro termo do Ea é o empuxo do peso próprio do solo (cresce com H²), o
segundo é a contribuição da sobrecarga e o terceiro é o alívio dado pela coesão.
Para retroaterro inclinado (i ≠ 0) e sem coesão, o programa usa a forma de
Rankine para talude, com Ka função de i e φ.

**Quando usar.** Paredes verticais ou quase (70° ≤ β ≤ 90°), aterro homogêneo. É
o ponto de partida natural; para paredes com atrito de face relevante, Coulomb é
mais realista. Fora dessa faixa, ou com face não perfeitamente vertical, o
programa avisa sozinho — ver "Avisos de aplicabilidade" abaixo.

**Como rodar.** Com o exemplo carregado, clique no método **Rankine** na
navbar (ou no menu Dimensionamento) — o resultado aparece na hora no painel da
direita, e a cunha real (não mais um traço genérico) é desenhada por cima do
muro no esquema central. O botão "Hipóteses / figura" mostra as hipóteses do
método a qualquer momento, sem travar o fluxo. Para guardar essa situação e
comparar com outra depois, clique em **Registrar no quadro**.

**Resultado no exemplo.** Ka = 0,333; Ea = **66,67 kN/m** (53,33 do solo + 13,33
da sobrecarga); cunha a 60°. O painel de resultados mostra um cartão **Ponto de
aplicação (H/3) = 1,33 m** (válido para o caso sem coesão/sobrecarga
concentrada).

**Avisos de aplicabilidade.** Como a face do exemplo é vertical (β = 90°),
nenhum aviso aparece. Se β caísse abaixo de 90°, um banner amarelo no painel de
resultados (e a primeira linha, replicada na barra de status) lembraria que
Rankine só é rigoroso para parede vertical; abaixo de 70° o aviso passa a
recomendar Bishop (cunha circular) em vez da cunha plana.

### 7.2 Método de Coulomb

**A ideia.** Coulomb (1776) equilibra as forças sobre uma cunha plana de ruptura
tentativa e procura, entre todas as inclinações possíveis, aquela que produz o
**maior** empuxo. A grande vantagem sobre Rankine é incorporar o **atrito
solo-muro (δ)** e faces inclinadas.

**Equações-chave.** Coeficiente ativo geral (θ = inclinação da face em relação à
vertical; δ = atrito solo-muro; i = inclinação do topo):

```
Ka = cos²(φ − θ) /
     { cos²θ · cos(δ+θ) · [ 1 + √( sen(φ+δ)·sen(φ−i) / (cos(δ+θ)·cos(θ−i)) ) ]² }
Ea = ½·γ·H²·Ka  (+ Ka·q·H para a sobrecarga)
```

Quando δ = 0, θ = 0 e i = 0, essa fórmula se reduz exatamente a Rankine — uma boa
maneira de conferir que tudo está coerente. O programa calcula o Ka de duas formas
independentes (a fórmula fechada acima e uma **busca de cunha** que varre o ângulo
do plano de ruptura), e as duas se conferem mutuamente.

**Quando usar.** Sempre que o atrito de face for relevante ou a face não for
perfeitamente vertical, ainda dentro da faixa de cunha plana (70°–90°) — fora
dela, o mesmo aviso de Rankine/Dois Blocos aparece, recomendando Bishop.

**Como rodar.** Clique no método **Coulomb** na navbar. As abas de entrada que
Coulomb usa (Geometria, Solo de aterro — incluindo δ — e Sobrecarga) ficam
destacadas em azul no painel da esquerda enquanto ele estiver ativo.

**Resultado no exemplo.** Com δ = 20°, Ka = 0,297; Ea = **59,46 kN/m**; cunha
crítica ≈ 56°. Repare que o empuxo é **menor** que o de Rankine (66,67): o atrito
entre solo e muro "segura" parte da massa, aliviando a estrutura — por isso
desprezá-lo (Rankine) é conservador. O painel de resultados quantifica essa
diferença sozinho, num cartão **"Coulomb 11% abaixo de Rankine"** (o programa
recalcula Rankine em segundo plano — é fechado e barato — só para essa
comparação).

### 7.3 Método dos Dois Blocos

**A ideia.** Em vez de uma reta, a superfície de ruptura é uma **linha quebrada
(bilinear)**, dividindo o solo em dois blocos que interagem. Isso aproxima melhor
a forma real de ruptura de estruturas mais abatidas ou reforçadas, situando-se
entre a cunha plana e a circular. Como não há fórmula fechada, o programa **busca
numericamente** a geometria bilinear que maximiza o esforço.

**Equações-chave.** Não há uma expressão única; o método resolve, para cada
geometria tentativa, o equilíbrio de forças dos dois blocos (peso, sobrecarga,
reações com atrito e coesão nas bases e a força de interface entre eles) e
maximiza o empuxo sobre os parâmetros da linha quebrada (os dois ângulos e a
posição do ponto de inflexão).

**Quando usar.** Estruturas com face mais abatida, ou quando se quer um resultado
intermediário entre Coulomb e a análise circular. Para o caso simples (parede
vertical, δ = 0) ele reproduz Rankine/Coulomb, o que serve de aferição.

**Como rodar.** Clique no método **Dois Blocos** na navbar. Este é um dos dois
métodos mais pesados computacionalmente (faz uma otimização com `scipy`), então
a primeira vez pode levar um instante — a barra de status mostra "Calculando
Método dos Dois Blocos…" e o cursor vira ampulheta enquanto isso. Trocar de
método e voltar depois, sem editar nada, é instantâneo (o resultado fica em
cache); editar qualquer campo invalida o cache e o próximo cálculo roda de
novo.

**Resultado no exemplo.** Ea = **63,74 kN/m**, com a primeira cunha a ≈30° e a
segunda a ≈60° — o esquema desenha as duas retas, quebrando no ponto de
inflexão. O valor cai entre Coulomb (59,46) e Rankine (66,67), como esperado
para um método intermediário — o cartão de comparação mostra
**"Dois Blocos 4% abaixo de Rankine"** (a mesma referência usada no cartão de
Coulomb, para comparar os três métodos de empuxo numa base comum).

### 7.4 Método de Bishop simplificado

**A ideia.** Para taludes e faces abatidas, a ruptura é melhor descrita por um
**arco de círculo**. Bishop (1955) divide a massa deslizante em **fatias verticais**
e faz o equilíbrio de momentos em torno do centro do círculo, desprezando as
forças horizontais entre fatias (a "simplificação"). O resultado é diretamente o
**fator de segurança**.

**Equações-chave.** Para cada fatia i (largura bᵢ, ângulo da base αᵢ, peso Wᵢ):

```
mα(i) = cos αᵢ + sen αᵢ · tan φ' / FS
FS = Σ[ (c'·bᵢ + Wᵢ·tan φ') / mα(i) ] / Σ[ Wᵢ · sen αᵢ ]
```

O FS aparece nos dois lados (dentro de mα), então a equação é resolvida por
**iteração** até convergir. Em seguida o programa **procura o círculo crítico** —
o de menor FS — varrendo posições de centro e raio.

**Quando usar.** Faces abatidas (β < 70°), taludes, verificação global de
estabilidade. Não faz sentido para uma parede perfeitamente vertical, onde a cunha
plana é a hipótese adequada — e o programa avisa: com β ≥ 70° um banner amarelo
recomenda Coulomb/Rankine, e com β ≥ 89° avisa que a face está praticamente
vertical e o círculo de ruptura **degenera** (resultado sem sentido físico —
tente rodar Bishop no exemplo condutor da seção 6, com β = 90°, para ver isso
na prática).

**Como rodar.** Como Bishop pede geometria abatida, use um **exemplo
complementar**: H = 5 m, face a β = 30°, γ = 19 kN/m³, φ = 25°, c = 10 kN/m².
Digite esses valores no painel de dados e clique no método **Bishop** na
navbar — este é o outro método que otimiza (busca do círculo crítico), então a
barra de status mostra "Calculando..." e o cursor vira ampulheta na primeira
vez. Ao lado da geometria, ele desenha o círculo crítico encontrado, passando
pelo pé do talude.

**Resultado no exemplo complementar.** FS = **1,95** — um talude estável, com boa
folga sobre o mínimo usual de 1,5. Reduzir a coesão ou aumentar a inclinação faz
o FS cair, o que você pode explorar para ganhar intuição.

**Interpretando o FS: selo ADEQUADO / INSUFICIENTE.** O painel de resultados não
só mostra o número — ele **julga**. O cartão do fator de segurança carrega um
selo verde **"ADEQUADO"** quando FS ≥ FS alvo, ou vermelho **"INSUFICIENTE"**
quando FS < FS alvo. O FS alvo vem do mesmo campo usado para dimensionar o
reforço (aba **Reforço**, seção 5) — o padrão é 1,5, então o FS = 1,95 do
exemplo aparece com o selo **ADEQUADO**. Mude o FS alvo para, digamos, 2,0 e o
mesmo resultado passa a aparecer como **INSUFICIENTE**, sem precisar recalcular
nada — é só um julgamento sobre o número que já estava lá.

### 7.5 Reforço com geossintéticos

**A ideia.** Aqui o programa deixa de só medir o empuxo e passa a **dimensionar a
solução**: quantas camadas de geossintético, com que espaçamento vertical e que
comprimento, são necessárias para estabilizar o maciço. A metodologia adotada é a
de equilíbrio-limite / *tieback* (linha FHWA GEC-011 / AASHTO "Simplified
Method"), padrão em projeto de muros de solo reforçado (ver seção 15/Parte II para
a justificativa).

**Equações-chave.** Camada a camada, na profundidade z:

```
σv(z) = γ·z + q                        tensão vertical
σh(z) = Ka·σv(z)                       tensão horizontal a resistir
Tmax  = σh(z)·Sv                       tração exigida da camada (Sv = espaçamento)
Tadm  = Tult / (RFcr·RFid·RFd)         tração admissível de longo prazo
Sv ≤ Tadm / (Ka·σv·FS)                 espaçamento máximo admissível
L = La + Le,  La = (H−z)·tan(45°−φ/2),  Le ≥ Tmax·FS / (2·σv·Ci·tan φ)
```

Os **fatores de redução** (RFcr para fluência, RFid para dano de instalação, RFd
para degradação química/biológica) transformam a resistência de curto prazo do
geossintético (Tult) na que se pode contar ao longo da vida útil (Tadm). O
comprimento total de cada camada soma a parte dentro da zona ativa (La) com o
comprimento de ancoragem por arrancamento (Le).

**Quando usar.** Sempre que a estrutura precisar de reforço para atingir o FS
alvo — ou seja, o coração do "solo reforçado". Compõe com qualquer método de cunha
para a verificação da estabilidade.

**Como rodar.** Ajuste os parâmetros do geossintético (na aba **Reforço**:
resistência Tult, fatores de redução, coeficiente de interação Ci e FS alvo) e
clique no método **Reforço (geossintético)** na navbar.

**Resultado no exemplo.** Com um geossintético de Tult = 40 kN/m e fatores
padrão (Tadm = 16,5 kN/m), FS alvo = 1,5: o programa indica **11 camadas** com
espaçamento uniforme Sv = 0,36 m — o esquema desenha as 11 linhas horizontais
do reforço, mais curtas perto da base (a zona ativa La encolhe com a
profundidade). A soma das trações exigidas, ΣTmax = 66,67 kN/m, **coincide com
o empuxo ativo de Rankine** para o mesmo muro — o reforço, no conjunto,
equilibra exatamente o empuxo do solo, o que confirma a consistência do
dimensionamento.

**Selo OK / ALERTA.** O cartão "Nº de camadas" também carrega um selo: verde
**"OK"** quando o dimensionamento fechou (nº de camadas e espaçamento Sv
finitos e positivos), ou vermelho **"ALERTA"** quando não fechou — o caso
típico é um Tult baixo demais para o empuxo do muro (γ·H + q), que o programa
já impede de virar um número sem sentido na tela.

## 8. Quadro resumo e interpretação

O botão **Quadro Resumo** abre um painel acoplável (dock, na base da janela)
com uma tabela que guarda as últimas situações analisadas (até oito colunas,
em rolamento) com a geometria, os parâmetros do solo, as sobrecargas e os
resultados de cada método — inclusive o **FS de Bishop** (linha "FS, Mét.
Bishop") e o **número de camadas** do reforço, cada um na sua própria linha.
É a ferramenta para **comparar cenários** — por exemplo, o mesmo muro com
φ = 28° e φ = 32°, ou com e sem sobrecarga — lado a lado.

Há duas formas de preencher o quadro. **Registrar no quadro**, no painel de
resultados, guarda só o método ativo naquele momento — é o fluxo de antes,
método a método. **Comparar métodos**, na navbar, roda os **cinco métodos de
uma vez** para o projeto atual e registra tudo numa **única coluna**
consolidada — desde que essa é a razão de ser do programa (comparar Rankine,
Coulomb, Dois Blocos, Bishop e o dimensionamento do reforço lado a lado), essa
é a forma recomendada no dia a dia. Métodos fora da faixa de validade daquela
geometria (ex.: Bishop numa parede vertical) não são pulados — continuam
rodando e entrando na coluna, só ficam listados como "fora de faixa" na barra
de status ao final, para você saber que aquele número deve ser lido com
ressalva (ver os avisos de cada método na seção 7).

## 9. Salvar e abrir projetos

Em **Sistema > Salvar como…** o projeto é gravado em um arquivo **JSON** legível —
você pode abri-lo em qualquer editor de texto e inspecionar os dados, e ele é
fácil de versionar. **Sistema > Abrir** recarrega um projeto salvo. Como o formato
é texto aberto (e não um binário proprietário como no programa antigo), seus dados
ficam portáveis e auditáveis.

**Alterações não salvas.** Assim que você edita qualquer campo, em qualquer aba,
um `*` aparece no final do título da janela — um lembrete simples de que o que
está na tela ainda não foi gravado em disco. Salvar (`Ctrl+S` ou Sistema >
Salvar) apaga o `*`. Se você tentar **Novo**, **Abrir** outro projeto ou
**fechar o programa** com alterações pendentes, o SoloRef pergunta antes de
prosseguir — **Salvar**, **Descartar** ou **Cancelar** — para não perder
trabalho por engano. Cancelar a caixa de "Salvar como…" nesse fluxo também
conta como não ter salvo: o programa não descarta nada até você confirmar de
algum jeito.

## 10. Validação e confiabilidade

Um diferencial do SoloRef é vir com uma **bateria de validação automática**. O
comando

```bash
python validar.py
```

roda todos os métodos contra casos de referência da literatura (fórmulas fechadas
e casos-limite) e gera dois produtos: um **log** com data/hora em `logs/` e um
relatório legível, `RELATORIO_VALIDACAO.md`, com a tabela de casos, o erro
percentual de cada um e a fonte teórica. Na versão atual, **todos os casos passam
com erro inferior a 0,01%**. Isso permite confiar nos números e, sempre que o
código mudar, reexecutar a validação para garantir que nada regrediu.

---

# Parte II — Documentação técnica do código

Esta parte é independente da Parte I e voltada a quem for manter ou estender o
programa. Um guia complementar mais detalhado, arquivo por arquivo, está em
`GUIA_DESENVOLVEDOR.md`.

## 11. Arquitetura geral

O programa é dividido em **duas camadas estritamente separadas**:

```
soloref/ui/    (PySide6)      → janelas, diálogos, desenho, eventos
      │  usa
      ▼
soloref/core/  (Python puro)  → modelos de dados, cálculos, persistência
```

A regra central é que **`core/` não importa nada de Qt**. Os cálculos são Python
puro e podem rodar em script, em teste automatizado, numa futura interface web ou
em linha de comando, sem depender da interface gráfica. A camada `ui/` apenas
coleta dados, dispara os cálculos e mostra resultados. Essa separação é o que
torna a validação automática (seção 17) possível sem abrir janela nenhuma, e o que
permitiria trocar o PySide6 por outra tecnologia sem reescrever a engenharia.

## 12. Estrutura de pastas

```
SoloRef/
├── main.py                 ponto de entrada (python main.py)
├── validar.py              runner de validação com log e relatório
├── requirements.txt        dependências
├── soloref/
│   ├── core/
│   │   ├── models.py       dataclasses (Projeto, Solo, Geometria, Reforco, …)
│   │   ├── persistence.py  salvar/carregar JSON
│   │   └── methods/        um arquivo por método
│   │       ├── base.py     MetodoAnalise (abstrata) + Resultado + avisos()
│   │       ├── rankine.py  coulomb.py  dois_blocos.py  bishop.py  geossintetico.py
│   └── ui/
│       ├── main_window.py       janela única (3 painéis), navbar, cálculo, log
│       ├── panels.py             PainelDados (abas) e PainelResultados (cartões)
│       ├── relevancia.py         quais abas cada método usa (sem Qt)
│       ├── interpretacao.py      selos/cartões de julgamento (sem Qt)
│       ├── resumo_map.py         Resultado -> linhas do Quadro Resumo (sem Qt)
│       ├── estado_projeto.py     "há alterações não salvas?" (sem Qt)
│       ├── cache_resultados.py   cache de Resultado por método (sem Qt)
│       └── dialogs/              esquema_widget, metodo_info, quadro_resumo,
│                                  entrada_dados (abas reaproveitadas por panels.py)
├── tests/
│   ├── casos_literatura.py dataset de validação (fonte única de verdade)
│   ├── test_*.py           testes por método + modelos + degenerescência +
│   │                       módulos de ui/ sem Qt (relevancia, interpretacao,
│   │                       resumo_map, estado_projeto, cache_resultados, validade)
│   └── casos_referencia_original.csv   (vazio; conferência opcional c/ o programa antigo)
└── logs/                   logs de validação e de execução do app
```

## 13. Bibliotecas e por que cada uma

**PySide6** (Qt para Python) constrói toda a interface: a janela única de três
painéis (dados, esquema, resultado), o dock do Quadro Resumo, e o esquema do
muro — inclusive a superfície crítica de cada método — desenhado vetorialmente
com `QPainter`. É o binding oficial do Qt, multiplataforma (Windows, Linux,
macOS), o que atende ao objetivo de rodar em sistemas atuais.

**NumPy** fornece a álgebra vetorial usada no núcleo dos métodos — resolução de
sistemas lineares dos triângulos de forças (equilíbrio das cunhas), operações com
as fatias de Bishop, áreas de polígonos.

**SciPy** (`scipy.optimize`) fornece os **otimizadores** que procuram a superfície
crítica: `minimize_scalar` para a busca de cunha de Coulomb (1 variável) e
`minimize` para a superfície bilinear de Dois Blocos e o círculo crítico de Bishop
(várias variáveis).

**pytest** roda a suíte de testes automatizados. A biblioteca padrão do Python
cobre o resto: `dataclasses` (modelo de dados), `json` (persistência), `math`
(trigonometria) e `logging` (logs de validação e de uso).

## 14. Modelo de dados

Em `core/models.py`, cada aba de entrada corresponde a uma `@dataclass`:
`Identificacao`, `Geometria`, `FaceEstrutura`, `Solo` (usada três vezes — aterro,
encosta, fundação), `Sobrecarga` e `Reforco` (parâmetros do geossintético). A
classe `Projeto` agrega todas elas e é o objeto único que circula pelo programa:
a UI o preenche, os métodos o consomem, a persistência o serializa. Os nomes dos
campos trazem a unidade embutida (por exemplo `peso_especifico_kN_m3`,
`angulo_atrito_g`) para evitar ambiguidade e ficar perto da notação da literatura.

## 15. Padrão dos métodos de cálculo

Todo método herda de `MetodoAnalise` (em `methods/base.py`), que define o contrato
mínimo: um atributo `nome`, uma `sigla`, uma tupla `hipoteses` (o texto mostrado
na interface) e o método `calcular(projeto) -> Resultado`. O
`Resultado` é uma dataclass com campos comuns (`solicitacao_kN_m`,
`inclinacao_cunha_g`, `fator_seguranca`) e um dicionário livre `extras` para os
dados específicos de cada método (Ka, geometria crítica, lista de camadas, etc.).

Além disso, `MetodoAnalise.avisos(projeto) -> list[str]` (default: lista vazia)
devolve avisos de aplicabilidade calculados só a partir dos dados de entrada,
sem rodar `calcular` — é o que alimenta o banner amarelo do painel de
resultados e a mensagem da barra de status (seção 7). Cada método sobrescreve
`avisos` conforme a faixa de validade já descrita em `hipoteses`: Coulomb,
Rankine e Dois Blocos avisam fora de 70°–90° de inclinação da face; Bishop
avisa dentro dessa faixa (o oposto — é um método de cunha circular) e alerta
separadamente quando a face está tão vertical que o círculo degenera; o
Geossintético avisa quando a tração admissível não fecha para o empuxo do
muro.

Esse padrão é o que faz adicionar um método novo não exigir mexer em nenhum outro:
cria-se o arquivo, herda-se de `MetodoAnalise`, implementa-se `calcular`, e
registra-se a classe. Os métodos sem fórmula fechada (Dois Blocos, Bishop) seguem
internamente a mesma estrutura: uma função que avalia uma geometria tentativa e
uma função de busca (grade grosseira + refino com SciPy) que encontra a crítica.

Sobre a escolha metodológica do reforço (seção 7.5): adotou-se a linha
**FHWA/AASHTO "Simplified Method"** por ser a mais documentada, determinística
(logo, testável) e padrão de projeto de muros de solo reforçado; a implementação
usa a **regra do ponto médio** para posicionar cada camada, o que faz a soma das
trações reproduzir exatamente o empuxo de Rankine e sustenta o teste de
consistência da validação.

## 16. Persistência

`core/persistence.py` salva e carrega o `Projeto` em **JSON**, usando
`dataclasses.asdict()` para serializar. O formato é texto legível, versionável em
git e independente de plataforma — uma melhoria deliberada sobre o arquivo binário
proprietário do programa original. Campos novos adicionados às dataclasses são
serializados automaticamente, sem alterar a persistência.

## 17. Testes e validação automática

Há duas camadas complementares de verificação. A primeira é o **pytest**
(`tests/test_*.py`): um arquivo por método, mais testes de modelos e de casos
degenerados, cada um comparando a saída contra valores conhecidos dentro de uma
tolerância. A segunda é o **runner** `validar.py`, que lê o dataset único
(`tests/casos_literatura.py`), roda cada caso, calcula o erro relativo, grava um
log com timestamp e gera o `RELATORIO_VALIDACAO.md`. O runner sai com código de
erro se algum caso falhar, o que o torna adequado para integração contínua.

A mesma regra de "sem Qt, então testável sem abrir janela" vale para a lógica
de interface que não é desenho puro: `test_relevancia.py`, `test_interpretacao.py`,
`test_resumo_map.py`, `test_estado_projeto.py` e `test_cache_resultados.py`
cobrem, respectivamente, o mapa de abas relevantes por método, os selos de
julgamento (ADEQUADO/INSUFICIENTE, OK/ALERTA), o mapeamento para o Quadro
Resumo, o rastreamento de alterações não salvas e o cache de resultados —
`test_validade.py` cobre os `avisos()` de cada método. Só o desenho do
esquema (`esquema_widget.py`) e a montagem dos widgets em si ficam fora do
pytest, por dependerem de Qt; esses foram conferidos manualmente, rodando o
app e tirando screenshot do esquema de cada método (seção 4).

O gabarito é **a literatura**: fórmulas fechadas (Rankine, Coulomb), casos-limite
auto-verificáveis (Coulomb que degenera em Rankine; talude infinito de Bishop com
FS → tan φ/tan β; consistência ΣTmax = Ea do reforço) e, opcionalmente, a
conferência com o programa original — para a qual existe o arquivo
`casos_referencia_original.csv` (hoje vazio), alimentado sob demanda sem que os
testes principais dependam dele.

## 18. Como estender o programa

O caminho para adicionar um método novo: criar `core/methods/<novo>.py` herdando
de `MetodoAnalise`, registrá-lo no `__init__.py` do pacote de métodos, acrescentar
sua aba de hipóteses em `dialogs/metodo_info.py` e ligá-lo na toolbar/menu de
`ui/main_window.py`. Para um campo de entrada novo, adiciona-se ao dataclass
correspondente em `models.py` e ao formulário em `dialogs/entrada_dados.py` — a
persistência acompanha sozinha. Para um novo caso de validação, basta uma entrada
no dataset `tests/casos_literatura.py`. O `GUIA_DESENVOLVEDOR.md` traz um cookbook
passo a passo para cada uma dessas situações.

---

# Parte III — Próximos passos

*(Seção reservada. Será preenchida com o roteiro de evolução do programa —
estabilidade externa e memorial de cálculo, prova de fidelidade ao programa
original, e os entregáveis acadêmicos.)*

---

## Referências

- Bishop, A. W. (1955). *The use of the slip circle in the stability analysis of
  slopes.* Géotechnique.
- Coulomb, C. A. (1776). *Essai sur une application des règles de maximis et
  minimis à quelques problèmes de statique.*
- Das, B. M. *Principles of Geotechnical Engineering.* Cengage.
- Craig, R. F. *Craig's Soil Mechanics.* CRC Press.
- FHWA. *Design of Mechanically Stabilized Earth Walls and Reinforced Soil Slopes*
  (GEC-011).
- Rankine, W. J. M. (1857). *On the stability of loose earth.* Philosophical
  Transactions of the Royal Society.

*Documento gerado como base para os entregáveis da Iniciação Científica. Os
valores numéricos do exemplo foram calculados com a própria implementação do
SoloRef.*
