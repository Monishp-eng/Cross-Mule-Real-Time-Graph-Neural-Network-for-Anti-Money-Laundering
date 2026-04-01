import { Navigate, Outlet } from 'react-router';

export function ProtectedRoute() {
  const token = localStorage.getItem('auth_token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}
