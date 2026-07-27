# SoloRef (reimplementação)

Reimplementação em Python/PySide6 do programa **SoloRef — Dimensionamento de Estruturas de Solo Reforçado**
(originalmente escrito para Windows 16/32 bits). Parte do projeto de Iniciação Científica de
**Yves Gabriel Queiroz de Sousa**, orientado pelo Prof. **José Antonio Schiavon**.

## Objetivo

- Recriar a funcionalidade do programa original em stack moderna e multiplataforma.
- Incorporar os métodos clássicos de cunha plana: **Coulomb**, **Rankine** e **Dois Blocos**.
- Adicionar o método simplificado de **Bishop** (cunha circular).
- Simular soluções de reforço com **geossintéticos**.

## Status

Os 5 métodos de cálculo estão implementados e conectados à interface (UI ↔ `core/`):
**Coulomb**, **Rankine**, **Dois Blocos**, **Bishop simplificado** e **Reforço com
geossintéticos**. Todos batem com os casos de literatura/limite do dataset de
validação — 100% verde em `RELATORIO_VALIDACAO.md` (ver seção
[Testes e validação](#testes-e-validação)). Pendências conhecidas: 2 benchmarks de
exemplos resolvidos de livro (Das/Craig e FHWA) ainda não transcritos, e Bishop/
Geossintético ainda não têm linha própria no Quadro Resumo da UI.

## Como executar

```bash
pip install -r requirements.txt
python main.py
```

## Testes e validação

Duas camadas complementares (ver `PLANO_IMPLEMENTACAO.md` para o detalhe de cada
fórmula e das decisões de modelagem):

```bash
pytest tests/ -v      # suíte pytest — um arquivo de teste por método + smoke tests do core
python validar.py     # runner de validação — gera RELATORIO_VALIDACAO.md e logs/validacao_*.log
```

`validar.py` percorre `tests/casos_literatura.py` (fórmulas fechadas e casos-limite
auto-verificáveis, a fonte de verdade principal), roda cada método, calcula o erro
relativo e sai com código ≠ 0 se algo não bater dentro da tolerância. Também carrega
`tests/casos_referencia_original.csv` se ele tiver linhas — uma conferência opcional
e secundária com o programa original (vazio por padrão; não afeta o código de saída).

## Estrutura

```
soloref/
├── core/         # modelos + cálculos (puro Python, sem Qt)
│   ├── models.py
│   ├── methods/  # um arquivo por método (extensível)
│   └── persistence.py
└── ui/           # interface PySide6
    ├── main_window.py
    └── dialogs/
tests/
├── casos_literatura.py            # dataset de casos de validação (fonte de verdade)
├── casos_referencia_original.csv  # conferência opcional com o programa original
└── test_*.py                      # suíte pytest, um arquivo por método
validar.py          # runner de validação (gera RELATORIO_VALIDACAO.md)
```

A camada `core/` é independente da UI — pode ser usada em scripts, testes e futuras
interfaces web sem reescrever os cálculos.
