# Estabilidade externa — fundamentação + prompt para o Claude Code

Este arquivo tem duas partes: (A) a **fundamentação de engenharia** (fórmulas,
convenções e casos de validação já calculados) e (B) o **prompt-mestre chunkado**
para o Claude Code implementar. Cole o prompt tarefa por tarefa, commitando entre
elas. Todos os números de referência abaixo foram calculados e conferidos.

---

# Parte A — Fundamentação

A estabilidade externa trata o **maciço reforçado como um bloco rígido** e
verifica três modos de falha, além de reaproveitar a análise global (Bishop) já
existente. É o que faltava para o dimensionamento fechar — e é o que dá função às
abas hoje "reservadas": **Solo de fundação** (atrito na base + capacidade de
carga) e **Solo de encosta** (solo retido que gera o empuxo externo).

## Convenções e geometria do bloco

Bloco reforçado retangular de largura `B` (`largura_aterro_B_m`) e altura `H`
(`altura_H_m`). Peso do bloco e da sobrecarga sobre ele:

```
W = γ_aterro · B · H          (peso do maciço reforçado, kN/m)
Q = q · B                     (sobrecarga uniforme sobre o topo, kN/m)
N = W + Q                     (vertical total na base)
```

**Empuxo motor (solo retido atrás do bloco).** Usa o solo de encosta como
retroaterro retido. O coeficiente é o de Rankine — para não duplicar cálculo,
**reutilize `MetodoRankine`** montando um `Projeto` temporário com
`solo_aterro = solo_encosta` (fonte única de verdade). O empuxo atua **inclinado**
de `δ_ret` em relação à horizontal (atrito solo-muro do retido), gerando uma
componente vertical que ALIVIA a estrutura:

```
Ka = tan²(45 − φ_ret/2)
Ea_solo = ½·Ka·γ_ret·H²        (parcela do peso de solo, aplicada a H/3)
Ea_sob  = Ka·q·H               (parcela da sobrecarga, aplicada a H/2)
Pah = Ea_solo + Ea_sob         (componente HORIZONTAL do empuxo)
Pav = Pah · tan(δ_ret)         (componente VERTICAL; δ_ret = atrito solo-muro do retido)
```

`δ_ret` é o atrito da interface do solo retido: default **0** (empuxo horizontal,
conservador — reproduz o exemplo condutor abaixo); para muros de solo reforçado
adota-se `δ_ret = φ_ret` (convenção FHWA/Wesley — necessária para reproduzir o
benchmark EXT-REF-01). Exponha `δ_ret` como parâmetro (ex.:
`solo_encosta.angulo_atrito_blocos_g`, 0 se None).

## 1. Deslizamento na base

```
Fr = (N + Pav)·tan(φ_base) + c_base·B    (a componente vertical Pav soma à normal)
FS_desl = Fr / Pah                       (alvo típico ≥ 1,5)
```
`φ_base`, `c_base` = atrito/coesão na base. Por padrão use o **solo de fundação**;
mas note que muros MSE deslizam pelo menor entre φ_fundação e φ_aterro — o
benchmark de Wesley (EXT-REF-01) usa o φ do **maciço reforçado**. Deixe a fonte de
φ_base configurável/documentada.

## 2. Tombamento em torno do pé (toe)

```
M_estab = N·(B/2) + Pav·B                      (peso no centro + Pav no extremo da base)
M_tomb  = Ea_solo·(H/3) + Ea_sob·(H/2)         (só a componente horizontal tomba)
FS_tomb = M_estab / M_tomb                     (alvo típico ≥ 2,0)
```
Excentricidade da resultante na base:
```
a = (M_estab − M_tomb) / (N + Pav)
e = B/2 − a                                    (exigir e ≤ B/6: sem tração)
```

## 3. Capacidade de carga da fundação (Vésic, sapata corrida)

```
B' = B − 2e                                    (largura efetiva de Meyerhof)
σ_v = N / B'                                   (tensão de contato efetiva)
Nq = e^(π·tanφ_f)·tan²(45 + φ_f/2)
Nc = (Nq − 1)/tanφ_f          (=5,14 se φ_f=0)
Nγ = 2·(Nq + 1)·tanφ_f                         (Vésic)
q_ult = c_f·Nc + γ_f·D·Nq + ½·γ_f·B'·Nγ        (D = embutimento, default 0)
FS_cap = q_ult / σ_v                           (alvo típico ≥ 2,0–3,0)
```
`c_f, φ_f, γ_f` = solo de fundação. `D` pode ser um campo novo (`embutimento_m`)
— a linha "embutimento" já existe no Quadro Resumo (hoje fixa em 0).

**FS global externo** = min(FS_desl, FS_tomb, FS_cap).

## Casos de validação (já calculados — usar como gabarito)

Fatores de capacidade de carga (Vésic):

| φ_f | Nc | Nq | Nγ |
|---|---|---|---|
| 25° | 20,72 | 10,66 | 10,88 |
| 30° | 30,14 | 18,40 | 22,40 |
| 35° | 46,12 | 33,30 | 48,03 |

Exemplo condutor — bloco H=4, B=5, γ=20, φ=30, c=0, q=10; fundação φ=30, c=15,
γ=20, D=0; solo retido = mesmo φ=30:

| Grandeza | Valor |
|---|---|
| W / Q / N | 400 / 50 / 450 kN/m |
| Ka / Eah | 0,3333 / 66,67 kN/m |
| Fr / **FS_desl** | 334,8 / **5,02** |
| M_estab / M_tomb / **FS_tomb** | 1125 / 97,78 / **11,51** |
| excentricidade e | 0,217 m (B/6=0,833 → OK) |
| B' / σ_v / q_ult / **FS_cap** | 4,565 / 98,57 / 1474,9 / **14,96** |

(Exemplo condutor usa `δ_ret = 0` → Pav = 0, logo os números acima não mudam.
Base larga de 5 m para muro de 4 m → tudo muito estável. Um caso com B menor,
p.ex. B=2,5, deve derrubar FS_desl e FS_tomb — bom caso de sensibilidade.)

**EXT-REF-01 — benchmark de literatura (conferido, reproduz exatamente).**
Wesley (2009), muro de solo reforçado. Bloco H=9, B=3,7; maciço reforçado
γ=18,2, φ=35; solo retido γ=16,8, φ=26, c=0, **com δ_ret = φ_ret = 26°**;
φ_base = 35° (maciço reforçado); sem sobrecarga.

| Grandeza | Esperado (Wesley) | Recálculo | 
|---|---|---|
| Ka (retido) | 0,391 | 0,3905 |
| Pah / Pav | 265,7 / 129,6 kN/m | 265,7 / 129,6 |
| W (peso do bloco) | 606,1 kN/m | 606,1 |
| **FS_deslizamento** | **1,94** | 1,94 |
| **FS_tombamento** | **2,00** | 2,01 |

Este caso só fecha com o empuxo **inclinado** (δ_ret=26°) e o Pav entrando na
resistência ao deslizamento e no momento estabilizante — por isso a formulação
acima. Adicione-o a `tests/casos_literatura.py` (metodo="externa") na Tarefa 4.

Fontes: FHWA GEC-011 e Das (capacidade de carga, Vésic); Wesley (2009),
*Fundamentals of Soil Mechanics*, cap. de muros de solo reforçado (EXT-REF-01).

> **Nota de schema (verificada):** o modelo **já separa** os pesos específicos —
> `solo_aterro.γ` (reforçado), `solo_encosta.γ` (retido) e `solo_fundacao.γ`
> (fundação) são campos independentes. Não é preciso alterar o schema; basta a
> implementação usar cada um no seu lugar (bloco ← aterro, empuxo ← encosta,
> capacidade de carga ← fundação).

---

# Parte B — Prompt-mestre (cole tarefa por tarefa)

## Contexto e regras

```
Você vai implementar a ESTABILIDADE EXTERNA do SoloRef (muro de solo reforçado
tratado como bloco rígido): deslizamento, tombamento e capacidade de carga.
Leia antes: PROMPTS_ESTABILIDADE_EXTERNA.md (Parte A — fórmulas e casos de
validação já calculados), MANUAL_SOLOREF.md, PLANO_IMPLEMENTACAO.md e
GUIA_DESENVOLVEDOR.md.

Arquitetura: core/ é Python puro (sem Qt); ui/ é PySide6. Métodos herdam de
MetodoAnalise (core/methods/base.py) e devolvem Resultado(fator_seguranca=...,
extras={...}). A UI já tem o botão/menu "Estabilidade externa" (act_ext), hoje
ligado a _nao_impl.

REGRAS INEGOCIÁVEIS:
1. NÃO altere as fórmulas dos métodos existentes. `python validar.py` deve
   continuar 100% verde e `pytest` (101 testes) não pode regredir.
2. Toda lógica de cálculo nova vai em core/ (Python puro, testável sem Qt).
3. ADICIONE testes para cada verificação nova, comparando com os valores da
   Parte A (FS_desl=5,02; FS_tomb=11,51; FS_cap=14,96; fatores de Vésic).
4. Rode `pytest -q` e `python validar.py` ao fim de CADA tarefa; commit por tarefa.

Modelos (core/models.py): Geometria(altura_H_m, largura_aterro_B_m, ...),
Solo(peso_especifico_kN_m3, coesao_kN_m2, angulo_atrito_g, ...), Sobrecarga
(uniforme_q_kN_m2). solo_fundacao e solo_encosta já existem no Projeto.
```

### Tarefa 1 — Núcleo de cálculo (core, testável)

```
Crie core/methods/estabilidade_externa.py com a classe
MetodoEstabilidadeExterna(MetodoAnalise): nome="Estabilidade externa",
sigla="Ext". Implemente calcular(projeto) seguindo EXATAMENTE as fórmulas da
Parte A:
- Peso W, sobrecarga Q, vertical N (γ do ATERRO, B, H + q).
- Empuxo motor: REUTILIZE MetodoRankine montando um Projeto temporário com
  solo_aterro = projeto.solo_encosta (o solo retido é o de encosta). Recupere
  Ea_solo e Ea_sob (recomponha com Ka e H se preciso; Ka vem de extras["Ka"]).
  Componente horizontal Pah = Ea_solo + Ea_sob; componente vertical
  Pav = Pah·tan(δ_ret), onde δ_ret é o atrito solo-muro do retido
  (solo_encosta.angulo_atrito_blocos_g, 0 se None). Pav alivia a estrutura.
- FS_desl = ((N+Pav)·tan(φ_base) + c_base·B) / Pah. Documente a fonte de φ_base
  (default: solo_fundacao; deixe possível usar o φ do aterro reforçado, como no
  benchmark EXT-REF-01).
- FS_tomb = (N·B/2 + Pav·B) / (Ea_solo·H/3 + Ea_sob·H/2); excentricidade
  e = B/2 − (M_estab−M_tomb)/(N+Pav).
- FS_cap (Vésic, com D=embutimento default 0), usando N+Pav como vertical.
- Fatores Nc, Nq, Nγ (Vésic) numa função pura à parte (fácil de testar).
- Devolva Resultado(fator_seguranca=min(FS_desl,FS_tomb,FS_cap),
  extras={FS_desl, FS_tomb, FS_cap, e_m, B_efetivo_m, sigma_v_kPa, q_ult_kPa,
  Pah_kN_m, Pav_kN_m, N_kN_m, Nc, Nq, Ngama}).
- avisos(projeto): alertar se e > B/6 (tração na base) e se B for pequeno
  demais em relação a H.
- Registre a classe em core/methods/__init__.py.

  Dois casos de teste na Parte A: (a) exemplo condutor com δ_ret=0
  (FS_desl=5,02; FS_tomb=11,51; FS_cap=14,96); (b) EXT-REF-01 (Wesley) com
  δ_ret=φ_ret=26° e φ_base=35° → Pah=265,7; Pav=129,6; FS_desl=1,94;
  FS_tomb=2,00. Ambos devem passar dentro de ~1%.

Crie tests/test_estabilidade_externa.py cobrindo: os três FS do exemplo condutor
(tolerância 0,5%), os fatores de Vésic para φ=25/30/35, e um caso com B=2,5 que
reprove deslizamento/tombamento (FS < alvo). Se precisar de um campo de
embutimento, adicione Geometria.embutimento_m: float = 0.0 (não quebra JSON
antigo; persistence acompanha).

Aceite: pytest verde (incluindo os novos); validar.py 9/9 verde (cálculos
antigos intactos).
```

### Tarefa 2 — Integração na interface

```
Ligue a estabilidade externa à UI (soloref/ui/), sem quebrar nada.

1. main_window.py: faça act_ext rodar MetodoEstabilidadeExterna e mostrar o
   resultado no PainelResultados (não precisa entrar no grupo exclusivo dos 5
   métodos de cunha — é uma verificação à parte). Use o mesmo caminho de
   _calcular (esquema + painel + log + cache), tratando "Ext" como sigla.
2. panels.py (_cartoes): quando o resultado for de estabilidade externa (tem
   extras["FS_desl"]), mostre três cartões — Deslizamento, Tombamento,
   Capacidade de carga — cada um com o FS e o selo ADEQUADO/INSUFICIENTE
   (verde/vermelho) via ui/interpretacao.py, comparando com os alvos
   (desl 1,5; tomb 2,0; cap 2,0 — deixe-os como constantes nomeadas). Some um
   cartão com a excentricidade e (e o limite B/6).
3. ui/relevancia.py: para a sigla "Ext", marque como relevantes as abas
   Geometria, Solo aterro, Solo encosta, Solo fundação e Sobrecarga; e faça as
   abas "Solo encosta" e "Solo fundação" DEIXAREM de ser tratadas como
   "reservadas" (agora são consumidas). "Face" continua reservada.
4. esquema_widget.py: no overlay do modo "Ext", desenhe o bloco reforçado (B×H),
   a resultante vertical N no ponto a partir do pé (com a excentricidade e) e a
   seta do empuxo motor Eah a H/3. Fallback seguro se faltar dado.

Aceite: clicar em "Estabilidade externa" mostra os três FS com selos; abas
encosta/fundação passam a ser destacadas nesse modo; app abre e roda ponta a
ponta; pytest/validar verdes.
```

### Tarefa 3 — Quadro Resumo e comparação

```
1. dialogs/quadro_resumo.py: adicione linhas "FS deslizamento", "FS tombamento"
   e "FS capacidade de carga"; popule a linha "embutimento (m)" já existente com
   Geometria.embutimento_m. Preserve todas as linhas/chaves atuais.
2. ui/resumo_map.py: mapeie o Resultado de MetodoEstabilidadeExterna para as
   novas chaves (ext_fs_desl, ext_fs_tomb, ext_fs_cap) e amplie os testes de
   resumo_map para cobri-lo.
3. Inclua a estabilidade externa no botão "Comparar métodos" (rodar junto e
   registrar na mesma coluna).

Aceite: comparar métodos preenche também os três FS externos; testes de
resumo_map verdes.
```

### Tarefa 4 — Validação, docs e fechamento

```
1. Adicione o exemplo condutor de estabilidade externa a
   tests/casos_literatura.py (mesmo schema) para que `validar.py` reporte os três
   FS externos junto dos demais casos; confirme 100% verde.
2. Rode `pytest -q` e `python validar.py` e cole os resumos.
3. Rode o app: exercite estabilidade externa (com B=5 → estável; com B=2,5 →
   reprova), comparação e Quadro Resumo; tire screenshots.
4. Atualize MANUAL_SOLOREF.md (nova seção de estabilidade externa na Parte I,
   com as fórmulas e o exemplo; e a menção na Parte II) e GUIA_DESENVOLVEDOR.md
   (novo método, novas linhas do quadro, campo embutimento). NÃO preencha a
   Parte III.

Aceite: suíte completa verde; documentação refletindo a estabilidade externa.
```

---

### Ordem e dependências

Tarefa 1 (core) é pré-requisito de tudo. As 2–3 são de UI e podem ir uma a uma.
A 4 fecha e documenta. Um commit por tarefa: se algo regredir, `validar.py` e
`pytest` acusam na hora — e como a Tarefa 1 não toca nos métodos existentes, o
9/9 da literatura é sua rede de segurança contra mexer no que já funciona.

> **Decisão a alinhar com o Prof. Schiavon:** os FS-alvo (deslizamento 1,5;
> tombamento 2,0; capacidade 2,0) e a escolha de Vésic para os fatores de
> capacidade de carga. Se a referência do seu trabalho usar outros valores
> (p.ex. Meyerhof, ou FS por norma), ajuste as constantes na Tarefa 2/1.
