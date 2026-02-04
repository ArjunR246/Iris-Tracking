/*
 Simple ESP32 web server that exposes /success and /fail endpoints.
 When /success is requested, a GREEN LED (GPIO2) is turned on briefly.
 When /fail is requested, a RED LED (GPIO4) is turned on briefly.
 Modify pins if your board's pins differ.
*/

#include <WiFi.h>
#include <WebServer.h>

const char* ssid = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";

WebServer server(80);

const int GREEN_PIN = 2; // AUTH_SUCCESS
const int RED_PIN = 4;   // AUTH_FAIL
const int BUZZER_PIN = 12;

void handleRoot() {
  server.send(200, "text/plain", "ESP32 Liveliness Controller");
}

void handleSuccess() {
  digitalWrite(GREEN_PIN, HIGH);
  digitalWrite(RED_PIN, LOW);
  tone(BUZZER_PIN, 2000, 100);
  server.send(200, "text/plain", "OK");
}

void handleFail() {
  digitalWrite(RED_PIN, HIGH);
  digitalWrite(GREEN_PIN, LOW);
  tone(BUZZER_PIN, 1000, 100);
  server.send(200, "text/plain", "OK");
}

void setup() {
  Serial.begin(115200);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(RED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(GREEN_PIN, LOW);
  digitalWrite(RED_PIN, LOW);

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Connected. IP: ");
  Serial.println(WiFi.localIP());

  server.on("/", handleRoot);
  server.on("/success", handleSuccess);
  server.on("/fail", handleFail);
  server.begin();
  Serial.println("HTTP server started");
}

void loop() {
  server.handleClient();
}
