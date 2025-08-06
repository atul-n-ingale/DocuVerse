import React, { useState, useEffect } from 'react';
import { Activity, Server, Database, Zap, ExternalLink } from 'lucide-react';

const SystemStatus = () => {
  const [status, setStatus] = useState({
    api: 'unknown',
    flower: 'unknown',
    mongodb: 'unknown',
    redis: 'unknown',
  });

  useEffect(() => {
    const checkStatus = async () => {
      const newStatus = { ...status };

      // Check API status
      try {
        const response = await fetch('http://localhost:8000/health');
        newStatus.api = response.ok ? 'online' : 'error';
      } catch (error) {
        newStatus.api = 'offline';
      }

      // Check Flower status
      try {
        const response = await fetch('http://localhost:5555/api/workers');
        newStatus.flower = response.ok ? 'online' : 'error';
      } catch (error) {
        newStatus.flower = 'offline';
      }

      // Check MongoDB (via API)
      try {
        const response = await fetch('http://localhost:8000/api/documents');
        newStatus.mongodb = response.ok ? 'online' : 'error';
      } catch (error) {
        newStatus.mongodb = 'offline';
      }

      // Check Redis (via API health)
      try {
        const response = await fetch('http://localhost:8000/health');
        newStatus.redis = response.ok ? 'online' : 'error';
      } catch (error) {
        newStatus.redis = 'offline';
      }

      setStatus(newStatus);
    };

    checkStatus();
    const interval = setInterval(checkStatus, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = status => {
    switch (status) {
      case 'online':
        return 'text-green-600 bg-green-100';
      case 'offline':
        return 'text-red-600 bg-red-100';
      case 'error':
        return 'text-yellow-600 bg-yellow-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = status => {
    switch (status) {
      case 'online':
        return <Activity className="w-4 h-4" />;
      case 'offline':
        return <Server className="w-4 h-4" />;
      case 'error':
        return <Zap className="w-4 h-4" />;
      default:
        return <Server className="w-4 h-4" />;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">System Status</h3>
        <a
          href="http://localhost:5555"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center text-sm text-blue-600 hover:text-blue-800"
        >
          <ExternalLink className="w-4 h-4 mr-1" />
          Flower Monitor
        </a>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center">
            <Server className="w-5 h-5 text-gray-400 mr-2" />
            <span className="text-sm font-medium text-gray-700">
              API Server
            </span>
          </div>
          <span
            className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(status.api)}`}
          >
            {getStatusIcon(status.api)}
            <span className="ml-1 capitalize">{status.api}</span>
          </span>
        </div>

        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center">
            <Activity className="w-5 h-5 text-gray-400 mr-2" />
            <span className="text-sm font-medium text-gray-700">
              Flower Monitor
            </span>
          </div>
          <span
            className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(status.flower)}`}
          >
            {getStatusIcon(status.flower)}
            <span className="ml-1 capitalize">{status.flower}</span>
          </span>
        </div>

        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center">
            <Database className="w-5 h-5 text-gray-400 mr-2" />
            <span className="text-sm font-medium text-gray-700">MongoDB</span>
          </div>
          <span
            className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(status.mongodb)}`}
          >
            {getStatusIcon(status.mongodb)}
            <span className="ml-1 capitalize">{status.mongodb}</span>
          </span>
        </div>

        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center">
            <Zap className="w-5 h-5 text-gray-400 mr-2" />
            <span className="text-sm font-medium text-gray-700">Redis</span>
          </div>
          <span
            className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(status.redis)}`}
          >
            {getStatusIcon(status.redis)}
            <span className="ml-1 capitalize">{status.redis}</span>
          </span>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          Status updates every 30 seconds. Click "Flower Monitor" for detailed
          task monitoring.
        </p>
      </div>
    </div>
  );
};

export default SystemStatus;
