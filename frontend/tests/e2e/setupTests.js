import '@testing-library/jest-dom';
import 'jest-canvas-mock';
import { setupServer } from 'msw/node';
import { rest } from 'msw';

// Mock server for API calls with more realistic delays
const server = setupServer(
  rest.get('/api/health', (req, res, ctx) => {
    return res(
      ctx.delay(100),
      ctx.json({ status: 'ok' })
    );
  }),
  rest.post('/api/documents/upload', (req, res, ctx) => {
    return res(
      ctx.delay(500),
      ctx.json({ 
        id: 'mock-doc-id',
        filename: 'test.pdf',
        status: 'uploaded'
      })
    );
  }),
  rest.get('/api/documents', (req, res, ctx) => {
    return res(
      ctx.delay(200),
      ctx.json([
        { id: '1', filename: 'test1.pdf', status: 'processed' },
        { id: '2', filename: 'test2.pdf', status: 'processing' }
      ])
    );
  }),
  rest.post('/api/query', (req, res, ctx) => {
    return res(
      ctx.delay(300),
      ctx.json({
        results: [
          { id: '1', content: 'Mock result 1', score: 0.95 },
          { id: '2', content: 'Mock result 2', score: 0.85 }
        ]
      })
    );
  }),
  rest.get('/api/documents/:id/status', (req, res, ctx) => {
    const { id } = req.params;
    return res(
      ctx.delay(150),
      ctx.json({
        id,
        status: 'processed',
        progress: 100
      })
    );
  })
);

// Start server before all tests
beforeAll(() => server.listen());

// Reset handlers after each test
afterEach(() => server.resetHandlers());

// Close server after all tests
afterAll(() => server.close());

// Mock localStorage with persistence simulation
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: jest.fn((key) => store[key] || null),
    setItem: jest.fn((key, value) => {
      store[key] = value.toString();
    }),
    removeItem: jest.fn((key) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
  };
})();
global.localStorage = localStorageMock;

// Mock sessionStorage
const sessionStorageMock = (() => {
  let store = {};
  return {
    getItem: jest.fn((key) => store[key] || null),
    setItem: jest.fn((key, value) => {
      store[key] = value.toString();
    }),
    removeItem: jest.fn((key) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
  };
})();
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

// Mock File and FileReader for file upload testing
global.File = jest.fn().mockImplementation((parts, filename, properties) => ({
  name: filename,
  size: parts.reduce((acc, part) => acc + part.length, 0),
  type: properties?.type || 'text/plain',
  lastModified: Date.now(),
}));

global.FileReader = jest.fn().mockImplementation(() => ({
  readAsDataURL: jest.fn(function() {
    setTimeout(() => {
      this.result = 'data:text/plain;base64,dGVzdA==';
      this.onload && this.onload();
    }, 100);
  }),
  readAsText: jest.fn(function() {
    setTimeout(() => {
      this.result = 'test content';
      this.onload && this.onload();
    }, 100);
  }),
  onload: null,
  onerror: null,
  result: null,
}));

// Mock WebSocket for real-time features
global.WebSocket = jest.fn().mockImplementation(() => ({
  send: jest.fn(),
  close: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  readyState: 1, // OPEN
}));

// Helper function to simulate user flow delays
global.waitForUserAction = (ms = 100) => new Promise(resolve => setTimeout(resolve, ms));

// Clear all mocks before each test
beforeEach(() => {
  jest.clearAllMocks();
  localStorage.clear();
  sessionStorage.clear();
});

// Global test timeout for E2E tests
jest.setTimeout(30000);

// Export server for use in tests
export { server, rest }; 