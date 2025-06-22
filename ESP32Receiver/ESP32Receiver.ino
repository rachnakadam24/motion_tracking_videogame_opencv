#include <WiFi.h>
#include <esp_now.h>

typedef struct struct_message {
  int id;
  int data;
} struct_message;


uint8_t receiverAddress[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF}; // Replace with actual MAC if needed
struct_message myData;
struct_message incomingData;

String inputString = "";

void OnDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
  // Serial.print("Send Status: ");
  // Serial.println(status == ESP_NOW_SEND_SUCCESS ? "Success" : "Fail");
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
  Serial.println("ESP32 Receiver Serial Started");
  
  WiFi.mode(WIFI_STA);
  if (esp_now_init() != ESP_OK) {
    Serial.println("Error initializing ESP-NOW");
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
  delay(10);
}
