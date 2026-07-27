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

Protótipo da interface (sem cálculos ainda).

## Como executar

```bash
pip install -r requirements.txt
python main.py
```

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
```

A camada `core/` é independente da UI — pode ser usada em scripts, testes e futuras
interfaces web sem reescrever os cálculos.
