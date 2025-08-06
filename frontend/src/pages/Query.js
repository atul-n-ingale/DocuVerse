import React, { useState } from 'react';
import { Search, Send, FileText, Clock, TrendingUp } from 'lucide-react';
import axios from 'axios';
import { API_URL } from '../api';
import toast from 'react-hot-toast';

const Query = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [maxResults, setMaxResults] = useState(5);
  const [includeSources, setIncludeSources] = useState(true);

  const handleSubmit = async e => {
    e.preventDefault();

    if (!query.trim()) {
      toast.error('Please enter a query');
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const response = await axios.post(`${API_URL}/query`, {
        query: query.trim(),
        max_results: maxResults,
        include_sources: includeSources,
      });

      setResult(response.data);
      toast.success('Query processed successfully!');
    } catch (error) {
      console.error('Query error:', error);
      toast.error(error.response?.data?.detail || 'Failed to process query');
    } finally {
      setLoading(false);
    }
  };

  const formatTime = seconds => {
    return `${(seconds * 1000).toFixed(0)}ms`;
  };

  const formatConfidence = confidence => {
    return `${(confidence * 100).toFixed(1)}%`;
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Semantic Search
        </h1>
        <p className="text-gray-600">
          Ask questions about your uploaded documents and get AI-powered
          answers.
        </p>
      </div>

      {/* Query Form */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
        <form onSubmit={handleSubmit}>
          <div className="flex flex-col space-y-4">
            <div>
              <label
                htmlFor="query"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Your Question
              </label>
              <div className="relative">
                <textarea
                  id="query"
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  placeholder="Ask a question about your documents..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  rows={3}
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="absolute bottom-3 right-3 p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? (
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <Send className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>

            <div className="flex flex-wrap gap-4">
              <div>
                <label
                  htmlFor="maxResults"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Max Results
                </label>
                <select
                  id="maxResults"
                  value={maxResults}
                  onChange={e => setMaxResults(Number(e.target.value))}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={loading}
                >
                  <option value={3}>3</option>
                  <option value={5}>5</option>
                  <option value={10}>10</option>
                  <option value={15}>15</option>
                </select>
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="includeSources"
                  checked={includeSources}
                  onChange={e => setIncludeSources(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  disabled={loading}
                />
                <label
                  htmlFor="includeSources"
                  className="text-sm font-medium text-gray-700"
                >
                  Include Sources
                </label>
              </div>
            </div>
          </div>
        </form>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Answer */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Answer</h2>
            <div className="prose max-w-none">
              <p className="text-gray-800 leading-relaxed">{result.answer}</p>
            </div>

            {/* Metadata */}
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="flex items-center space-x-6 text-sm text-gray-600">
                <div className="flex items-center space-x-1">
                  <Clock className="w-4 h-4" />
                  <span>Processed in {formatTime(result.processing_time)}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <TrendingUp className="w-4 h-4" />
                  <span>Confidence: {formatConfidence(result.confidence)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Sources */}
          {includeSources && result.sources && result.sources.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Sources
              </h2>
              <div className="space-y-3">
                {result.sources.map((source, index) => (
                  <div
                    key={index}
                    className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg"
                  >
                    <FileText className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900">
                        {source.filename}
                      </p>
                      <div className="flex items-center space-x-4 text-sm text-gray-600 mt-1">
                        <span>Chunk #{source.chunk_index + 1}</span>
                        {source.page_number && (
                          <span>Page {source.page_number}</span>
                        )}
                        <span>Score: {(source.score * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center space-x-3">
            <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-600">Processing your query...</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default Query;
