import React from 'react';
import { useQuery } from 'react-query';
import { Link } from 'react-router-dom';
import {
  FileText,
  Upload,
  Search,
  Database,
  CheckCircle,
  Clock,
  AlertCircle,
} from 'lucide-react';
import axios from 'axios';
import { API_URL } from '../api';
import SystemStatus from '../components/SystemStatus';

const Dashboard = () => {
  const { data: documents, isLoading } = useQuery('documents', async () => {
    const response = await axios.get(`${API_URL}/documents`);
    return response.data;
  });

  const getStats = () => {
    if (!documents)
      return {
        total: 0,
        completed: 0,
        processing: 0,
        failed: 0,
        totalChunks: 0,
      };

    const total = documents.length;
    const completed = documents.filter(d => d.status === 'completed').length;
    const processing = documents.filter(d => d.status === 'processing').length;
    const failed = documents.filter(d => d.status === 'failed').length;
    const totalChunks = documents.reduce(
      (sum, d) => sum + (d.chunks_count || 0),
      0
    );

    return { total, completed, processing, failed, totalChunks };
  };

  const stats = getStats();

  const StatCard = ({ title, value, icon: Icon, color, description }) => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center">
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {description && (
            <p className="text-sm text-gray-500">{description}</p>
          )}
        </div>
      </div>
    </div>
  );

  const QuickActionCard = ({ title, description, icon: Icon, href, color }) => (
    <Link
      to={href}
      className="block bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
    >
      <div className="flex items-center">
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        <div className="ml-4">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          <p className="text-gray-600">{description}</p>
        </div>
      </div>
    </Link>
  );

  const RecentDocuments = () => {
    if (!documents || documents.length === 0) {
      return (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No documents yet
          </h3>
          <p className="text-gray-600 mb-4">
            Get started by uploading your first document.
          </p>
          <Link
            to="/upload"
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Upload className="w-4 h-4 mr-2" />
            Upload Document
          </Link>
        </div>
      );
    }

    const recentDocs = documents
      .sort((a, b) => new Date(b.upload_date) - new Date(a.upload_date))
      .slice(0, 5);

    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Recent Documents
          </h3>
        </div>
        <div className="divide-y divide-gray-200">
          {recentDocs.map(doc => (
            <div key={doc.id} className="px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <FileText className="w-5 h-5 text-gray-400 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {doc.filename}
                    </p>
                    <p className="text-sm text-gray-500">
                      {new Date(doc.upload_date).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center">
                  {doc.status === 'completed' && (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  )}
                  {doc.status === 'processing' && (
                    <Clock className="w-5 h-5 text-blue-500 animate-spin" />
                  )}
                  {doc.status === 'failed' && (
                    <AlertCircle className="w-5 h-5 text-red-500" />
                  )}
                  <span
                    className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      doc.status === 'completed'
                        ? 'bg-green-100 text-green-800'
                        : doc.status === 'processing'
                          ? 'bg-blue-100 text-blue-800'
                          : doc.status === 'failed'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {doc.status}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
        {documents.length > 5 && (
          <div className="px-6 py-3 border-t border-gray-200">
            <Link
              to="/documents"
              className="text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              View all documents →
            </Link>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Dashboard</h1>
        <p className="text-gray-600">
          Welcome to DocuVerse. Manage your documents and perform semantic
          searches.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Documents"
          value={stats.total}
          icon={FileText}
          color="bg-blue-500"
        />
        <StatCard
          title="Completed"
          value={stats.completed}
          icon={CheckCircle}
          color="bg-green-500"
        />
        <StatCard
          title="Processing"
          value={stats.processing}
          icon={Clock}
          color="bg-yellow-500"
        />
        <StatCard
          title="Total Chunks"
          value={stats.totalChunks}
          icon={Database}
          color="bg-purple-500"
        />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <QuickActionCard
          title="Upload Documents"
          description="Add new documents to your collection"
          icon={Upload}
          href="/upload"
          color="bg-blue-500"
        />
        <QuickActionCard
          title="Search Documents"
          description="Ask questions about your documents"
          icon={Search}
          href="/query"
          color="bg-green-500"
        />
        <QuickActionCard
          title="Manage Documents"
          description="View and manage your document library"
          icon={Database}
          href="/documents"
          color="bg-purple-500"
        />
      </div>

      {/* Recent Documents and System Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <RecentDocuments />
        <SystemStatus />
      </div>
    </div>
  );
};

export default Dashboard;
