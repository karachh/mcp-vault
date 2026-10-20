import json
import unicodedata
from pathlib import Path

from mcp.server.mcpserver import MCPServer

VAULT = Path.home() / "Documentos/Vaults/1-Tributech"
CATALOGO = VAULT / "20-Banco/_gerado"
DIFERENCAS = CATALOGO / "_diferencas"

# Banco usado para gerar o catálogo. Troque aqui se a referência mudar.
REFERENCIA = "geon_pr_novaesperanca"

mcp = MCPServer("vault-trabalho")


def normalizar(texto):
    """'Nova Esperança' -> 'novaesperanca': minúsculas, sem acento e sem espaço."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sem_acento.lower().replace(" ", "").replace("-", "").replace("_", "")


def achar_tabela(tabela):
    """Procura a nota da tabela no catálogo. Devolve (nota, None) ou (None, mensagem de erro)."""
    nome = tabela.lower()
    achados = [
        nota for nota in CATALOGO.rglob("*.md")
        if nota.stem.lower() == nome or nota.stem.lower().endswith("." + nome)
    ]
    if not achados:
        return None, f"Nenhuma tabela '{tabela}' no catálogo de referência ({REFERENCIA})."
    if len(achados) > 1:
        opcoes = ", ".join(nota.stem for nota in achados)
        return None, f"Existe mais de uma tabela com esse nome: {opcoes}. Informe o schema."
    return achados[0], None


def achar_diferencas(municipio):
    """Procura o JSON de diferenças do município. Aceita 'Astorga' ou 'geon_pr_astorga'."""
    alvo = normalizar(municipio)
    for arquivo in DIFERENCAS.glob("*.json"):
        if normalizar(arquivo.stem).endswith(alvo):
            return json.loads(arquivo.read_text(encoding="utf-8"))
    return None


def descrever_diferencas(chave, dif):
    """Monta o texto com as diferenças de uma tabela num município."""
    if chave in dif["tabelas_ausentes"]:
        return "**Esta tabela NÃO existe neste município.**"

    cols = dif["colunas"].get(chave)
    if not cols:
        return "Nenhuma diferença de estrutura em relação à referência."

    linhas = []
    for coluna in cols["colunas_ausentes"]:
        linhas.append(f"- Coluna `{coluna}` não existe neste município.")
    for item in cols["colunas_extras"]:
        linhas.append(f"- Coluna `{item['coluna']}` ({item['tipo']}) existe só neste município.")
    for item in cols["tipo_diferente"]:
        linhas.append(
            f"- Coluna `{item['coluna']}` tem tipo `{item['municipio']}` aqui, "
            f"e `{item['referencia']}` na referência."
        )
    return "\n".join(linhas)


@mcp.tool()
def estrutura_tabela(tabela: str, municipio: str | None = None) -> str:
    """Retorna as colunas, tipos e descrições de uma tabela do banco.

    tabela: 'schema.tabela' (ex: 'imobiliario.edificacao') ou só o nome da tabela.
    municipio: opcional (ex: 'Astorga'). Se informado, mostra também as diferenças
    de estrutura desse município em relação ao banco de referência.

    Cada município tem seu próprio banco, e as estruturas podem variar. Sempre
    repasse ao usuário o aviso sobre qual estrutura está sendo mostrada."""
    nota, erro = achar_tabela(tabela)
    if erro:
        return erro

    chave = nota.stem
    estrutura = nota.read_text(encoding="utf-8")

    if not municipio:
        aviso = (
            f"AVISO: estrutura do banco de referência ({REFERENCIA}). "
            "Outros municípios podem ter diferenças. Informe o município para vê-las."
        )
        return f"{aviso}\n\n{estrutura}"

    dif = achar_diferencas(municipio)
    if dif is None:
        aviso = (
            f"AVISO: não há comparação gerada para '{municipio}'. "
            f"Mostrando a estrutura do banco de referência ({REFERENCIA}), "
            "que pode não corresponder a esse município."
        )
        return f"{aviso}\n\n{estrutura}"

    aviso = f"AVISO: estrutura do banco de referência ({REFERENCIA})."
    return (
        f"{aviso}\n\n"
        f"## Diferenças em {dif['banco']}\n{descrever_diferencas(chave, dif)}\n\n"
        f"## Estrutura de referência\n{estrutura}"
    )


if __name__ == "__main__":
    mcp.run()
