"""
Módulo B: Cliente da Aplicação SOAP (Padrão XML baseado em WSDL)
Consome o Web Service SOAP público DataAccess NumberConversion.
Link Direto do WSDL: https://www.dataaccess.com/webservicesserver/NumberConversion.wso?WSDL
Documentação Oficial: https://www.dataaccess.com/webservicesserver/NumberConversion.wso
"""

from decimal import Decimal, ROUND_HALF_UP
import time
from typing import Any, Dict, Optional, Tuple
import xml.dom.minidom
import xml.etree.ElementTree as ET
import requests

try:
    from zeep import Client, Settings
    from zeep.plugins import HistoryPlugin
    from zeep.transports import Transport
    from lxml import etree

    ZEEP_AVAILABLE = True
except ImportError:
    ZEEP_AVAILABLE = False


SOAP_WSDL_URL = "https://www.dataaccess.com/webservicesserver/NumberConversion.wso?WSDL"
SOAP_ENDPOINT_URL = "https://www.dataaccess.com/webservicesserver/NumberConversion.wso"
SOAP_DOCS_URL = "https://www.dataaccess.com/webservicesserver/NumberConversion.wso"
SOAP_NAMESPACE = "http://www.dataaccess.com/webservicesserver/"

_CACHED_ZEEP_CLIENT: Optional[ Tuple[Any, Any] ] = None


def _get_zeep_client() -> Tuple[Any, Any]:
    """Inicializa e mantém em cache o cliente WSDL do Zeep para evitar re-download do WSDL a cada chamada."""
    global _CACHED_ZEEP_CLIENT
    if _CACHED_ZEEP_CLIENT is None:
        history = HistoryPlugin()
        settings = Settings(strict=False, xml_huge_tree=True)
        transport = Transport(timeout=5, operation_timeout=5)
        client = Client(
            wsdl=SOAP_WSDL_URL,
            settings=settings,
            transport=transport,
            plugins=[history],
        )
        _CACHED_ZEEP_CLIENT = (client, history)
    return _CACHED_ZEEP_CLIENT


def _pretty_format_xml(xml_string: str) -> str:
    """Formata uma string XML com indentação legível para exibição técnica e no README."""
    try:
        parsed = xml.dom.minidom.parseString(xml_string.encode("utf-8"))
        lines = [
            line
            for line in parsed.toprettyxml(indent="  ").splitlines()
            if line.strip()
        ]
        return "\n".join(lines)
    except Exception:
        return xml_string.strip()


def convert_amount_to_dollars_soap(amount: float) -> Dict[str, Any]:
    """
    Consome a operação SOAP 'NumberToDollars' definida no WSDL público.
    Converte um valor numérico (ex: 34.97) para seu cheque oficial em extenso em inglês
    (ex: 'thirty four dollars and ninety seven cents'), capturando o bloco XML real.
    """
    decimal_value = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if ZEEP_AVAILABLE:
        try:
            client, history = _get_zeep_client()
            start_time = time.perf_counter()
            result_text = client.service.NumberToDollars(dNum=decimal_value)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

            sent_envelope = ""
            received_envelope = ""
            payload_bytes = 0

            if history.last_sent:
                sent_bytes = etree.tostring(
                    history.last_sent["envelope"], encoding="utf-8", pretty_print=True
                )
                sent_envelope = sent_bytes.decode("utf-8")

            if history.last_received:
                recv_bytes = etree.tostring(
                    history.last_received["envelope"], encoding="utf-8", pretty_print=True
                )
                payload_bytes = len(recv_bytes)
                received_envelope = recv_bytes.decode("utf-8")

            return {
                "protocol": "SOAP 1.1 (WSDL / Zeep)",
                "format": "XML",
                "wsdl_url": SOAP_WSDL_URL,
                "documentation_url": SOAP_DOCS_URL,
                "operation": "NumberToDollars",
                "input_value": float(decimal_value),
                "result_text": str(result_text).strip(),
                "latency_ms": elapsed_ms,
                "payload_bytes": payload_bytes,
                "raw_xml_request": sent_envelope.strip(),
                "raw_xml_response": received_envelope.strip(),
            }
        except Exception:
            pass

    # Envelope SOAP 1.1 baseado no contrato do WSDL NumberConversion.wso?WSDL
    soap_request_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:web="{SOAP_NAMESPACE}">
  <soap:Header/>
  <soap:Body>
    <web:NumberToDollars>
      <web:dNum>{decimal_value}</web:dNum>
    </web:NumberToDollars>
  </soap:Body>
</soap:Envelope>"""

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": '""',
        "User-Agent": "IFNMG-SistemasDistribuidos-SOAPClient/1.0",
    }

    start_time = time.perf_counter()
    response = requests.post(
        SOAP_ENDPOINT_URL,
        data=soap_request_xml.encode("utf-8"),
        headers=headers,
        timeout=8,
    )
    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
    response.raise_for_status()

    raw_response_xml = response.text
    payload_bytes = len(response.content)

    root = ET.fromstring(raw_response_xml)
    result_text = ""
    for elem in root.iter():
        if elem.tag.endswith("NumberToDollarsResult") and elem.text:
            result_text = elem.text.strip()
            break

    return {
        "protocol": "SOAP 1.1 (WSDL)",
        "format": "XML",
        "wsdl_url": SOAP_WSDL_URL,
        "documentation_url": SOAP_DOCS_URL,
        "operation": "NumberToDollars",
        "input_value": float(decimal_value),
        "result_text": result_text,
        "latency_ms": elapsed_ms,
        "payload_bytes": payload_bytes,
        "raw_xml_request": _pretty_format_xml(soap_request_xml),
        "raw_xml_response": _pretty_format_xml(raw_response_xml),
    }


def convert_number_to_words_soap(number: int) -> Dict[str, Any]:
    """
    Consome a operação SOAP 'NumberToWords' definida no WSDL público.
    Converte um número inteiro (ex: orçamento da rodada) em palavras por extenso via XML.
    """
    clean_int = max(0, int(number))

    soap_request_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:web="{SOAP_NAMESPACE}">
  <soap:Header/>
  <soap:Body>
    <web:NumberToWords>
      <web:ubiNum>{clean_int}</web:ubiNum>
    </web:NumberToWords>
  </soap:Body>
</soap:Envelope>"""

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": '""',
        "User-Agent": "IFNMG-SistemasDistribuidos-SOAPClient/1.0",
    }

    start_time = time.perf_counter()
    response = requests.post(
        SOAP_ENDPOINT_URL,
        data=soap_request_xml.encode("utf-8"),
        headers=headers,
        timeout=8,
    )
    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
    response.raise_for_status()

    raw_response_xml = response.text
    payload_bytes = len(response.content)

    root = ET.fromstring(raw_response_xml)
    result_text = ""
    for elem in root.iter():
        if elem.tag.endswith("NumberToWordsResult") and elem.text:
            result_text = elem.text.strip()
            break

    return {
        "protocol": "SOAP 1.1 (WSDL)",
        "format": "XML",
        "wsdl_url": SOAP_WSDL_URL,
        "documentation_url": SOAP_DOCS_URL,
        "operation": "NumberToWords",
        "input_value": clean_int,
        "result_text": result_text,
        "latency_ms": elapsed_ms,
        "payload_bytes": payload_bytes,
        "raw_xml_request": _pretty_format_xml(soap_request_xml),
        "raw_xml_response": _pretty_format_xml(raw_response_xml),
    }


def certify_knapsack_proximity_soap(proximity_percent: float) -> Dict[str, Any]:
    """
    Consome o Web Service SOAP (operação 'NumberToWords' do WSDL) para certificar
    por extenso o percentual de proximidade do jogador em relação à solução ótima
    do algoritmo da Mochila 0/1 (Ex: 85.0% -> 'eighty five percent').
    """
    rounded_pct = max(0, min(100, int(round(proximity_percent))))
    soap_res = convert_number_to_words_soap(rounded_pct)
    words = soap_res["result_text"]
    return {
        **soap_res,
        "proximity_numeric": round(float(proximity_percent), 1),
        "proximity_rounded": rounded_pct,
        "proximity_in_words": f"{words} percent",
        "certification_text": (
            f"{round(float(proximity_percent), 1)}% de proximidade da solução ideal "
            f"(SOAP XML: '{words} percent')"
        ),
    }



if __name__ == "__main__":
    print("=" * 70)
    print("TESTE ISOLADO - APLICAÇÃO SOAP (DataAccess WSDL - XML)")
    print("=" * 70)
    soap_res = convert_amount_to_dollars_soap(34.97)
    print(f"Arquivo WSDL    : {soap_res['wsdl_url']}")
    print(f"Operação SOAP   : {soap_res['operation']}({soap_res['input_value']})")
    print(f"Resultado SOAP  : {soap_res['result_text']}")
    print(f"Latência (ms)   : {soap_res['latency_ms']} ms")
    print(f"Tamanho Payload : {soap_res['payload_bytes']} bytes")
    print("\nExemplo Real do Bloco XML Recebido (SOAP Response):")
    print(soap_res["raw_xml_response"])
