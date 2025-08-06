import React from 'react';
import { render, queries } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { axe, toHaveNoViolations } from 'jest-axe';

// Add jest-axe matcher
expect.extend(toHaveNoViolations);

// Create a custom render function that includes providers
const AllTheProviders = ({ children }) => {
  return (
    <MemoryRouter>
      {children}
    </MemoryRouter>
  );
};

const customRender = (ui, options) =>
  render(ui, { wrapper: AllTheProviders, ...options });

// Mock API responses
export const mockApiResponse = (data, status = 200) => ({
  data,
  status,
  statusText: status === 200 ? 'OK' : 'Error',
  headers: {},
  config: {},
});

// Mock file for file upload testing
export const createMockFile = (name = 'test.pdf', size = 1024, type = 'application/pdf') => {
  const file = new File(['test content'], name, { type });
  Object.defineProperty(file, 'size', { value: size });
  return file;
};

// Mock drag and drop events
export const createMockDragEvent = (files = []) => ({
  dataTransfer: {
    files,
    items: files.map(file => ({
      kind: 'file',
      type: file.type,
      getAsFile: () => file,
    })),
    types: ['Files'],
  },
  preventDefault: jest.fn(),
  stopPropagation: jest.fn(),
});

// Wait for loading states to complete
export const waitForLoadingToFinish = () =>
  new Promise(resolve => setTimeout(resolve, 0));

// Mock axios for API testing
export const mockAxios = {
  get: jest.fn(() => Promise.resolve({ data: {} })),
  post: jest.fn(() => Promise.resolve({ data: {} })),
  put: jest.fn(() => Promise.resolve({ data: {} })),
  delete: jest.fn(() => Promise.resolve({ data: {} })),
  patch: jest.fn(() => Promise.resolve({ data: {} })),
  create: jest.fn(() => mockAxios),
  defaults: {
    baseURL: 'http://localhost:8000',
  },
};

// Mock react-query hooks
export const mockUseQuery = (data, options = {}) => ({
  data,
  isLoading: false,
  isError: false,
  error: null,
  refetch: jest.fn(),
  ...options,
});

export const mockUseMutation = (options = {}) => ({
  mutate: jest.fn(),
  mutateAsync: jest.fn(),
  isLoading: false,
  isError: false,
  error: null,
  data: null,
  reset: jest.fn(),
  ...options,
});

// Accessibility testing helper
export const checkAccessibility = async (container) => {
  const results = await axe(container);
  expect(results).toHaveNoViolations();
};

// Custom queries for testing
const customQueries = {
  ...queries,
  // Add custom queries here if needed
};

// Re-export everything
export * from '@testing-library/react';
export * from '@testing-library/user-event';
export { customRender as render, customQueries };
export { axe, toHaveNoViolations }; 