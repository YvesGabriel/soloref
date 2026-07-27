# Prompts para o Claude Code (VS Code)

Cole um prompt por vez, **na ordem**. Cada um é autocontido e termina com um
critério de aceite (testes verdes). Só avance quando o anterior passar.

> Contexto comum: projeto **SoloRef**, reimplementação PySide6 de programa de
> muros de solo reforçado. Arquitetura `core/` (Python puro) × `ui/` (PySide6).
> O plano completo está em `PLANO_IMPLEMENTACAO.md` — leia-o antes de começar.
> Gabarito dos testes = **literatura** (não dependa de rodar o programa antigo).

---

## Prompt 0 — Ambiente e fundação de testes

```
Leia PLANO_IMPLEMENTACAO.md e GUIA_DESENVOLVEDOR.md para entender a arquitetura.

Sem implementar nenhum método de cálculo ainda, prepare a fundação de testes:

1. Adicione `scipy` e `pytest` ao requirements.txt.
2. Crie tests/casos_literatura.py com uma estrutura de dados (lista de
   dataclasses ou dicts) para casos de validação, cada um com: id, metodo,
   fonte, entradas (que montam um Projeto), esperado (dict) e tolerancia.
   Já popule com os casos da tabela da seção 4.1 do plano cujos valores estão
   confirmados: RANK-01, RANK-02, RANK-03, COUL-01, COUL-02, BISH-01, GEO-01.
3. Crie validar.py na raiz: um runner que percorre todos os casos, monta o
   Projeto, chama o método correspondente, compara com o esperado calculando
   erro relativo (%), marca pass/fail, escreve log estruturado via `logging`
   em logs/validacao_<timestamp>.log e gera RELATORIO_VALIDACAO.md legível
   (tabela, taxa de aprovação, pior erro por método, fonte de cada caso).
   Sai com código != 0 se houver falha. Como nenhum método está implementado,
   nesta etapa todos devem falhar de forma controlada (sem exceção não tratada).
4. Rode `pytest tests/ -v` (test_models.py deve continuar passando) e
   `python validar.py` (deve rodar até o fim e gerar o relatório).

Não altere core/methods/*.py nesta etapa além do necessário para importar.
```

---

## Prompt 1 — Rankine + testes

```
Implemente o Método de Rankine em soloref/core/methods/rankine.py conforme a
seção 3.1 de PLANO_IMPLEMENTACAO.md:
- Ka = (1 - sinφ)/(1 + sinφ); Ea = ½·Ka·γ·H² + Ka·q·H − 2c·H·√Ka;
  cunha = 45 + φ/2; para i≠0 e c=0 use a forma de Rankine para talude.
- Preencha Resultado com solicitacao_kN_m, inclinacao_cunha_g e extras (Ka, z0).
- Docstring citando a fonte (Das/Craig) e a faixa de validade (β vertical).

Crie tests/test_rankine.py lendo tests/casos_literatura.py e validando
RANK-01, RANK-02, RANK-03 dentro da tolerância. Adicione asserts de sanidade
(Ea>0; Ka entre 0 e 1).

Rode `pytest tests/test_rankine.py -v` e `python validar.py`. Os casos RANK-*
devem ficar verdes no RELATORIO_VALIDACAO.md.
```

---

## Prompt 2 — Conexão UI ↔ cálculo + log do app

```
Conecte a UI aos cálculos conforme a seção 6 de PLANO_IMPLEMENTACAO.md.

1. Em soloref/ui/main_window.py, método _mostrar_metodo(aba): após o diálogo de
   hipóteses, mapeie aba -> classe de método
   ([MetodoCoulomb, MetodoRankine, MetodoDoisBlocos, MetodoBishop,
   MetodoGeossintetico]), chame .calcular(self.projeto), e passe o Resultado
   para self._resumo_widget.adicionar_situacao(...). Envolva em try/except:
   em erro, mostre mensagem na status bar e não quebre o app.
2. Ajuste soloref/ui/dialogs/quadro_resumo.py para exibir os resultados reais
   (solicitação e inclinação da cunha por método). Métodos ainda placeholders
   devem aparecer como "—" sem quebrar.
3. Configure logging no app: ao rodar um método pela UI, logue entrada +
   Resultado em logs/soloref_app.log.

Como só Rankine está implementado, teste manualmente: abrir o app, Entrada de
Dados com defaults, clicar Rank, e conferir Ea≈53,33 no Quadro Resumo e no log.
Garanta que pytest e validar.py continuam funcionando.
```

---

## Prompt 3 — Coulomb + testes

```
Implemente o Método de Coulomb em soloref/core/methods/coulomb.py conforme a
seção 3.2 de PLANO_IMPLEMENTACAO.md:
- Ka geral com θ=90−β, δ=solo_aterro.angulo_atrito_blocos_g, i=inclinacao_topo.
- Ea = ½·γ·H²·Ka; documente a convenção adotada para a sobrecarga q.
- Implemente TAMBÉM uma busca de cunha (trial wedge / Culmann) e verifique no
  teste que o Ea da busca coincide com o da fórmula fechada.

Crie tests/test_coulomb.py com COUL-01 (degenerado: θ=0,δ=0,i=0 ⇒ Ka=Rankine,
tolerância apertada ~1e-6) e COUL-02 (δ=15 ⇒ Ka=0,30142). Adicione o caso
degenerado também a tests/test_degeneracia.py.

Rode `pytest -v` e `python validar.py`. COUL-* verdes.
```

---

## Prompt 4 — Dois Blocos + testes

```
Implemente o Método dos Dois Blocos (cunha bilinear) em
soloref/core/methods/dois_blocos.py conforme a seção 3.3 do plano:
- Parametrize a superfície bilinear; para cada candidata monte o equilíbrio dos
  dois blocos; busque a superfície crítica (máxima solicitação) por grade +
  refino ou scipy.optimize.
- Resultado com solicitacao_kN_m, inclinacao_cunha_g e extras (geometria crítica).

Como não há fórmula fechada, crie tests/test_dois_blocos.py com:
- Limite inferior: solicitação >= Ea de Rankine para geometria simples.
- Proximidade de Coulomb em caso de parede vertical.
- Monotonicidade: ↑φ ⇒ ↓solicitação; ↑γ e ↑H ⇒ ↑solicitação.
- Convergência: mesmo crítico com refino mais fino.

Rode `pytest -v` e `python validar.py`.
```

---

## Prompt 5 — Bishop simplificado + testes

```
Implemente o Bishop simplificado em soloref/core/methods/bishop.py conforme a
seção 3.4 do plano:
- Fatias; FS iterativo com mα = cosα + sinα·tanφ'/FS; iterar até convergir.
- Busca do círculo crítico (centro/raio de menor FS) por grade + refino.
- Resultado com fator_seguranca e extras (círculo crítico, nº de fatias).

Crie tests/test_bishop.py com:
- BISH-01 (talude infinito, c=0, φ=30, β=20 ⇒ FS≈1,5863).
- Caso φ=0 conferido analiticamente para um círculo dado.
- 1 benchmark de livro (Das ou Craig) transcrito — peça a referência exata a
  mim se precisar; não invente números.
- Convergência da iteração e da busca.

Rode `pytest -v` e `python validar.py`.
```

---

## Prompt 6 — Geossintéticos + testes

```
Implemente o dimensionamento com geossintéticos em
soloref/core/methods/geossintetico.py conforme a seção 3.5 do plano
(equilíbrio-limite / tieback estilo FHWA-AASHTO):
- σv(z)=γz+q; σh=Ka·σv; Tmax=σh·Sv; Tadm=Tult/(RFcr·RFid·RFd·FS);
  Sv ≤ Tadm/(Ka·σv·FS); L=La+Le com La=(H−z)·tan(45−φ/2) e
  Le≥Tmax·FS/(2·σv·Ci·tanφ).
- Se faltarem campos no modelo (Tult, RFs, Ci, FS-alvo, Sv), adicione uma
  dataclass Reforco em core/models.py e uma aba correspondente em
  entrada_dados.py (siga a seção 5.2 do GUIA_DESENVOLVEDOR).
- Resultado com nº de camadas, espaçamentos e comprimentos em extras.

Crie tests/test_geossintetico.py com:
- GEO-01: ΣTmax das camadas ≈ Ea de Rankine (consistência interna).
- Monotonicidade: ↑q ⇒ ↑nº de camadas; ↑Tult ⇒ ↓nº de camadas.
- 1 exemplo resolvido FHWA/livro transcrito, se disponível.

Rode `pytest -v` e `python validar.py`.
```

---

## Prompt 7 — Fechamento e documentação

```
Feche o ciclo:
1. Rode `python validar.py` e confirme 100% dos casos de literatura verdes no
   RELATORIO_VALIDACAO.md.
2. Crie tests/casos_referencia_original.csv VAZIO (só cabeçalho, mesmo schema
   do dataset) e faça validar.py carregá-lo se existir, reportando numa seção
   separada "Conferência com o programa original".
3. Atualize README.md (status: métodos implementados + como rodar a validação),
   GUIA_DESENVOLVEDOR.md (nova pasta tests/, validar.py, dataset) e o
   CHECKLIST_TESTES.md com os itens de cálculo.
4. Rode `pytest tests/ -v` inteiro e cole o resumo final.
```

---

## Dicas de uso no Claude Code

- Deixe o Claude Code **rodar os testes ele mesmo** a cada etapa — o loop
  editar→`pytest`→corrigir é onde ele é mais forte que este ambiente.
- Se ele pedir um valor de benchmark de livro (Bishop/Geossintético), me chame
  aqui: eu confirmo o número e a citação antes de virar teste.
- Commit por prompt (um commit por etapa) facilita reverter se algo sair torto.
