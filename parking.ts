// Type definitions for the IoT Smart Parking System

export interface ParkingSpot {
  id: string;
  location: string;
  level: string;
  zone: string;
  spot_number?: number;
  is_occupied: boolean;
  is_reserved: boolean;
  is_disabled?: boolean;
  sensor_type: 'ultrasonic' | 'magnetic' | 'camera' | 'infrared';
  coordinates_x?: number;
  coordinates_y?: number;
  hourly_rate: number;
  last_updated?: string;
  created_at?: string;
  status: 'available' | 'occupied' | 'reserved' | 'disabled';
  sensor_health?: SensorHealth;
}

export interface SensorHealth {
  sensor_id: string;
  last_heartbeat?: string;
  last_data_received?: string;
  battery_level?: number;
  signal_strength?: number;
  firmware_version?: string;
  error_count: number;
  last_error?: string;
  last_error_time?: string;
  is_online: boolean;
  maintenance_mode: boolean;
  updated_at?: string;
}

export interface SensorData {
  id: number;
  sensor_id: string;
  timestamp: string;
  occupied: boolean;
  distance_cm?: number;
  magnetic_field?: number;
  battery_level?: number;
  signal_strength?: number;
  temperature?: number;
  humidity?: number;
  firmware_version?: string;
  raw_data?: Record<string, any>;
}

export interface Reservation {
  id: string;
  spot_id: string;
  user_email: string;
  user_phone?: string;
  user_name?: string;
  start_time: string;
  end_time: string;
  duration_hours: number;
  total_amount: number;
  payment_status: 'pending' | 'paid' | 'failed' | 'refunded';
  payment_intent_id?: string;
  payment_method?: string;
  status: 'active' | 'completed' | 'cancelled' | 'expired';
  check_in_time?: string;
  check_out_time?: string;
  notes?: string;
  created_at: string;
  updated_at?: string;
  spot?: ParkingSpot;
}

export interface PaymentTransaction {
  id: number;
  reservation_id: string;
  transaction_id: string;
  amount: number;
  currency: string;
  payment_method?: string;
  status: 'pending' | 'completed' | 'failed' | 'refunded';
  gateway: string;
  gateway_response?: Record<string, any>;
  processed_at?: string;
  created_at: string;
}

export interface OccupancyStats {
  overall: {
    total_spots: number;
    occupied_spots: number;
    reserved_spots: number;
    available_spots: number;
    occupancy_rate: number;
  };
  by_level: LevelStats[];
  timestamp: string;
}

export interface LevelStats {
  level: string;
  total_spots: number;
  occupied_spots: number;
  available_spots: number;
  occupancy_rate: number;
}

export interface DailyOccupancyStats {
  id: number;
  date: string;
  level?: string;
  zone?: string;
  total_spots: number;
  peak_occupancy: number;
  avg_occupancy: number;
  occupancy_rate: number;
  total_revenue: number;
  total_reservations: number;
  created_at: string;
}

export interface HourlyOccupancyStats {
  id: number;
  datetime: string;
  level?: string;
  zone?: string;
  occupied_spots: number;
  total_spots: number;
  occupancy_rate: number;
  created_at: string;
}

export interface SystemEvent {
  id: number;
  event_type: string;
  entity_type?: string;
  entity_id?: string;
  user_id?: string;
  event_data?: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
  timestamp: string;
}

// API Response Types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
  status: number;
}

export interface ParkingSpotsResponse {
  spots: ParkingSpot[];
  total_count: number;
  available_count: number;
  occupied_count: number;
  reserved_count: number;
}

export interface ReservationCreateRequest {
  spot_id: string;
  user_email: string;
  user_phone?: string;
  user_name?: string;
  start_time: string;
  duration_hours: number;
}

export interface ReservationCreateResponse {
  reservation: Reservation;
  client_secret: string; // Stripe payment intent client secret
}

// WebSocket Event Types
export interface SocketEvents {
  spot_status_changed: {
    spot_id: string;
    occupied: boolean;
    timestamp: string;
  };
  spot_reserved: {
    spot_id: string;
    reservation_id: string;
  };
  occupancy_update: OccupancyStats;
  sensor_error: {
    sensor_id: string;
    error_type: string;
    timestamp: string;
  };
  sensor_heartbeat: {
    sensor_id: string;
    status: string;
    timestamp: string;
  };
}

// Filter and Search Types
export interface FilterOptions {
  level?: string;
  zone?: string;
  status?: 'available' | 'occupied' | 'reserved' | 'disabled';
  sensor_type?: 'ultrasonic' | 'magnetic' | 'camera' | 'infrared';
  battery_low?: boolean;
  offline?: boolean;
}

export interface SearchOptions {
  query?: string;
  filters?: FilterOptions;
  sort_by?: 'id' | 'location' | 'level' | 'last_updated';
  sort_order?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

// Chart Data Types
export interface ChartDataPoint {
  x: string | number;
  y: number;
  label?: string;
}

export interface OccupancyChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string;
    borderColor?: string;
    fill?: boolean;
  }[];
}

// Component Props Types
export interface ParkingSpotProps {
  spot: ParkingSpot;
  onClick: (spot: ParkingSpot) => void;
  size?: 'small' | 'medium' | 'large';
  showDetails?: boolean;
}

export interface ReservationFormData {
  spot_id: string;
  user_email: string;
  user_phone: string;
  user_name: string;
  start_time: Date;
  duration_hours: number;
}

// Context Types
export interface ParkingContextType {
  spots: ParkingSpot[];
  loading: boolean;
  error: string | null;
  updateSpotStatus: (spotId: string, updates: Partial<ParkingSpot>) => void;
  refreshSpots: () => Promise<void>;
}

export interface SocketContextType {
  socket: any; // Socket.IO client instance
  connected: boolean;
  connect: () => void;
  disconnect: () => void;
}