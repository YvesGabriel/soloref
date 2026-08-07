# SoloRef — inputs de cada método (para buscar exemplos de validação)

Este documento descreve **exatamente** quais dados de entrada cada método do
SoloRef consome, com unidade, faixa e significado, e **qual saída** ele produz —
para que se possam buscar na literatura exemplos resolvidos (com resposta
conhecida) e usá-los como casos de teste.

## Convenções gerais (valem para todos)

- Unidades: comprimento em **m**, ângulo em **graus (°)**, peso específico em
  **kN/m³**, coesão e tensão/sobrecarga em **kN/m² (= kPa)**, empuxo por metro
  linear de muro em **kN/m**.
- **β (inclinação da face)** é medida **a partir da horizontal**: 90° = parede
  vertical; 70° = face abatida 20° em relação à vertical.
- **i (inclinação do topo)** = inclinação do talude sobre o muro (0 = topo
  horizontal).
- **δ (atrito solo-muro)** = ângulo de atrito da interface entre o solo e a face.
- **φ (ângulo de atrito)** e **c (coesão)** = parâmetros de resistência do solo.
- Convenção de sinal e hipóteses seguem a teoria clássica de empuxo ativo
  (muro tende a se afastar do solo).

Um "bom exemplo" é um **problema resolvido de livro/norma** que forneça as
entradas abaixo **e** a resposta (Ka, Ea, FS, etc.), para conferência numérica.

---

## 1. Rankine (empuxo ativo, cunha plana)

**Entradas consumidas:**

| Símbolo | Campo | Unidade | Faixa | Significado |
|---|---|---|---|---|
| H | altura da parte reforçada | m | > 0 | altura do muro |
| β | inclinação da face | ° | 70–90 | 90 = vertical (rigoroso só na vertical) |
| i | inclinação do topo | ° | −45 a 45 | talude sobre o muro |
| γ | peso específico do aterro | kN/m³ | ~15–22 | solo retido |
| φ | ângulo de atrito do aterro | ° | 0–45 | resistência do aterro |
| c | coesão do aterro | kN/m² | ≥ 0 | coesão do aterro |
| q | sobrecarga uniforme | kN/m² | ≥ 0 | carga distribuída no topo |

**Saídas (para conferir):** coeficiente ativo **Ka = tan²(45 − φ/2)**; empuxo
total **Ea** (kN/m); inclinação da cunha **45 + φ/2**. Com coesão: profundidade
da trinca de tração z₀.

**Que exemplos buscar:** empuxo ativo de Rankine em parede vertical, solo
granular (c = 0) e solo c–φ; caso com retroaterro inclinado (i ≠ 0, c = 0);
com e sem sobrecarga uniforme. (Das, Craig, Bowles, Budhu.)

---

## 2. Coulomb (empuxo ativo, cunha plana com atrito de muro)

**Entradas consumidas:** as mesmas de Rankine **mais**:

| Símbolo | Campo | Unidade | Faixa | Significado |
|---|---|---|---|---|
| δ | ângulo de atrito entre blocos / solo-muro | ° | 0–φ | atrito na interface solo-muro |

(β pode ser < 90° — face inclinada. i = talude do topo.)

**Saídas (para conferir):** **Ka de Coulomb** (função de φ, δ, θ=90−β, i);
empuxo **Ea**; ângulo da cunha crítica. Caso particular: δ = 0, β = 90°, i = 0
⇒ Ka deve coincidir com Rankine.

**Que exemplos buscar:** coeficiente/empuxo ativo de Coulomb com atrito de muro
δ (ex.: δ = ⅔φ), face inclinada e/ou retroaterro inclinado. (Das, Bowles.)

---

## 3. Dois Blocos (cunha bilinear)

**Entradas consumidas:** iguais às de Coulomb (H, β, i, γ, φ, c, δ, q).

**Saídas (para conferir):** empuxo **Ea** e a geometria da cunha bilinear (dois
ângulos + ponto de inflexão). Não há fórmula fechada — para o caso simples
(parede vertical, δ = 0) o Ea deve ficar **próximo de Coulomb/Rankine**; para
faces abatidas fica um pouco maior.

**Que exemplos buscar:** métodos de **cunha bilinear / two-part wedge** para
muros de solo reforçado (FHWA/AASHTO), ou exemplos que comparem cunha bilinear
com cunha plana. São mais raros; se não achar caso fechado, servem exemplos de
Coulomb para comparação de ordem de grandeza.

---

## 4. Bishop simplificado (estabilidade de talude, cunha circular)

**Atenção:** aqui o campo **β (inclinação da face) é usado como o ângulo do
talude natural**, medido da horizontal. O método vale para **taludes abatidos
(β < 70°)**; solo **homogêneo** de uma camada; círculo passando pelo pé do
talude ("toe circle").

**Entradas consumidas:**

| Símbolo | Campo | Unidade | Faixa | Significado |
|---|---|---|---|---|
| H | altura | m | > 0 | altura do talude |
| β | inclinação do talude | ° | 10–70 | ângulo do talude com a horizontal |
| γ | peso específico | kN/m³ | ~15–22 | solo do talude |
| φ | ângulo de atrito | ° | 0–40 | resistência |
| c | coesão | kN/m² | ≥ 0 | coesão (drenada c′) |

**Saída (para conferir):** **fator de segurança FS** (o programa busca o círculo
crítico de menor FS). Casos-limite úteis: talude infinito c = 0 ⇒ FS =
tanφ/tanβ; caso φ = 0 (não drenado) ⇒ número de estabilidade de Taylor.

**Que exemplos buscar:** exemplos resolvidos de **estabilidade de talude pelo
método de Bishop simplificado** (método das fatias) em **solo homogêneo**, com
FS conhecido; e benchmarks de estabilidade de talude (ex.: ACADS/associação
australiana). Devem informar H, β, γ, φ, c e o FS. (Das, Craig, Duncan.)

---

## 5. Reforço com geossintéticos (dimensionamento interno)

**Entradas consumidas:**

| Símbolo | Campo | Unidade | Faixa | Significado |
|---|---|---|---|---|
| H | altura | m | > 0 | altura do muro reforçado |
| γ | peso específico do aterro | kN/m³ | ~15–22 | aterro reforçado |
| φ | ângulo de atrito do aterro | ° | 25–40 | resistência do aterro |
| q | sobrecarga uniforme | kN/m² | ≥ 0 | carga no topo |
| Tult | resistência à tração última do geossintético | kN/m | > 0 | do produto |
| RFcr | fator de redução — fluência | – | ≥ 1 | tipicamente 2–4 |
| RFid | fator de redução — dano de instalação | – | ≥ 1 | tipicamente 1,1–1,5 |
| RFd | fator de redução — degradação | – | ≥ 1 | tipicamente 1,1–1,5 |
| Ci | coeficiente de interação (arrancamento) | – | 0–1 | interface solo-reforço |
| FS | fator de segurança de projeto | – | ≥ 1 | alvo (ex.: 1,5) |

**Saídas (para conferir):** **número de camadas**, **espaçamento vertical Sv**,
tração admissível **Tadm = Tult/(RFcr·RFid·RFd)**, e comprimentos (ancoragem
Le + zona ativa La). Consistência: a soma das trações ≈ empuxo ativo de Rankine.

**Que exemplos buscar:** exemplos resolvidos de **dimensionamento interno de
muro de solo reforçado com geossintético** (método FHWA GEC-011 / AASHTO
"Simplified Method"): dado H, γ, φ, q, Tult e fatores de redução, quantas
camadas e que espaçamento. (FHWA, Koerner *Designing with Geosynthetics*.)

---

## 6. Estabilidade externa *(planejada — ainda não implementada)*

Inclua exemplos também para esta etapa, que trata o maciço como bloco rígido:

**Entradas:** B (largura da base, m), H, γ_aterro, q; solo **retido** (φ, c) para
o empuxo; solo de **fundação** (φ_f, c_f, γ_f) para atrito na base e capacidade
de carga; embutimento D (m, opcional).

**Saídas (para conferir):** FS de **deslizamento**, FS de **tombamento**,
excentricidade e, e FS de **capacidade de carga** (fatores de Vésic Nc, Nq, Nγ).

**Que exemplos buscar:** verificação de **estabilidade externa de muro de solo
reforçado / muro de arrimo** (deslizamento, tombamento, capacidade de carga) e
exemplos de **capacidade de carga de sapata corrida** (Terzaghi/Vésic/Meyerhof)
com q_ult conhecido. (Das *Principles*, FHWA GEC-011.)

---

## Pedido pronto para a outra IA

> Preciso de **problemas resolvidos da literatura de geotecnia** para validar um
> programa de muros de solo reforçado. Para cada um dos temas abaixo, traga de 2
> a 3 exemplos numéricos **com resposta conhecida** (de livros como Das, Craig,
> Bowles, Budhu, Koerner, ou de normas FHWA/AASHTO), citando a fonte:
>
> 1. Empuxo ativo de **Rankine** (parede vertical; casos c=0, c–φ, e com
>    retroaterro inclinado). Dar H, γ, φ, c, q e a resposta Ka e Ea.
> 2. Empuxo ativo de **Coulomb** com atrito de muro δ e/ou face inclinada. Dar
>    φ, δ, β, i e a resposta Ka e Ea.
> 3. **Cunha bilinear / two-part wedge** para solo reforçado, se houver caso
>    resolvido.
> 4. Estabilidade de talude por **Bishop simplificado** em solo homogêneo. Dar
>    H, inclinação do talude, γ, φ, c e o FS.
> 5. Dimensionamento **interno com geossintético** (FHWA/AASHTO). Dar H, γ, φ,
>    q, Tult e fatores de redução, e a resposta (nº de camadas, espaçamento).
> 6. **Estabilidade externa** de muro (deslizamento, tombamento, capacidade de
>    carga) e capacidade de carga de sapata (Vésic/Terzaghi). Dar geometria e
>    parâmetros do solo de fundação, e os FS / q_ult.
>
> Para cada exemplo, devolva neste formato, para eu inserir direto nos testes:
>
> ```
> id:        (ex.: RANK-EXT-01)
> metodo:    rankine | coulomb | dois_blocos | bishop | geossintetico | externa
> fonte:     (autor, obra, página/exemplo)
> entradas:  H=..., beta=..., i=..., gamma=..., phi=..., c=..., q=...,
>            delta=..., Tult=..., RFcr=..., RFid=..., RFd=..., Ci=..., FS=...
>            (só os campos que o método usa)
> esperado:  Ka=... e/ou Ea=... e/ou FS=... e/ou n_camadas=... (com unidades)
> tolerancia: (ex.: 1%)
> ```
>
> Use as unidades: m, graus, kN/m³, kN/m², kN/m. β é medido da horizontal
> (90° = parede vertical). Priorize exemplos com número fechado e fonte citável.
