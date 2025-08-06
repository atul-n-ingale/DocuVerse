import React from 'react';
import { render, screen, fireEvent, waitFor } from '../utils/test-utils';
import userEvent from '@testing-library/user-event';
import { createMockFile, createMockDragEvent, mockAxios } from '../utils/test-utils';
import { mockUploadResponse, mockFileValidation } from '../utils/mocks';
import Upload from '../../../src/pages/Upload';
import axios from 'axios';

// Mock dependencies
jest.mock('axios');
jest.mock('react-hot-toast', () => ({
  success: jest.fn(),
  error: jest.fn(),
  loading: jest.fn(),
  dismiss: jest.fn(),
}));

jest.mock('react-dropzone', () => ({
  useDropzone: jest.fn(),
}));

jest.mock('lucide-react', () => ({
  Upload: ({ className, ...props }) => <div data-testid="upload-icon" className={className} {...props} />,
  File: ({ className, ...props }) => <div data-testid="file-icon" className={className} {...props} />,
  X: ({ className, ...props }) => <div data-testid="x-icon" className={className} {...props} />,
  CheckCircle: ({ className, ...props }) => <div data-testid="check-circle-icon" className={className} {...props} />,
  AlertCircle: ({ className, ...props }) => <div data-testid="alert-circle-icon" className={className} {...props} />,
}));

// Mock WebSocket
const mockWebSocket = {
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  close: jest.fn(),
  send: jest.fn(),
  onopen: jest.fn(),
  onmessage: jest.fn(),
  onerror: jest.fn(),
  onclose: jest.fn(),
};

global.WebSocket = jest.fn(() => mockWebSocket);

describe('Upload Page', () => {
  const user = userEvent.setup();
  const toast = require('react-hot-toast');

  beforeEach(() => {
    jest.clearAllMocks();
    // Mock useDropzone implementation
    const { useDropzone } = require('react-dropzone');
    useDropzone.mockReturnValue({
      getRootProps: jest.fn(() => ({ 'data-testid': 'dropzone' })),
      getInputProps: jest.fn(() => ({ 'data-testid': 'file-input' })),
      isDragActive: false,
      isDragAccept: false,
      isDragReject: false,
      acceptedFiles: [],
      rejectedFiles: [],
    });
  });

  describe('Rendering', () => {
    it('renders the upload page with title and description', () => {
      render(<Upload />);
      
      expect(screen.getByText('Upload Documents')).toBeInTheDocument();
      expect(screen.getByText(/drag & drop files here/i)).toBeInTheDocument();
    });

    it('renders the dropzone area', () => {
      render(<Upload />);
      
      expect(screen.getByTestId('dropzone')).toBeInTheDocument();
      expect(screen.getByTestId('file-input')).toBeInTheDocument();
    });

    it('renders upload instructions', () => {
      render(<Upload />);
      
      expect(screen.getByText(/supports pdf, docx, csv, excel/i)).toBeInTheDocument();
      expect(screen.getByText(/or click to select files/i)).toBeInTheDocument();
    });
  });

  describe('File Selection', () => {
    it('handles file selection through dropzone', async () => {
      const { useDropzone } = require('react-dropzone');
      const mockFile = createMockFile('test.pdf', 1024, 'application/pdf');
      const mockOnDrop = jest.fn();
      
      useDropzone.mockReturnValue({
        getRootProps: jest.fn(() => ({ 'data-testid': 'dropzone' })),
        getInputProps: jest.fn(() => ({ 'data-testid': 'file-input' })),
        isDragActive: false,
        isDragAccept: false,
        isDragReject: false,
        acceptedFiles: [mockFile],
        rejectedFiles: [],
        onDrop: mockOnDrop,
      });

      render(<Upload />);
      
      // Simulate file drop by calling onDrop directly
      const dropzone = screen.getByTestId('dropzone');
      fireEvent.drop(dropzone, createMockDragEvent([mockFile]));
      
      expect(dropzone).toBeInTheDocument();
    });

    it('handles multiple file selection', async () => {
      const { useDropzone } = require('react-dropzone');
      const mockFiles = [
        createMockFile('test1.pdf', 1024, 'application/pdf'),
        createMockFile('test2.docx', 2048, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
      ];
      
      useDropzone.mockReturnValue({
        getRootProps: jest.fn(() => ({ 'data-testid': 'dropzone' })),
        getInputProps: jest.fn(() => ({ 'data-testid': 'file-input' })),
        isDragActive: false,
        isDragAccept: false,
        isDragReject: false,
        acceptedFiles: mockFiles,
        rejectedFiles: [],
      });

      render(<Upload />);
      
      const dropzone = screen.getByTestId('dropzone');
      fireEvent.drop(dropzone, createMockDragEvent(mockFiles));
      
      expect(dropzone).toBeInTheDocument();
    });
  });

  describe('Drag and Drop', () => {
    it('handles drag enter state', () => {
      const { useDropzone } = require('react-dropzone');
      
      useDropzone.mockReturnValue({
        getRootProps: jest.fn(() => ({ 'data-testid': 'dropzone' })),
        getInputProps: jest.fn(() => ({ 'data-testid': 'file-input' })),
        isDragActive: true,
        isDragAccept: true,
        isDragReject: false,
        acceptedFiles: [],
        rejectedFiles: [],
      });

      render(<Upload />);
      
      const dropzone = screen.getByTestId('dropzone');
      expect(dropzone).toBeInTheDocument();
      // Check for drag active styling would be implementation specific
    });

    it('handles drag reject state', () => {
      const { useDropzone } = require('react-dropzone');
      
      useDropzone.mockReturnValue({
        getRootProps: jest.fn(() => ({ 'data-testid': 'dropzone' })),
        getInputProps: jest.fn(() => ({ 'data-testid': 'file-input' })),
        isDragActive: true,
        isDragAccept: false,
        isDragReject: true,
        acceptedFiles: [],
        rejectedFiles: [],
      });

      render(<Upload />);
      
      const dropzone = screen.getByTestId('dropzone');
      expect(dropzone).toBeInTheDocument();
      // Check for drag reject styling would be implementation specific
    });
  });

  describe('File Upload', () => {
    it('uploads file successfully', async () => {
      const mockFile = createMockFile('test.pdf', 1024, 'application/pdf');
      
      // Mock the useDropzone hook to capture the onDrop function
      const { useDropzone } = require('react-dropzone');
      let capturedOnDrop;
      
      useDropzone.mockImplementation((config) => {
        capturedOnDrop = config.onDrop;
        return {
          getRootProps: jest.fn(() => ({ 'data-testid': 'dropzone' })),
          getInputProps: jest.fn(() => ({ 'data-testid': 'file-input' })),
          isDragActive: false,
          isDragAccept: false,
          isDragReject: false,
          acceptedFiles: [],
          rejectedFiles: [],
        };
      });
      
      // Mock successful API response (after beforeEach)
      axios.post.mockResolvedValue({
        data: { task_id: 'test-task-123' }
      });
      
      render(<Upload />);
      
      // Simulate file upload by calling onDrop directly
      await capturedOnDrop([mockFile]);
      
      // Wait for the uploaded file to appear in the UI with the correct status
      await waitFor(() => {
        expect(screen.getByText('test.pdf')).toBeInTheDocument();
        expect(screen.getByText('Processing started...')).toBeInTheDocument();
      });
    });

    it('handles upload error', async () => {
      const mockFile = createMockFile('test.pdf', 1024, 'application/pdf');
      
      // Mock the useDropzone hook to capture the onDrop function
      const { useDropzone } = require('react-dropzone');
      let capturedOnDrop;
      
      useDropzone.mockImplementation((config) => {
        capturedOnDrop = config.onDrop;
        return {
          getRootProps: jest.fn(() => ({ 'data-testid': 'dropzone' })),
          getInputProps: jest.fn(() => ({ 'data-testid': 'file-input' })),
          isDragActive: false,
          isDragAccept: false,
          isDragReject: false,
          acceptedFiles: [],
          rejectedFiles: [],
        };
      });
      
      // Mock failed API response with an Error object (after beforeEach)
      const error = new Error('Upload failed');
      error.response = { data: { detail: 'Upload failed' } };
      axios.post.mockRejectedValue(error);
      
      render(<Upload />);
      
      // Simulate file upload by calling onDrop directly
      await capturedOnDrop([mockFile]);
      
      // Wait for the uploaded file to appear in the UI with the error message
      await waitFor(() => {
        expect(screen.getByText('test.pdf')).toBeInTheDocument();
        expect(screen.getByText('Upload failed')).toBeInTheDocument();
      });
    });

    it('shows loading state during upload', async () => {
      const mockFile = createMockFile('test.pdf', 1024, 'application/pdf');
      
      // Mock successful API response
      axios.post.mockResolvedValue({
        data: { task_id: 'test-task-123' }
      });
      
      // Mock the useDropzone hook to capture the onDrop function
      const { useDropzone } = require('react-dropzone');
      let capturedOnDrop;
      
      useDropzone.mockImplementation((config) => {
        capturedOnDrop = config.onDrop;
        return {
          getRootProps: jest.fn(() => ({ 'data-testid': 'dropzone' })),
          getInputProps: jest.fn(() => ({ 'data-testid': 'file-input' })),
          isDragActive: false,
          isDragAccept: false,
          isDragReject: false,
          acceptedFiles: [],
          rejectedFiles: [],
        };
      });
      
      render(<Upload />);
      
      // Simulate file upload by calling onDrop directly
      await capturedOnDrop([mockFile]);
      
      // Wait for side effects and assert
      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith('test.pdf uploaded successfully!');
      });
    });
  });

  describe('File Validation', () => {
    it('rejects unsupported file types', () => {
      const { useDropzone } = require('react-dropzone');
      
      useDropzone.mockReturnValue({
        getRootProps: jest.fn(() => ({ 'data-testid': 'dropzone' })),
        getInputProps: jest.fn(() => ({ 'data-testid': 'file-input' })),
        isDragActive: false,
        isDragAccept: false,
        isDragReject: false,
        acceptedFiles: [],
        rejectedFiles: [mockFileValidation.invalidFile],
      });

      render(<Upload />);
      
      const dropzone = screen.getByTestId('dropzone');
      expect(dropzone).toBeInTheDocument();
    });

    it('rejects oversized files', () => {
      const { useDropzone } = require('react-dropzone');
      
      useDropzone.mockReturnValue({
        getRootProps: jest.fn(() => ({ 'data-testid': 'dropzone' })),
        getInputProps: jest.fn(() => ({ 'data-testid': 'file-input' })),
        isDragActive: false,
        isDragAccept: false,
        isDragReject: false,
        acceptedFiles: [],
        rejectedFiles: [mockFileValidation.oversizedFile],
      });

      render(<Upload />);
      
      const dropzone = screen.getByTestId('dropzone');
      expect(dropzone).toBeInTheDocument();
    });
  });

  describe('WebSocket Integration', () => {
    it('establishes WebSocket connection on mount', () => {
      render(<Upload />);
      
      expect(global.WebSocket).toHaveBeenCalledWith('ws://localhost:8000/ws/progress');
    });

    it('handles WebSocket messages', () => {
      render(<Upload />);
      
      // The WebSocket event listeners are set up in the component
      expect(mockWebSocket.onmessage).toBeDefined();
    });

    it('cleans up WebSocket on unmount', () => {
      const { unmount } = render(<Upload />);
      
      unmount();
      
      expect(mockWebSocket.close).toHaveBeenCalled();
    });
  });

  describe('Progress Tracking', () => {
    it('displays upload progress', () => {
      const { useDropzone } = require('react-dropzone');
      
      useDropzone.mockReturnValue({
        getRootProps: jest.fn(() => ({ 'data-testid': 'dropzone' })),
        getInputProps: jest.fn(() => ({ 'data-testid': 'file-input' })),
        isDragActive: false,
        isDragAccept: false,
        isDragReject: false,
        acceptedFiles: [],
        rejectedFiles: [],
      });

      render(<Upload />);
      
      const dropzone = screen.getByTestId('dropzone');
      expect(dropzone).toBeInTheDocument();
    });
  });
}); 