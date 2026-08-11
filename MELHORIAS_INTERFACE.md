# Melhorias de interface — SoloRef

Análise crítica da interface e backlog de melhorias. Base: leitura das escolhas
de estilo no código (as cores são hardcoded) e das telas vistas no redesenho.
Uma segunda passada com screenshot do app aberto pode afinar a parte visual.

## Visual

- **Fundo do esquema em cinza sólido (`#c8c8c8`)** — pesado e datado; destoa do
  restante claro. Trocar por branco / cinza-claríssimo.
- **Nada se adapta ao modo escuro.** Cores fixas em hex (esquema, selos, avisos).
  Só os cartões usam `palette(base)/palette(mid)` (acompanham o tema). Em dark
  mode do Windows, o miolo parece remendado e alguns textos perdem contraste.

## Cores

- Paleta coerente (tons Material 700/800) e **uso semântico correto**: verde
  ADEQUADO (`#2e7d32`), vermelho INSUFICIENTE (`#c62828`), âmbar para avisos.
- **Cores demais no esquema** — azul, roxo, verde, laranja e rosa para elementos
  da cunha (`#1565c0`, `#6a1b9a`, `#2e7d32`, `#e65100`, `#ad1457`). Reduzir para
  2–3 (estrutura / superfície de ruptura / cargas).
- **Dois azuis conflitantes**: navy `#0b3d91` (destaque de aba) vs. `#1565c0`/
  `#0066aa` (esquema). Unificar num azul de marca.
- **Sinalização só por cor** (aba relevante azul vs. cinza) — frágil para
  daltônicos. Reforçar com negrito ou um ponto/ícone.

## Intuitividade e usabilidade

- **"Calcular" × "Registrar no quadro"** — como trocar de método já recalcula, o
  "Calcular" é redundante; unificar num único "Adicionar ao comparativo".
- **Estabilidade externa fora do grupo de abas** — comportamento diferente na
  mesma barra; virar a 6ª aba ou separar visualmente como "verificação global".
- **Aba "Face (reservado)"** — coleta dados que nada usa; esconder ou marcar mais
  forte.
- **Falta um ponto de partida didático** — carregar casos de exemplo com 1 clique.

## Botões / funcionalidades que fariam falta (ordem de utilidade)

1. **Gerar relatório/memorial (PDF)** — o botão "Rela" ainda é placeholder. É a
   funcionalidade mais sentida.
2. **Exportar** — esquema como imagem (PNG/SVG) e Quadro Resumo como CSV.
3. **Carregar caso de exemplo** — menu "Exemplos" com 2–3 projetos didáticos.
4. **Zoom/ajuste no esquema** + legenda de cores/símbolos.
5. **Tooltips de ajuda nos parâmetros** (um "?" com definição e faixa típica).
6. **Arquivos recentes** no menu Sistema.
7. **Interpretação mais forte** — mostrar FS-alvo ao lado do FS; no comparativo,
   destacar o método mais crítico/conservador.

## Síntese

Arquitetura visual e fluxo bons e coerentes. O que falta é **polimento** (fundo
do esquema, adaptação a tema, menos cores no desenho) e um punhado de **botões de
saída** — relatório PDF, exportar imagem/CSV e casos de exemplo — que transformam
uma boa ferramenta de análise numa ferramenta didática completa.

**Prioridade sugerida:** (1) relatório/memorial em PDF, (2) casos de exemplo,
(3) polimento visual (fundo do esquema + tema escuro).
