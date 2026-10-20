from pathlib import Path

from mcp.server.mcpserver import MCPServer

VAULT = Path.home() / "Documentos/Vaults/1-Tributech"
CATALOGO = VAULT / "20-Banco/_gerado"

mcp = MCPServer("vault-trabalho")


@mcp.tool()
def estrutura_tabela(tabela: str) -> str:
    """Retorna as colunas, tipos e descrições de uma tabela do banco.
    Aceita 'schema.tabela' (ex: 'imobiliario.edificacao') ou só o nome da tabela."""
    nome = tabela.lower()
    achados = [
        nota for nota in CATALOGO.rglob("*.md")
        if nota.stem.lower() == nome or nota.stem.lower().endswith("." + nome)
    ]
    if not achados:
        return f"Nenhuma tabela '{tabela}' no catálogo."
    if len(achados) > 1:
        opcoes = ", ".join(nota.stem for nota in achados)
        return f"Existe mais de uma tabela com esse nome: {opcoes}. Informe o schema."
    return achados[0].read_text(encoding="utf-8")


if __name__ == "__main__":
    mcp.run()
