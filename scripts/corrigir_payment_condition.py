from pathlib import Path
import re
import shutil
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "app" / "models" / "payment_condition.py"

if not TARGET.exists():
    raise SystemExit(f"Arquivo não encontrado: {TARGET}")

backup = TARGET.with_suffix(f".py.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
shutil.copy2(TARGET, backup)

text = TARGET.read_text(encoding="utf-8")

# Remove/comenta especificamente o relacionamento que está quebrando o SQLAlchemy:
# PaymentCondition.orders -> Order sem ForeignKey correspondente.
patterns = [
    r'^\s*orders\s*=\s*relationship\(\s*["\']Order["\'].*?\)\s*$',
    r'^\s*orders:\s*Mapped\[.*?\]\s*=\s*relationship\(\s*["\']Order["\'].*?\)\s*$',
]

new_text = text
for pattern in patterns:
    new_text = re.sub(
        pattern,
        "    # orders = relationship('Order', back_populates='payment_condition')  # Removido: não há FK em orders",
        new_text,
        flags=re.MULTILINE,
    )

# Se ainda existir algum relationship para Order em bloco multilinha, remove de forma mais ampla.
new_text = re.sub(
    r'\n\s*orders\s*=\s*relationship\(\s*["\']Order["\'][\s\S]*?\)\s*\n',
    "\n    # orders removido: relacionamento sem ForeignKey causava erro no mapper do SQLAlchemy\n",
    new_text,
    flags=re.MULTILINE,
)

TARGET.write_text(new_text, encoding="utf-8")

print("Correção aplicada com sucesso.")
print(f"Backup criado em: {backup}")
print("Agora rode: docker compose down && docker compose up -d --build")
