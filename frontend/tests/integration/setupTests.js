import '@testing-library/jest-dom';
import 'jest-canvas-mock';
import { setupServer } from 'msw/node';
import { rest } from 'msw';

// Mock server for API calls
const server = setupServer(
  // Mock API endpoints
  rest.get('/api/health', (req, res, ctx) => {
    return res(ctx.json({ status: 'ok' }));
  }),
  rest.post('/api/documents/upload', (req, res, ctx) => {
    return res(ctx.json({ 
      id: 'mock-doc-id',
      filename: 'test.pdf',
      status: 'uploaded'
    }));
  }),
  rest.get('/api/documents', (req, res, ctx) => {
    return res(ctx.json([
      { id: '1', filename: 'test1.pdf', status: 'processed' },
      { id: '2', filename: 'test2.pdf', status: 'processing' }
    ]));
  }),
  rest.post('/api/query', (req, res, ctx) => {
    return res(ctx.json({
      results: [
        { id: '1', content: 'Mock result 1', score: 0.95 },
        { id: '2', content: 'Mock result 2', score: 0.85 }
      ]
    }));
  })
);

// Start server before all tests
beforeAll(() => server.listen());

// Reset handlers after each test
afterEach(() => server.resetHandlers());

// Close server after all tests
afterAll(() => server.close());

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock sessionStorage
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.sessionStorage = sessionStorageMock;

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock URL.createObjectURL
global.URL.createObjectURL = jest.fn(() => 'mocked-url');
global.URL.revokeObjectURL = jest.fn();

// Mock WebSocket for real-time features
global.WebSocket = jest.fn().mockImplementation(() => ({
  send: jest.fn(),
  close: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  readyState: 1, // OPEN
}));

// Clear all mocks before each test
beforeEach(() => {
  jest.clearAllMocks();
  localStorage.clear();
  sessionStorage.clear();
});

// Global test timeout
jest.setTimeout(10000);

// Export server for use in tests
export { server, rest }; 