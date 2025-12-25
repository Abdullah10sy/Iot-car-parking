import React, { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import { useNavigate } from 'react-router-dom';
import { 
  MapIcon, 
  FunnelIcon, 
  MagnifyingGlassIcon,
  ViewColumnsIcon,
  Squares2X2Icon
} from '@heroicons/react/24/outline';

// Services
import { parkingService } from '../../services/parkingService';

// Components
import ParkingSpot from './ParkingSpot';
import FilterPanel from './FilterPanel';
import SearchBar from './SearchBar';
import LoadingSpinner from '../Common/LoadingSpinner';
import ErrorMessage from '../Common/ErrorMessage';

// Hooks
import { useParkingContext } from '../../context/ParkingContext';
import { useSocket } from '../../context/SocketContext';

// Types
import { ParkingSpot as ParkingSpotType } from '../../types/parking';

type ViewMode = 'grid' | 'list';
type FilterOptions = {
  level: string;
  zone: string;
  status: string;
  sensorType: string;
};

const ParkingMap: React.FC = () => {
  const navigate = useNavigate();
  const { spots, updateSpotStatus } = useParkingContext();
  const { socket } = useSocket();

  // Local state
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [showFilters, setShowFilters] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState<FilterOptions>({
    level: '',
    zone: '',
    status: '',
    sensorType: ''
  });

  // Fetch parking spots
  const { 
    data: spotsData, 
    isLoading, 
    error,
    refetch 
  } = useQuery('parking-spots', parkingService.getAllSpots, {
    refetchInterval: 30000,
  });

  // Socket event listeners
  useEffect(() => {
    if (!socket) return;

    const handleSpotStatusChanged = (data: any) => {
      updateSpotStatus(data.spot_id, {
        is_occupied: data.occupied,
        last_updated: data.timestamp
      });
    };

    const handleSpotReserved = (data: any) => {
      updateSpotStatus(data.spot_id, {
        is_reserved: true
      });
    };

    socket.on('spot_status_changed', handleSpotStatusChanged);
    socket.on('spot_reserved', handleSpotReserved);

    return () => {
      socket.off('spot_status_changed', handleSpotStatusChanged);
      socket.off('spot_reserved', handleSpotReserved);
    };
  }, [socket, updateSpotStatus]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <ErrorMessage 
        message="Failed to load parking map" 
        onRetry={refetch} 
      />
    );
  }

  const allSpots = spotsData?.spots || [];

  // Filter and search spots
  const filteredSpots = allSpots.filter((spot: ParkingSpotType) => {
    // Search filter
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      const matchesSearch = 
        spot.id.toLowerCase().includes(searchLower) ||
        spot.location.toLowerCase().includes(searchLower) ||
        spot.level.toLowerCase().includes(searchLower) ||
        spot.zone.toLowerCase().includes(searchLower);
      
      if (!matchesSearch) return false;
    }

    // Level filter
    if (filters.level && spot.level !== filters.level) return false;

    // Zone filter
    if (filters.zone && spot.zone !== filters.zone) return false;

    // Status filter
    if (filters.status) {
      const status = spot.is_occupied ? 'occupied' : 
                    spot.is_reserved ? 'reserved' : 'available';
      if (status !== filters.status) return false;
    }

    // Sensor type filter
    if (filters.sensorType && spot.sensor_type !== filters.sensorType) return false;

    return true;
  });

  // Group spots by level and zone for grid view
  const groupedSpots = filteredSpots.reduce((acc: any, spot: ParkingSpotType) => {
    const key = `${spot.level}-${spot.zone}`;
    if (!acc[key]) {
      acc[key] = {
        level: spot.level,
        zone: spot.zone,
        spots: []
      };
    }
    acc[key].spots.push(spot);
    return acc;
  }, {});

  const handleSpotClick = (spot: ParkingSpotType) => {
    navigate(`/spot/${spot.id}`);
  };

  const handleFilterChange = (newFilters: Partial<FilterOptions>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  };

  const clearFilters = () => {
    setFilters({
      level: '',
      zone: '',
      status: '',
      sensorType: ''
    });
    setSearchTerm('');
  };

  const getStatusCounts = () => {
    const available = filteredSpots.filter(s => !s.is_occupied && !s.is_reserved).length;
    const occupied = filteredSpots.filter(s => s.is_occupied).length;
    const reserved = filteredSpots.filter(s => s.is_reserved).length;
    
    return { available, occupied, reserved, total: filteredSpots.length };
  };

  const statusCounts = getStatusCounts();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center space-x-3">
            <MapIcon className="h-8 w-8 text-blue-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Parking Map</h1>
              <p className="text-gray-600">
                {statusCounts.total} spots • {statusCounts.available} available
              </p>
            </div>
          </div>

          <div className="mt-4 sm:mt-0 flex items-center space-x-3">
            {/* View Mode Toggle */}
            <div className="flex rounded-lg border border-gray-300">
              <button
                onClick={() => setViewMode('grid')}
                className={`px-3 py-2 text-sm font-medium rounded-l-lg ${
                  viewMode === 'grid'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                <Squares2X2Icon className="h-4 w-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`px-3 py-2 text-sm font-medium rounded-r-lg ${
                  viewMode === 'list'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                <ViewColumnsIcon className="h-4 w-4" />
              </button>
            </div>

            {/* Filter Toggle */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`px-4 py-2 text-sm font-medium rounded-lg border ${
                showFilters
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              <FunnelIcon className="h-4 w-4 mr-2 inline" />
              Filters
            </button>
          </div>
        </div>

        {/* Status Summary */}
        <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{statusCounts.available}</div>
            <div className="text-sm text-green-700">Available</div>
          </div>
          <div className="text-center p-3 bg-red-50 rounded-lg">
            <div className="text-2xl font-bold text-red-600">{statusCounts.occupied}</div>
            <div className="text-sm text-red-700">Occupied</div>
          </div>
          <div className="text-center p-3 bg-yellow-50 rounded-lg">
            <div className="text-2xl font-bold text-yellow-600">{statusCounts.reserved}</div>
            <div className="text-sm text-yellow-700">Reserved</div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-600">{statusCounts.total}</div>
            <div className="text-sm text-gray-700">Total</div>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="space-y-4">
        <SearchBar
          value={searchTerm}
          onChange={setSearchTerm}
          placeholder="Search by spot ID, location, level, or zone..."
        />

        {showFilters && (
          <FilterPanel
            filters={filters}
            onFilterChange={handleFilterChange}
            onClearFilters={clearFilters}
            spots={allSpots}
          />
        )}
      </div>

      {/* Parking Spots Display */}
      {viewMode === 'grid' ? (
        <div className="space-y-6">
          {Object.values(groupedSpots).map((group: any) => (
            <div key={`${group.level}-${group.zone}`} className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Level {group.level} - Zone {group.zone}
              </h3>
              
              <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-3">
                {group.spots.map((spot: ParkingSpotType) => (
                  <ParkingSpot
                    key={spot.id}
                    spot={spot}
                    onClick={() => handleSpotClick(spot)}
                    size="small"
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Parking Spots List</h3>
          </div>
          
          <div className="divide-y divide-gray-200">
            {filteredSpots.map((spot: ParkingSpotType) => (
              <div
                key={spot.id}
                onClick={() => handleSpotClick(spot)}
                className="px-6 py-4 hover:bg-gray-50 cursor-pointer transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <ParkingSpot spot={spot} size="small" onClick={() => {}} />
                    <div>
                      <p className="font-medium text-gray-900">{spot.id}</p>
                      <p className="text-sm text-gray-500">{spot.location}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">
                        Level {spot.level} - Zone {spot.zone}
                      </p>
                      <p className="text-sm text-gray-500">
                        {spot.sensor_type} sensor
                      </p>
                    </div>
                    
                    <div className="text-right">
                      <p className="text-sm text-gray-500">Last updated</p>
                      <p className="text-sm font-medium text-gray-900">
                        {spot.last_updated 
                          ? new Date(spot.last_updated).toLocaleTimeString()
                          : 'Never'
                        }
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {filteredSpots.length === 0 && (
        <div className="text-center py-12">
          <MagnifyingGlassIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No spots found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Try adjusting your search or filter criteria.
          </p>
          <div className="mt-6">
            <button
              onClick={clearFilters}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
            >
              Clear filters
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ParkingMap;