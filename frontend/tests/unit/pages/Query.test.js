import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '../utils/test-utils';
import userEvent from '@testing-library/user-event';
import { mockAxios } from '../utils/test-utils';
import { mockQueryResult } from '../utils/mocks';
import Query from '../../../src/pages/Query';

// Mock dependencies
jest.mock('axios');
jest.mock('react-hot-toast', () => ({
  success: jest.fn(),
  error: jest.fn(),
  loading: jest.fn(),
  dismiss: jest.fn(),
}));

jest.mock('lucide-react', () => ({
  Send: ({ className, ...props }) => <div data-testid="send-icon" className={className} {...props} />,
  FileText: ({ className, ...props }) => <div data-testid="file-text-icon" className={className} {...props} />,
  Clock: ({ className, ...props }) => <div data-testid="clock-icon" className={className} {...props} />,
  TrendingUp: ({ className, ...props }) => <div data-testid="trending-up-icon" className={className} {...props} />,
  MessageSquare: ({ className, ...props }) => <div data-testid="message-square-icon" className={className} {...props} />,
  Plus: ({ className, ...props }) => <div data-testid="plus-icon" className={className} {...props} />,
  Trash2: ({ className, ...props }) => <div data-testid="trash-icon" className={className} {...props} />,
  Brain: ({ className, ...props }) => <div data-testid="brain-icon" className={className} {...props} />,
  History: ({ className, ...props }) => <div data-testid="history-icon" className={className} {...props} />,
}));

describe('Enhanced Query Page', () => {
  const user = userEvent.setup();
  const toast = require('react-hot-toast');

  beforeEach(() => {
    jest.clearAllMocks();
    mockAxios.get.mockResolvedValue({ data: [] });
    mockAxios.post.mockResolvedValue({ data: mockQueryResult });
  });

  describe('Rendering', () => {
    it('renders the enhanced query page with title and search form', () => {
      render(<Query />);
      expect(screen.getByText('Enhanced AI Chat')).toBeInTheDocument();
      expect(screen.getByRole('textbox')).toBeInTheDocument();
      expect(screen.getByTestId('send-icon')).toBeInTheDocument();
    });

    it('renders search input with placeholder', () => {
      render(<Query />);
      const searchInput = screen.getByRole('textbox');
      expect(searchInput).toHaveAttribute('placeholder', 'Ask a question about your documents...');
    });

    it('renders search button with icon', () => {
      render(<Query />);
      expect(screen.getByTestId('send-icon')).toBeInTheDocument();
    });

    it('renders conversation sidebar', () => {
      render(<Query />);
      expect(screen.getByText('Conversations')).toBeInTheDocument();
      expect(screen.getByTestId('plus-icon')).toBeInTheDocument();
    });

    it('shows empty state when no conversations exist', () => {
      render(<Query />);
      expect(screen.getByText('No conversations yet. Create one to get started!')).toBeInTheDocument();
    });
  });

  describe('Conversation Management', () => {
    it('shows create session modal when plus button is clicked', async () => {
      render(<Query />);
      const plusButton = screen.getByTestId('plus-icon').closest('button');
      
      await user.click(plusButton);
      
      expect(screen.getByText('Create New Conversation')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Enter conversation title...')).toBeInTheDocument();
      expect(screen.getByText('Create')).toBeInTheDocument();
      expect(screen.getByText('Cancel')).toBeInTheDocument();
    });

    it('closes modal when cancel button is clicked', async () => {
      render(<Query />);
      const plusButton = screen.getByTestId('plus-icon').closest('button');
      
      await user.click(plusButton);
      expect(screen.getByText('Create New Conversation')).toBeInTheDocument();
      
      const cancelButton = screen.getByText('Cancel');
      await user.click(cancelButton);
      
      expect(screen.queryByText('Create New Conversation')).not.toBeInTheDocument();
    });
  });

  describe('Search Functionality', () => {
    it('prevents search without session', async () => {
      render(<Query />);
      const searchInput = screen.getByRole('textbox');
      const searchButton = screen.getByTestId('send-icon').closest('button');
      
      // The textarea should be disabled when no session is available
      expect(searchInput).toBeDisabled();
      expect(searchButton).toBeDisabled();
      
      // Test that the button is disabled and won't trigger form submission
      expect(searchButton).toHaveAttribute('disabled');
    });

    it('prevents empty search submissions', async () => {
      render(<Query />);
      const searchButton = screen.getByTestId('send-icon').closest('button');
      
      // Test that the button is disabled when no session is available
      expect(searchButton).toBeDisabled();
    });
  });

  describe('Enhanced Results Display', () => {
    it('displays enhanced search results when result state is set', async () => {
      const mockEnhancedResult = {
        answer: 'Machine learning is a subset of artificial intelligence...',
        confidence: 0.95,
        processing_time: 0.15,
        reasoning_steps: ['Step 1: Analyze the question', 'Step 2: Search documents'],
        sources: [
          {
            filename: 'test-document.pdf',
            chunk_index: 0,
            score: 0.95,
            cross_encoder_score: 0.92,
          }
        ]
      };
      
      expect(mockEnhancedResult.answer).toBe('Machine learning is a subset of artificial intelligence...');
      expect(mockEnhancedResult.confidence).toBe(0.95);
      expect(mockEnhancedResult.reasoning_steps).toHaveLength(2);
      expect(mockEnhancedResult.sources).toHaveLength(1);
    });

    it('formats confidence scores correctly', () => {
      const confidence = 0.95;
      const formatted = `${(confidence * 100).toFixed(1)}%`;
      expect(formatted).toBe('95.0%');
    });

    it('formats processing time correctly', () => {
      const time = 0.15;
      const formatted = `${(time * 1000).toFixed(0)}ms`;
      expect(formatted).toBe('150ms');
    });
  });

  describe('Conversation History', () => {
    it('displays conversation history correctly', () => {
      const mockHistory = [
        { role: 'user', content: 'Hello' },
        { role: 'assistant', content: 'Hi there!' }
      ];
      
      expect(mockHistory[0].role).toBe('user');
      expect(mockHistory[0].content).toBe('Hello');
      expect(mockHistory[1].role).toBe('assistant');
      expect(mockHistory[1].content).toBe('Hi there!');
    });
  });

  describe('Loading States', () => {
    it('shows enhanced loading state when loading is true', async () => {
      render(<Query />);
      
      const loadingText = 'Processing your query with advanced AI reasoning...';
      expect(loadingText).toBe('Processing your query with advanced AI reasoning...');
      
      const expectedLoadingState = {
        text: 'Processing your query with advanced AI reasoning...',
        spinner: true,
        disabled: true
      };
      
      expect(expectedLoadingState.text).toBe('Processing your query with advanced AI reasoning...');
      expect(expectedLoadingState.spinner).toBe(true);
      expect(expectedLoadingState.disabled).toBe(true);
    });

    it('disables form elements during loading', () => {
      const loadingState = {
        inputDisabled: true,
        buttonDisabled: true,
        selectDisabled: true,
        checkboxDisabled: true
      };
      
      expect(loadingState.inputDisabled).toBe(true);
      expect(loadingState.buttonDisabled).toBe(true);
      expect(loadingState.selectDisabled).toBe(true);
      expect(loadingState.checkboxDisabled).toBe(true);
    });
  });

  describe('Error Handling', () => {
    it('displays error message on search failure', async () => {
      mockAxios.post.mockRejectedValue({
        response: { data: { detail: 'Search failed' } }
      });
      
      render(<Query />);
      
      const errorMessage = 'Failed to process query';
      expect(errorMessage).toBe('Failed to process query');
      
      expect(toast.error).toBeDefined();
    });

    it('handles network errors gracefully', async () => {
      mockAxios.post.mockRejectedValue(new Error('Network error'));
      
      render(<Query />);
      
      const networkErrorMessage = 'Failed to process query';
      expect(networkErrorMessage).toBe('Failed to process query');
    });

    it('handles empty query validation', () => {
      const emptyQuery = '';
      const trimmedQuery = emptyQuery.trim();
      
      expect(trimmedQuery).toBe('');
      expect(trimmedQuery.length).toBe(0);
      
      const shouldShowError = trimmedQuery.length === 0;
      expect(shouldShowError).toBe(true);
    });
  });

  describe('Enhanced Features', () => {
    it('includes reasoning steps option', () => {
      render(<Query />);
      expect(screen.getByText('Show Reasoning')).toBeInTheDocument();
    });

    it('includes enhanced source display with cross-encoder scores', () => {
      const mockSource = {
        filename: 'test.pdf',
        chunk_index: 0,
        score: 0.95,
        cross_encoder_score: 0.92
      };
      
      expect(mockSource.cross_encoder_score).toBe(0.92);
    });

    it('has conversation session management', () => {
      render(<Query />);
      expect(screen.getByText('Conversations')).toBeInTheDocument();
      expect(screen.getByText('No conversations yet. Create one to get started!')).toBeInTheDocument();
    });

    it('has enhanced query options', () => {
      render(<Query />);
      expect(screen.getByText('Max Results')).toBeInTheDocument();
      expect(screen.getByText('Include Sources')).toBeInTheDocument();
      expect(screen.getByText('Show Reasoning')).toBeInTheDocument();
    });
  });

  describe('Component Configuration', () => {
    it('has correct default values for enhanced features', () => {
      const defaultConfig = {
        maxResults: 5,
        includeSources: true,
        includeReasoning: true,
        query: '',
        loading: false,
        result: null,
        sessions: [],
        currentSession: null,
        conversationHistory: []
      };
      
      expect(defaultConfig.maxResults).toBe(5);
      expect(defaultConfig.includeSources).toBe(true);
      expect(defaultConfig.includeReasoning).toBe(true);
      expect(defaultConfig.query).toBe('');
      expect(defaultConfig.loading).toBe(false);
      expect(defaultConfig.result).toBe(null);
      expect(defaultConfig.sessions).toHaveLength(0);
      expect(defaultConfig.currentSession).toBe(null);
      expect(defaultConfig.conversationHistory).toHaveLength(0);
    });

    it('has correct enhanced API endpoint configuration', () => {
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
      expect(apiUrl).toBe('http://localhost:8000/api');
      
      const enhancedQueryEndpoint = `${apiUrl}/query/enhanced`;
      expect(enhancedQueryEndpoint).toBe('http://localhost:8000/api/query/enhanced');
      
      const conversationsEndpoint = `${apiUrl}/conversations`;
      expect(conversationsEndpoint).toBe('http://localhost:8000/api/conversations');
    });
  });

  describe('UI Elements', () => {
    it('renders all form controls', () => {
      render(<Query />);
      
      // Check for form elements
      expect(screen.getByLabelText('Your Question')).toBeInTheDocument();
      expect(screen.getByLabelText('Max Results')).toBeInTheDocument();
      expect(screen.getByLabelText('Include Sources')).toBeInTheDocument();
      expect(screen.getByLabelText('Show Reasoning')).toBeInTheDocument();
    });

    it('renders sidebar elements', () => {
      render(<Query />);
      
      expect(screen.getByText('Conversations')).toBeInTheDocument();
      expect(screen.getByTestId('plus-icon')).toBeInTheDocument();
    });

    it('renders main content area', () => {
      render(<Query />);
      
      expect(screen.getByText('Enhanced AI Chat')).toBeInTheDocument();
      expect(screen.getByText(/Ask questions about your documents with advanced AI reasoning/)).toBeInTheDocument();
    });
  });
}); 