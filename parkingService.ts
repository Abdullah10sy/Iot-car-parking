import axios from 'axios';
import { 
  ParkingSpot, 
  ParkingSpotsResponse, 
  Reservation, 
  ReservationCreateRequest, 
  ReservationCreateResponse,
  OccupancyStats,
  SensorData,
  ApiResponse 
} from '../types/parking';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth tokens (if needed)
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export class ParkingService {
  // Health check
  async healthCheck(): Promise<any> {
    const response = await api.get('/api/health');
    return response.data;
  }

  // Parking Spots
  async getAllSpots(): Promise<ParkingSpotsResponse> {
    const response = await api.get('/api/spots');
    return response.data;
  }

  async getSpot(spotId: string): Promise<{ spot: ParkingSpot; recent_sensor_data: SensorData[] }> {
    const response = await api.get(`/api/spots/${spotId}`);
    return response.data;
  }

  async getAvailableSpots(level?: string, zone?: string): Promise<{ available_spots: ParkingSpot[]; count: number }> {
    const params = new URLSearchParams();
    if (level) params.append('level', level);
    if (zone) params.append('zone', zone);
    
    const response = await api.get(`/api/spots/available?${params.toString()}`);
    return response.data;
  }

  async createSpot(spotData: Partial<ParkingSpot>): Promise<ParkingSpot> {
    const response = await api.post('/api/spots', spotData);
    return response.data;
  }

  async updateSpot(spotId: string, updates: Partial<ParkingSpot>): Promise<ParkingSpot> {
    const response = await api.put(`/api/spots/${spotId}`, updates);
    return response.data;
  }

  async deleteSpot(spotId: string): Promise<void> {
    await api.delete(`/api/spots/${spotId}`);
  }

  // Sensor Data
  async sendSensorData(sensorData: any): Promise<any> {
    const response = await api.post('/api/sensor-data', sensorData);
    return response.data;
  }

  async getSensorHistory(sensorId: string, limit: number = 100): Promise<SensorData[]> {
    const response = await api.get(`/api/sensors/${sensorId}/history?limit=${limit}`);
    return response.data;
  }

  // Reservations
  async createReservation(reservationData: ReservationCreateRequest): Promise<ReservationCreateResponse> {
    const response = await api.post('/api/reservations', reservationData);
    return response.data;
  }

  async getReservation(reservationId: string): Promise<{ reservation: Reservation }> {
    const response = await api.get(`/api/reservations/${reservationId}`);
    return response.data;
  }

  async getUserReservations(userEmail: string): Promise<Reservation[]> {
    const response = await api.get(`/api/reservations?user_email=${userEmail}`);
    return response.data;
  }

  async updateReservation(reservationId: string, updates: Partial<Reservation>): Promise<Reservation> {
    const response = await api.put(`/api/reservations/${reservationId}`, updates);
    return response.data;
  }

  async cancelReservation(reservationId: string): Promise<void> {
    await api.delete(`/api/reservations/${reservationId}`);
  }

  // Analytics
  async getOccupancyAnalytics(): Promise<OccupancyStats> {
    const response = await api.get('/api/analytics/occupancy');
    return response.data;
  }

  async getOccupancyTrends(period: '24h' | '7d' | '30d' = '24h'): Promise<any> {
    const response = await api.get(`/api/analytics/trends?period=${period}`);
    return response.data;
  }

  async getRevenueAnalytics(startDate?: string, endDate?: string): Promise<any> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    const response = await api.get(`/api/analytics/revenue?${params.toString()}`);
    return response.data;
  }

  async getPredictions(): Promise<any> {
    const response = await api.get('/api/analytics/predictions');
    return response.data;
  }

  // Payments
  async createPaymentIntent(amount: number, reservationId: string): Promise<{ client_secret: string }> {
    const response = await api.post('/api/payments/create-intent', {
      amount,
      reservation_id: reservationId,
    });
    return response.data;
  }

  async confirmPayment(paymentIntentId: string): Promise<any> {
    const response = await api.post('/api/payments/confirm', {
      payment_intent_id: paymentIntentId,
    });
    return response.data;
  }

  // System Management
  async getSystemEvents(limit: number = 50): Promise<any[]> {
    const response = await api.get(`/api/system/events?limit=${limit}`);
    return response.data;
  }

  async getSensorHealth(): Promise<any[]> {
    const response = await api.get('/api/system/sensor-health');
    return response.data;
  }

  async updateSensorConfig(sensorId: string, config: any): Promise<void> {
    await api.put(`/api/sensors/${sensorId}/config`, config);
  }

  // Utility methods
  async searchSpots(query: string, filters?: any): Promise<ParkingSpot[]> {
    const params = new URLSearchParams();
    params.append('q', query);
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, String(value));
      });
    }
    
    const response = await api.get(`/api/spots/search?${params.toString()}`);
    return response.data.spots;
  }

  async getStatistics(): Promise<any> {
    const response = await api.get('/api/statistics');
    return response.data;
  }

  // Batch operations
  async bulkUpdateSpots(updates: { spotId: string; data: Partial<ParkingSpot> }[]): Promise<void> {
    await api.post('/api/spots/bulk-update', { updates });
  }

  async exportData(format: 'csv' | 'json' = 'json', type: 'spots' | 'reservations' | 'analytics' = 'spots'): Promise<Blob> {
    const response = await api.get(`/api/export/${type}?format=${format}`, {
      responseType: 'blob',
    });
    return response.data;
  }
}

// Create singleton instance
export const parkingService = new ParkingService();

// Export individual methods for convenience
export const {
  getAllSpots,
  getSpot,
  getAvailableSpots,
  createReservation,
  getReservation,
  getOccupancyAnalytics,
  createPaymentIntent,
  confirmPayment,
} = parkingService;