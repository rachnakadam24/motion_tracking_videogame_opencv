#include <Wire.h>
#include <MPU6050.h>
#include <SoftwareSerial.h>

// === Constants ===
#define RED_PUNCH 100   // Left hand (red)
#define BLUE_PUNCH 200  // Right hand (blue)

MPU6050 mpuLeft(0x68);   // AD0 = LOW
MPU6050 mpuRight(0x69);  // AD0 = HIGH
SoftwareSerial espSerial(3, 8); // RX, TX (connect to ESP32)

// === Filters and thresholds ===
const int filterSize = 10;
float accelBufferLeft[filterSize] = {0};
float accelBufferRight[filterSize] = {0};
int bufferIndex = 0;

const float punchStartThreshold = 20.0;   // Minimum jerk to detect start
const float punchEndThreshold = -20.0;    // Negative jerk to detect impact

// === Timers ===
unsigned long lastTime = 0;
unsigned long lastPrintTime = 0;
unsigned long lastPunchTimeLeft = 0;
unsigned long lastPunchTimeRight = 0;
const unsigned long printInterval = 2000;
const unsigned long punchCooldown = 500;

// === States ===
float lastAccelLeft = 0;
float lastAccelRight = 0;
bool leftPunching = false;
bool rightPunching = false;

void setup() {
  Serial.begin(9600);
  espSerial.begin(9600);
  Wire.begin();

  mpuLeft.initialize();
  mpuRight.initialize();

  if (!mpuLeft.testConnection()) Serial.println("Left MPU6050 not connected!");
  if (!mpuRight.testConnection()) Serial.println("Right MPU6050 not connected!");

  lastTime = millis();
  lastPrintTime = millis();
}

void loop() {
  unsigned long currentTime = millis();
  float dt = (currentTime - lastTime) / 1000.0;

  float aL = getMagnitude(mpuLeft);
  float aR = getMagnitude(mpuRight);

  float smoothedLeft = getSmoothedAccel(aL, accelBufferLeft);
  float smoothedRight = getSmoothedAccel(aR, accelBufferRight);

  float jerkLeft = (smoothedLeft - lastAccelLeft) / dt;
  float jerkRight = (smoothedRight - lastAccelRight) / dt;

  // === LEFT Hand ===
  if (!leftPunching && jerkLeft > punchStartThreshold) {
    leftPunching = true;
    Serial.println("[LEFT] Punch started");
  }

  if (leftPunching && jerkLeft < punchEndThreshold && (currentTime - lastPunchTimeLeft) > punchCooldown) {
    leftPunching = false;
    Serial.print("[LEFT] Punch END (impact), Jerk: "); Serial.println(jerkLeft, 2);
    espSerial.println(RED_PUNCH);
    lastPunchTimeLeft = currentTime;
  }

  // === RIGHT Hand ===
  if (!rightPunching && jerkRight > punchStartThreshold) {
    rightPunching = true;
    Serial.println("[RIGHT] Punch started");
  }

  if (rightPunching && jerkRight < punchEndThreshold && (currentTime - lastPunchTimeRight) > punchCooldown) {
    rightPunching = false;
    Serial.print("[RIGHT] Punch END (impact), Jerk: "); Serial.println(jerkRight, 2);
    espSerial.println(BLUE_PUNCH);
    lastPunchTimeRight = currentTime;
  }

  // === Battery Status ===
  if ((currentTime - lastPrintTime) > printInterval) {
    int sensorValue = analogRead(A0);
    float batteryVoltage = sensorValue * (5.0 / 1023.0);
    int batteryLevel = getBatteryLevel(batteryVoltage);
    Serial.print("[BATTERY] Voltage: ");
    Serial.print(batteryVoltage);
    Serial.print(" V | Level: ");
    Serial.println(batteryLevel);
    espSerial.println(batteryLevel);
    lastPrintTime = currentTime;
  }

  // === Update for next loop ===
  lastAccelLeft = smoothedLeft;
  lastAccelRight = smoothedRight;
  lastTime = currentTime;
  bufferIndex = (bufferIndex + 1) % filterSize;

  delay(5);
}

// === Helper: Smoothed acceleration ===
float getSmoothedAccel(float newVal, float* buffer) {
  buffer[bufferIndex] = newVal;
  float sum = 0;
  for (int i = 0; i < filterSize; i++) sum += buffer[i];
  return sum / filterSize;
}

// === Helper: Total acceleration magnitude ===
float getMagnitude(MPU6050& mpu) {
  int ax, ay, az;
  mpu.getAcceleration(&ax, &ay, &az);
  float axg = ax / 16384.0;
  float ayg = ay / 16384.0;
  float azg = az / 16384.0;
  return sqrt(axg * axg + ayg * ayg + azg * azg);
}

// === Helper: Battery level (0 to 5) ===
int getBatteryLevel(float voltage) {
  const float minVoltage = 3.0;
  const float maxVoltage = 4.2;

  voltage = constrain(voltage, minVoltage, maxVoltage);
  return (int)((voltage - minVoltage) / (maxVoltage - minVoltage) * 5.0 + 0.5);
}
