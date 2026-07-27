# Plano de implementação — SoloRef

Documento mestre de arquitetura para (1) implementar todos os métodos de cálculo,
(2) montar uma base de testes coerente com a literatura e (3) rodar um **teste
completo do programa** de forma automática, com logs.

> **Decisões travadas com o orientando (Yves):**
> - **Gabarito dos testes = literatura.** Fórmulas fechadas e casos-limite
>   auto-verificáveis são a fonte de verdade. Nada crítico depende de rodar o
>   programa antigo.
> - **Programa original = conferência secundária e opcional.** Rodar o SoloRef
>   antigo dá muito trabalho, então o mecanismo de comparação existe, mas fica
>   desativado por padrão e é alimentado sob demanda (ver §5).
> - **Geossintéticos = metodologia de equilíbrio-limite tipo FHWA/AASHTO**
>   (justificada em §3.5).

Todas as fórmulas-âncora deste documento foram verificadas numericamente
(Rankine H=4/γ=20/φ=30 → Ea = 53,3333 kN/m; Coulomb degenera em Rankine com
erro ~1e-17).

---

## 1. Onde o projeto está

- Arquitetura `core/` (Python puro) × `ui/` (PySide6) já pronta e limpa.
- **UI funcional, cálculos inexistentes.** Os cinco métodos (`coulomb`,
  `rankine`, `dois_blocos`, `bishop`, `geossintetico`) são placeholders que
  retornam `Resultado()` vazio.
- **UI não conectada ao cálculo.** Em `main_window._mostrar_metodo` (linha ~204)
  chama-se `adicionar_situacao(self.projeto)` sem nunca invocar
  `metodo().calcular(...)`.
- Testes cobrem só o modelo de dados. Não há `test_methods.py` nem harness de
  validação.

O objetivo deste plano é fechar exatamente essas três lacunas.

---

## 2. Estratégia geral e ordem de execução

Ordem pensada para fechar o loop ponta-a-ponta cedo e sempre com rede de testes:

1. **Fundação de testes** — dataset de casos + harness de validação com log
   (mesmo antes dos métodos, para que cada método nasça testado).
2. **Rankine** — mais simples, fórmula fechada, é o oráculo de referência para
   os demais (todo método deve concordar com Rankine no caso degenerado).
3. **Conexão UI ↔ cálculo** — assim que Rankine existe, ligar a UI e ver número
   real na tela + log de execução do app.
4. **Coulomb** — caso geral (parede inclinada θ, atrito de muro δ, talude i).
5. **Dois Blocos** — cunha bilinear com busca da superfície crítica.
6. **Bishop simplificado** — fatias + iteração de FS + busca do círculo crítico.
7. **Geossintéticos** — dimensionamento interno (nº de camadas, Sv, La+Le).
8. **Fechamento** — relatório de validação consolidado + logs do app + revisão.

Cada etapa é um chunk isolado com prompt próprio (ver `PROMPTS_CLAUDE_CODE.md`).

**Regra de ouro:** nenhum método é dado como pronto sem (a) um teste de
literatura, (b) um teste de caso degenerado batendo com Rankine/Coulomb quando
aplicável, e (c) testes de limites/monotonicidade.

---

## 3. Métodos: fórmulas e o que implementar

Convenção de geometria do projeto (`models.py`): `β` (`inclinacao_face_beta_g`)
é a inclinação da face medida **da horizontal** (90° = parede vertical). Logo o
ângulo da parede **em relação à vertical** usado em Coulomb é `θ = 90 − β`. O
talude do topo é `i` (`inclinacao_topo_i_g`). O atrito solo-muro `δ` sai de
`solo_aterro.angulo_atrito_blocos_g`.

### 3.1 Rankine (`rankine.py`) — Prioridade 1

Empuxo ativo, parede vertical, retroaterro horizontal:

```
Ka = tan²(45 − φ/2) = (1 − sinφ)/(1 + sinφ)
σa(z) = Ka·γ·z + Ka·q − 2c·√Ka
Ea = ½·Ka·γ·H² + Ka·q·H − 2c·H·√Ka
z0 (trinca de tração) = (2c − ... )/(γ√Ka)   # profundidade onde σa = 0
```

Inclinação da cunha de ruptura = **45 + φ/2**. Ponto de aplicação a H/3 (caso
sem coesão/sobrecarga).

Retroaterro inclinado (i ≠ 0), c = 0 (Rankine para talude):
```
Ka = cos i · (cos i − √(cos²i − cos²φ)) / (cos i + √(cos²i − cos²φ))
Ea = ½·γ·H²·Ka   (empuxo paralelo ao talude)
```

**Ressalva de validade (já nas hipóteses):** rigoroso só para parede vertical;
para 70° ≤ β < 90° usa-se como aproximação.

### 3.2 Coulomb (`coulomb.py`) — Prioridade 2

Coeficiente ativo geral:
```
Ka = cos²(φ − θ)
     ────────────────────────────────────────────────────────────
     cos²θ · cos(δ + θ) · [ 1 + √( sin(φ+δ)·sin(φ−i) /
                                    ( cos(δ+θ)·cos(θ−i) ) ) ]²
Ea = ½·γ·H²·Ka         (atua a δ da normal à parede)
```
com θ = 90 − β (parede em relação à vertical), δ = atrito solo-muro, i = talude.

Sobrecarga uniforme q: tratar como altura equivalente de solo `heq = q/γ` ou
somar termo `Ka·q·H` conforme a convenção adotada — **documentar a escolha**.

**Teste degenerado (oráculo forte):** θ=0, δ=0, i=0 ⇒ Ka deve igualar Rankine
(verificado: erro ~1e-17). Este teste sozinho pega a maioria dos erros de sinal.

Ângulo da cunha crítica: pode-se obter por forma fechada ou por busca de cunha
(Culmann). Sugerido implementar a **busca de cunha (trial wedge)** e conferir
que o Ea resultante coincide com a fórmula fechada — dois caminhos independentes
validando um ao outro.

### 3.3 Dois Blocos (`dois_blocos.py`) — Prioridade 3

Equilíbrio-limite com **superfície de ruptura bilinear** (duas cunhas), que
aproxima a circular para paredes mais abatidas. Não há fórmula fechada:

1. Parametrizar a superfície (ângulos das duas cunhas / posição do ponto de
   inflexão).
2. Para cada candidata, montar o equilíbrio dos dois blocos (peso, empuxo entre
   blocos, atrito e coesão nas bases) e extrair a solicitação.
3. **Buscar a superfície crítica** (máxima solicitação) por grade + refinamento
   ou `scipy.optimize` (adicionar `scipy` ao `requirements.txt`).

**Oráculos (sem fórmula fechada):**
- **Limites:** solicitação ≥ empuxo ativo de Rankine e na vizinhança de Coulomb
  para geometria simples.
- **Monotonicidade:** ↑φ ⇒ ↓solicitação; ↑γ e ↑H ⇒ ↑solicitação.
- **Convergência:** a busca retorna sempre o mesmo crítico com refino.
- **Opcional:** comparação com o programa original (§5).

### 3.4 Bishop simplificado (`bishop.py`)

Ruptura circular, método das fatias, FS iterativo:
```
FS = Σ[ (c'·b + (W − u·b)·tanφ') / mα ] / Σ[ W·sinα ]
mα = cosα + (sinα·tanφ') / FS
```
Iterar FS até convergir (ponto fixo, tolerância ~1e-4). Depois **buscar o
círculo crítico** (centro/raio de menor FS) por grade + refino.

**Oráculos de literatura (hand-checkable):**
- **Talude infinito, c=0:** FS → tanφ/tanβ (verificado: φ=30,β=20 → 1,5863).
  Um círculo muito raso/longo deve tender a esse valor.
- **φ=0 (não drenado):** FS = c·L_arco·R / (W·d) — checável analiticamente para
  um círculo dado; casa com os números de estabilidade de **Taylor**.
- **Benchmark publicado:** transcrever 1–2 exemplos resolvidos de Das
  (*Principles of Geotechnical Engineering*) ou Craig (*Soil Mechanics*) — só
  copiar entrada/saída do livro, sem precisar rodar nada.
- **Convergência** da iteração de FS e da busca do círculo.

### 3.5 Geossintéticos (`geossintetico.py`) — metodologia recomendada

**Escolha: método de equilíbrio-limite / tieback (linha FHWA GEC-011 / AASHTO
"Simplified Method").** Justificativa: é o procedimento mais documentado, com
exemplos resolvidos publicados, determinístico (bom para virar teste), e é o
padrão de projeto de muros de solo reforçado (MSE walls). É compatível com
qualquer método de cunha já implementado para a estabilidade externa.

Estabilidade **interna**, camada a camada:
```
σv(z) = γ·z + q                      (tensão vertical na profundidade z)
σh(z) = Kr·σv(z)                     (Kr = Ka para geossintéticos)
Tmax  = σh(z)·Sv                     (tração requerida por camada, por metro)
Tadm  = Tult / (RFcr·RFid·RFd·FS)    (tração admissível de longo prazo)
        RFcr = fluência, RFid = dano de instalação, RFd = degradação química/bio
Espaçamento:  Sv ≤ Tadm / (Kr·σv·FS)
Comprimento:  L = La + Le
   La = (H − z)·tan(45 − φ/2)                 (dentro da zona ativa)
   Le ≥ Tmax·FS / (2·σv·Ci·tanφ)              (ancoragem por arranque/pullout)
```

**Oráculos:**
- **Consistência interna:** Σ(Tmax das camadas) ≈ empuxo ativo total de Rankine
  (fecha o balanço de forças) — teste cruzado poderoso.
- **Exemplo resolvido FHWA/livro** transcrito (por camada é hand-checkable).
- **Monotonicidade:** ↑q ⇒ ↑nº de camadas; ↑Tult ⇒ ↓nº de camadas.

---

## 4. Base de testes e o "teste completo do programa"

Duas camadas complementares: **pytest** (pass/fail para CI/rotina) e um
**runner de validação com log e relatório legível** (o "teste completo").

### 4.1 Dataset de casos (fonte única de verdade)

Arquivo `tests/casos_literatura.py` (ou `.yaml`) com uma tabela de casos, cada
um com: `id`, `metodo`, `fonte` (citação bibliográfica ou "degenerado"/"limite"),
`entradas` (dict que monta um `Projeto`), `esperado` (dict de saídas) e
`tolerancia`. Exemplos que já entram prontos:

| id | método | fonte | entrada | esperado |
|---|---|---|---|---|
| RANK-01 | Rankine | fechada | H=4, γ=20, φ=30, c=0 | Ea=53,333; cunha=60° |
| RANK-02 | Rankine | fechada | H=6, γ=17,5, φ=20, c=10 | Ea=70,417; z0=1,632 |
| RANK-03 | Rankine | talude | i=10, φ=30 | Ka=0,34952 |
| COUL-01 | Coulomb | degenerado | θ=0, δ=0, i=0, φ=30 | Ka=0,33333 (=Rankine) |
| COUL-02 | Coulomb | fechada | δ=15, θ=0, i=0, φ=30 | Ka=0,30142 |
| BISH-01 | Bishop | limite | talude infinito, c=0, φ=30, β=20 | FS=1,5863 |
| GEO-01 | Geossint. | consistência | — | ΣTmax ≈ Ea_Rankine |

(Valores acima já conferidos numericamente. Benchmarks de livro para Dois
Blocos/Bishop entram por transcrição, conforme §3.)

### 4.2 pytest — um arquivo por método

`tests/test_rankine.py`, `test_coulomb.py`, `test_dois_blocos.py`,
`test_bishop.py`, `test_geossintetico.py`, `test_degeneracia.py` (todos os
casos degenerados num lugar) e `test_integracao.py` (roda o método via a mesma
função que a UI usa, sem abrir Qt). Cada teste lê o dataset e compara dentro da
tolerância. `test_models.py` continua como está.

### 4.3 Runner de validação com log — `validar.py`

Um script único (`python validar.py`, ou `python -m soloref.validacao`) que:

1. Percorre **todos** os casos do dataset.
2. Monta o `Projeto`, roda o método, compara com o esperado, calcula o **erro
   relativo (%)** e marca ✔/�’✗.
3. Emite **log estruturado** via `logging` (timestamp, nível, caso, entrada,
   saída, esperado, erro) para `logs/validacao_AAAA-MM-DD_HHMMSS.log`.
4. Gera **`RELATORIO_VALIDACAO.md`** legível: tabela de resultados, taxa de
   aprovação, pior erro por método, e a citação da fonte de cada caso.
5. Sai com código ≠ 0 se algo falhar (serve de CI/pré-commit).

Esse runner é o "teste completo do programa": um comando, um relatório, um log
auditável — coerente com a literatura e reexecutável a qualquer momento.

### 4.4 Logs de execução do app (uso real)

Além dos testes, instrumentar o app: sempre que um método roda pela UI, logar
entrada + `Resultado` em `logs/soloref_app.log`. Isso dá rastros de uso real que
podem ser comparados aos casos de validação e ajuda a depurar em campo.

---

## 5. Conferência opcional com o programa original

Sem tornar os testes principais dependentes disso:

- O dataset aceita casos com `fonte="SoloRef original"` no **mesmo schema**. Um
  arquivo separado `tests/casos_referencia_original.csv` fica **vazio por
  padrão**; o runner o carrega automaticamente se existir e reporta numa seção à
  parte do relatório.
- **Caminho mais barato primeiro:** transcrever exemplos numéricos que já estejam
  no **manual do programa antigo, na dissertação/relatório de origem ou em
  material do Prof. Schiavon** — isso dá pontos de referência do original **sem
  rodar** o executável.
- Se em algum momento rodar o SoloRef antigo (DOSBox/VM), basta anotar
  entrada→saída nesse CSV. O mecanismo já está pronto; só falta alimentar.

> **A pensar com o orientador:** definir 5–10 casos canônicos (as situações do
> Quadro Resumo) que sirvam de "prova de fidelidade" entre original e
> reimplementação. Fica registrado aqui como pendência de decisão.

---

## 6. Integração UI ↔ cálculo

Em `main_window._mostrar_metodo(aba)`, após o diálogo de hipóteses, instanciar o
método correspondente à aba, rodar `.calcular(self.projeto)` e passar o
`Resultado` para `self._resumo_widget.adicionar_situacao(...)`. Mapear
`aba → classe` por lista (`[MetodoCoulomb, MetodoRankine, MetodoDoisBlocos,
MetodoBishop, MetodoGeossintetico]`). Envolver em try/except mostrando erro na
status bar (ex.: método fora da faixa de validade de β) e logar. Ajustar
`quadro_resumo.py` para exibir as novas linhas (FS Bishop, nº de camadas etc.).

---

## 7. Dependências e convenções

- Adicionar `scipy` (otimização de Dois Blocos/Bishop) e `pytest` ao
  `requirements.txt`.
- `core/` continua **sem importar Qt**. Toda a lógica testável fora da UI.
- Nomes de campos em português com unidade no nome, como já é a convenção.
- Cada método documenta no docstring a **fonte** da formulação e a **faixa de
  validade**.

---

## 8. Checklist de conclusão

- [ ] Runner de validação e dataset criados; `test_models.py` ainda passa.
- [ ] Rankine implementado + testes (RANK-01/02/03) verdes.
- [ ] UI conectada ao cálculo; número real aparece no Quadro Resumo; app loga.
- [ ] Coulomb implementado; teste degenerado bate com Rankine.
- [ ] Dois Blocos implementado; limites e monotonicidade ok.
- [ ] Bishop implementado; limite de talude infinito e benchmark ok.
- [ ] Geossintéticos implementado; ΣTmax ≈ Ea_Rankine ok.
- [ ] `RELATORIO_VALIDACAO.md` gerado com 100% dos casos de literatura verdes.
- [ ] `requirements.txt`, README e GUIA_DESENVOLVEDOR atualizados.
- [ ] Mecanismo de conferência com o original pronto (CSV vazio + seção no
      relatório).
