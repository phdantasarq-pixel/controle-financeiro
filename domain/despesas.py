from dataclasses import dataclass

@dataclass
class Despesa:
    descricao: str
    divida: float
    pago: float
    tipo: str           # fixo | variavel
    vencimento: str
    valor_mensal: float
