# Frontend Testing Guide

This guide covers the comprehensive testing framework for the DocuVerse frontend application, including unit, integration, and end-to-end tests.

## Table of Contents

1. [Overview](#overview)
2. [Test Structure](#test-structure)
3. [Test Types](#test-types)
4. [Running Tests](#running-tests)
5. [Writing Tests](#writing-tests)
6. [Test Utilities](#test-utilities)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Overview

The frontend testing framework is organized into three distinct test types:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions and API integration
- **E2E Tests**: Test complete user workflows and system behavior

Each test type has its own directory structure, configuration, and utilities.

## Test Structure

```
frontend/
├── tests/
│   ├── unit/
│   │   ├── components/
│   │   │   ├── Navbar.test.js
│   │   │   └── SystemStatus.test.js
│   │   ├── pages/
│   │   │   ├── Dashboard.test.js
│   │   │   ├── Documents.test.js
│   │   │   ├── Query.test.js
│   │   │   └── Upload.test.js
│   │   ├── utils/
│   │   │   ├── test-utils.js
│   │   │   └── mocks.js
│   │   ├── setupTests.js
│   │   └── jest.config.js
│   ├── integration/
│   │   ├── components/
│   │   │   └── Navbar.test.js
│   │   ├── pages/
│   │   ├── api/
│   │   ├── utils/
│   │   │   └── test-utils.js
│   │   ├── setupTests.js
│   │   └── jest.config.js
│   └── e2e/
│       ├── flows/
│       │   └── document-upload-flow.test.js
│       ├── scenarios/
│       ├── utils/
│       │   └── test-utils.js
│       ├── setupTests.js
│       └── jest.config.js
├── jest.config.js (main configuration)
└── package.json
```

## Test Types

### Unit Tests

**Purpose**: Test individual components in isolation with minimal dependencies.

**Characteristics**:
- Fast execution (< 5 seconds timeout)
- Mocked dependencies
- Focus on component behavior
- High coverage requirements (70%)

**Example**:
```javascript
// tests/unit/components/Navbar.test.js
import { render, screen } from '../utils/test-utils';
import Navbar from '../../../src/components/Navbar';

describe('Navbar Component', () => {
  it('renders navigation items', () => {
    render(<Navbar />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });
});
```

### Integration Tests

**Purpose**: Test component interactions, API integration, and data flow.

**Characteristics**:
- Medium execution time (< 10 seconds timeout)
- MSW for API mocking
- Real component interactions
- Moderate coverage requirements (60%)

**Example**:
```javascript
// tests/integration/components/Navbar.test.js
import { render, screen, fireEvent } from '../utils/test-utils';
import Navbar from '../../../src/components/Navbar';

describe('Navbar Integration', () => {
  it('navigates between pages', async () => {
    render(<Navbar />);
    fireEvent.click(screen.getByRole('link', { name: /upload/i }));
    // Test navigation behavior
  });
});
```

### E2E Tests

**Purpose**: Test complete user workflows and system integration.

**Characteristics**:
- Longer execution time (< 30 seconds timeout)
- Real user interactions
- Full system testing
- Lower coverage requirements (50%)

**Example**:
```javascript
// tests/e2e/flows/document-upload-flow.test.js
import { render, screen, waitFor } from '../utils/test-utils';
import { simulateDocumentUploadFlow } from '../utils/test-utils';
import App from '../../../src/App';

describe('Document Upload Flow', () => {
  it('completes full upload workflow', async () => {
    render(<App />);
    await simulateDocumentUploadFlow(['test.pdf']);
    // Test complete workflow
  });
});
```

## Running Tests

### Basic Commands

```bash
# Run all tests
npm test

# Run specific test types
npm run test:unit
npm run test:integration
npm run test:e2e

# Run with coverage
npm run test:coverage
npm run test:unit:coverage
npm run test:integration:coverage
npm run test:e2e:coverage

# Watch mode
npm run test:watch
npm run test:unit:watch
npm run test:integration:watch
```

### Advanced Commands

```bash
# Run tests in parallel
npm run test:parallel

# Run tests serially
npm run test:serial

# Run specific test file
npm run test:file -- Navbar.test.js

# Run tests matching pattern
npm run test:specific -- "navigation"

# Run only failed tests
npm run test:failed

# Run only changed tests
npm run test:changed

# Clear Jest cache
npm run test:clean

# Verbose output
npm run test:verbose

# Silent output
npm run test:silent
```

## Writing Tests

### Test File Structure

```javascript
import React from 'react';
import { render, screen, fireEvent, waitFor } from '../utils/test-utils';
import ComponentName from '../../../src/components/ComponentName';

// Mock external dependencies
jest.mock('external-library');

describe('ComponentName', () => {
  beforeEach(() => {
    // Setup before each test
  });

  afterEach(() => {
    // Cleanup after each test
  });

  describe('Rendering', () => {
    it('renders component correctly', () => {
      render(<ComponentName />);
      expect(screen.getByText('Expected Text')).toBeInTheDocument();
    });
  });

  describe('Interactions', () => {
    it('handles user interactions', async () => {
      render(<ComponentName />);
      fireEvent.click(screen.getByRole('button'));
      await waitFor(() => {
        expect(screen.getByText('Updated Text')).toBeInTheDocument();
      });
    });
  });
});
```

### Test Naming Conventions

- **Test files**: `ComponentName.test.js`
- **Test suites**: Use `describe()` for logical grouping
- **Test cases**: Use `it()` with descriptive names
- **Mock files**: `ComponentName.mock.js`

## Test Utilities

### Unit Test Utils

```javascript
// tests/unit/utils/test-utils.js
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';

const customRender = (ui, options = {}) => {
  const Wrapper = ({ children }) => (
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter>
        {children}
      </MemoryRouter>
    </QueryClientProvider>
  );
  return render(ui, { wrapper: Wrapper, ...options });
};

export { customRender as render };
export * from '@testing-library/react';
```

### Integration Test Utils

```javascript
// tests/integration/utils/test-utils.js
import { server } from '../setupTests';
import { rest } from 'msw';

export const mockApiResponse = (url, response, status = 200) => {
  server.use(
    rest.get(url, (req, res, ctx) => {
      return res(ctx.status(status), ctx.json(response));
    })
  );
};

export const waitForApiCall = async (url) => {
  return new Promise((resolve) => {
    server.use(
      rest.get(url, (req, res, ctx) => {
        resolve(req);
        return res(ctx.json({}));
      })
    );
  });
};
```

### E2E Test Utils

```javascript
// tests/e2e/utils/test-utils.js
export const simulateUserFlow = async (steps) => {
  const user = userEvent.setup();
  for (const step of steps) {
    await step.action(user);
  }
};

export const simulateDocumentUploadFlow = async (files) => {
  // Complete upload workflow simulation
};
```

## Best Practices

### General Guidelines

1. **Test Behavior, Not Implementation**
   - Focus on what the component does, not how it does it
   - Test user interactions and expected outcomes

2. **Use Descriptive Test Names**
   ```javascript
   // Good
   it('displays error message when API call fails')
   
   // Bad
   it('test error')
   ```

3. **Arrange, Act, Assert Pattern**
   ```javascript
   it('updates counter when button is clicked', () => {
     // Arrange
     render(<Counter />);
     
     // Act
     fireEvent.click(screen.getByRole('button'));
     
     // Assert
     expect(screen.getByText('1')).toBeInTheDocument();
   });
   ```

### Unit Test Guidelines

1. **Mock External Dependencies**
   ```javascript
   jest.mock('axios');
   jest.mock('react-router-dom');
   ```

2. **Test Edge Cases**
   - Empty states
   - Error conditions
   - Loading states

3. **Use Data-Testids Sparingly**
   - Prefer semantic queries (getByRole, getByText)
   - Use data-testid only when necessary

### Integration Test Guidelines

1. **Use MSW for API Mocking**
   ```javascript
   import { rest } from 'msw';
   import { server } from '../setupTests';
   
   server.use(
     rest.get('/api/documents', (req, res, ctx) => {
       return res(ctx.json(mockDocuments));
     })
   );
   ```

2. **Test Real Component Interactions**
   - Don't mock child components
   - Test data flow between components

### E2E Test Guidelines

1. **Test Complete User Workflows**
   - Start from user's perspective
   - Test realistic scenarios

2. **Use Helper Functions**
   ```javascript
   const uploadDocument = async (filename) => {
     // Complete upload flow
   };
   ```

3. **Handle Asynchronous Operations**
   ```javascript
   await waitFor(() => {
     expect(screen.getByText('Upload complete')).toBeInTheDocument();
   });
   ```

## Troubleshooting

### Common Issues

1. **Tests Timing Out**
   - Increase timeout in jest.config.js
   - Use waitFor() for async operations
   - Check for infinite loops

2. **Module Resolution Errors**
   - Verify moduleNameMapping in jest.config.js
   - Check import paths
   - Ensure files exist

3. **Mock Issues**
   - Clear mocks between tests
   - Verify mock implementations
   - Check mock file locations

4. **Coverage Issues**
   - Review collectCoverageFrom patterns
   - Check for untested code paths
   - Verify test completeness

### Debug Commands

```bash
# Run tests with debug output
npm run test:debug

# Run specific test with verbose output
npm run test:verbose -- --testNamePattern="specific test"

# Clear cache and run tests
npm run test:clean && npm test
```

### Environment Variables

```bash
# Set test environment
NODE_ENV=test npm test

# Enable debug mode
DEBUG=true npm test

# Set API URL for tests
REACT_APP_API_URL=http://localhost:8000 npm test
```

## Coverage Reports

Coverage reports are generated in the `coverage/` directory:

- `coverage/lcov-report/index.html` - HTML coverage report
- `coverage/lcov.info` - LCOV format for CI/CD
- `coverage/coverage-final.json` - JSON format

### Coverage Thresholds

- **Unit Tests**: 70% (branches, functions, lines, statements)
- **Integration Tests**: 60% (branches, functions, lines, statements)
- **E2E Tests**: 50% (branches, functions, lines, statements)

## Continuous Integration

### GitHub Actions Example

```yaml
name: Frontend Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '16'
      - run: npm ci
      - run: npm run test:ci
      - run: npm run test:coverage
```

### Pre-commit Hooks

```json
{
  "husky": {
    "hooks": {
      "pre-commit": "npm run test:changed"
    }
  }
}
```

## Additional Resources

- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro)
- [MSW Documentation](https://mswjs.io/docs/)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)

---

For questions or issues with the testing framework, please refer to the troubleshooting section or contact the development team. 