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

# Listas (ou deques) para armazenar os dados recebidos
temperaturas = deque(maxlen=100)
umidades = deque(maxlen=100)
luminosidades = deque(maxlen=100)
alertas = deque(maxlen=10)  # Apenas os últimos 10 alertas

# Função de callback MQTT
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

# Inscrever-se nos tópicos
client.subscribe(temperature_topic)
client.subscribe(humidity_topic)
client.subscribe(luminosity_topic)
client.subscribe(alert_topic)

# Layout do Dash
app.layout = html.Div(children=[
    html.H1("Dashboard de Monitoramento de Energia Renovável"),

    dcc.Graph(id='temperatura-graph'),
    dcc.Graph(id='umidade-graph'),
    dcc.Graph(id='luminosidade-graph'),
    dcc.Graph(id='eficiencia-graph'),  # Gráfico de eficiência

    html.H2("Alertas Recentes"),
    html.Ul(id='alertas-list'),

    dcc.Interval(
        id='interval-component',
        interval=5000,  # Atualiza a cada 5 segundos
        n_intervals=0
    )
])

# Atualização dos gráficos e alertas
@app.callback(
    [dash.dependencies.Output('temperatura-graph', 'figure'),
     dash.dependencies.Output('umidade-graph', 'figure'),
     dash.dependencies.Output('luminosidade-graph', 'figure'),
     dash.dependencies.Output('eficiencia-graph', 'figure'),
     dash.dependencies.Output('alertas-list', 'children')],
    [dash.dependencies.Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    # Gráfico de Temperatura
    fig_temp = go.Figure(go.Scatter(
        x=list(range(len(temperaturas))),
        y=list(temperaturas),
        mode='lines+markers',
        name='Temperatura (°C)',
        line=dict(color='red')
    ))
    fig_temp.update_layout(title='Temperatura ao Longo do Tempo', xaxis_title='Tempo', yaxis_title='Temperatura (°C)')

    # Gráfico de Umidade
    fig_hum = go.Figure(go.Scatter(
        x=list(range(len(umidades))),
        y=list(umidades),
        mode='lines+markers',
        name='Umidade (%)',
        line=dict(color='blue')
    ))
    fig_hum.update_layout(title='Umidade ao Longo do Tempo', xaxis_title='Tempo', yaxis_title='Umidade (%)')

    # Gráfico de Luminosidade
    fig_lum = go.Figure(go.Scatter(
        x=list(range(len(luminosidades))),
        y=list(luminosidades),
        mode='lines+markers',
        name='Luminosidade',
        line=dict(color='green')
    ))
    fig_lum.update_layout(title='Luminosidade ao Longo do Tempo', xaxis_title='Tempo', yaxis_title='Luminosidade')

    # Gráfico de Eficiência
    eficiencia = [lum * 0.5 for lum in luminosidades]  # Exemplo simples de cálculo de eficiência
    fig_eff = go.Figure(go.Scatter(
        x=list(range(len(eficiencia))),
        y=eficiencia,
        mode='lines+markers',
        name='Eficiência (%)',
        line=dict(color='purple')
    ))
    fig_eff.update_layout(title='Eficiência do Sistema Solar', xaxis_title='Tempo', yaxis_title='Eficiência (%)')

    # Atualizar a lista de alertas
    alertas_items = [html.Li(alerta) for alerta in alertas]

    return fig_temp, fig_hum, fig_lum, fig_eff, alertas_items

# Função para rodar o MQTT em paralelo
def mqtt_loop():
    while True:
        client.loop()
        time.sleep(1)

# Rodar o servidor Dash
if __name__ == '__main__':
    from threading import Thread

    mqtt_thread = Thread(target=mqtt_loop)
    mqtt_thread.start()
    app.run_server(debug=True, use_reloader=False)
