import React, { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import {
  FileText,
  Clock,
  CheckCircle,
  AlertCircle,
  Trash2,
  Eye,
  Loader,
} from 'lucide-react';
import axios from 'axios';
import { API_URL } from '../api';
import toast from 'react-hot-toast';

const Documents = () => {
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [showChunks, setShowChunks] = useState(false);
  const [deletingDocuments, setDeletingDocuments] = useState(new Set());

  const {
    data: documents,
    isLoading,
    error,
    refetch,
  } = useQuery(
    'documents',
    async () => {
      const response = await axios.get(`${API_URL}/documents`);
      console.log('Documents fetched:', response.data);
      console.log('First document:', response.data[0]);
      return response.data;
    },
    {
      refetchInterval: 5000, // Refetch every 5 seconds to get updated status
    }
  );

  // WebSocket connection for real-time updates
  useEffect(() => {
    let wsUrl;
    if (process.env.REACT_APP_API_URL) {
      const apiUrl = process.env.REACT_APP_API_URL;
      if (apiUrl.includes('backend:8000')) {
        wsUrl = 'ws://localhost:8000/ws/progress';
      } else {
        wsUrl =
          apiUrl
            .replace('/api', '')
            .replace('http://', 'ws://')
            .replace('https://', 'wss://') + '/ws/progress';
      }
    } else {
      wsUrl = 'ws://localhost:8000/ws/progress';
    }

    console.log('Connecting to WebSocket:', wsUrl);
    const websocket = new WebSocket(wsUrl);

    websocket.onopen = () => {
      console.log('WebSocket connected successfully to:', wsUrl);
    };

    websocket.onmessage = event => {
      try {
        const data = JSON.parse(event.data);
        console.log('WebSocket message received:', data);
        handleWebSocketMessage(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error, event.data);
      }
    };

    websocket.onerror = error => {
      console.error('WebSocket connection error:', error);
    };

    websocket.onclose = event => {
      console.log(
        'WebSocket disconnected. Code:',
        event.code,
        'Reason:',
        event.reason
      );
    };

    return () => {
      websocket.close();
    };
  }, []);

  const handleWebSocketMessage = data => {
    switch (data.type) {
      case 'document_deletion_started':
        console.log('Document deletion started:', data.document_id);
        setDeletingDocuments(prev => new Set(prev).add(data.document_id));
        toast.loading('Deleting document...', {
          id: `delete-${data.document_id}`,
        });
        break;

      case 'document_deleted_success':
        console.log('Document deleted successfully:', data.document_id);
        setDeletingDocuments(prev => {
          const newSet = new Set(prev);
          newSet.delete(data.document_id);
          return newSet;
        });
        toast.success('Document deleted successfully!', {
          id: `delete-${data.document_id}`,
        });
        refetch(); // Refresh the documents list
        break;

      case 'document_deleted_failed':
        console.log('Document deletion failed:', data.document_id, data.error);
        setDeletingDocuments(prev => {
          const newSet = new Set(prev);
          newSet.delete(data.document_id);
          return newSet;
        });
        toast.error(`Failed to delete document: ${data.error}`, {
          id: `delete-${data.document_id}`,
        });
        refetch(); // Refresh the documents list
        break;

      default:
        console.log('Unknown WebSocket message type:', data.type);
        break;
    }
  };

  const handleDelete = async documentId => {
    console.log('handleDelete called with documentId:', documentId);
    console.log('documentId type:', typeof documentId);

    if (!documentId || documentId === 'undefined' || documentId === 'null') {
      console.error('Invalid documentId:', documentId);
      toast.error('Invalid document ID');
      return;
    }

    if (!window.confirm('Are you sure you want to delete this document?')) {
      return;
    }

    try {
      // Add to deleting set immediately
      setDeletingDocuments(prev => new Set(prev).add(documentId));

      console.log(
        'Making DELETE request to:',
        `${API_URL}/documents/${documentId}`
      );
      await axios.delete(`${API_URL}/documents/${documentId}`);
      // Don't show success toast here as it will come via WebSocket
      // Don't refetch here as the document will be removed via WebSocket
    } catch (error) {
      console.error('Delete error:', error);
      // Remove from deleting set on error
      setDeletingDocuments(prev => {
        const newSet = new Set(prev);
        newSet.delete(documentId);
        return newSet;
      });
      toast.error('Failed to start document deletion');
    }
  };

  const handleViewChunks = async documentId => {
    try {
      const response = await axios.get(
        `${API_URL}/documents/${documentId}/chunks`
      );
      setSelectedDocument({
        id: documentId,
        chunks: response.data.chunks,
      });
      setShowChunks(true);
    } catch (error) {
      console.error('Error fetching chunks:', error);
      toast.error('Failed to fetch document chunks');
    }
  };

  const formatFileSize = bytes => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = dateString => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusIcon = status => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'processing':
        return <Clock className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'deleting':
        return <Loader className="w-5 h-5 text-orange-500 animate-spin" />;
      case 'delete_error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = status => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'deleting':
        return 'bg-orange-100 text-orange-800';
      case 'delete_error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Documents</h1>
          <p className="text-gray-600">
            View and manage your uploaded documents.
          </p>
        </div>
        <div className="flex items-center justify-center py-12">
          <div className="flex items-center space-x-3">
            <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-600">Loading documents...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Documents</h1>
          <p className="text-gray-600">
            View and manage your uploaded documents.
          </p>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">
            Error loading documents: {error.message}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Documents</h1>
        <p className="text-gray-600">
          View and manage your uploaded documents.
        </p>
      </div>

      {documents && documents.length > 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Document
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Size
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Uploaded
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {documents.map(doc => {
                  return (
                    <tr key={doc.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <FileText className="w-5 h-5 text-gray-400 mr-3" />
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {doc.filename}
                            </div>
                            {doc.chunks_count > 0 && (
                              <div className="text-sm text-gray-500">
                                {doc.chunks_count} chunks
                              </div>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          {doc.file_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatFileSize(doc.file_size)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          {getStatusIcon(doc.status)}
                          <span
                            className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(doc.status)}`}
                          >
                            {doc.status}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatDate(doc.upload_date)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => handleViewChunks(doc.id)}
                            className="text-blue-600 hover:text-blue-900"
                            title="View chunks"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => {
                              console.log(
                                'Delete button clicked for doc:',
                                doc
                              );
                              console.log('doc.id:', doc.id);
                              console.log('doc._id:', doc._id);
                              handleDelete(doc.id);
                            }}
                            className="text-red-600 hover:text-red-900"
                            title="Delete document"
                            disabled={deletingDocuments.has(doc.id)}
                          >
                            {deletingDocuments.has(doc.id) ? (
                              <Loader className="w-4 h-4 animate-spin" />
                            ) : (
                              <Trash2 className="w-4 h-4" />
                            )}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No documents yet
          </h3>
          <p className="text-gray-600 mb-4">
            Upload your first document to get started with DocuVerse.
          </p>
        </div>
      )}

      {/* Chunks Modal */}
      {showChunks && selectedDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[80vh] overflow-hidden">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">
                Document Chunks
              </h2>
              <button
                onClick={() => setShowChunks(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg
                  className="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              <div className="space-y-4">
                {selectedDocument.chunks.map((chunk, index) => (
                  <div
                    key={chunk.id}
                    className="border border-gray-200 rounded-lg p-4"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-900">
                        Chunk #{chunk.chunk_index + 1}
                      </span>
                      {chunk.metadata?.page_number && (
                        <span className="text-sm text-gray-500">
                          Page {chunk.metadata.page_number}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-700 leading-relaxed">
                      {chunk.content}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Documents;
