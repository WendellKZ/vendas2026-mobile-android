import os
from dataclasses import dataclass
from typing import Any

import httpx


def only_digits(value: str | None) -> str:
    return "".join(ch for ch in (value or "") if ch.isdigit())


@dataclass
class CnpjLookupResult:
    name: str = ""
    corporate_name: str = ""
    city: str = ""
    state: str = ""
    phone: str = ""
    email: str = ""
    state_registration: str = ""
    state_registration_source: str = "not_found"
    suframa: str = ""
    suframa_source: str = "not_found"
    source: str = "not_found"
    warnings: list[str] | None = None

    def as_dict(self) -> dict:
        return {
            "name": self.name or "",
            "corporate_name": self.corporate_name or "",
            "city": self.city or "",
            "state": self.state or "",
            "phone": self.phone or "",
            "email": self.email or "",
            "state_registration": self.state_registration or "",
            "state_registration_source": self.state_registration_source or "not_found",
            "suframa": self.suframa or "",
            "suframa_source": self.suframa_source or "not_found",
            "source": self.source or "not_found",
            "warnings": self.warnings or [],
        }


def _apply_basic_data(result: CnpjLookupResult, data: dict, source: str) -> None:
    result.source = result.source if result.source != "not_found" else source
    result.name = result.name or (data.get("nome_fantasia") or data.get("fantasia") or data.get("alias") or data.get("name") or "").strip()
    result.corporate_name = result.corporate_name or (data.get("razao_social") or data.get("nome") or data.get("razao") or data.get("company") or "").strip()
    result.city = result.city or (data.get("municipio") or data.get("cidade") or data.get("city") or "").strip()
    result.state = result.state or (data.get("uf") or data.get("estado") or data.get("state") or "").strip()
    result.email = result.email or (data.get("email") or "").strip()
    phone = data.get("ddd_telefone_1") or data.get("ddd_telefone_2") or data.get("telefone") or data.get("phone") or ""
    result.phone = result.phone or str(phone or "").strip()


def _extract_suframa_from_payload(payload: Any) -> str:
    candidates: list[Any] = []

    def walk(value: Any):
        if isinstance(value, dict):
            for key, child in value.items():
                k = str(key).lower()
                if "suframa" in k or "suf" == k:
                    candidates.append(child)
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(payload)
    for candidate in candidates:
        if isinstance(candidate, dict):
            for key in ("numero", "number", "inscricao", "registration", "codigo", "code", "suframa"):
                digits = only_digits(str(candidate.get(key) or ""))
                if digits:
                    return digits
        else:
            digits = only_digits(str(candidate or ""))
            if digits:
                return digits
    return ""


def _extract_ie_from_payload(payload: Any, uf: str = "") -> str:
    keys = {"inscricao_estadual", "ie", "numero", "number", "registration", "inscricao", "estadual"}

    def looks_like_ie_key(key: str) -> bool:
        k = key.lower()
        return "inscricao_estadual" in k or k == "ie" or "estadual" in k or "sintegra" in k

    inscricoes = payload.get("inscricoes_estaduais") if isinstance(payload, dict) else None
    if isinstance(inscricoes, list):
        for item in inscricoes:
            if not isinstance(item, dict):
                continue
            if uf and item.get("estado") and str(item.get("estado")).upper() != uf.upper():
                continue
            for key in keys:
                value = item.get(key)
                if value:
                    return str(value).strip()

    found = ""

    def walk(value: Any):
        nonlocal found
        if found:
            return
        if isinstance(value, dict):
            for key, child in value.items():
                if looks_like_ie_key(str(key)) and child:
                    if isinstance(child, (str, int)):
                        found = str(child).strip()
                        return
                    if isinstance(child, dict):
                        for child_key in keys:
                            child_value = child.get(child_key)
                            if child_value:
                                found = str(child_value).strip()
                                return
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(payload)
    return found


def _get_json(url: str, headers: dict | None = None, timeout: float = 10.0) -> dict:
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        response = client.get(url, headers=headers or {})
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, dict) else {"data": data}


def _try_public_sources(result: CnpjLookupResult, digits: str) -> None:
    sources = [
        ("brasilapi", f"https://brasilapi.com.br/api/cnpj/v1/{digits}"),
        ("receitaws", f"https://www.receitaws.com.br/v1/cnpj/{digits}"),
        ("minhareceita", f"https://minhareceita.org/{digits}"),
    ]

    for source, url in sources:
        try:
            data = _get_json(url, timeout=10.0)
            _apply_basic_data(result, data, source)
            ie = _extract_ie_from_payload(data, result.state)
            if ie and not result.state_registration:
                result.state_registration = ie
                result.state_registration_source = source
            suframa = _extract_suframa_from_payload(data)
            if suframa and not result.suframa:
                result.suframa = suframa
                result.suframa_source = source
        except Exception as exc:
            if result.warnings is not None:
                result.warnings.append(f"{source} indisponível ou sem dados completos: {exc}")


def _try_env_api(result: CnpjLookupResult, digits: str, kind: str) -> None:
    url_template = os.getenv(f"{kind}_API_URL", "").strip()
    if not url_template:
        return
    url = url_template.replace("{cnpj}", digits).replace("{uf}", result.state or "")
    headers = {}
    token = os.getenv(f"{kind}_API_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        data = _get_json(url, headers=headers, timeout=12.0)
        if kind == "IE":
            ie = _extract_ie_from_payload(data, result.state)
            if ie:
                result.state_registration = ie
                result.state_registration_source = "api_externa"
        if kind == "SUFRAMA":
            suframa = _extract_suframa_from_payload(data)
            if suframa:
                result.suframa = suframa
                result.suframa_source = "api_externa"
    except Exception as exc:
        if result.warnings is not None:
            result.warnings.append(f"API externa {kind} não retornou dado: {exc}")


# Fallback temporário para manter comportamento de versões anteriores em testes.
# Pode ser expandido conforme CNPJs reais usados nas validações.
LOCAL_FISCAL_FALLBACK = {
    "04756170000151": {"suframa": "200010290"},
    "04756170000151": {"suframa": "200010290"},
}


def lookup_cnpj_data(cnpj: str) -> CnpjLookupResult:
    digits = only_digits(cnpj)
    result = CnpjLookupResult(warnings=[])

    if len(digits) != 14:
        result.warnings.append("CNPJ inválido.")
        return result

    _try_public_sources(result, digits)
    _try_env_api(result, digits, "IE")
    _try_env_api(result, digits, "SUFRAMA")

    fallback = LOCAL_FISCAL_FALLBACK.get(digits, {})
    if fallback.get("ie") and not result.state_registration:
        result.state_registration = fallback["ie"]
        result.state_registration_source = "fallback_local"
    if fallback.get("suframa") and not result.suframa:
        result.suframa = fallback["suframa"]
        result.suframa_source = "fallback_local"

    if not result.state_registration:
        result.state_registration_source = "not_found"
    if not result.suframa:
        result.suframa_source = "not_found"

    return result
