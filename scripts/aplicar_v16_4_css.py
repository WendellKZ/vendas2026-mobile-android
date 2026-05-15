from pathlib import Path

root = Path(__file__).resolve().parents[1]
style = root / "static" / "css" / "style.css"
patch = root / "static" / "css" / "v16_4_patch.css"

if not style.exists():
    raise SystemExit("Arquivo static/css/style.css não encontrado.")

css = style.read_text(encoding="utf-8")
patch_css = patch.read_text(encoding="utf-8")

marker = "/* V16.4 - Correção ícones do menu + agente de pedidos */"
if marker not in css:
    style.write_text(css + "\n\n" + patch_css, encoding="utf-8")
    print("CSS V16.4 aplicado em static/css/style.css")
else:
    print("CSS V16.4 já estava aplicado")

print("Substitua também templates/base.html pelo arquivo do ZIP, se ainda não tiver feito.")
