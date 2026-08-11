# Guia de teste manual — SoloRef

Percorra este roteiro com o app aberto (`python main.py`). Cada teste traz:
**onde digitar** (aba → campo → valor), **o que fazer**, **o que o app deve
mostrar** e a **referência da literatura** para comparar. Os valores "app" foram
calculados com o próprio código do programa; os "literatura" vêm das fontes
citadas (USACE 1989; Wesley 2009) e de fórmulas fechadas.

> Convenções: β = inclinação da face medida da horizontal (90° = vertical).
> No **Bishop**, o campo β (Geometria) é usado como o ângulo do talude.
> Empuxos em kN/m; Ka e FS adimensionais. Aceite diferença de ±0,5% nos casos de
> fórmula fechada e ±2–3% nos que fazem busca de superfície (Bishop, Dois Blocos).

---

## 1. Boot e janela

1. Rode `python main.py`. **Esperado:** abre sem erro; título "SoloRef —
   Dimensionamento de Estruturas de Solo Reforçado"; barra de ferramentas com
   Entrada de dados · Coulomb · Rankine · Dois Blocos · Bishop · Reforço ·
   Estabilidade externa · Quadro Resumo · Relatórios.
2. Ao abrir, o método **Rankine** já vem selecionado e calculado. **Esperado:**
   painel de resultados mostra o empuxo (ver Teste 2); esquema desenha o muro.

---

## 2. Rankine (empuxo ativo de cunha plana)

**2a — Caso padrão.** Sem alterar nada (H=4 m, γ=20, φ=30°, c=0, q=0), clique em
**Rankine**.

| Grandeza | App deve mostrar | Literatura |
|---|---|---|
| Ka | 0,333 | Ka = tan²(45−φ/2) = 1/3 |
| Empuxo Ea | 53,33 kN/m | ½·Ka·γ·H² = ½·(1/3)·20·16 = 53,33 |
| Inclinação da cunha | 60,0° | 45 + φ/2 = 60° |

**2b — Empuxo com H=6, γ=18.** Geometria → H = 6; Solo aterro → γ = 18. Clique
Rankine. **App:** Ea = **108,0 kN/m**. **Literatura (USACE):** ½·(1/3)·18·36 = 108.

**2c — Com sobrecarga.** No 2b, Sobrecarga → q = 20. **App:** Ea = **148,0 kN/m**.
**Literatura:** 108 + Ka·q·H = 108 + (1/3)·20·6 = 148.

**2d — Com coesão.** H = 6; γ = 17,5; φ = 20; c = 10; q = 0. **App:** Ea =
**70,42 kN/m**. **Literatura:** ½KaγH² − 2cH√Ka = 70,42 (Ka=0,490).
*(Obs.: o painel mostra Ea, Ka e cunha; a profundidade da trinca z0≈1,63 m é
calculada mas não exibida nos cartões.)*

**2e — Retroaterro inclinado.** Volte ao padrão; Geometria → i (inclinação do
topo) = 10; φ = 30. **App (Ka):** **0,349**. **Literatura (Rankine para talude):**
Ka = cos i·(cos i − √(cos²i − cos²φ))/(cos i + √…) = 0,34952.

---

## 3. Coulomb (cunha plana com atrito de muro)

**3a — Degenerescência (prova de coerência).** Padrão (H=4, γ=20, φ=30), mas
Solo aterro → "Atrito entre blocos δ" = **0**. Clique **Coulomb**.
**App:** Ka = **0,333**, Ea = **53,33 kN/m** — *idêntico a Rankine*.
**Literatura (USACE):** com δ=0, β=90°, i=0, Coulomb reduz-se a Rankine.

**3b — Efeito do atrito de muro.** Solo aterro → δ = **20**; φ = 30.
**App (Ka):** **0,297**. **Literatura:** Ka de Coulomb ≈ 0,297 para φ=30°, δ=20°.
*(Com o δ padrão de 30°, Ka≈0,297 e Ea≈47,6 kN/m — também aceitável.)*

**3c — Face vertical, retroaterro inclinado (Wesley).** H = 8; β = 90; i = 15;
γ = 18,5; φ = 28; c = 0; δ = 0. **App:** Ea ≈ **260,7 kN/m**, cunha ≈ **53°**.
**Literatura (Wesley 2009):** Ea = **261,1 kN/m**, cunha = **53°**.

---

## 4. Dois Blocos (cunha bilinear)

**4a — Coerência com δ=0.** Padrão (H=4, γ=20, φ=30), δ = **0**, q = 0. Clique
**Dois Blocos**. **Esperado:** Ea próximo de Rankine/Coulomb (~53 kN/m) — a
cunha bilinear degenera no caso simples. Observe o cursor de ampulheta e
"Calculando…" na primeira vez (o método otimiza).
*(Não há exemplo fechado de literatura para o Dois Blocos no schema atual; valide
por coerência: Ea ≥ Rankine e ~vizinhança de Coulomb.)*

**4b — Sensibilidade.** Aumente φ para 35 e depois 25. **Esperado:** Ea diminui
quando φ sobe e aumenta quando φ cai (monotonicidade).

---

## 5. Bishop simplificado (cunha circular) — usa β como talude

**5a — Aviso de validade.** Com o padrão (β = 90°, vertical), clique **Bishop**.
**Esperado:** aparece um **aviso** de que Bishop é para taludes abatidos (β < 70°)
e/ou que a face vertical degenera. (Não confie no número nesse caso.)

**5b — Limite de talude infinito.** Geometria → β = **20**, H = 10; Solo aterro →
γ = 18; φ = 30; c = 0. **App (FS):** **1,586**. **Literatura:** talude infinito
c=0 → FS = tan φ/tan β = tan30/tan20 = 1,5863.

**5c — Talude c–φ (Wesley).** β = **45**; H = 10; γ = 17; φ = 35; c = 21.
**App (FS):** ≈ **1,95**. **Literatura (Wesley 2009):** FS = **1,98** (seco).

**5d — Segundo caso Wesley.** β = **47**; H = 15; γ = 16,8; φ = 30; c = 23.
**App (FS):** ≈ **1,48**. **Literatura (Wesley 2009):** FS ≈ **1,50**.

---

## 6. Reforço com geossintéticos (dimensionamento interno)

**6a — Caso padrão.** Padrão (H=4, γ=20, φ=30, q=0); aba Reforço com os defaults
(Tult=40 kN/m; RFcr=2,0; RFid=1,1; RFd=1,1; Ci=0,8; FS=1,5). Clique **Reforço**.

| Grandeza | App deve mostrar | Verificação |
|---|---|---|
| Nº de camadas | 10 | ⌈H / Sv⌉ |
| Espaçamento Sv | 0,400 m | H/10 |
| Tadm | 16,53 kN/m | Tult/(RFcr·RFid·RFd)=40/2,42 |
| ΣTmax | 53,33 kN/m | **= Ea de Rankine** (consistência interna) |

**Literatura/coerência:** a soma das trações das camadas deve igualar o empuxo
ativo de Rankine para a mesma geometria (53,33) — é a prova de consistência.

**6b — Sensibilidade.** Sobrecarga → q = 20. **Esperado:** nº de camadas aumenta
e ΣTmax cresce (fica ≈ 66,7, o Ea de Rankine com q=20 para H=4... confira que
ΣTmax acompanha o empuxo).

---

## 7. Estabilidade externa (deslizamento, tombamento, capacidade de carga)

Preencha também **Solo de fundação** (base) e **Solo de encosta** (solo retido).

**7a — Caso padrão.** Sem alterar (H=4, B=5, γ=20, φ=30, c=0, q=0; encosta φ=30
c=0 γ=20, δ_ret=0; fundação φ=30 c=15 γ=20). Clique **Estabilidade externa**.
**App:** FS_desl ≈ **5,74**, FS_tomb ≈ **14,06**, FS_cap ≈ **17,33**, e ≈ 0,178 m.
Todos com selo verde (base larga de 5 m para muro de 4 m → muito estável).

**7b — Caso condutor (com sobrecarga).** No 7a, Sobrecarga → q = 10.
**App:** FS_desl ≈ **5,02**, FS_tomb ≈ **11,51**, FS_cap ≈ **14,96**, e ≈ 0,217 m.

**7c — Muro reforçado de Wesley (comparação com literatura).**
Geometria → H = 9; B = 3,7. Solo aterro → γ = 18,2; φ = 35; c = 0.
Solo encosta → γ = 16,8; φ = 26; c = 0; **δ_ret = 26**. Solo fundação → φ = 35;
**c = 0**; γ = 18,2. Sobrecarga q = 0. Clique Estabilidade externa.
**App:** FS_desl ≈ **1,94**, FS_tomb ≈ **2,01**. **Literatura (Wesley 2009):**
FS_desl = **1,94**, FS_tomb = **2,00**.
*(Atenção: se deixar a coesão da fundação no default 15, o FS de deslizamento sobe
para ~2,15 — por isso zere c da fundação para reproduzir o Wesley.)*

**7d — Sensibilidade.** No 7b, reduza B para **2,5**. **Esperado:** FS_desl e
FS_tomb caem bastante (base estreita) — a verificação "morde".

---

## 8. Comparar métodos e Quadro Resumo

1. Clique em **Comparar métodos** (ou registre método a método com "Registrar no
   quadro"). **Esperado:** o dock **Quadro Resumo** abre embaixo com uma coluna
   preenchida — solicitação de Coulomb/Rankine/Dois Blocos, FS de Bishop, nº de
   camadas do geossintético e os três FS da estabilidade externa.
2. Mude um parâmetro (ex.: φ = 32) e compare de novo. **Esperado:** nova coluna
   ao lado, permitindo confrontar as duas situações.

---

## 9. Interpretação dos resultados (selos)

1. Selecione **Bishop** no caso 5d (FS ≈ 1,48) com FS-alvo 1,5 (aba Reforço).
   **Esperado:** selo **INSUFICIENTE** (vermelho), pois FS < alvo.
2. No caso 5c (FS ≈ 1,95): selo **ADEQUADO** (verde).

---

## 10. Cache e desempenho

1. Selecione **Dois Blocos** (calcula, com ampulheta). Vá para **Bishop** e
   **volte** para Dois Blocos sem mudar dados. **Esperado:** a volta é
   **instantânea** (usa cache).
2. Agora **mude** um dado (ex.: γ). **Esperado:** ao reselecionar Dois Blocos,
   recalcula (ampulheta de novo) — o cache foi invalidado.

---

## 11. Avisos de aplicabilidade

1. Rankine/Coulomb com β = 45° (Geometria). **Esperado:** aviso de que a cunha
   plana é rigorosa só para 70°–90°.
2. Bishop com β = 90°. **Esperado:** aviso de talude/face inadequados (Teste 5a).

---

## 12. Salvar, abrir e alterações não salvas

1. Edite qualquer campo. **Esperado:** aparece "*" no título (alterações não
   salvas).
2. **Sistema → Salvar como…** `teste.json`. **Esperado:** "*" some; arquivo é
   JSON legível (abra num editor para conferir chaves geometria/solo_aterro/…).
3. Edite de novo e clique **Novo** (ou feche a janela). **Esperado:** pergunta
   Salvar/Descartar/Cancelar.
4. **Sistema → Abrir** `teste.json`. **Esperado:** os valores voltam; status
   "Carregado: teste.json".

---

## 13. Hipóteses e figura do método

Clique no botão **Hipóteses / figura** no painel de resultados. **Esperado:**
abre o diálogo com a figura da cunha do método ativo e o texto das hipóteses.

---

## Tabela-resumo dos gabaritos (literatura)

| Método | Entrada | App | Literatura |
|---|---|---|---|
| Rankine | φ=30, H=4 | Ea=53,33; 60° | Ka=1/3; Ea=53,33 |
| Rankine | φ=30, H=6, γ=18 | Ea=108,0 | 108 (USACE) |
| Rankine | +q=20 | Ea=148,0 | 148 |
| Rankine | φ=20, c=10, H=6, γ=17,5 | Ea=70,42 | 70,42 |
| Rankine | i=10, φ=30 | Ka=0,349 | 0,34952 |
| Coulomb | δ=0 (=Rankine) | Ka=0,333 | identidade (USACE) |
| Coulomb | δ=20, φ=30 | Ka=0,297 | 0,297 |
| Coulomb | H=8, i=15, φ=28, δ=0 | Ea=260,7; 53° | 261,1; 53° (Wesley) |
| Bishop | β=20, φ=30, c=0 | FS=1,586 | tan30/tan20=1,586 |
| Bishop | β=45, φ=35, c=21 | FS≈1,95 | 1,98 (Wesley) |
| Bishop | β=47, φ=30, c=23 | FS≈1,48 | ~1,50 (Wesley) |
| Geossint. | padrão | 10 cam.; ΣTmax=53,33 | ΣTmax=Ea Rankine |
| Externa | Wesley (c_fund=0) | 1,94 / 2,01 | 1,94 / 2,00 (Wesley) |

Se algum valor destoar muito do esperado (além das tolerâncias), anote a entrada
e o resultado obtido — comparado ao gabarito acima, isso localiza rapidamente se
é bug de cálculo, de exibição ou de unidade.
