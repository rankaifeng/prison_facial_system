import cache from '@/utils/cache';
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';

const AuthGuard = ({ children }) => {
  const token = cache.getVal('token');
  const location = useLocation();

  if (!token && location.pathname !== '/login') {
    return <Navigate to="/login" replace />;
  }

  if (token && location.pathname === '/login') {
    return <Navigate to="/" replace />;
  }

  return children;
};

export default AuthGuard;
