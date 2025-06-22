#include <WiFi.h>
#include <esp_now.h>

HardwareSerial &arduinoSerial = Serial1;

typedef struct struct_message {
  int id;
  int data;
} struct_message;


uint8_t receiverAddress[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF}; // Replace with actual MAC if needed
struct_message myData;
struct_message incomingData;

String inputString = "";

void OnDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
  Serial.print("Send Status: ");
  Serial.println(status == ESP_NOW_SEND_SUCCESS ? "Success" : "Fail");
}


void OnDataRecv(const esp_now_recv_info_t *recvInfo, const uint8_t *data, int len) {
  memcpy(&incomingData, data, sizeof(incomingData));
  
  char macStr[18];
  snprintf(macStr, sizeof(macStr), "%02X:%02X:%02X:%02X:%02X:%02X",
            recvInfo->src_addr[0], recvInfo->src_addr[1], recvInfo->src_addr[2],
            recvInfo->src_addr[3], recvInfo->src_addr[4], recvInfo->src_addr[5]);

  Serial.print("Received from: ");
  Serial.println(macStr);
  Serial.print("ID: ");
  Serial.print(incomingData.id);
  Serial.print(" | Data: ");
  Serial.println(incomingData.data);
}

void setup() {
  Serial.begin(115200);
  arduinoSerial.begin(9600, SERIAL_8N1, 17, 18);  // RX, TX
  Serial.println("ESP32 Transmitter Serial Started");

  WiFi.mode(WIFI_STA);
  if (esp_now_init() != ESP_OK) {
    Serial.println("ESP-NOW init failed");
    return;
  }
  esp_now_register_send_cb(OnDataSent);
  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, receiverAddress, 6);
  peerInfo.channel = 0;
  peerInfo.encrypt = false;
  if (!esp_now_is_peer_exist(receiverAddress)) {
    esp_now_add_peer(&peerInfo);
  }
  esp_now_register_recv_cb(OnDataRecv);
}

void loop() {
  while (arduinoSerial.available()) {
    char c = arduinoSerial.read();
    if (c == '\n') {
      int ardu_data = inputString.toInt();
      Serial.print("Received punch: ");
      Serial.println(ardu_data);

      myData.id = 1;
      myData.data = ardu_data;

      esp_err_t result = esp_now_send(receiverAddress, (uint8_t *)&myData, sizeof(myData));
      if (result == ESP_OK) {
        Serial.println("Sent via ESP-NOW");
      } else {
        Serial.println("Send failed");
      }

      inputString = "";
    } else {
      inputString += c;
    }
  }
}
