"""Runner de validação — o "teste completo do programa".

Percorre todos os casos de `tests/casos_literatura.py`, monta o `Projeto`
de cada um, roda o método correspondente, compara com o valor esperado
(erro relativo, em %) e produz:

  - log estruturado em `logs/validacao_<timestamp>.log`;
  - `RELATORIO_VALIDACAO.md` legível na raiz do projeto.

Uso:
    python validar.py

Sai com código 0 se todos os casos do dataset de literatura passarem, 1
caso contrário (inclusive quando um cálculo lança exceção — isso vira um
caso "ERRO", nunca derruba o runner).

Conferência opcional com o programa original (PLANO_IMPLEMENTACAO.md §5):
se `tests/casos_referencia_original.csv` tiver linhas além do cabeçalho,
elas são carregadas, avaliadas com o mesmo mecanismo, e relatadas numa
seção à parte do `RELATORIO_VALIDACAO.md` — sem afetar o código de saída
nem a "taxa de aprovação geral", que continuam refletindo só o dataset de
literatura (fonte de verdade principal).
"""
from __future__ import annotations

import csv
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from tests.casos_literatura import CASOS, METODOS, CasoLiteratura, monta_projeto

RAIZ = Path(__file__).resolve().parent
LOGS_DIR = RAIZ / "logs"
RELATORIO_PATH = RAIZ / "RELATORIO_VALIDACAO.md"
CASOS_ORIGINAL_PATH = RAIZ / "tests" / "casos_referencia_original.csv"

_STATUS_MARCA = {"PASS": "✔", "FAIL": "✗", "ERRO": "⚠"}


@dataclass
class ResultadoCaso:
    caso_id: str
    metodo: str
    fonte: str
    campo: str
    esperado: float
    obtido: float | None
    erro_pct: float | None
    status: str  # "PASS" | "FAIL" | "ERRO"
    detalhe: str = ""


def _extrai_campo(resultado, campo: str) -> float | None:
    """Busca `campo` primeiro nos atributos de `Resultado`, senão em `extras`."""
    if hasattr(resultado, campo):
        return getattr(resultado, campo)
    return resultado.extras.get(campo)


def _erro_relativo(obtido: float, esperado: float) -> float:
    if esperado == 0:
        return abs(obtido - esperado) * 100.0
    return abs(obtido - esperado) / abs(esperado) * 100.0


def carregar_casos_referencia_original() -> list[CasoLiteratura]:
    """Lê `tests/casos_referencia_original.csv` se ele existir e tiver
    linhas de dados. Mesmo schema de `CasoLiteratura`, mas achatado em CSV
    (`entradas`/`esperado` viram colunas JSON). Arquivo ausente ou vazio
    (só cabeçalho) devolve lista vazia — não é erro, é o padrão.
    """
    if not CASOS_ORIGINAL_PATH.exists():
        return []
    casos: list[CasoLiteratura] = []
    with CASOS_ORIGINAL_PATH.open(newline="", encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            casos.append(
                CasoLiteratura(
                    id=linha["id"],
                    metodo=linha["metodo"],
                    fonte=linha["fonte"],
                    entradas=json.loads(linha["entradas_json"]),
                    esperado=json.loads(linha["esperado_json"]),
                    tolerancia=float(linha["tolerancia"]),
                )
            )
    return casos


def avaliar_caso(caso, logger: logging.Logger) -> list[ResultadoCaso]:
    """Roda um caso e devolve uma linha de resultado por campo esperado.

    Nunca propaga exceção: um erro no cálculo vira status "ERRO" para
    todos os campos do caso, registrado no log com stack trace.
    """
    linhas: list[ResultadoCaso] = []
    logger.info("Caso %s (%s) — fonte: %s", caso.id, caso.metodo, caso.fonte)

    try:
        projeto = monta_projeto(caso.entradas)
        metodo_cls = METODOS[caso.metodo]
        resultado = metodo_cls().calcular(projeto)
    except Exception as exc:  # método ainda não implementado ou instável
        logger.exception("Falha ao calcular caso %s", caso.id)
        for campo, esperado in caso.esperado.items():
            linhas.append(
                ResultadoCaso(
                    caso_id=caso.id,
                    metodo=caso.metodo,
                    fonte=caso.fonte,
                    campo=campo,
                    esperado=esperado,
                    obtido=None,
                    erro_pct=None,
                    status="ERRO",
                    detalhe=f"{type(exc).__name__}: {exc}",
                )
            )
        return linhas

    for campo, esperado in caso.esperado.items():
        obtido = _extrai_campo(resultado, campo)
        if obtido is None:
            status, erro_pct, detalhe = (
                "FAIL",
                None,
                "campo ausente em Resultado/extras (método não implementado?)",
            )
        else:
            erro_pct = _erro_relativo(obtido, esperado)
            status = "PASS" if erro_pct <= caso.tolerancia else "FAIL"
            detalhe = ""
        logger.info(
            "  campo=%s esperado=%s obtido=%s erro=%s status=%s",
            campo,
            esperado,
            obtido,
            f"{erro_pct:.4f}%" if erro_pct is not None else "-",
            status,
        )
        linhas.append(
            ResultadoCaso(
                caso_id=caso.id,
                metodo=caso.metodo,
                fonte=caso.fonte,
                campo=campo,
                esperado=esperado,
                obtido=obtido,
                erro_pct=erro_pct,
                status=status,
                detalhe=detalhe,
            )
        )
    return linhas


def configurar_logger() -> tuple[logging.Logger, Path]:
    LOGS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    caminho_log = LOGS_DIR / f"validacao_{timestamp}.log"

    logger = logging.getLogger("soloref.validacao")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    logger.propagate = False

    arquivo = logging.FileHandler(caminho_log, encoding="utf-8")
    arquivo.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    )
    logger.addHandler(arquivo)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(console)

    return logger, caminho_log


def _tabela_resultados(linhas: list[ResultadoCaso]) -> list[str]:
    partes = [
        "| id | método | campo | esperado | obtido | erro (%) | status | detalhe |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for l in linhas:
        obtido_fmt = f"{l.obtido:.5g}" if l.obtido is not None else "—"
        erro_fmt = f"{l.erro_pct:.3f}" if l.erro_pct is not None else "—"
        marca = _STATUS_MARCA[l.status]
        partes.append(
            f"| {l.caso_id} | {l.metodo} | {l.campo} | {l.esperado} | "
            f"{obtido_fmt} | {erro_fmt} | {marca} {l.status} | {l.detalhe} |"
        )
    return partes


def gerar_relatorio(
    linhas: list[ResultadoCaso], caminho_log: Path,
    linhas_original: list[ResultadoCaso] | None = None,
) -> None:
    linhas_original = linhas_original or []
    total = len(linhas)
    aprovados = sum(1 for l in linhas if l.status == "PASS")
    taxa = (aprovados / total * 100.0) if total else 0.0

    piores: dict[str, ResultadoCaso] = {}
    for l in linhas:
        if l.erro_pct is None:
            continue
        atual = piores.get(l.metodo)
        if atual is None or l.erro_pct > atual.erro_pct:
            piores[l.metodo] = l

    fontes: dict[str, str] = {}
    for l in linhas:
        fontes.setdefault(l.caso_id, l.fonte)

    partes: list[str] = []
    partes.append("# Relatório de validação — SoloRef")
    partes.append("")
    partes.append(
        f"Gerado em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. "
        f"Log completo: `{caminho_log.relative_to(RAIZ)}`."
    )
    partes.append("")
    partes.append(f"**Taxa de aprovação geral: {aprovados}/{total} ({taxa:.1f}%)**")
    partes.append("")

    partes.append("## Resultados por caso")
    partes.append("")
    partes.extend(_tabela_resultados(linhas))
    partes.append("")

    partes.append("## Pior erro por método")
    partes.append("")
    partes.append("| método | pior caso | campo | erro (%) |")
    partes.append("|---|---|---|---|")
    if piores:
        for metodo in sorted(piores):
            l = piores[metodo]
            partes.append(f"| {metodo} | {l.caso_id} | {l.campo} | {l.erro_pct:.3f} |")
    else:
        partes.append("| — | — | — | nenhum caso produziu valor numérico comparável ainda |")
    partes.append("")

    partes.append("## Fonte de cada caso")
    partes.append("")
    partes.append("| id | fonte |")
    partes.append("|---|---|")
    for caso_id, fonte in fontes.items():
        partes.append(f"| {caso_id} | {fonte} |")
    partes.append("")

    partes.append("## Conferência com o programa original (opcional)")
    partes.append("")
    partes.append(
        "Ver PLANO_IMPLEMENTACAO.md §5. Alimentada sob demanda em "
        "`tests/casos_referencia_original.csv`; **não conta** para a taxa de "
        "aprovação geral nem para o código de saída deste script — é só uma "
        "conferência secundária."
    )
    partes.append("")
    if not linhas_original:
        partes.append(
            "Nenhum caso cadastrado ainda — `tests/casos_referencia_original.csv` "
            "está vazio (só o cabeçalho)."
        )
    else:
        aprovados_orig = sum(1 for l in linhas_original if l.status == "PASS")
        partes.append(
            f"**{aprovados_orig}/{len(linhas_original)} casos do programa original "
            "batem com a reimplementação.**"
        )
        partes.append("")
        partes.extend(_tabela_resultados(linhas_original))
    partes.append("")

    RELATORIO_PATH.write_text("\n".join(partes), encoding="utf-8")


def main() -> int:
    logger, caminho_log = configurar_logger()
    logger.info("Iniciando validação — %d casos no dataset", len(CASOS))

    linhas: list[ResultadoCaso] = []
    for caso in CASOS:
        linhas.extend(avaliar_caso(caso, logger))

    casos_original = carregar_casos_referencia_original()
    linhas_original: list[ResultadoCaso] = []
    if casos_original:
        logger.info(
            "Conferência com o programa original — %d casos em %s",
            len(casos_original), CASOS_ORIGINAL_PATH.relative_to(RAIZ),
        )
        for caso in casos_original:
            linhas_original.extend(avaliar_caso(caso, logger))
    else:
        logger.info(
            "Conferência com o programa original: nenhum caso cadastrado "
            "(tests/casos_referencia_original.csv vazio)."
        )

    gerar_relatorio(linhas, caminho_log, linhas_original)

    total = len(linhas)
    aprovados = sum(1 for l in linhas if l.status == "PASS")
    logger.info("Validação concluída: %d/%d campos aprovados", aprovados, total)
    print(
        f"\nValidação concluída: {aprovados}/{total} campos aprovados.\n"
        f"Relatório: {RELATORIO_PATH.name}\n"
        f"Log: {caminho_log.relative_to(RAIZ)}"
    )

    return 0 if aprovados == total else 1


if __name__ == "__main__":
    sys.exit(main())
