/**
 * EmotionPulseTile.tsx - Individual NovaTiny Agent Emotion Display
 * 
 * Displays real-time emotion data from individual NovaTiny agents in a
 * visually appealing tile format with pulse animations and status indicators.
 * 
 * Features:
 * - Real-time emotion visualization with color coding
 * - Pulse animation based on emotion intensity
 * - Battery level and signal strength indicators
 * - Last seen timestamp with relative time
 * - Alert system for high-intensity emotions
 * - Responsive design for different screen sizes
 * 
 * @author Nova Development Team
 * @version 1.0.0
 * @date 2024
 */

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { formatDistanceToNow } from 'date-fns';
import { 
  Battery, 
  Signal, 
  AlertTriangle, 
  Heart, 
  Activity,
  Clock,
  Wifi,
  WifiOff
} from 'lucide-react';
import { cn } from '@/lib/utils';

// Emotion data interface
export interface EmotionData {
  device_id: string;
  timestamp: number;
  emotion_label: string;
  emotion_confidence: number;
  emotion_intensity: number;
  battery_level: number;
  signal_strength: number;
  edge_node_id: string;
  received_at: string;
}

// Component props
interface EmotionPulseTileProps {
  device: string;
  emotion: EmotionData;
  lastSeen: Date;
  isOnline: boolean;
  onAlert?: (deviceId: string, emotion: string, intensity: number) => void;
  className?: string;
}

// Emotion color mapping
const emotionColors = {
  neutral: { bg: 'bg-gray-100', text: 'text-gray-700', pulse: 'bg-gray-400' },
  happy: { bg: 'bg-green-100', text: 'text-green-700', pulse: 'bg-green-400' },
  sad: { bg: 'bg-blue-100', text: 'text-blue-700', pulse: 'bg-blue-400' },
  angry: { bg: 'bg-red-100', text: 'text-red-700', pulse: 'bg-red-400' },
  fear: { bg: 'bg-purple-100', text: 'text-purple-700', pulse: 'bg-purple-400' },
  surprise: { bg: 'bg-yellow-100', text: 'text-yellow-700', pulse: 'bg-yellow-400' },
  disgust: { bg: 'bg-orange-100', text: 'text-orange-700', pulse: 'bg-orange-400' },
  contempt: { bg: 'bg-pink-100', text: 'text-pink-700', pulse: 'bg-pink-400' },
  engaged: { bg: 'bg-emerald-100', text: 'text-emerald-700', pulse: 'bg-emerald-400' },
  distracted: { bg: 'bg-amber-100', text: 'text-amber-700', pulse: 'bg-amber-400' },
  stressed: { bg: 'bg-rose-100', text: 'text-rose-700', pulse: 'bg-rose-400' },
  relaxed: { bg: 'bg-teal-100', text: 'text-teal-700', pulse: 'bg-teal-400' }
};

// Battery level indicators
const getBatteryIcon = (level: number) => {
  if (level > 0.8) return <Battery className="w-4 h-4 text-green-500" />;
  if (level > 0.4) return <Battery className="w-4 h-4 text-yellow-500" />;
  return <Battery className="w-4 h-4 text-red-500" />;
};

// Signal strength indicators
const getSignalIcon = (strength: number, isOnline: boolean) => {
  if (!isOnline) return <WifiOff className="w-4 h-4 text-red-500" />;
  
  if (strength > -50) return <Wifi className="w-4 h-4 text-green-500" />;
  if (strength > -70) return <Wifi className="w-4 h-4 text-yellow-500" />;
  return <Wifi className="w-4 h-4 text-red-500" />;
};

export const EmotionPulseTile: React.FC<EmotionPulseTileProps> = ({
  device,
  emotion,
  lastSeen,
  isOnline,
  onAlert,
  className
}) => {
  const [timeAgo, setTimeAgo] = useState<string>('');
  const [showAlert, setShowAlert] = useState<boolean>(false);

  // Update time ago every minute
  useEffect(() => {
    const updateTimeAgo = () => {
      setTimeAgo(formatDistanceToNow(lastSeen, { addSuffix: true }));
    };
    
    updateTimeAgo();
    const interval = setInterval(updateTimeAgo, 60000);
    
    return () => clearInterval(interval);
  }, [lastSeen]);

  // Check for high-intensity emotions and trigger alerts
  useEffect(() => {
    const isHighIntensity = emotion.emotion_intensity > 0.8;
    const isAlertEmotion = ['angry', 'fear', 'stressed'].includes(emotion.emotion_label);
    
    if (isHighIntensity && isAlertEmotion && onAlert) {
      setShowAlert(true);
      onAlert(device, emotion.emotion_label, emotion.emotion_intensity);
      
      // Clear alert after 5 seconds
      setTimeout(() => setShowAlert(false), 5000);
    }
  }, [emotion, device, onAlert]);

  // Get emotion styling
  const emotionStyle = emotionColors[emotion.emotion_label as keyof typeof emotionColors] || emotionColors.neutral;

  // Calculate pulse animation duration based on intensity
  const pulseDuration = Math.max(0.5, 2 - emotion.emotion_intensity);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className={cn(
        'relative p-4 rounded-lg border shadow-sm transition-all duration-300',
        emotionStyle.bg,
        emotionStyle.text,
        'hover:shadow-md hover:scale-105',
        showAlert && 'ring-2 ring-red-500 ring-opacity-50',
        className
      )}
    >
      {/* Alert indicator */}
      <AnimatePresence>
        {showAlert && (
          <motion.div
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0 }}
            className="absolute -top-2 -right-2 z-10"
          >
            <AlertTriangle className="w-6 h-6 text-red-500 animate-pulse" />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Pulse animation */}
      <div className="relative">
        <motion.div
          animate={{
            scale: [1, 1.1, 1],
            opacity: [0.7, 0.3, 0.7]
          }}
          transition={{
            duration: pulseDuration,
            repeat: Infinity,
            ease: "easeInOut"
          }}
          className={cn(
            'absolute inset-0 rounded-lg',
            emotionStyle.pulse,
            'opacity-30'
          )}
        />
      </div>

      {/* Device header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-sm truncate">{device}</h3>
        <div className="flex items-center space-x-1">
          {getBatteryIcon(emotion.battery_level)}
          {getSignalIcon(emotion.signal_strength, isOnline)}
        </div>
      </div>

      {/* Emotion display */}
      <div className="mb-3">
        <div className="flex items-center justify-between">
          <span className="text-lg font-bold capitalize">
            {emotion.emotion_label}
          </span>
          <div className="flex items-center space-x-1">
            <Heart className="w-4 h-4" />
            <span className="text-sm font-medium">
              {Math.round(emotion.emotion_intensity * 100)}%
            </span>
          </div>
        </div>
        
        {/* Confidence indicator */}
        <div className="mt-1">
          <div className="flex items-center justify-between text-xs text-gray-600">
            <span>Confidence</span>
            <span>{Math.round(emotion.emotion_confidence * 100)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-1 mt-1">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${emotion.emotion_confidence * 100}%` }}
              transition={{ duration: 0.5 }}
              className="bg-current h-1 rounded-full"
            />
          </div>
        </div>
      </div>

      {/* Status indicators */}
      <div className="flex items-center justify-between text-xs text-gray-600">
        <div className="flex items-center space-x-1">
          <Clock className="w-3 h-3" />
          <span>{timeAgo}</span>
        </div>
        
        <div className="flex items-center space-x-1">
          <Activity className="w-3 h-3" />
          <span className={cn(
            isOnline ? 'text-green-600' : 'text-red-600'
          )}>
            {isOnline ? 'Online' : 'Offline'}
          </span>
        </div>
      </div>

      {/* Battery and signal details */}
      <div className="mt-2 pt-2 border-t border-gray-200">
        <div className="flex items-center justify-between text-xs">
          <span>Battery: {Math.round(emotion.battery_level * 100)}%</span>
          <span>Signal: {emotion.signal_strength} dBm</span>
        </div>
      </div>
    </motion.div>
  );
};

export default EmotionPulseTile; 