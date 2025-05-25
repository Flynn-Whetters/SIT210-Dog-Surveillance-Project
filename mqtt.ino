#include <WiFiNINA.h>
#include <PubSubClient.h>
#include <Servo.h>

const char* ssid = "SimonHub11";
const char* password = "SimonHub11";
const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;

WiFiClient wifiClient;
PubSubClient client(wifiClient);
Servo myServo;

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print(" Message arrived on topic: ");
  Serial.println(topic);

  String message;
  for (int i = 0; i < length; i++) { 
    message += (char)payload[i];
  }

  Serial.print(" Payload: ");
  Serial.println(message);

  if (message == "feed") {
  Serial.println("Feed command received. Dispensing full meal...");
  myServo.write(45);  // Open
  delay(2000);        // Full meal delay
  myServo.write(0);   // Close
  Serial.println("Full meal dispensed.");
} 
else if (message == "treat") {
  Serial.println("Treat command received. Dispensing treat...");
  myServo.write(45);  // Open
  delay(600);         // Short delay for treat
  myServo.write(0);   // Close
  Serial.println("Treat dispensed.");
}
}


void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("ArduinoClient")) {
      Serial.println(" MQTT connected!");
      client.subscribe("dogfeeder/command");
    } else {
      Serial.print(" failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}
void setup() {
  Serial.begin(9600);
  while (!Serial);  

  myServo.attach(9);

  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }

  Serial.println("\n Connected to WiFi!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}
