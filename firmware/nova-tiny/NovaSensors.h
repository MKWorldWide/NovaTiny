/**
 * NovaSensors.h - Sensor Management Interface
 * 
 * Provides unified interface for all sensor types used in NovaTiny agents:
 * - Audio sensors (microphone) for voice emotion detection
 * - Motion sensors (accelerometer, gyroscope) for activity detection
 * - Environmental sensors (temperature, humidity) for context
 * - Heart rate sensors (if available) for physiological data
 * 
 * Features:
 * - Automatic sensor detection and initialization
 * - Data fusion and preprocessing
 * - Calibration and drift compensation
 * - Error handling and recovery
 * - Power-efficient sampling strategies
 * 
 * @author Nova Development Team
 * @version 1.0.0
 * @date 2024
 */

#ifndef NOVA_SENSORS_H
#define NOVA_SENSORS_H

#include <Arduino.h>
#include <Wire.h>
#include <SPI.h>

// Sensor configuration structure
struct SensorConfig {
  bool enableAudio;           // Enable microphone sensor
  bool enableMotion;          // Enable accelerometer/gyroscope
  bool enableEnvironmental;   // Enable temperature/humidity
  bool enableHeartRate;       // Enable heart rate sensor (if available)
  
  uint16_t audioSampleRate;   // Audio sampling rate (Hz)
  uint16_t motionSampleRate;  // Motion sampling rate (Hz)
  uint16_t envSampleRate;     // Environmental sampling rate (Hz)
  uint16_t hrSampleRate;      // Heart rate sampling rate (Hz)
  
  uint8_t audioGain;          // Microphone gain setting
  uint8_t motionRange;        // Accelerometer range (±2g, ±4g, ±8g, ±16g)
  uint8_t motionBandwidth;    // Motion sensor bandwidth
  
  bool enableCalibration;     // Enable automatic calibration
  bool enableDriftComp;       // Enable drift compensation
};

// Raw sensor data structures
struct AudioData {
  float* samples;             // Raw audio samples
  uint16_t sampleCount;       // Number of samples
  float rms;                  // Root mean square amplitude
  float peak;                 // Peak amplitude
  float frequency;            // Dominant frequency
  float spectralCentroid;     // Spectral centroid
  float zeroCrossingRate;     // Zero crossing rate
  uint32_t timestamp;         // Timestamp of data collection
};

struct MotionData {
  float accelX, accelY, accelZ;  // Accelerometer readings (g)
  float gyroX, gyroY, gyroZ;     // Gyroscope readings (deg/s)
  float magX, magY, magZ;        // Magnetometer readings (uT)
  float temperature;             // Sensor temperature (°C)
  float magnitude;               // Total acceleration magnitude
  float pitch, roll, yaw;        // Calculated orientation
  uint32_t timestamp;            // Timestamp of data collection
};

struct EnvironmentalData {
  float temperature;         // Ambient temperature (°C)
  float humidity;            // Relative humidity (%)
  float pressure;            // Atmospheric pressure (hPa)
  float light;               // Ambient light level (lux)
  float noise;               // Ambient noise level (dB)
  uint32_t timestamp;        // Timestamp of data collection
};

struct HeartRateData {
  uint16_t bpm;              // Beats per minute
  float confidence;           // Detection confidence (0-1)
  uint16_t rrInterval;       // R-R interval (ms)
  float hrv;                 // Heart rate variability
  uint32_t timestamp;        // Timestamp of data collection
};

// Fused sensor data structure
struct SensorData {
  AudioData audio;           // Audio sensor data
  MotionData motion;         // Motion sensor data
  EnvironmentalData env;     // Environmental sensor data
  HeartRateData heartRate;   // Heart rate data
  
  uint32_t collectionTime;   // Total time to collect all data
  bool audioValid;           // Audio data validity flag
  bool motionValid;          // Motion data validity flag
  bool envValid;             // Environmental data validity flag
  bool heartRateValid;       // Heart rate data validity flag
  
  // Derived features for ML inference
  float activityLevel;       // Overall activity level (0-1)
  float stressLevel;         // Estimated stress level (0-1)
  float engagementLevel;     // Engagement/attention level (0-1)
};

// Sensor status and health information
struct SensorStatus {
  bool audioConnected;       // Audio sensor connection status
  bool motionConnected;      // Motion sensor connection status
  bool envConnected;         // Environmental sensor connection status
  bool heartRateConnected;   // Heart rate sensor connection status
  
  float audioQuality;        // Audio signal quality (0-1)
  float motionQuality;       // Motion signal quality (0-1)
  float envQuality;          // Environmental signal quality (0-1)
  float heartRateQuality;    // Heart rate signal quality (0-1)
  
  uint32_t lastCalibration;  // Last calibration timestamp
  uint32_t uptime;           // Sensor system uptime
  uint32_t errorCount;       // Total error count
};

// NovaSensors class declaration
class NovaSensors {
public:
  // Initialization and configuration
  static bool init(const SensorConfig& config);
  static bool setConfig(const SensorConfig& config);
  static SensorConfig getConfig();
  
  // Data collection
  static bool collect(SensorData* data);
  static bool collectAudio(AudioData* data);
  static bool collectMotion(MotionData* data);
  static bool collectEnvironmental(EnvironmentalData* data);
  static bool collectHeartRate(HeartRateData* data);
  
  // Calibration and maintenance
  static bool calibrate();
  static bool calibrateAudio();
  static bool calibrateMotion();
  static bool calibrateEnvironmental();
  static bool calibrateHeartRate();
  
  // Health monitoring
  static bool healthCheck();
  static SensorStatus getStatus();
  static bool reset();
  
  // Power management
  static void enterLowPowerMode();
  static void exitLowPowerMode();
  static void sleep();
  static void wake();
  
  // Data processing utilities
  static float calculateActivityLevel(const MotionData& motion);
  static float calculateStressLevel(const HeartRateData& hr, const EnvironmentalData& env);
  static float calculateEngagementLevel(const AudioData& audio, const MotionData& motion);
  
private:
  static SensorConfig currentConfig;
  static SensorStatus status;
  static bool initialized;
  
  // Internal helper functions
  static bool detectSensors();
  static bool validateSensorData(const SensorData& data);
  static void updateStatus();
  static void handleError(const char* error);
  
  // Sensor-specific initialization
  static bool initAudioSensor();
  static bool initMotionSensor();
  static bool initEnvironmentalSensor();
  static bool initHeartRateSensor();
  
  // Data preprocessing
  static void preprocessAudio(AudioData* data);
  static void preprocessMotion(MotionData* data);
  static void preprocessEnvironmental(EnvironmentalData* data);
  static void preprocessHeartRate(HeartRateData* data);
};

#endif // NOVA_SENSORS_H 