/**
 * NovaComms.h - Communication Interface for NovaTiny
 * 
 * Provides unified communication interface for NovaTiny agents, supporting
 * both BLE (Bluetooth Low Energy) and Wi-Fi connectivity with automatic
 * fallback and encryption. Designed for secure, low-power data transmission
 * in distributed emotion detection networks.
 * 
 * Features:
 * - BLE advertising and GATT services
 * - Wi-Fi connectivity with automatic reconnection
 * - AES-256 encryption for all data packets
 * - Automatic protocol selection and fallback
 * - Packet queuing and retry mechanisms
 * - Signal strength monitoring
 * - Power-efficient transmission strategies
 * 
 * Security:
 * - End-to-end encryption with rotating keys
 * - Secure key exchange protocols
 * - Anti-replay protection
 * - Tamper detection and reporting
 * 
 * @author Nova Development Team
 * @version 1.0.0
 * @date 2024
 */

#ifndef NOVA_COMMS_H
#define NOVA_COMMS_H

#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include "NovaML.h"

// Communication protocols
enum CommProtocol {
  PROTOCOL_BLE = 0,
  PROTOCOL_WIFI = 1,
  PROTOCOL_AUTO = 2
};

// Packet types for different data formats
enum PacketType {
  PACKET_EMOTION = 0x01,      // Emotion inference result
  PACKET_HEALTH = 0x02,       // System health status
  PACKET_CONFIG = 0x03,       // Configuration update
  PACKET_ALERT = 0x04,        // High-priority alert
  PACKET_BATCH = 0x05,        // Batched data packets
  PACKET_ACK = 0x06,          // Acknowledgment
  PACKET_ERROR = 0x07         // Error report
};

// Encryption configuration
struct EncryptionConfig {
  uint8_t key[32];            // AES-256 encryption key
  uint8_t iv[16];             // Initialization vector
  uint32_t keyVersion;        // Key version for rotation
  uint32_t sequenceNumber;    // Sequence number for anti-replay
  bool enableEncryption;      // Enable/disable encryption
};

// BLE configuration
struct BLEConfig {
  const char* deviceName;     // BLE device name
  const char* serviceUUID;    // Primary service UUID
  const char* charUUID;       // Characteristic UUID
  uint16_t advInterval;       // Advertising interval (ms)
  int8_t txPower;            // Transmission power (dBm)
  bool enableConnectable;     // Allow connections
  bool enableDiscoverable;    // Make device discoverable
};

// Wi-Fi configuration
struct WiFiConfig {
  const char* ssid;          // Network SSID
  const char* password;      // Network password
  const char* serverURL;     // Cloud server URL
  uint16_t serverPort;       // Server port
  bool enableSSL;            // Enable SSL/TLS
  uint32_t timeout;          // Connection timeout (ms)
  uint8_t retryCount;        // Reconnection attempts
};

// Network packet structure
struct NovaPacket {
  uint8_t header[4];         // Packet header (magic bytes)
  uint8_t version;           // Protocol version
  PacketType type;           // Packet type
  uint32_t deviceId;         // Device identifier
  uint32_t timestamp;        // Timestamp
  uint32_t sequence;         // Sequence number
  uint16_t payloadSize;      // Payload size in bytes
  uint8_t* payload;          // Encrypted payload
  uint8_t checksum[32];      // SHA-256 checksum
  uint8_t signature[64];     // Digital signature (if enabled)
};

// Communication status
struct CommStatus {
  CommProtocol activeProtocol;   // Currently active protocol
  bool bleConnected;             // BLE connection status
  bool wifiConnected;            // Wi-Fi connection status
  int8_t signalStrength;         // Signal strength (dBm)
  uint32_t packetsSent;          // Total packets sent
  uint32_t packetsReceived;      // Total packets received
  uint32_t errors;               // Communication errors
  uint32_t lastTransmission;     // Last transmission time
  float batteryImpact;           // Battery impact of current protocol
};

// Queue management for packet retry
struct QueuedPacket {
  NovaPacket packet;
  uint32_t timestamp;
  uint8_t retryCount;
  uint32_t nextRetry;
};

// NovaComms class declaration
class NovaComms {
public:
  // Initialization and configuration
  static bool initBLE(const BLEConfig& config);
  static bool initWiFi(const WiFiConfig& config);
  static bool setEncryptionConfig(const EncryptionConfig& config);
  static bool setProtocol(CommProtocol protocol);
  
  // Packet transmission
  static bool broadcast(const NovaPacket& packet);
  static bool sendEmotionData(const EmotionResult& emotion, float batteryLevel);
  static bool sendHealthStatus(const SensorStatus& status);
  static bool sendAlert(const char* message, uint8_t priority);
  
  // Connection management
  static bool connect();
  static bool disconnect();
  static bool isConnected();
  static bool reconnect();
  
  // Status and monitoring
  static CommStatus getStatus();
  static int8_t getSignalStrength();
  static bool healthCheck();
  static void updateStatus();
  
  // Queue management
  static bool queueForRetry(const NovaPacket& packet);
  static bool processRetryQueue();
  static uint8_t getQueueSize();
  static bool clearQueue();
  
  // Power management
  static void enterLowPowerMode();
  static void exitLowPowerMode();
  static float getBatteryImpact();
  
  // Security functions
  static bool rotateEncryptionKey();
  static bool verifyPacketIntegrity(const NovaPacket& packet);
  static bool generateSignature(const NovaPacket& packet, uint8_t* signature);
  
private:
  // BLE components
  static BLEServer* bleServer;
  static BLEService* bleService;
  static BLECharacteristic* bleCharacteristic;
  static BLEConfig bleConfig;
  static bool bleInitialized;
  static bool bleConnected;
  
  // Wi-Fi components
  static WiFiConfig wifiConfig;
  static bool wifiInitialized;
  static bool wifiConnected;
  static HTTPClient httpClient;
  static WiFiClientSecure sslClient;
  
  // Encryption components
  static EncryptionConfig encryptionConfig;
  static bool encryptionEnabled;
  
  // Queue management
  static QueuedPacket retryQueue[10];
  static uint8_t queueHead;
  static uint8_t queueTail;
  static uint8_t queueSize;
  
  // Status tracking
  static CommStatus status;
  static CommProtocol currentProtocol;
  
  // Internal helper functions
  static bool initBLEAdvertising();
  static bool initBLEService();
  static bool initWiFiConnection();
  static bool sendPacketBLE(const NovaPacket& packet);
  static bool sendPacketWiFi(const NovaPacket& packet);
  static bool encryptPacket(NovaPacket* packet);
  static bool decryptPacket(NovaPacket* packet);
  static bool calculateChecksum(const NovaPacket& packet, uint8_t* checksum);
  static bool validateChecksum(const NovaPacket& packet);
  static void handleConnectionEvent(bool connected);
  static void handleError(const char* error);
  
  // Packet construction helpers
  static bool buildEmotionPacket(const EmotionResult& emotion, float batteryLevel, NovaPacket* packet);
  static bool buildHealthPacket(const SensorStatus& status, NovaPacket* packet);
  static bool buildAlertPacket(const char* message, uint8_t priority, NovaPacket* packet);
  
  // BLE callbacks
  static void onBLEConnect(BLEServer* server);
  static void onBLEDisconnect(BLEServer* server);
  static void onBLEWrite(BLECharacteristic* characteristic);
  
  // Utility functions
  static uint32_t generateSequenceNumber();
  static bool isPacketExpired(const NovaPacket& packet);
  static CommProtocol selectOptimalProtocol();
  static void updateBatteryImpact();
};

// BLE Service UUIDs (standardized for Nova network)
#define NOVA_SERVICE_UUID        "12345678-1234-1234-1234-123456789abc"
#define NOVA_CHARACTERISTIC_UUID "87654321-4321-4321-4321-cba987654321"

// Packet header magic bytes
#define PACKET_HEADER_MAGIC_0    0x4E  // 'N'
#define PACKET_HEADER_MAGIC_1    0x6F  // 'o'
#define PACKET_HEADER_MAGIC_2    0x76  // 'v'
#define PACKET_HEADER_MAGIC_3    0x61  // 'a'

// Protocol version
#define PROTOCOL_VERSION         0x01

// Maximum packet sizes
#define MAX_PAYLOAD_SIZE         1024
#define MAX_PACKET_SIZE          2048

// Retry configuration
#define MAX_RETRY_COUNT          3
#define RETRY_DELAY_MS           1000
#define PACKET_TIMEOUT_MS        5000

#endif // NOVA_COMMS_H 