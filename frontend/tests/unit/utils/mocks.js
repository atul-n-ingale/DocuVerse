// Mock data for testing
export const mockDocument = {
  id: 'doc-123',
  filename: 'test-document.pdf',
  file_type: 'pdf',
  file_size: 1024000,
  status: 'completed',
  chunks_count: 5,
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
};

export const mockDocuments = [
  mockDocument,
  {
    id: 'doc-456',
    filename: 'another-document.docx',
    file_type: 'docx',
    file_size: 2048000,
    status: 'processing',
    chunks_count: 0,
    created_at: '2023-01-02T00:00:00Z',
    updated_at: '2023-01-02T00:00:00Z',
  },
  {
    id: 'doc-789',
    filename: 'failed-document.pdf',
    file_type: 'pdf',
    file_size: 512000,
    status: 'failed',
    chunks_count: 0,
    created_at: '2023-01-03T00:00:00Z',
    updated_at: '2023-01-03T00:00:00Z',
  },
];

export const mockQueryResult = {
  query: 'What is machine learning?',
  answer: 'Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed.',
  confidence: 0.95,
  processing_time: 0.15,
  sources: [
    {
      filename: 'test-document.pdf',
      chunk_index: 0,
      page_number: 1,
      score: 0.95,
    },
    {
      filename: 'another-document.docx',
      chunk_index: 1,
      page_number: 2,
      score: 0.87,
    },
  ],
};

export const mockSystemStatus = {
  backend: {
    status: 'healthy',
    uptime: 3600,
    version: '1.0.0',
  },
  worker: {
    status: 'healthy',
    active_tasks: 2,
    pending_tasks: 0,
  },
  database: {
    status: 'healthy',
    connection_pool: {
      active: 5,
      idle: 10,
    },
  },
  redis: {
    status: 'healthy',
    memory_usage: '45MB',
  },
  vector_store: {
    status: 'healthy',
    total_vectors: 1500,
    index_size: '2.3MB',
  },
};

export const mockUploadResponse = {
  message: 'File uploaded successfully',
  document_id: 'doc-new-123',
  filename: 'uploaded-file.pdf',
  task_id: 'task-456',
  data: {
    task_id: 'task-456',
    document_id: 'doc-new-123',
    filename: 'uploaded-file.pdf',
  },
};

// Mock API responses
export const mockApiResponses = {
  // Document endpoints
  '/api/documents': {
    get: { data: mockDocuments },
    post: { data: mockUploadResponse },
  },
  '/api/documents/doc-123': {
    get: { data: mockDocument },
    delete: { data: { message: 'Document deleted successfully' } },
  },
  
  // Query endpoint
  '/api/query': {
    post: { data: mockQueryResult },
  },
  
  // System status
  '/api/system/status': {
    get: { data: mockSystemStatus },
  },
  
  // Worker endpoints
  '/api/worker/status': {
    get: { data: { status: 'healthy', active_tasks: 2 } },
  },
};

// Mock WebSocket messages
export const mockWebSocketMessages = {
  documentProcessing: {
    type: 'document_processing',
    data: {
      document_id: 'doc-123',
      status: 'processing',
      progress: 50,
    },
  },
  documentCompleted: {
    type: 'document_completed',
    data: {
      document_id: 'doc-123',
      status: 'completed',
      chunks_count: 5,
    },
  },
  documentFailed: {
    type: 'document_failed',
    data: {
      document_id: 'doc-123',
      status: 'failed',
      error: 'Processing failed',
    },
  },
};

// Mock toast notifications
export const mockToasts = {
  success: jest.fn(),
  error: jest.fn(),
  loading: jest.fn(),
  dismiss: jest.fn(),
};

// Mock react-dropzone
export const mockDropzone = {
  getRootProps: jest.fn(() => ({ 'data-testid': 'dropzone' })),
  getInputProps: jest.fn(() => ({ 'data-testid': 'file-input' })),
  isDragActive: false,
  isDragAccept: false,
  isDragReject: false,
  acceptedFiles: [],
  rejectedFiles: [],
};

// Mock file validation
export const mockFileValidation = {
  validPdfFile: new File(['pdf content'], 'test.pdf', { type: 'application/pdf' }),
  validDocxFile: new File(['docx content'], 'test.docx', { 
    type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' 
  }),
  invalidFile: new File(['txt content'], 'test.txt', { type: 'text/plain' }),
  oversizedFile: new File(['large content'], 'large.pdf', { type: 'application/pdf' }),
};

// Set oversized file size
Object.defineProperty(mockFileValidation.oversizedFile, 'size', {
  value: 100 * 1024 * 1024, // 100MB
});

export default {
  mockDocument,
  mockDocuments,
  mockQueryResult,
  mockSystemStatus,
  mockUploadResponse,
  mockApiResponses,
  mockWebSocketMessages,
  mockToasts,
  mockDropzone,
  mockFileValidation,
}; 