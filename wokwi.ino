#include <WiFi.h>
#include <WiFiClientSecure.h> // Para suporte a TLS
#include <PubSubClient.h>
#include <DHT.h>

// Configurações da rede WiFi
const char* ssid = "Wokwi-GUEST";
const char* password = "";

// Configuração do broker MQTT
const char* mqtt_server = "4774fc7629144bce88648f900411e8bb.s1.eu.hivemq.cloud";
const int mqtt_port = 8883;
const char* mqtt_user = "hivemq.webclient.1731952553915";
const char* mqtt_password = "uBgCe1K,0#7aj@9A.PLr";

// Configuração do cliente MQTT com TLS
WiFiClientSecure espClient;
PubSubClient client(espClient);

// Configuração do DHT22
#define DHTPIN 15
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// Configuração do sensor LDR
#define LDRPIN 36

// LED de alerta
#define LEDPIN 2

// Variáveis dos sensores
float temperatura;
float umidade;
int luminosidade;

// Função para reconectar ao broker MQTT
void reconnect() {
  while (!client.connected()) {
    Serial.print("Tentando conectar ao broker MQTT...");
    if (client.connect("ESP32_Client", mqtt_user, mqtt_password)) {
      Serial.println("Conectado!");
    } else {
      Serial.print("Falha. Código: ");
      Serial.print(client.state());
      Serial.println(" Tentando novamente em 5 segundos...");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);

  pinMode(LEDPIN, OUTPUT);
  digitalWrite(LEDPIN, LOW);

  dht.begin();

  Serial.print("Conectando ao WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nWiFi conectado!");

  espClient.setInsecure();
  client.setServer(mqtt_server, mqtt_port);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Ler dados do DHT22
  temperatura = dht.readTemperature();
  umidade = dht.readHumidity();

  // Ler dados do sensor LDR
  int valorLDR = analogRead(LDRPIN);
  luminosidade = map(valorLDR, 0, 4095, 0, 100);

  if (!isnan(temperatura) && !isnan(umidade)) {
    // Publicar temperatura
    char tempString[8];
    dtostrf(temperatura, 1, 2, tempString);
    client.publish("renovavel/temperatura", tempString);
    Serial.print("Temperatura: ");
    Serial.println(tempString);

    // Publicar umidade
    char humString[8];
    dtostrf(umidade, 1, 2, humString);
    client.publish("renovavel/umidade", humString);
    Serial.print("Umidade: ");
    Serial.println(humString);

    // Publicar luminosidade
    char lumString[8];
    sprintf(lumString, "%d", luminosidade);
    client.publish("renovavel/luminosidade", lumString);
    Serial.print("Luminosidade: ");
    Serial.println(lumString);

    // Verificar alertas
    bool alerta = false;

    if (temperatura > 45.0) {
      client.publish("alertas/energia", "ALERTA: Temperatura alta crítica!");
      alerta = true;
    } else if (temperatura < 0.0) {
      client.publish("alertas/energia", "ALERTA: Temperatura baixa crítica!");
      alerta = true;
    }

    if (umidade > 85.0) {
      client.publish("alertas/energia", "ALERTA: Umidade alta crítica!");
      alerta = true;
    } else if (umidade < 20.0) {
      client.publish("alertas/energia", "ALERTA: Umidade baixa crítica!");
      alerta = true;
    }

    if (luminosidade > 90) {
      client.publish("alertas/energia", "ALERTA: Luminosidade excessiva!");
      alerta = true;
    } else if (luminosidade < 20) {
      client.publish("alertas/energia", "ALERTA: Luminosidade extremamente baixa!");
      alerta = true;
    }

    digitalWrite(LEDPIN, alerta ? HIGH : LOW);
  } else {
    Serial.println("Erro ao ler os dados do DHT22.");
  }

  delay(5000);
}
