#include <WiFi.h>
#include <WiFiClientSecure.h> // Para suporte a TLS
#include <PubSubClient.h>
#include <DHT.h>

// Configurações da rede WiFi do Wokwi
const char* ssid = "Wokwi-GUEST"; // Nome da rede WiFi
const char* password = "";        // Wi-Fi do Wokwi não requer senha

// Configuração do broker MQTT
const char* mqtt_server = "4774fc7629144bce88648f900411e8bb.s1.eu.hivemq.cloud";
const int mqtt_port = 8883; // Porta para conexões TLS

// Credenciais MQTT (substitua pelos seus dados do HiveMQ Cloud)
const char* mqtt_user = "hivemq.webclient.1731952553915";
const char* mqtt_password = "uBgCe1K,0#7aj@9A.PLr";

// Configuração do cliente MQTT com TLS
WiFiClientSecure espClient; // Cliente seguro para TLS
PubSubClient client(espClient);

// Configuração do DHT22
#define DHTPIN 15        // Pino de dados do DHT22 conectado ao GPIO15
#define DHTTYPE DHT22    // Tipo do sensor
DHT dht(DHTPIN, DHTTYPE);

// Configuração do sensor LDR
#define LDRPIN 36        // Pino do LDR conectado ao GPIO36 (ADC)

// LED de alerta
#define LEDPIN 2         // Pino do LED conectado ao GPIO2

// Variáveis para armazenamento de dados
float temperatura;
float umidade;
int luminosidade;

// Função para reconectar ao broker MQTT
void reconnect() {
  while (!client.connected()) {
    Serial.print("Tentando conectar ao broker MQTT...");
    if (client.connect("ESP32_Client", mqtt_user, mqtt_password)) {
      Serial.println("Conectado ao broker!");
    } else {
      Serial.print("Falha na conexão. Código de erro: ");
      Serial.print(client.state());
      Serial.println(". Tentando novamente em 5 segundos...");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);

  // Configuração do pino do LED
  pinMode(LEDPIN, OUTPUT);
  digitalWrite(LEDPIN, LOW);

  // Inicialização do DHT22
  dht.begin();

  // Conexão WiFi
  Serial.print("Conectando ao WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nWiFi conectado!");

  // Configuração do cliente seguro (desabilitando verificação de certificado para testes)
  espClient.setInsecure();
  client.setServer(mqtt_server, mqtt_port);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Ler dados do sensor DHT22
  temperatura = dht.readTemperature();
  umidade = dht.readHumidity();

  // Ler dados do sensor LDR e converter para porcentagem
  int valorLDR = analogRead(LDRPIN);
  luminosidade = map(valorLDR, 0, 4095, 0, 100); // Convertendo para escala de 0 a 100%

  // Verificar se os valores são válidos
  if (!isnan(temperatura) && !isnan(umidade)) {
    // Publicar dados normais
    char tempString[8], humString[8], lumString[8];
    dtostrf(temperatura, 1, 2, tempString);
    dtostrf(umidade, 1, 2, humString);
    sprintf(lumString, "%d", luminosidade);
    client.publish("renovavel/temperatura", tempString);
    client.publish("renovavel/umidade", humString);
    client.publish("renovavel/luminosidade", lumString);

    // Lógica de alertas para situações críticas
    if (temperatura > 45.0) {
      client.publish("alertas/energia", "Temperatura alta crítica detectada!");
      digitalWrite(LEDPIN, HIGH);
    } else if (temperatura < 0.0) {
      client.publish("alertas/energia", "Temperatura baixa crítica detectada!");
      digitalWrite(LEDPIN, HIGH);
    } else if (umidade > 85.0) {
      client.publish("alertas/energia", "Umidade alta crítica detectada!");
      digitalWrite(LEDPIN, HIGH);
    } else if (umidade < 20.0) {
      client.publish("alertas/energia", "Umidade baixa crítica detectada!");
      digitalWrite(LEDPIN, HIGH);
    } else if (luminosidade < 20) {
      client.publish("alertas/energia", "Condição de luz extremamente baixa!");
      digitalWrite(LEDPIN, HIGH);
    } else if (luminosidade > 90) {
      client.publish("alertas/energia", "Condição de luz excessivamente alta!");
      digitalWrite(LEDPIN, HIGH);
    } else {
      digitalWrite(LEDPIN, LOW); // Sem alerta
    }
  } else {
    Serial.println("Falha ao ler os dados do DHT22!");
  }

  delay(5000); // Intervalo entre leituras
}
