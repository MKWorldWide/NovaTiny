/**
 * Pioneer Grid Dashboard - Main Page
 * 
 * Real-time dashboard displaying emotion data from NovaTiny agents
 * in a responsive grid layout with live updates via WebSocket.
 * 
 * Features:
 * - Real-time emotion pulse tiles
 * - Live WebSocket connection to NovaSanctum
 * - Responsive grid layout
 * - Alert system for high-intensity emotions
 * - Device filtering and search
 * - Analytics overview
 * 
 * @author Nova Development Team
 * @version 1.0.0
 * @date 2024
 */

import React, { useEffect, useState } from 'react';
import { io, Socket } from 'socket.io-client';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, 
  Filter, 
  Settings, 
  BarChart3, 
  Users, 
  Activity,
  AlertTriangle,
  Wifi,
  WifiOff
} from 'lucide-react';
import { EmotionPulseTile, EmotionData } from '@/components/EmotionPulseTile';
import { toast } from 'react-hot-toast';

// Dashboard state interface
interface DashboardState {
  devices: Map<string, EmotionData>;
  isConnected: boolean;
  totalDevices: number;
  activeDevices: number;
  alerts: Array<{
    id: string;
    deviceId: string;
    emotion: string;
    intensity: number;
    timestamp: Date;
  }>;
}

// Analytics data interface
interface AnalyticsData {
  totalEmotions: number;
  emotionDistribution: Record<string, number>;
  averageIntensity: number;
  averageConfidence: number;
  activeRegions: number;
}

const PioneerGrid: React.FC = () => {
  const [state, setState] = useState<DashboardState>({
    devices: new Map(),
    isConnected: false,
    totalDevices: 0,
    activeDevices: 0,
    alerts: []
  });

  const [analytics, setAnalytics] = useState<AnalyticsData>({
    totalEmotions: 0,
    emotionDistribution: {},
    averageIntensity: 0,
    averageConfidence: 0,
    activeRegions: 0
  });

  const [searchTerm, setSearchTerm] = useState('');
  const [filterEmotion, setFilterEmotion] = useState<string>('all');
  const [socket, setSocket] = useState<Socket | null>(null);

  // Initialize WebSocket connection
  useEffect(() => {
    const newSocket = io(process.env.NEXT_PUBLIC_NOVA_SANCTUM_URL || 'http://localhost:5000', {
      transports: ['websocket'],
      autoConnect: true,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5
    });

    newSocket.on('connect', () => {
      console.log('Connected to NovaSanctum');
      setState(prev => ({ ...prev, isConnected: true }));
      toast.success('Connected to Nova network');
    });

    newSocket.on('disconnect', () => {
      console.log('Disconnected from NovaSanctum');
      setState(prev => ({ ...prev, isConnected: false }));
      toast.error('Disconnected from Nova network');
    });

    newSocket.on('emotion_data', (data: EmotionData) => {
      handleEmotionData(data);
    });

    newSocket.on('connect_error', (error) => {
      console.error('Connection error:', error);
      toast.error('Failed to connect to Nova network');
    });

    setSocket(newSocket);

    return () => {
      newSocket.close();
    };
  }, []);

  // Handle incoming emotion data
  const handleEmotionData = (data: EmotionData) => {
    setState(prev => {
      const newDevices = new Map(prev.devices);
      newDevices.set(data.device_id, data);

      // Update analytics
      const allEmotions = Array.from(newDevices.values());
      const newAnalytics = calculateAnalytics(allEmotions);

      return {
        ...prev,
        devices: newDevices,
        totalDevices: newDevices.size,
        activeDevices: allEmotions.filter(d => 
          Date.now() - new Date(d.received_at).getTime() < 5 * 60 * 1000
        ).length
      };
    });

    setAnalytics(prev => ({
      ...prev,
      ...calculateAnalytics(Array.from(state.devices.values()))
    }));
  };

  // Calculate analytics from emotion data
  const calculateAnalytics = (emotions: EmotionData[]): Partial<AnalyticsData> => {
    if (emotions.length === 0) return {};

    const distribution: Record<string, number> = {};
    let totalIntensity = 0;
    let totalConfidence = 0;

    emotions.forEach(emotion => {
      distribution[emotion.emotion_label] = (distribution[emotion.emotion_label] || 0) + 1;
      totalIntensity += emotion.emotion_intensity;
      totalConfidence += emotion.emotion_confidence;
    });

    return {
      totalEmotions: emotions.length,
      emotionDistribution: distribution,
      averageIntensity: totalIntensity / emotions.length,
      averageConfidence: totalConfidence / emotions.length,
      activeRegions: new Set(emotions.map(e => e.edge_node_id)).size
    };
  };

  // Handle alert from emotion tile
  const handleAlert = (deviceId: string, emotion: string, intensity: number) => {
    const alert = {
      id: `${deviceId}-${Date.now()}`,
      deviceId,
      emotion,
      intensity,
      timestamp: new Date()
    };

    setState(prev => ({
      ...prev,
      alerts: [alert, ...prev.alerts.slice(0, 9)] // Keep last 10 alerts
    }));

    toast.error(`High intensity ${emotion} detected on ${deviceId}`, {
      duration: 5000,
      icon: '⚠️'
    });
  };

  // Filter devices based on search and emotion filter
  const filteredDevices = Array.from(state.devices.values()).filter(device => {
    const matchesSearch = device.device_id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesEmotion = filterEmotion === 'all' || device.emotion_label === filterEmotion;
    return matchesSearch && matchesEmotion;
  });

  // Check if device is online (active in last 5 minutes)
  const isDeviceOnline = (device: EmotionData) => {
    const lastSeen = new Date(device.received_at);
    return Date.now() - lastSeen.getTime() < 5 * 60 * 1000;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">Nova Pioneer Grid</h1>
              <div className="flex items-center space-x-2">
                {state.isConnected ? (
                  <Wifi className="w-5 h-5 text-green-500" />
                ) : (
                  <WifiOff className="w-5 h-5 text-red-500" />
                )}
                <span className={`text-sm ${state.isConnected ? 'text-green-600' : 'text-red-600'}`}>
                  {state.isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <Users className="w-4 h-4" />
                <span>{state.totalDevices} devices</span>
              </div>
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <Activity className="w-4 h-4" />
                <span>{state.activeDevices} active</span>
              </div>
              <button className="p-2 text-gray-400 hover:text-gray-600">
                <Settings className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Analytics Overview */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white p-4 rounded-lg shadow-sm"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Emotions</p>
                <p className="text-2xl font-bold text-gray-900">{analytics.totalEmotions}</p>
              </div>
              <BarChart3 className="w-8 h-8 text-blue-500" />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white p-4 rounded-lg shadow-sm"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Avg Intensity</p>
                <p className="text-2xl font-bold text-gray-900">
                  {Math.round(analytics.averageIntensity * 100)}%
                </p>
              </div>
              <Activity className="w-8 h-8 text-green-500" />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white p-4 rounded-lg shadow-sm"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Avg Confidence</p>
                <p className="text-2xl font-bold text-gray-900">
                  {Math.round(analytics.averageConfidence * 100)}%
                </p>
              </div>
              <BarChart3 className="w-8 h-8 text-purple-500" />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white p-4 rounded-lg shadow-sm"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Regions</p>
                <p className="text-2xl font-bold text-gray-900">{analytics.activeRegions}</p>
              </div>
              <Users className="w-8 h-8 text-orange-500" />
            </div>
          </motion.div>
        </div>

        {/* Filters and Search */}
        <div className="bg-white p-4 rounded-lg shadow-sm mb-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search devices..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <select
                value={filterEmotion}
                onChange={(e) => setFilterEmotion(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Emotions</option>
                <option value="happy">Happy</option>
                <option value="sad">Sad</option>
                <option value="angry">Angry</option>
                <option value="fear">Fear</option>
                <option value="surprise">Surprise</option>
                <option value="neutral">Neutral</option>
                <option value="stressed">Stressed</option>
                <option value="relaxed">Relaxed</option>
              </select>
            </div>
          </div>
        </div>

        {/* Emotion Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <AnimatePresence>
            {filteredDevices.map((device) => (
              <motion.div
                key={device.device_id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.2 }}
              >
                <EmotionPulseTile
                  device={device.device_id}
                  emotion={device}
                  lastSeen={new Date(device.received_at)}
                  isOnline={isDeviceOnline(device)}
                  onAlert={handleAlert}
                />
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Empty State */}
        {filteredDevices.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-12"
          >
            <div className="text-gray-400">
              <Activity className="w-16 h-16 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No devices found
              </h3>
              <p className="text-gray-500">
                {state.devices.size === 0 
                  ? 'Waiting for NovaTiny agents to connect...'
                  : 'No devices match your current filters'
                }
              </p>
            </div>
          </motion.div>
        )}
      </div>

      {/* Alerts Panel */}
      {state.alerts.length > 0 && (
        <div className="fixed bottom-4 right-4 w-80 bg-white rounded-lg shadow-lg border">
          <div className="p-4 border-b">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              <h3 className="font-semibold text-gray-900">Recent Alerts</h3>
            </div>
          </div>
          <div className="max-h-64 overflow-y-auto">
            {state.alerts.map((alert) => (
              <div key={alert.id} className="p-3 border-b last:border-b-0">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {alert.deviceId}
                    </p>
                    <p className="text-xs text-gray-500 capitalize">
                      {alert.emotion} ({Math.round(alert.intensity * 100)}%)
                    </p>
                  </div>
                  <span className="text-xs text-gray-400">
                    {alert.timestamp.toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PioneerGrid; 