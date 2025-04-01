import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext'; // Make sure this import is correct

// Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ProjectView from './pages/ProjectView';
import Review from './pages/Review';

// Components
import ProtectedRoute from './components/auth/ProtectedRoute';
import Loading from './components/shared/Loading';

function App() {
  const [initializing, setInitializing] = useState(true);

  useEffect(() => {
    // Check for authentication state
    const checkAuth = async () => {
      try {
        // Simulate API call to validate token
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // In a real app, you would verify token with your backend
      } catch (error) {
        console.error('Auth check error:', error);
        // Clear invalid auth
        localStorage.removeItem('isLoggedIn');
        localStorage.removeItem('user');
      } finally {
        setInitializing(false);
      }
    };

    checkAuth();
  }, []);

  if (initializing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <Loading message="Initializing application..." />
      </div>
    );
  }

  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          
          {/* Protected routes */}
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/project/:id" 
            element={
              <ProtectedRoute>
                <ProjectView />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/review/:projectId" 
            element={
              <ProtectedRoute>
                <Review />
              </ProtectedRoute>
            } 
          />
          
          {/* Redirect to dashboard if logged in, otherwise to login */}
          <Route 
            path="/" 
            element={
              localStorage.getItem('isLoggedIn') === 'true' ? 
                <Navigate to="/dashboard" replace /> : 
                <Navigate to="/login" replace />
            } 
          />
          
          {/* Catch-all route */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;