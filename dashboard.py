"""
Integrantes:

Arthur Galvão Alves - RM554462
Felipe Braunstein e Silva - RM554483
"""

import dash
from dash import dcc, html
import plotly.graph_objs as go
import paho.mqtt.client as mqtt
from collections import deque
import time

# Configurações do MQTT
mqtt_broker = "4774fc7629144bce88648f900411e8bb.s1.eu.hivemq.cloud"
mqtt_port = 8883
mqtt_user = "hivemq.webclient.1731952553915"
mqtt_password = "uBgCe1K,0#7aj@9A.PLr"
temperature_topic = "renovavel/temperatura"
humidity_topic = "renovavel/umidade"
luminosity_topic = "renovavel/luminosidade"
alert_topic = "alertas/energia"

# Inicialização do Dash
app = dash.Dash(__name__)

# Listas para armazenamento de dados
temperaturas = deque(maxlen=100)
umidades = deque(maxlen=100)
luminosidades = deque(maxlen=100)
alertas = deque(maxlen=10)  # Apenas últimos 10 alertas
eficiencia = deque(maxlen=100)  # Armazenar os valores de eficiência

# Função de callback do MQTT
def on_message(client, userdata, message):
    topic = message.topic
    payload = message.payload.decode()

    if topic == temperature_topic:
        temperaturas.append(float(payload))
    elif topic == humidity_topic:
        umidades.append(float(payload))
    elif topic == luminosity_topic:
        luminosidades.append(int(payload))
    elif topic == alert_topic:
        alertas.append(payload)

# Configuração do cliente MQTT
client = mqtt.Client()
client.username_pw_set(mqtt_user, mqtt_password)
client.on_message = on_message
client.tls_set()
client.connect(mqtt_broker, mqtt_port)
client.subscribe(temperature_topic)
client.subscribe(humidity_topic)
client.subscribe(luminosity_topic)
client.subscribe(alert_topic)

# Função para manter o loop MQTT
def mqtt_loop():
    while True:
        client.loop()
        time.sleep(1)

# Função para calcular a eficiência
def calcular_eficiencia(temperatura, luminosidade):
    return (100 - abs(temperatura - 25)) * (luminosidade / 100)

# Layout do Dash
app.layout = html.Div([
    html.H1("Dashboard de Monitoramento de Energia Renovável"),
    dcc.Graph(id='temperatura-graph'),
    dcc.Graph(id='umidade-graph'),
    dcc.Graph(id='luminosidade-graph'),
    dcc.Graph(id='eficiencia-graph'),
    html.H2("Alertas Recentes"),
    html.Ul(id='alertas-list'),
    dcc.Interval(id='interval-component', interval=5000, n_intervals=0)
])

@app.callback(
    [dash.dependencies.Output('temperatura-graph', 'figure'),
     dash.dependencies.Output('umidade-graph', 'figure'),
     dash.dependencies.Output('luminosidade-graph', 'figure'),
     dash.dependencies.Output('eficiencia-graph', 'figure'),
     dash.dependencies.Output('alertas-list', 'children')],
    [dash.dependencies.Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    # Gráfico de temperatura
    fig_temp = go.Figure(go.Scatter(y=list(temperaturas), mode='lines+markers', name='Temperatura', line=dict(color='red')))
    fig_temp.update_layout(title='Temperatura (°C)', xaxis_title='Tempo', yaxis_title='°C')

    # Gráfico de umidade
    fig_hum = go.Figure(go.Scatter(y=list(umidades), mode='lines+markers', name='Umidade', line=dict(color='blue')))
    fig_hum.update_layout(title='Umidade (%)', xaxis_title='Tempo', yaxis_title='%')

    # Gráfico de luminosidade
    fig_lum = go.Figure(go.Scatter(y=list(luminosidades), mode='lines+markers', name='Luminosidade', line=dict(color='green')))
    fig_lum.update_layout(title='Luminosidade', xaxis_title='Tempo', yaxis_title='Luminosidade (%)')

    # Cálculo da eficiência e gráfico
    if len(temperaturas) > 0 and len(luminosidades) > 0:
        ultima_temperatura = temperaturas[-1]
        ultima_luminosidade = luminosidades[-1]
        eficiencia_valor = calcular_eficiencia(ultima_temperatura, ultima_luminosidade)
        eficiencia.append(eficiencia_valor)
    fig_efic = go.Figure(go.Scatter(y=list(eficiencia), mode='lines+markers', name='Eficiência', line=dict(color='orange')))
    fig_efic.update_layout(title='Eficiência do Sistema (%)', xaxis_title='Tempo', yaxis_title='Eficiência (%)')

    # Lista de alertas
    alertas_items = [html.Li(alerta, style={'color': 'red', 'font-weight': 'bold'}) for alerta in alertas]

    return fig_temp, fig_hum, fig_lum, fig_efic, alertas_items

if __name__ == '__main__':
    import threading
    threading.Thread(target=mqtt_loop).start()
    app.run_server(debug=True)
