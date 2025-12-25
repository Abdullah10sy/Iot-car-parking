import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';
import { loadStripe } from '@stripe/stripe-js';
import { Elements } from '@stripe/react-stripe-js';

// Components
import Layout from './components/Layout/Layout';
import Dashboard from './components/Dashboard/Dashboard';
import ParkingMap from './components/ParkingMap/ParkingMap';
import Reservations from './components/Reservations/Reservations';
import Analytics from './components/Analytics/Analytics';
import SpotDetails from './components/ParkingMap/SpotDetails';

// Providers
import { ParkingProvider } from './context/ParkingContext';
import { SocketProvider } from './context/SocketContext';

// Initialize Stripe
const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || '');

// Initialize React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30000, // 30 seconds
    },
  },
});

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <Elements stripe={stripePromise}>
        <ParkingProvider>
          <SocketProvider>
            <Router>
              <div className="min-h-screen bg-gray-50">
                <Layout>
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/parking-map" element={<ParkingMap />} />
                    <Route path="/spot/:spotId" element={<SpotDetails />} />
                    <Route path="/reservations" element={<Reservations />} />
                    <Route path="/analytics" element={<Analytics />} />
                  </Routes>
                </Layout>
                
                {/* Toast notifications */}
                <Toaster
                  position="top-right"
                  toastOptions={{
                    duration: 4000,
                    style: {
                      background: '#363636',
                      color: '#fff',
                    },
                    success: {
                      duration: 3000,
                      iconTheme: {
                        primary: '#10B981',
                        secondary: '#fff',
                      },
                    },
                    error: {
                      duration: 5000,
                      iconTheme: {
                        primary: '#EF4444',
                        secondary: '#fff',
                      },
                    },
                  }}
                />
              </div>
            </Router>
          </SocketProvider>
        </ParkingProvider>
      </Elements>
    </QueryClientProvider>
  );
};

export default App;