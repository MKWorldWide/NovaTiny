/**
 * NovaTiny™ Agent Core - Main Firmware
 * 
 * This is the primary firmware for NovaTiny agents, designed for ESP32/STM32/ARM Cortex-M
 * platforms. The agent performs local emotion inference using TensorFlow Lite Micro
 * and broadcasts encrypted results via BLE or Wi-Fi.
 * 
 * Architecture:
 * - NovaSensors: Handles all sensor data collection (audio, motion, environmental)
 * - NovaML: Manages TensorFlow Lite Micro model inference
 * - NovaComms: Handles BLE/Wi-Fi communication and encryption
 * 
 * Power Management:
 * - Deep sleep between sampling cycles
 * - Adaptive sampling frequency based on activity
 * - Battery level monitoring and reporting
 * 
 * Security:
 * - AES-256 encryption for all outgoing packets
 * - Secure key storage in protected memory
 * - Anti-tampering detection
 * 
 * @author Nova Development Team
 * @version 1.0.0
 * @date 2024
 */

#include "NovaSensors.h"
#include "NovaML.h"
#include "NovaComms.h"
#include "NovaConfig.h"
#include "NovaPower.h"

// Global configuration and state management
NovaConfig config;
NovaPower powerManager;
bool systemInitialized = false;

/**
 * System initialization sequence
 * 
 * Performs all necessary setup including:
 * - Sensor calibration and validation
 * - ML model loading and verification
 * - Communication system initialization
 * - Power management setup
 * - Security key establishment
 */
void setup() {
  // Initialize serial communication for debugging
  Serial.begin(115200);
  Serial.println("NovaTiny Agent - Initializing...");
  
  // Initialize power management first
  if (!powerManager.begin()) {
    Serial.println("ERROR: Power management initialization failed");
    return;
  }
  
  // Load configuration from persistent storage
  if (!config.load()) {
    Serial.println("WARNING: Using default configuration");
    config.setDefaults();
  }
  
  // Initialize sensor subsystem
  if (!NovaSensors::init(config.getSensorConfig())) {
    Serial.println("ERROR: Sensor initialization failed");
    return;
  }
  
  // Initialize ML inference engine
  if (!NovaML::initModel(config.getModelPath())) {
    Serial.println("ERROR: ML model initialization failed");
    return;
  }
  
  // Initialize communication system (BLE with Wi-Fi fallback)
  if (!NovaComms::initBLE(config.getBLEConfig())) {
    Serial.println("WARNING: BLE initialization failed, trying Wi-Fi...");
    if (!NovaComms::initWiFi(config.getWiFiConfig())) {
      Serial.println("ERROR: Communication system initialization failed");
      return;
    }
  }
  
  // Perform system health check
  if (!performHealthCheck()) {
    Serial.println("ERROR: System health check failed");
    return;
  }
  
  systemInitialized = true;
  Serial.println("NovaTiny Agent - Initialization complete");
  Serial.println("Nova is awake. Begin pulse logging.");
}

/**
 * Main processing loop
 * 
 * Executes the core NovaTiny workflow:
 * 1. Collect sensor data
 * 2. Perform emotion inference
 * 3. Encrypt and broadcast results
 * 4. Manage power and sleep cycles
 */
void loop() {
  if (!systemInitialized) {
    Serial.println("ERROR: System not initialized, attempting recovery...");
    delay(5000);
    return;
  }
  
  // Check battery level and adjust operation mode
  powerManager.updateBatteryStatus();
  if (powerManager.isLowBattery()) {
    Serial.println("WARNING: Low battery, entering power-saving mode");
    powerManager.enterPowerSaveMode();
  }
  
  // Collect sensor data with error handling
  SensorData data;
  if (!NovaSensors::collect(&data)) {
    Serial.println("ERROR: Sensor data collection failed");
    delay(1000);
    return;
  }
  
  // Perform emotion inference using TensorFlow Lite Micro
  EmotionResult result;
  if (!NovaML::infer(data, &result)) {
    Serial.println("ERROR: ML inference failed");
    delay(1000);
    return;
  }
  
  // Log inference results for debugging
  Serial.printf("Emotion: %s, Confidence: %.2f, Intensity: %.2f\n", 
                result.label.c_str(), result.confidence, result.intensity);
  
  // Prepare and encrypt data packet
  NovaPacket packet;
  packet.deviceId = config.getDeviceId();
  packet.timestamp = millis();
  packet.emotion = result;
  packet.batteryLevel = powerManager.getBatteryLevel();
  packet.signalStrength = NovaComms::getSignalStrength();
  
  // Broadcast encrypted packet
  if (!NovaComms::broadcast(packet)) {
    Serial.println("WARNING: Packet broadcast failed");
    // Store packet for retry on next cycle
    NovaComms::queueForRetry(packet);
  }
  
  // Adaptive sleep based on activity and battery level
  unsigned long sleepDuration = calculateSleepDuration(result, powerManager.getBatteryLevel());
  Serial.printf("Sleeping for %lu ms\n", sleepDuration);
  
  // Enter deep sleep to conserve power
  powerManager.deepSleep(sleepDuration);
}

/**
 * Performs comprehensive system health check
 * 
 * Validates all subsystems and returns true if all checks pass.
 * Critical for ensuring reliable operation in the field.
 */
bool performHealthCheck() {
  Serial.println("Performing system health check...");
  
  // Check sensor subsystem
  if (!NovaSensors::healthCheck()) {
    Serial.println("FAIL: Sensor health check failed");
    return false;
  }
  
  // Check ML model integrity
  if (!NovaML::healthCheck()) {
    Serial.println("FAIL: ML model health check failed");
    return false;
  }
  
  // Check communication system
  if (!NovaComms::healthCheck()) {
    Serial.println("FAIL: Communication health check failed");
    return false;
  }
  
  // Check power management
  if (!powerManager.healthCheck()) {
    Serial.println("FAIL: Power management health check failed");
    return false;
  }
  
  Serial.println("PASS: All health checks completed successfully");
  return true;
}

/**
 * Calculates optimal sleep duration based on emotion intensity and battery level
 * 
 * Higher emotion intensity triggers more frequent sampling,
 * while low battery levels increase sleep duration to conserve power.
 */
unsigned long calculateSleepDuration(const EmotionResult& emotion, float batteryLevel) {
  // Base sleep duration (1 second)
  unsigned long baseSleep = 1000;
  
  // Adjust based on emotion intensity (higher intensity = shorter sleep)
  float intensityFactor = 1.0 - (emotion.intensity * 0.5);
  
  // Adjust based on battery level (lower battery = longer sleep)
  float batteryFactor = 1.0 + ((1.0 - batteryLevel) * 2.0);
  
  // Apply safety limits
  unsigned long sleepDuration = (unsigned long)(baseSleep * intensityFactor * batteryFactor);
  sleepDuration = constrain(sleepDuration, 100, 10000); // 100ms to 10s
  
  return sleepDuration;
} 