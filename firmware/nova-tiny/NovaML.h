/**
 * NovaML.h - Machine Learning Interface for NovaTiny
 * 
 * Provides TensorFlow Lite Micro integration for real-time emotion inference
 * on embedded devices. Supports multiple model types and inference strategies
 * optimized for low-power, low-memory environments.
 * 
 * Features:
 * - TensorFlow Lite Micro model loading and inference
 * - Multi-modal emotion detection (audio, motion, physiological)
 * - Model quantization and optimization
 * - Adaptive inference based on confidence thresholds
 * - Model versioning and OTA updates
 * - Memory-efficient feature extraction
 * 
 * Supported Models:
 * - Audio-based emotion recognition
 * - Motion-based activity classification
 * - Physiological stress detection
 * - Multi-modal fusion models
 * 
 * @author Nova Development Team
 * @version 1.0.0
 * @date 2024
 */

#ifndef NOVA_ML_H
#define NOVA_ML_H

#include <Arduino.h>
#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_error_reporter.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "NovaSensors.h"

// Emotion classification labels
enum EmotionLabel {
  EMOTION_NEUTRAL = 0,
  EMOTION_HAPPY = 1,
  EMOTION_SAD = 2,
  EMOTION_ANGRY = 3,
  EMOTION_FEAR = 4,
  EMOTION_SURPRISE = 5,
  EMOTION_DISGUST = 6,
  EMOTION_CONTEMPT = 7,
  EMOTION_ENGAGED = 8,
  EMOTION_DISTRACTED = 9,
  EMOTION_STRESSED = 10,
  EMOTION_RELAXED = 11,
  EMOTION_UNKNOWN = 12
};

// Emotion result structure
struct EmotionResult {
  EmotionLabel label;         // Primary emotion classification
  float confidence;           // Classification confidence (0-1)
  float intensity;            // Emotion intensity (0-1)
  
  // Secondary emotions (for multi-label classification)
  float secondaryConfidences[12];  // Confidence scores for all emotions
  EmotionLabel secondaryLabel;     // Second most likely emotion
  
  // Contextual information
  float arousal;              // Arousal level (0-1)
  float valence;              // Valence level (0-1)
  float dominance;            // Dominance level (0-1)
  
  // Temporal information
  uint32_t timestamp;         // Inference timestamp
  uint32_t processingTime;    // Time taken for inference (ms)
  
  // Quality metrics
  float inputQuality;         // Quality of input data (0-1)
  bool reliable;              // Whether the result is reliable
};

// Model configuration structure
struct ModelConfig {
  const char* modelPath;      // Path to TFLite model file
  uint32_t modelSize;         // Size of model in bytes
  uint8_t modelVersion;       // Model version number
  
  // Input configuration
  uint16_t inputSize;         // Number of input features
  uint16_t sequenceLength;    // Sequence length for time-series models
  uint8_t numChannels;        // Number of input channels
  
  // Output configuration
  uint8_t numClasses;         // Number of output classes
  float confidenceThreshold;  // Minimum confidence for reliable prediction
  
  // Performance settings
  uint8_t numThreads;         // Number of inference threads
  bool enableQuantization;    // Enable quantized inference
  bool enablePruning;         // Enable model pruning
  
  // Memory settings
  uint32_t tensorArenaSize;   // Size of tensor arena (bytes)
  uint32_t maxWorkspaceSize;  // Maximum workspace size (bytes)
};

// Feature extraction configuration
struct FeatureConfig {
  // Audio features
  bool enableMFCC;            // Enable Mel-frequency cepstral coefficients
  bool enableSpectral;        // Enable spectral features
  bool enableTemporal;        // Enable temporal features
  
  // Motion features
  bool enableStatistical;     // Enable statistical motion features
  bool enableFrequency;       // Enable frequency-domain features
  bool enableOrientation;     // Enable orientation features
  
  // Physiological features
  bool enableHRV;             // Enable heart rate variability features
  bool enableStress;          // Enable stress indicators
  
  // Feature parameters
  uint8_t mfccCoefficients;   // Number of MFCC coefficients
  uint8_t fftSize;            // FFT size for spectral analysis
  uint16_t windowSize;        // Analysis window size
  uint16_t hopSize;           // Hop size between windows
};

// Model performance metrics
struct ModelMetrics {
  uint32_t totalInferences;   // Total number of inferences performed
  uint32_t successfulInferences; // Number of successful inferences
  float averageProcessingTime;    // Average processing time (ms)
  float averageConfidence;        // Average confidence score
  uint32_t lastUpdateTime;        // Last metrics update time
  
  // Memory usage
  uint32_t peakMemoryUsage;   // Peak memory usage (bytes)
  uint32_t currentMemoryUsage;    // Current memory usage (bytes)
  
  // Error tracking
  uint32_t errorCount;        // Total error count
  uint32_t timeoutCount;      // Timeout count
  uint32_t lowConfidenceCount;    // Low confidence count
};

// NovaML class declaration
class NovaML {
public:
  // Initialization and configuration
  static bool initModel(const char* modelPath = nullptr);
  static bool setModelConfig(const ModelConfig& config);
  static bool setFeatureConfig(const FeatureConfig& config);
  static ModelConfig getModelConfig();
  static FeatureConfig getFeatureConfig();
  
  // Model management
  static bool loadModel(const char* modelPath);
  static bool unloadModel();
  static bool isModelLoaded();
  static uint8_t getModelVersion();
  
  // Inference
  static bool infer(const SensorData& data, EmotionResult* result);
  static bool inferAudio(const AudioData& audio, EmotionResult* result);
  static bool inferMotion(const MotionData& motion, EmotionResult* result);
  static bool inferMultiModal(const SensorData& data, EmotionResult* result);
  
  // Feature extraction
  static bool extractFeatures(const SensorData& data, float* features, uint16_t* featureCount);
  static bool extractAudioFeatures(const AudioData& audio, float* features);
  static bool extractMotionFeatures(const MotionData& motion, float* features);
  static bool extractPhysiologicalFeatures(const HeartRateData& hr, float* features);
  
  // Model updates and versioning
  static bool updateModel(const uint8_t* newModel, uint32_t modelSize);
  static bool checkForUpdates();
  static bool rollbackModel();
  
  // Performance monitoring
  static bool healthCheck();
  static ModelMetrics getMetrics();
  static void resetMetrics();
  static bool optimizePerformance();
  
  // Memory management
  static uint32_t getMemoryUsage();
  static uint32_t getPeakMemoryUsage();
  static bool cleanupMemory();
  
  // Utility functions
  static const char* getEmotionLabel(EmotionLabel label);
  static float calculateConfidence(const float* probabilities, uint8_t numClasses);
  static EmotionLabel getTopPrediction(const float* probabilities, uint8_t numClasses);
  
private:
  // TensorFlow Lite Micro components
  static tflite::MicroErrorReporter micro_error_reporter;
  static tflite::ErrorReporter* error_reporter;
  static const tflite::Model* model;
  static tflite::MicroInterpreter* interpreter;
  static TfLiteTensor* input;
  static TfLiteTensor* output;
  
  // Configuration and state
  static ModelConfig modelConfig;
  static FeatureConfig featureConfig;
  static ModelMetrics metrics;
  static bool modelLoaded;
  static bool initialized;
  
  // Memory management
  static uint8_t* tensor_arena;
  static uint32_t tensor_arena_size;
  
  // Internal helper functions
  static bool validateModel(const uint8_t* model_data);
  static bool allocateMemory();
  static void deallocateMemory();
  static bool prepareInput(const float* features, uint16_t featureCount);
  static bool processOutput(EmotionResult* result);
  static void updateMetrics(uint32_t processingTime, float confidence);
  
  // Feature extraction helpers
  static bool computeMFCC(const AudioData& audio, float* mfcc);
  static bool computeSpectralFeatures(const AudioData& audio, float* features);
  static bool computeMotionFeatures(const MotionData& motion, float* features);
  static bool computeHRVFeatures(const HeartRateData& hr, float* features);
  
  // Signal processing utilities
  static void applyWindow(float* data, uint16_t size, const char* windowType);
  static void computeFFT(float* real, float* imag, uint16_t size);
  static float computeRMS(const float* data, uint16_t size);
  static float computeSpectralCentroid(const float* magnitude, uint16_t size, float sampleRate);
};

// Utility functions for emotion label conversion
inline const char* NovaML::getEmotionLabel(EmotionLabel label) {
  static const char* labels[] = {
    "neutral", "happy", "sad", "angry", "fear", "surprise",
    "disgust", "contempt", "engaged", "distracted", "stressed", "relaxed", "unknown"
  };
  return (label < 13) ? labels[label] : "unknown";
}

#endif // NOVA_ML_H 