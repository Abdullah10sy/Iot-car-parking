import React from 'react';
import { useQuery } from 'react-query';
import { 
  ChartBarIcon, 
  MapIcon, 
  ClockIcon, 
  CurrencyDollarIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

// Services
import { parkingService } from '../../services/parkingService';

// Components
import StatCard from './StatCard';
import OccupancyChart from './OccupancyChart';
import RecentActivity from './RecentActivity';
import QuickActions from './QuickActions';
import LoadingSpinner from '../Common/LoadingSpinner';
import ErrorMessage from '../Common/ErrorMessage';

// Types
import { ParkingSpot, OccupancyStats } from '../../types/parking';

const Dashboard: React.FC = () => {
  // Fetch parking spots data
  const { 
    data: spotsData, 
    isLoading: spotsLoading, 
    error: spotsError 
  } = useQuery('parking-spots', parkingService.getAllSpots, {
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Fetch occupancy analytics
  const { 
    data: analyticsData, 
    isLoading: analyticsLoading 
  } = useQuery('occupancy-analytics', parkingService.getOccupancyAnalytics, {
    refetchInterval: 60000, // Refetch every minute
  });

  if (spotsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (spotsError) {
    return (
      <ErrorMessage 
        message="Failed to load dashboard data" 
        onRetry={() => window.location.reload()} 
      />
    );
  }

  const spots = spotsData?.spots || [];
  const stats = spotsData || {};
  const analytics = analyticsData?.overall || {};

  // Calculate additional metrics
  const occupancyRate = stats.total_count > 0 
    ? ((stats.occupied_count / stats.total_count) * 100).toFixed(1)
    : '0';

  const availabilityRate = stats.total_count > 0 
    ? ((stats.available_count / stats.total_count) * 100).toFixed(1)
    : '0';

  // Get spots with low battery or offline sensors
  const alertSpots = spots.filter((spot: ParkingSpot) => 
    spot.sensor_health?.battery_level < 20 || !spot.sensor_health?.is_online
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Smart Parking Dashboard
            </h1>
            <p className="text-gray-600 mt-1">
              Real-time parking management and analytics
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">Last updated</p>
            <p className="text-sm font-medium text-gray-900">
              {new Date().toLocaleTimeString()}
            </p>
          </div>
        </div>
      </div>

      {/* Alert Banner */}
      {alertSpots.length > 0 && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded-lg">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
            <div className="ml-3">
              <p className="text-sm text-yellow-700">
                <span className="font-medium">{alertSpots.length} sensor(s)</span> require attention 
                (low battery or offline)
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Spots"
          value={stats.total_count || 0}
          icon={MapIcon}
          color="blue"
          subtitle="Parking spaces"
        />
        
        <StatCard
          title="Available"
          value={stats.available_count || 0}
          icon={ChartBarIcon}
          color="green"
          subtitle={`${availabilityRate}% available`}
        />
        
        <StatCard
          title="Occupied"
          value={stats.occupied_count || 0}
          icon={ClockIcon}
          color="red"
          subtitle={`${occupancyRate}% occupied`}
        />
        
        <StatCard
          title="Reserved"
          value={stats.reserved_count || 0}
          icon={CurrencyDollarIcon}
          color="yellow"
          subtitle="Active reservations"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Occupancy Chart */}
        <div className="lg:col-span-2">
          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">
                Occupancy Trends
              </h2>
              <select className="text-sm border-gray-300 rounded-md">
                <option value="24h">Last 24 Hours</option>
                <option value="7d">Last 7 Days</option>
                <option value="30d">Last 30 Days</option>
              </select>
            </div>
            
            {analyticsLoading ? (
              <div className="flex items-center justify-center h-64">
                <LoadingSpinner />
              </div>
            ) : (
              <OccupancyChart data={analyticsData} />
            )}
          </div>
        </div>

        {/* Quick Actions & Recent Activity */}
        <div className="space-y-6">
          <QuickActions />
          <RecentActivity />
        </div>
      </div>

      {/* Level Breakdown */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Occupancy by Level
        </h2>
        
        <div className="space-y-4">
          {analytics.by_level?.map((level: any) => (
            <div key={level.level} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <span className="text-blue-600 font-semibold">{level.level}</span>
                </div>
                <div>
                  <p className="font-medium text-gray-900">Level {level.level}</p>
                  <p className="text-sm text-gray-500">
                    {level.available_spots} of {level.total_spots} available
                  </p>
                </div>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <p className="text-lg font-semibold text-gray-900">
                    {level.occupancy_rate.toFixed(1)}%
                  </p>
                  <p className="text-sm text-gray-500">Occupied</p>
                </div>
                
                <div className="w-24 bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${level.occupancy_rate}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;