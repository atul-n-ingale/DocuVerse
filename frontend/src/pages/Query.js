import React, { useState, useEffect } from 'react';
import {
  Send,
  FileText,
  Clock,
  TrendingUp,
  MessageSquare,
  Plus,
  Trash2,
  Brain,
  History,
} from 'lucide-react';
import axios from 'axios';
import { API_URL } from '../api';
import toast from 'react-hot-toast';

const Query = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [maxResults, setMaxResults] = useState(5);
  const [includeSources, setIncludeSources] = useState(true);
  const [includeReasoning, setIncludeReasoning] = useState(true);

  // Conversation management
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [showSessionModal, setShowSessionModal] = useState(false);
  const [newSessionTitle, setNewSessionTitle] = useState('');

  // Load sessions on component mount
  useEffect(() => {
    loadSessions();
  }, []);

  // Load conversation history when session changes
  useEffect(() => {
    if (currentSession) {
      loadConversationHistory(currentSession.id);
    }
  }, [currentSession]);

  const loadSessions = async () => {
    try {
      const response = await axios.get(`${API_URL}/conversations`);
      setSessions(response.data);

      // Set first session as current if no session is selected
      if (response.data.length > 0 && !currentSession) {
        setCurrentSession(response.data[0]);
      }
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  };

  const loadConversationHistory = async sessionId => {
    try {
      const response = await axios.get(`${API_URL}/conversations/${sessionId}`);
      setConversationHistory(response.data.messages || []);
    } catch (error) {
      console.error('Failed to load conversation history:', error);
    }
  };

  const createSession = async () => {
    if (!newSessionTitle.trim()) {
      toast.error('Please enter a session title');
      return;
    }

    try {
      const response = await axios.post(`${API_URL}/conversations`, {
        title: newSessionTitle.trim(),
      });

      setSessions([...sessions, response.data]);
      setCurrentSession(response.data);
      setConversationHistory([]);
      setNewSessionTitle('');
      setShowSessionModal(false);
      toast.success('New conversation session created!');
    } catch (error) {
      console.error('Failed to create session:', error);
      toast.error('Failed to create session');
    }
  };

  const deleteSession = async sessionId => {
    try {
      await axios.delete(`${API_URL}/conversations/${sessionId}`);
      setSessions(sessions.filter(s => s.id !== sessionId));

      if (currentSession?.id === sessionId) {
        setCurrentSession(sessions[0] || null);
        setConversationHistory([]);
      }

      toast.success('Session deleted successfully!');
    } catch (error) {
      console.error('Failed to delete session:', error);
      toast.error('Failed to delete session');
    }
  };

  const handleSubmit = async e => {
    e.preventDefault();

    if (!query.trim()) {
      toast.error('Please enter a query');
      return;
    }

    if (!currentSession) {
      toast.error('Please create or select a conversation session');
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const response = await axios.post(`${API_URL}/query/enhanced`, {
        query: query.trim(),
        session_id: currentSession.id,
        max_results: maxResults,
        include_sources: includeSources,
        include_reasoning: includeReasoning,
      });

      setResult(response.data);

      // Update conversation history
      await loadConversationHistory(currentSession.id);

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
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Enhanced AI Chat
        </h1>
        <p className="text-gray-600">
          Ask questions about your documents with advanced AI reasoning and
          conversation memory.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar - Sessions */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">
                Conversations
              </h2>
              <button
                onClick={() => setShowSessionModal(true)}
                className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              >
                <Plus className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-2">
              {sessions.map(session => (
                <div
                  key={session.id}
                  className={`p-3 rounded-lg cursor-pointer transition-colors ${
                    currentSession?.id === session.id
                      ? 'bg-blue-50 border border-blue-200'
                      : 'hover:bg-gray-50'
                  }`}
                  onClick={() => setCurrentSession(session)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 truncate">
                        {session.title}
                      </p>
                      <p className="text-sm text-gray-500">
                        {session.message_count} messages
                      </p>
                    </div>
                    <button
                      onClick={e => {
                        e.stopPropagation();
                        deleteSession(session.id);
                      }}
                      className="p-1 text-red-500 hover:bg-red-50 rounded transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {sessions.length === 0 && (
              <p className="text-gray-500 text-sm text-center py-4">
                No conversations yet. Create one to get started!
              </p>
            )}
          </div>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3 space-y-6">
          {/* Query Form */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
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
                      disabled={loading || !currentSession}
                    />
                    <button
                      type="submit"
                      disabled={loading || !currentSession}
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

                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="includeReasoning"
                      checked={includeReasoning}
                      onChange={e => setIncludeReasoning(e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      disabled={loading}
                    />
                    <label
                      htmlFor="includeReasoning"
                      className="text-sm font-medium text-gray-700"
                    >
                      Show Reasoning
                    </label>
                  </div>
                </div>
              </div>
            </form>
          </div>

          {/* Conversation History */}
          {conversationHistory.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <History className="w-5 h-5 mr-2" />
                Conversation History
              </h2>
              <div className="space-y-4">
                {conversationHistory.map((message, index) => (
                  <div
                    key={index}
                    className={`p-4 rounded-lg ${
                      message.role === 'user'
                        ? 'bg-blue-50 border border-blue-200'
                        : 'bg-gray-50 border border-gray-200'
                    }`}
                  >
                    <div className="flex items-start space-x-3">
                      <div
                        className={`p-2 rounded-full ${
                          message.role === 'user'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-600 text-white'
                        }`}
                      >
                        {message.role === 'user' ? (
                          <MessageSquare className="w-4 h-4" />
                        ) : (
                          <Brain className="w-4 h-4" />
                        )}
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-700 mb-1">
                          {message.role === 'user' ? 'You' : 'AI Assistant'}
                        </p>
                        <p className="text-gray-800">{message.content}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Current Result */}
          {result && (
            <div className="space-y-6">
              {/* Answer */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Answer
                </h2>
                <div className="prose max-w-none">
                  <p className="text-gray-800 leading-relaxed">
                    {result.answer}
                  </p>
                </div>

                {/* Metadata */}
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="flex items-center space-x-6 text-sm text-gray-600">
                    <div className="flex items-center space-x-1">
                      <Clock className="w-4 h-4" />
                      <span>
                        Processed in {formatTime(result.processing_time)}
                      </span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <TrendingUp className="w-4 h-4" />
                      <span>
                        Confidence: {formatConfidence(result.confidence)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Reasoning Steps */}
              {includeReasoning &&
                result.reasoning_steps &&
                result.reasoning_steps.length > 0 && (
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                      <Brain className="w-5 h-5 mr-2" />
                      Reasoning Process
                    </h2>
                    <div className="space-y-3">
                      {result.reasoning_steps.map((step, index) => (
                        <div
                          key={index}
                          className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg"
                        >
                          <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium flex-shrink-0">
                            {index + 1}
                          </div>
                          <p className="text-gray-800">{step}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

              {/* Sources */}
              {includeSources &&
                result.sources &&
                result.sources.length > 0 && (
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
                              <span>
                                Score: {(source.score * 100).toFixed(1)}%
                              </span>
                              {source.cross_encoder_score && (
                                <span>
                                  Rerank:{' '}
                                  {(source.cross_encoder_score * 100).toFixed(
                                    1
                                  )}
                                  %
                                </span>
                              )}
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
                <p className="text-gray-600">
                  Processing your query with advanced AI reasoning...
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Session Creation Modal */}
      {showSessionModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Create New Conversation
            </h3>
            <input
              type="text"
              value={newSessionTitle}
              onChange={e => setNewSessionTitle(e.target.value)}
              placeholder="Enter conversation title..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent mb-4"
              onKeyPress={e => e.key === 'Enter' && createSession()}
            />
            <div className="flex space-x-3">
              <button
                onClick={createSession}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Create
              </button>
              <button
                onClick={() => {
                  setShowSessionModal(false);
                  setNewSessionTitle('');
                }}
                className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-400 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Query;
