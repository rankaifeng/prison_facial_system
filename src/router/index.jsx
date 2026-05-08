import React from 'react';
import Login from '@/pages/login';
import MainLayout from '@/layouts/MainLayout';
import Dashboard from '@/pages/dashboard';
import PrisonerList from '@/pages/prisoners/list';
import PrisonerDetail from '@/pages/prisoners/detail';
import Statistics from '@/pages/statistics';
import ExitRecords from '@/pages/exit-records';
import Permission from '@/pages/permission';

const routes = [
  { path: '/login', element: <Login /> },
  {
    path: '/',
    element: <MainLayout />,
    children: [
      { path: '/dashboard', element: <Dashboard /> },
      { path: '/prisoners', element: <PrisonerList /> },
      { path: '/prisoners/:id', element: <PrisonerDetail /> },
      { path: '/statistics', element: <Statistics /> },
      // { path: '/exit-records', element: <ExitRecords /> },
      { path: '/permission', element: <Permission /> },
    ],
  },
  { path: '*', element: <div>404 Not Found</div> }
];

export default routes;
