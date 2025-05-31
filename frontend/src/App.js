import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Utility function for API calls
const apiCall = async (endpoint, options = {}) => {
  const token = localStorage.getItem('token');
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    ...options,
  };

  if (options.body) {
    config.body = JSON.stringify(options.body);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Something went wrong');
  }
  
  return response.json();
};

// Login Component
const Login = ({ onLoginSuccess, switchToRegister }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await apiCall('/api/auth/login', {
        method: 'POST',
        body: { email, password },
      });

      localStorage.setItem('token', response.access_token);
      onLoginSuccess();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-2xl p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Welcome Back</h1>
          <p className="text-gray-600">Sign in to your shared shopping lists</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your email"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your password"
              required
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-3 px-4 rounded-lg transition duration-200 disabled:opacity-50"
          >
            {loading ? 'Signing In...' : 'Sign In'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-gray-600">
            Don't have an account?{' '}
            <button
              onClick={switchToRegister}
              className="text-blue-500 hover:text-blue-600 font-semibold"
            >
              Sign up
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

// Register Component
const Register = ({ onRegisterSuccess, switchToLogin }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await apiCall('/api/auth/register', {
        method: 'POST',
        body: { name, email, password },
      });

      localStorage.setItem('token', response.access_token);
      onRegisterSuccess();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-500 to-blue-600 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-2xl p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Join Us</h1>
          <p className="text-gray-600">Create your account to start sharing lists</p>
        </div>

        <form onSubmit={handleRegister} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Full Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              placeholder="Enter your full name"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              placeholder="Enter your email"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              placeholder="Create a password"
              required
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-500 hover:bg-green-600 text-white font-semibold py-3 px-4 rounded-lg transition duration-200 disabled:opacity-50"
          >
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-gray-600">
            Already have an account?{' '}
            <button
              onClick={switchToLogin}
              className="text-green-500 hover:text-green-600 font-semibold"
            >
              Sign in
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

// Dashboard Component
const Dashboard = ({ onSelectList, onLogout }) => {
  const [lists, setLists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newListName, setNewListName] = useState('');
  const [creating, setCreating] = useState(false);
  const [user, setUser] = useState(null);

  useEffect(() => {
    fetchUserInfo();
    fetchLists();
  }, []);

  const fetchUserInfo = async () => {
    try {
      const userData = await apiCall('/api/auth/me');
      setUser(userData);
    } catch (err) {
      console.error('Failed to fetch user info:', err);
    }
  };

  const fetchLists = async () => {
    try {
      const listsData = await apiCall('/api/lists');
      setLists(listsData);
    } catch (err) {
      console.error('Failed to fetch lists:', err);
    } finally {
      setLoading(false);
    }
  };

  const createList = async (e) => {
    e.preventDefault();
    setCreating(true);

    try {
      await apiCall('/api/lists', {
        method: 'POST',
        body: { name: newListName },
      });

      setNewListName('');
      setShowCreateModal(false);
      fetchLists();
    } catch (err) {
      console.error('Failed to create list:', err);
    } finally {
      setCreating(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    onLogout();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading your shopping lists...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Shopping Lists</h1>
            {user && <p className="text-gray-600">Welcome back, {user.name}!</p>}
          </div>
          <button
            onClick={handleLogout}
            className="text-gray-600 hover:text-gray-800 font-medium"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-xl font-semibold text-gray-800">Your Lists</h2>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg font-medium transition duration-200"
          >
            + New List
          </button>
        </div>

        {lists.length === 0 ? (
          <div className="text-center py-16">
            <div className="text-gray-400 text-6xl mb-4">📝</div>
            <h3 className="text-xl font-semibold text-gray-600 mb-2">No lists yet</h3>
            <p className="text-gray-500 mb-6">Create your first shopping list to get started</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg font-medium transition duration-200"
            >
              Create Your First List
            </button>
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {lists.map((list) => (
              <div
                key={list.id}
                onClick={() => onSelectList(list)}
                className="bg-white rounded-xl shadow-sm border hover:shadow-md transition duration-200 cursor-pointer p-6"
              >
                <h3 className="text-lg font-semibold text-gray-800 mb-2">{list.name}</h3>
                <p className="text-gray-500 text-sm mb-4">
                  Created {new Date(list.created_at).toLocaleDateString()}
                </p>
                <div className="flex items-center text-sm text-gray-400">
                  <span>👥 {list.shared_with.length + 1} member{list.shared_with.length === 0 ? '' : 's'}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Create List Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-md w-full p-6">
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Create New List</h3>
            <form onSubmit={createList}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  List Name
                </label>
                <input
                  type="text"
                  value={newListName}
                  onChange={(e) => setNewListName(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., Weekly Groceries"
                  required
                />
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setNewListName('');
                  }}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg font-medium transition duration-200 disabled:opacity-50"
                >
                  {creating ? 'Creating...' : 'Create List'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

// Shopping List View Component
const ShoppingListView = ({ list, onBack }) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newItemName, setNewItemName] = useState('');
  const [showShareModal, setShowShareModal] = useState(false);
  const [shareEmail, setShareEmail] = useState('');
  const [sharing, setSharing] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(null);

  useEffect(() => {
    fetchItems();
    
    // Set up polling for real-time updates every 3 seconds
    const interval = setInterval(fetchItems, 3000);
    setRefreshInterval(interval);

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [list.id]);

  const fetchItems = async () => {
    try {
      const itemsData = await apiCall(`/api/lists/${list.id}/items`);
      setItems(itemsData);
    } catch (err) {
      console.error('Failed to fetch items:', err);
    } finally {
      setLoading(false);
    }
  };

  const addItem = async (e) => {
    e.preventDefault();
    if (!newItemName.trim()) return;

    try {
      await apiCall(`/api/lists/${list.id}/items`, {
        method: 'POST',
        body: { name: newItemName.trim() },
      });

      setNewItemName('');
      fetchItems(); // Refresh immediately after adding
    } catch (err) {
      console.error('Failed to add item:', err);
    }
  };

  const toggleItem = async (itemId, currentStatus) => {
    try {
      await apiCall(`/api/items/${itemId}`, {
        method: 'PUT',
        body: { is_purchased: !currentStatus },
      });

      fetchItems(); // Refresh immediately after toggling
    } catch (err) {
      console.error('Failed to toggle item:', err);
    }
  };

  const deleteItem = async (itemId) => {
    try {
      await apiCall(`/api/items/${itemId}`, {
        method: 'DELETE',
      });

      fetchItems(); // Refresh immediately after deleting
    } catch (err) {
      console.error('Failed to delete item:', err);
    }
  };

  const shareList = async (e) => {
    e.preventDefault();
    setSharing(true);

    try {
      await apiCall(`/api/lists/${list.id}/share`, {
        method: 'POST',
        body: { email: shareEmail },
      });

      setShareEmail('');
      setShowShareModal(false);
      alert('List shared successfully!');
    } catch (err) {
      alert(err.message);
    } finally {
      setSharing(false);
    }
  };

  const remainingItems = items.filter(item => !item.is_purchased);
  const purchasedItems = items.filter(item => item.is_purchased);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading items...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={onBack}
                className="text-gray-600 hover:text-gray-800"
              >
                ← Back
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-800">{list.name}</h1>
                <p className="text-gray-500 text-sm">
                  {remainingItems.length} item{remainingItems.length !== 1 ? 's' : ''} remaining
                </p>
              </div>
            </div>
            <button
              onClick={() => setShowShareModal(true)}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-medium transition duration-200"
            >
              Share List
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Add Item Form */}
        <div className="bg-white rounded-xl shadow-sm border p-6 mb-8">
          <form onSubmit={addItem} className="flex space-x-4">
            <input
              type="text"
              value={newItemName}
              onChange={(e) => setNewItemName(e.target.value)}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Add an item to your list..."
            />
            <button
              type="submit"
              className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg font-medium transition duration-200"
            >
              Add Item
            </button>
          </form>
        </div>

        {/* Items List */}
        <div className="space-y-6">
          {/* Remaining Items */}
          {remainingItems.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border">
              <div className="p-6 border-b">
                <h2 className="text-lg font-semibold text-gray-800">Shopping List</h2>
              </div>
              <div className="divide-y">
                {remainingItems.map((item) => (
                  <div key={item.id} className="p-4 flex items-center justify-between hover:bg-gray-50">
                    <div className="flex items-center space-x-3">
                      <button
                        onClick={() => toggleItem(item.id, item.is_purchased)}
                        className="w-6 h-6 rounded-full border-2 border-gray-300 hover:border-blue-500 transition duration-200"
                      />
                      <div>
                        <p className="font-medium text-gray-800">{item.name}</p>
                        <p className="text-sm text-gray-500">Qty: {item.quantity}</p>
                      </div>
                    </div>
                    <button
                      onClick={() => deleteItem(item.id)}
                      className="text-gray-400 hover:text-red-500 transition duration-200"
                    >
                      🗑️
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Purchased Items */}
          {purchasedItems.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border">
              <div className="p-6 border-b">
                <h2 className="text-lg font-semibold text-gray-800">Purchased ({purchasedItems.length})</h2>
              </div>
              <div className="divide-y">
                {purchasedItems.map((item) => (
                  <div key={item.id} className="p-4 flex items-center justify-between hover:bg-gray-50 opacity-60">
                    <div className="flex items-center space-x-3">
                      <button
                        onClick={() => toggleItem(item.id, item.is_purchased)}
                        className="w-6 h-6 rounded-full bg-green-500 border-2 border-green-500 flex items-center justify-center"
                      >
                        <span className="text-white text-xs">✓</span>
                      </button>
                      <div>
                        <p className="font-medium text-gray-800 line-through">{item.name}</p>
                        <p className="text-sm text-gray-500">Qty: {item.quantity}</p>
                      </div>
                    </div>
                    <button
                      onClick={() => deleteItem(item.id)}
                      className="text-gray-400 hover:text-red-500 transition duration-200"
                    >
                      🗑️
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Empty State */}
          {items.length === 0 && (
            <div className="text-center py-16 bg-white rounded-xl shadow-sm border">
              <div className="text-gray-400 text-6xl mb-4">🛒</div>
              <h3 className="text-xl font-semibold text-gray-600 mb-2">Your list is empty</h3>
              <p className="text-gray-500">Add some items to get started!</p>
            </div>
          )}
        </div>
      </main>

      {/* Share Modal */}
      {showShareModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-md w-full p-6">
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Share List</h3>
            <form onSubmit={shareList}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address
                </label>
                <input
                  type="email"
                  value={shareEmail}
                  onChange={(e) => setShareEmail(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter email to share with"
                  required
                />
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowShareModal(false);
                    setShareEmail('');
                  }}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={sharing}
                  className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg font-medium transition duration-200 disabled:opacity-50"
                >
                  {sharing ? 'Sharing...' : 'Share List'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

// Main App Component
function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [selectedList, setSelectedList] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('token');
    if (token) {
      setIsAuthenticated(true);
    }
    setLoading(false);
  }, []);

  const handleAuthSuccess = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setSelectedList(null);
  };

  const handleSelectList = (list) => {
    setSelectedList(list);
  };

  const handleBackToDashboard = () => {
    setSelectedList(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return showRegister ? (
      <Register
        onRegisterSuccess={handleAuthSuccess}
        switchToLogin={() => setShowRegister(false)}
      />
    ) : (
      <Login
        onLoginSuccess={handleAuthSuccess}
        switchToRegister={() => setShowRegister(true)}
      />
    );
  }

  if (selectedList) {
    return (
      <ShoppingListView
        list={selectedList}
        onBack={handleBackToDashboard}
      />
    );
  }

  return (
    <Dashboard
      onSelectList={handleSelectList}
      onLogout={handleLogout}
    />
  );
}

export default App;