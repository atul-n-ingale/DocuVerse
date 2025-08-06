import React, { useState, useEffect, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Upload as UploadIcon,
  File,
  X,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';
import toast from 'react-hot-toast';
import axios from 'axios';
import { API_URL } from '../api';

const Upload = () => {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [ws, setWs] = useState(null);

  // WebSocket connection for real-time progress
  useEffect(() => {
    // For WebSocket, we need to connect to the host machine's address
    // In Docker, the browser connects to localhost, not the internal Docker network
    let wsUrl;
    if (process.env.REACT_APP_API_URL) {
      // Extract the port from the API URL and use localhost for WebSocket
      const apiUrl = process.env.REACT_APP_API_URL;
      if (apiUrl.includes('backend:8000')) {
        // Docker environment - use localhost for WebSocket
        wsUrl = 'ws://localhost:8000/ws/progress';
      } else {
        // Local development or other environment
        wsUrl =
          apiUrl
            .replace('/api', '')
            .replace('http://', 'ws://')
            .replace('https://', 'wss://') + '/ws/progress';
      }
    } else {
      // Fallback for local development
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
      // Try to reconnect after a delay
      setTimeout(() => {
        console.log('Attempting to reconnect WebSocket...');
        const newWebsocket = new WebSocket(wsUrl);
        newWebsocket.onopen = () =>
          console.log('WebSocket reconnected to:', wsUrl);
        newWebsocket.onmessage = websocket.onmessage;
        newWebsocket.onerror = websocket.onerror;
        newWebsocket.onclose = websocket.onclose;
        setWs(newWebsocket);
      }, 3000);
    };

    setWs(websocket);

    return () => {
      websocket.close();
    };
  }, []);

  const handleWebSocketMessage = data => {
    console.log('Handling WebSocket message:', data);
    switch (data.type) {
      case 'progress_update':
        console.log('Progress update:', data);
        updateFileProgress(
          data.task_id,
          data.progress,
          data.status,
          data.message
        );
        break;
      case 'processing_complete':
        console.log('Processing complete:', data);
        updateFileComplete(data.task_id, data.document_id);
        break;
      case 'error':
        console.log('Error message:', data);
        updateFileError(data.task_id, data.error);
        break;
      default:
        console.log('Unknown message type:', data.type);
        break;
    }
  };

  const updateFileProgress = (taskId, progress, status, message) => {
    setUploadedFiles(prev =>
      prev.map(file =>
        file.taskId === taskId ? { ...file, progress, status, message } : file
      )
    );
  };

  const updateFileComplete = (taskId, documentId) => {
    setUploadedFiles(prev =>
      prev.map(file =>
        file.taskId === taskId
          ? { ...file, status: 'completed', progress: 100, documentId }
          : file
      )
    );
    toast.success('Document processing completed!');
  };

  const updateFileError = (taskId, error) => {
    console.log('Updating file error for taskId:', taskId, 'error:', error);
    setUploadedFiles(prev =>
      prev.map(file =>
        file.taskId === taskId
          ? { ...file, status: 'error', error, progress: 0 }
          : file
      )
    );
    toast.error(`Processing failed: ${error}`);
  };

  const onDrop = useCallback(async acceptedFiles => {
    setUploading(true);

    for (const file of acceptedFiles) {
      const formData = new FormData();
      formData.append('file', file);

      // Add file to state immediately
      const fileInfo = {
        id: Date.now() + Math.random(),
        name: file.name,
        size: file.size,
        taskId: null,
        status: 'uploading',
        progress: 0,
        message: 'Uploading file...',
      };

      setUploadedFiles(prev => [...prev, fileInfo]);

      try {
        const response = await axios.post(`${API_URL}/upload`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });

        // Update file with task ID
        setUploadedFiles(prev =>
          prev.map(f =>
            f.id === fileInfo.id
              ? {
                  ...f,
                  taskId: response.data.task_id,
                  status: 'processing',
                  message: 'Processing started...',
                }
              : f
          )
        );

        toast.success(`${file.name} uploaded successfully!`);
      } catch (error) {
        console.error('Upload error:', error);
        setUploadedFiles(prev =>
          prev.map(f =>
            f.id === fileInfo.id
              ? {
                  ...f,
                  status: 'error',
                  error: error.response?.data?.detail || 'Upload failed',
                }
              : f
          )
        );
        toast.error(`Failed to upload ${file.name}`);
      }
    }

    setUploading(false);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        ['.docx'],
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': [
        '.xlsx',
      ],
      'application/vnd.ms-excel': ['.xls'],
      'image/png': ['.png'],
      'image/jpeg': ['.jpg', '.jpeg'],
    },
    multiple: true,
  });

  const removeFile = fileId => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const formatFileSize = bytes => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusIcon = status => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <File className="w-5 h-5 text-blue-500" />;
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Upload Documents
        </h1>
        <p className="text-gray-600">
          Upload your documents to DocuVerse for semantic search and analysis.
        </p>
      </div>

      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <input {...getInputProps()} />
        <UploadIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <p className="text-lg font-medium text-gray-900 mb-2">
          {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
        </p>
        <p className="text-gray-500 mb-4">or click to select files</p>
        <p className="text-sm text-gray-400">
          Supports PDF, DOCX, CSV, Excel, PNG, JPEG files
        </p>
      </div>

      {/* Uploaded Files */}
      {uploadedFiles.length > 0 && (
        <div className="mt-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Uploaded Files
          </h2>
          <div className="space-y-4">
            {uploadedFiles.map(file => (
              <div
                key={file.id}
                className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(file.status)}
                    <div>
                      <p className="font-medium text-gray-900">{file.name}</p>
                      <p className="text-sm text-gray-500">
                        {formatFileSize(file.size)}
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={() => removeFile(file.id)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {file.status !== 'completed' && file.status !== 'error' && (
                  <div className="mt-3">
                    <div className="flex justify-between text-sm text-gray-600 mb-1">
                      <span>{file.message}</span>
                      <span>{file.progress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${file.progress}%` }}
                      />
                    </div>
                  </div>
                )}

                {file.status === 'error' && (
                  <p className="mt-2 text-sm text-red-600">{file.error}</p>
                )}

                {file.status === 'completed' && (
                  <p className="mt-2 text-sm text-green-600">
                    Processing completed successfully!
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Upload;
