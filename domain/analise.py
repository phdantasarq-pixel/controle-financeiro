import pandas as pd
import plotly.graph_objects as go


# --- [H8.3] ANÁLISE DE PARETO ---

def calcular_pareto_categorias(df_lancamentos):
    """
    Calcula a representatividade de cada categoria de despesa (Gasto Bruto).
    """
    if df_lancamentos is None or df_lancamentos.empty:
        return None

    # Filtrar apenas despesas para identificar os 'vilões' reais
    df_despesas = df_lancamentos[df_lancamentos['tipo'] == "Despesa"].copy()

    if df_despesas.empty:
        return None

    # Agrupamento por categoria
    df_agrupado = df_despesas.groupby('categoria')['valor'].sum().reset_index()
    df_agrupado = df_agrupado.sort_values(by='valor', ascending=False)

    # Cálculos de Pareto
    total_geral = df_agrupado['valor'].sum()
    df_agrupado['percentual'] = (df_agrupado['valor'] / total_geral) * 100
    df_agrupado['acumulado'] = df_agrupado['percentual'].cumsum()

    return df_agrupado


def gerar_grafico_pareto(df_pareto):
    """
    Gera o gráfico de Pareto com barras para valores e linha para o acumulado.
    """
    if df_pareto is None or df_pareto.empty:
        return None

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_pareto['categoria'],
        y=df_pareto['valor'],
        name="Gasto Bruto (R$)",
        marker_color='#EF553B',
        hovertemplate="<b>%{x}</b><br>Total: R$ %{y:,.2f}<extra></extra>"
    ))

    fig.add_trace(go.Scatter(
        x=df_pareto['categoria'],
        y=df_pareto['acumulado'],
        name="% Acumulado",
        yaxis="y2",
        line=dict(color="#636EFA", width=4, shape='spline'),
        hovertemplate="Acumulado: %{y:.1f}%<extra></extra>"
    ))

    fig.update_layout(
        title="<b>Análise de Pareto: Vilões de Gastos (Regra 80/20)</b>",
        template="plotly_white",
        yaxis=dict(title="Gasto Bruto (R$)", side="left"),
        yaxis2=dict(
            title="Percentual Acumulado (%)",
            overlaying="y",
            side="right",
            range=[0, 110],
            showgrid=False
        ),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=80, b=20),
        height=500
    )

    fig.add_hline(
        y=80,
        line_dash="dash",
        line_color="grey",
        yref="y2",
        annotation_text="Ponto de Corte 80%",
        annotation_position="bottom right"
    )

    return fig


# --- [H6.1] DASHBOARD DE PERFORMANCE (PAGO VS PENDENTE) ---

def calcular_performance_pagamentos(df_lancamentos):
    """
    Agrupa as despesas por status (Pago vs Pendente) para medir eficiência.
    """
    if df_lancamentos is None or df_lancamentos.empty:
        return None

    # Foco exclusivo em despesas
    df_despesas = df_lancamentos[df_lancamentos['tipo'] == "Despesa"].copy()

    if df_despesas.empty:
        return None

    # Agrupamento por Status
    df_status = df_despesas.groupby('status')['valor'].sum().reset_index()
    return df_status


def gerar_grafico_performance(df_status):
    """
    Gera gráfico de rosca (Donut Chart) para visualizar Pago vs Pendente.
    """
    if df_status is None or df_status.empty:
        return None

    # Mapeamento de cores: Verde para Pago, Laranja para Pendente
    cores_map = {
        'Pago': '#26a69a',
        'Pendente': '#ffa726'
    }

    # Garante que as cores sigam a ordem dos dados no DataFrame
    cores_lista = [cores_map.get(s, '#bdbdbd') for s in df_status['status']]

    fig = go.Figure(data=[go.Pie(
        labels=df_status['status'],
        values=df_status['valor'],
        hole=.6,
        marker=dict(colors=cores_lista),
        textinfo='percent+label',
        hovertemplate="<b>%{label}</b><br>Total: R$ %{value:,.2f}<br>%{percent}<extra></extra>"
    )])

    fig.update_layout(
        title="<b>Performance de Pagamentos</b>",
        template="plotly_white",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=50, b=20),
        height=400,
        annotations=[dict(text='Status', x=0.5, y=0.5, font_size=20, showarrow=False)]
    )

    return fig