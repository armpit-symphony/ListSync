import React, { useState, useEffect } from 'react';
import './App.css';
import LoadingSpinner from './components/LoadingSpinner';
import { ToastContainer } from './components/NotificationToast';
import useToast from './hooks/useToast';
import ErrorBoundary from './components/ErrorBoundary';

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

// Landing Page Component
const LandingPage = ({ onHouseholdLogin, onStoreLogin, onAdminLogin }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full text-center">
        <div className="mb-12">
          <h1 className="text-5xl font-bold text-white mb-6">ShopSync</h1>
          <p className="text-xl text-blue-100 mb-8">
            The shared shopping list platform connecting households with local stores
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-3xl mx-auto">
          {/* Household Users */}
          <div className="bg-white rounded-xl shadow-2xl p-8 hover:transform hover:scale-105 transition duration-300">
            <div className="text-6xl mb-4">🏠</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">For Households</h2>
            <p className="text-gray-600 mb-6">
              Create shared shopping lists with your household. See local store prices and never forget an item again.
            </p>
            <div className="space-y-3 mb-6 text-left">
              <div className="flex items-center text-gray-700">
                <span className="text-green-500 mr-2">✓</span>
                Shared household shopping lists
              </div>
              <div className="flex items-center text-gray-700">
                <span className="text-green-500 mr-2">✓</span>
                Real-time collaboration
              </div>
              <div className="flex items-center text-gray-700">
                <span className="text-green-500 mr-2">✓</span>
                Local store prices
              </div>
              <div className="flex items-center text-gray-700">
                <span className="text-green-500 mr-2">✓</span>
                Free forever
              </div>
            </div>
            <button
              onClick={onHouseholdLogin}
              className="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-3 px-4 rounded-lg transition duration-200"
            >
              Get Started - Free
            </button>
          </div>

          {/* Stores */}
          <div className="bg-white rounded-xl shadow-2xl p-8 hover:transform hover:scale-105 transition duration-300">
            <div className="text-6xl mb-4">🏪</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">For Stores</h2>
            <p className="text-gray-600 mb-6">
              Advertise your products to local customers. Increase foot traffic and customer engagement.
            </p>
            <div className="space-y-3 mb-6 text-left">
              <div className="flex items-center text-gray-700">
                <span className="text-green-500 mr-2">✓</span>
                Product advertising platform
              </div>
              <div className="flex items-center text-gray-700">
                <span className="text-green-500 mr-2">✓</span>
                Target local customers
              </div>
              <div className="flex items-center text-gray-700">
                <span className="text-green-500 mr-2">✓</span>
                $12/month or $74.99/year
              </div>
              <div className="flex items-center text-gray-700">
                <span className="text-green-500 mr-2">✓</span>
                7-day free trial
              </div>
            </div>
            <button
              onClick={onStoreLogin}
              className="w-full bg-green-500 hover:bg-green-600 text-white font-semibold py-3 px-4 rounded-lg transition duration-200"
            >
              Start Free Trial
            </button>
          </div>
        </div>

        {/* Admin Link */}
        <div className="mt-8">
          <button
            onClick={onAdminLogin}
            className="text-blue-100 hover:text-white text-sm underline"
          >
            Admin Access
          </button>
        </div>

        <div className="mt-12 text-blue-100">
          <p className="text-lg">Trusted by households and stores nationwide</p>
        </div>
      </div>
    </div>
  );
};

// Admin Login Component (Enhanced)
const AdminLogin = ({ onLoginSuccess, onBack, showToast }) => {
  const [email, setEmail] = useState('admin@shopsync.com'); // Pre-fill for convenience
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await apiCall('/api/admin/auth/login', {
        method: 'POST',
        body: { email, password },
      });

      localStorage.setItem('token', response.access_token);
      localStorage.setItem('userType', response.user_type);
      showToast.success('Admin login successful! Welcome to the admin dashboard.');
      onLoginSuccess('admin');
    } catch (err) {
      showToast.error(`Login failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-700 to-gray-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-2xl p-8 transform transition-all duration-300 hover:scale-105">
        <div className="text-center mb-8">
          <button
            onClick={onBack}
            className="text-gray-600 hover:text-gray-800 mb-4 flex items-center transition duration-200"
          >
            ← Back to Home
          </button>
          <div className="text-4xl mb-4">🔐</div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Admin Access</h1>
          <p className="text-gray-600">Platform administration dashboard</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Admin Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent transition duration-200"
              placeholder="Enter admin email"
              required
              disabled={loading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent transition duration-200"
                placeholder="Enter password"
                required
                disabled={loading}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                disabled={loading}
              >
                {showPassword ? '👁️' : '👁️‍🗨️'}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gray-700 hover:bg-gray-800 text-white font-semibold py-3 px-4 rounded-lg transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {loading ? (
              <>
                <LoadingSpinner size="sm" />
                <span className="ml-2">Signing In...</span>
              </>
            ) : (
              'Admin Sign In'
            )}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-gray-500">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="font-medium">Default Credentials:</p>
            <p>Email: admin@shopsync.com</p>
            <p>Password: admin123</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Admin Dashboard Component
const AdminDashboard = ({ onLogout }) => {
  const [stats, setStats] = useState(null);
  const [subscriptions, setSubscriptions] = useState([]);
  const [paymentConfig, setPaymentConfig] = useState({});
  const [configStatus, setConfigStatus] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [adminInfo, setAdminInfo] = useState(null);

  useEffect(() => {
    fetchAdminData();
  }, []);

  const fetchAdminData = async () => {
    try {
      const [statsData, subscriptionsData, configStatusData, adminData] = await Promise.all([
        apiCall('/api/admin/stats'),
        apiCall('/api/admin/subscriptions'),
        apiCall('/api/admin/payment/config'),
        apiCall('/api/admin/auth/me')
      ]);

      setStats(statsData);
      setSubscriptions(subscriptionsData.subscriptions);
      setConfigStatus(configStatusData);
      setAdminInfo(adminData);
    } catch (err) {
      console.error('Failed to fetch admin data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleConfigUpdate = async () => {
    try {
      await apiCall('/api/admin/payment/config', {
        method: 'POST',
        body: paymentConfig,
      });

      alert('Payment configuration updated successfully');
      fetchAdminData();
    } catch (err) {
      alert('Failed to update configuration: ' + err.message);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userType');
    onLogout();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading admin dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">ShopSync Admin</h1>
            {adminInfo && <p className="text-gray-600">Welcome, {adminInfo.name}</p>}
          </div>
          <button
            onClick={handleLogout}
            className="text-gray-600 hover:text-gray-800 font-medium"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {['overview', 'payments', 'subscriptions'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-2 px-1 border-b-2 font-medium text-sm capitalize ${
                  activeTab === tab
                    ? 'border-gray-500 text-gray-700'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {activeTab === 'overview' && (
          <AdminOverview stats={stats} />
        )}
        {activeTab === 'payments' && (
          <AdminPayments 
            paymentConfig={paymentConfig}
            setPaymentConfig={setPaymentConfig}
            configStatus={configStatus}
            onConfigUpdate={handleConfigUpdate}
          />
        )}
        {activeTab === 'subscriptions' && (
          <AdminSubscriptions subscriptions={subscriptions} />
        )}
      </main>
    </div>
  );
};

// Admin Overview Component
const AdminOverview = ({ stats }) => {
  if (!stats) return <div>Loading...</div>;

  return (
    <div className="space-y-8">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Total Stores</h3>
          <p className="text-3xl font-bold text-blue-500">{stats.total_stores}</p>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Active Subscriptions</h3>
          <p className="text-3xl font-bold text-green-500">{stats.active_subscriptions}</p>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Trial Stores</h3>
          <p className="text-3xl font-bold text-yellow-500">{stats.trial_stores}</p>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Total Households</h3>
          <p className="text-3xl font-bold text-purple-500">{stats.total_households}</p>
        </div>
      </div>

      {/* Revenue Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Monthly Revenue</h3>
          <p className="text-3xl font-bold text-green-600">${stats.monthly_revenue.toFixed(2)}</p>
          <p className="text-sm text-gray-500">From monthly plans</p>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Yearly Revenue</h3>
          <p className="text-3xl font-bold text-green-600">${stats.yearly_revenue.toFixed(2)}</p>
          <p className="text-sm text-gray-500">From yearly plans</p>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Total MRR</h3>
          <p className="text-3xl font-bold text-green-700">${stats.total_monthly_recurring.toFixed(2)}</p>
          <p className="text-sm text-gray-500">Monthly recurring revenue</p>
        </div>
      </div>

      {/* Additional Stats */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Platform Overview</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <p className="text-gray-600 mb-2"><strong>Total Products Listed:</strong> {stats.total_products}</p>
            <p className="text-gray-600 mb-2"><strong>Conversion Rate:</strong> {((stats.active_subscriptions / stats.total_stores) * 100).toFixed(1)}%</p>
          </div>
          <div>
            <p className="text-gray-600 mb-2"><strong>Average Revenue Per Store:</strong> ${(stats.total_monthly_recurring / stats.active_subscriptions || 0).toFixed(2)}</p>
            <p className="text-gray-600 mb-2"><strong>Stores in Trial:</strong> {stats.trial_stores}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Admin Payments Component
const AdminPayments = ({ paymentConfig, setPaymentConfig, configStatus, onConfigUpdate }) => {
  const handleInputChange = (field, value) => {
    setPaymentConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-semibold text-gray-800">Payment Configuration</h2>
      
      {/* Configuration Status */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Configuration Status</h3>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-gray-700">Stripe Integration</span>
            <span className={`px-3 py-1 rounded-full text-sm ${
              configStatus.stripe_configured 
                ? 'bg-green-100 text-green-800' 
                : 'bg-red-100 text-red-800'
            }`}>
              {configStatus.stripe_configured ? 'Configured' : 'Not Configured'}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-700">PayPal Integration</span>
            <span className={`px-3 py-1 rounded-full text-sm ${
              configStatus.paypal_configured 
                ? 'bg-green-100 text-green-800' 
                : 'bg-red-100 text-red-800'
            }`}>
              {configStatus.paypal_configured ? 'Configured' : 'Not Configured'}
            </span>
          </div>
        </div>
      </div>

      {/* Stripe Configuration */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Stripe Configuration</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Secret Key
            </label>
            <input
              type="password"
              value={paymentConfig.stripe_secret_key || ''}
              onChange={(e) => handleInputChange('stripe_secret_key', e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent"
              placeholder="sk_test_... or sk_live_..."
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Publishable Key
            </label>
            <input
              type="text"
              value={paymentConfig.stripe_publishable_key || ''}
              onChange={(e) => handleInputChange('stripe_publishable_key', e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent"
              placeholder="pk_test_... or pk_live_..."
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Webhook Endpoint Secret
            </label>
            <input
              type="password"
              value={paymentConfig.stripe_endpoint_secret || ''}
              onChange={(e) => handleInputChange('stripe_endpoint_secret', e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent"
              placeholder="whsec_..."
            />
          </div>
        </div>
      </div>

      {/* PayPal Configuration */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">PayPal Configuration</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Client ID
            </label>
            <input
              type="text"
              value={paymentConfig.paypal_client_id || ''}
              onChange={(e) => handleInputChange('paypal_client_id', e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent"
              placeholder="PayPal Client ID"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Client Secret
            </label>
            <input
              type="password"
              value={paymentConfig.paypal_client_secret || ''}
              onChange={(e) => handleInputChange('paypal_client_secret', e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent"
              placeholder="PayPal Client Secret"
            />
          </div>
        </div>
      </div>

      {/* Update Button */}
      <div className="flex justify-end">
        <button
          onClick={onConfigUpdate}
          className="bg-gray-700 hover:bg-gray-800 text-white px-8 py-3 rounded-lg font-medium transition duration-200"
        >
          Update Configuration
        </button>
      </div>

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-blue-800 mb-4">Setup Instructions</h3>
        <div className="space-y-3 text-blue-700">
          <p><strong>Stripe:</strong> Get your API keys from <a href="https://dashboard.stripe.com/apikeys" target="_blank" rel="noopener noreferrer" className="underline">Stripe Dashboard</a></p>
          <p><strong>PayPal:</strong> Create an app at <a href="https://developer.paypal.com/developer/applications" target="_blank" rel="noopener noreferrer" className="underline">PayPal Developer</a></p>
          <p><strong>Webhooks:</strong> Set up webhook endpoints for payment event handling</p>
          <p><strong>Security:</strong> All API keys are encrypted before storage</p>
        </div>
      </div>
    </div>
  );
};

// Admin Subscriptions Component
const AdminSubscriptions = ({ subscriptions }) => {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold text-gray-800">Store Subscriptions</h2>
      
      {subscriptions.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-xl shadow-sm border">
          <div className="text-gray-400 text-6xl mb-4">📊</div>
          <h3 className="text-xl font-semibold text-gray-600 mb-2">No subscriptions yet</h3>
          <p className="text-gray-500">Stores haven't started subscribing yet</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-800">All Subscriptions</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Store
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Plan
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Revenue
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Provider
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Start Date
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {subscriptions.map((subscription) => (
                  <tr key={subscription.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {subscription.store_name || 'Unknown Store'}
                        </div>
                        <div className="text-sm text-gray-500">
                          {subscription.store_email}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-900 capitalize">
                        {subscription.plan}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        subscription.status === 'active' 
                          ? 'bg-green-100 text-green-800'
                          : subscription.status === 'trial'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {subscription.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${subscription.monthly_price.toFixed(2)}/month
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 capitalize">
                      {subscription.provider}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(subscription.start_date).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

// Store Subscription Component (Updated Pricing)
const StoreSubscription = ({ subscription, onSubscriptionChange }) => {
  const [loading, setLoading] = useState(false);

  const handleStripeSubscribe = async (plan) => {
    setLoading(true);
    try {
      const response = await apiCall('/api/stripe/create-checkout-session', {
        method: 'POST',
        body: { plan_type: plan }
      });
      
      // Redirect to Stripe Checkout
      window.location.href = response.session_url;
    } catch (err) {
      console.error('Stripe subscription failed:', err);
      alert('Failed to start subscription process: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  if (subscription) {
    return (
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Current Subscription</h2>
        <div className="space-y-4">
          <p><strong>Plan:</strong> {subscription.plan} Plan</p>
          <p><strong>Status:</strong> {subscription.status}</p>
          <p><strong>Monthly Price:</strong> ${subscription.monthly_price.toFixed(2)}</p>
          <p><strong>Expires:</strong> {new Date(subscription.end_date).toLocaleDateString()}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold text-gray-800">Choose Your Plan</h2>
      
      <div className="grid md:grid-cols-2 gap-6">
        {/* Monthly Plan - UPDATED PRICING */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Monthly Plan</h3>
          <p className="text-3xl font-bold text-gray-800 mb-4">$12.00<span className="text-lg font-normal">/month</span></p>
          <ul className="space-y-2 mb-6">
            <li className="flex items-center text-gray-700">
              <span className="text-green-500 mr-2">✓</span>
              Unlimited product listings
            </li>
            <li className="flex items-center text-gray-700">
              <span className="text-green-500 mr-2">✓</span>
              Local family advertising
            </li>
            <li className="flex items-center text-gray-700">
              <span className="text-green-500 mr-2">✓</span>
              Analytics dashboard
            </li>
            <li className="flex items-center text-gray-700">
              <span className="text-green-500 mr-2">✓</span>
              Customer insights
            </li>
          </ul>
          <button
            onClick={() => handleStripeSubscribe('monthly')}
            disabled={loading}
            className="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-3 px-4 rounded-lg transition duration-200 disabled:opacity-50"
          >
            {loading ? 'Processing...' : 'Subscribe Monthly - $12.00'}
          </button>
        </div>

        {/* Yearly Plan - UPDATED PRICING */}
        <div className="bg-white rounded-xl shadow-sm border p-6 ring-2 ring-green-500">
          <div className="text-center">
            <span className="bg-green-500 text-white px-3 py-1 rounded-full text-sm font-medium">BEST VALUE</span>
          </div>
          <h3 className="text-xl font-semibold text-gray-800 mb-4 mt-4">Yearly Plan</h3>
          <p className="text-3xl font-bold text-gray-800 mb-4">
            $74.99<span className="text-lg font-normal">/year</span>
            <span className="block text-sm text-gray-500">Just $6.25/month - Save 48%!</span>
          </p>
          <ul className="space-y-2 mb-6">
            <li className="flex items-center text-gray-700">
              <span className="text-green-500 mr-2">✓</span>
              Everything in Monthly Plan
            </li>
            <li className="flex items-center text-gray-700">
              <span className="text-green-500 mr-2">✓</span>
              48% savings vs monthly
            </li>
            <li className="flex items-center text-gray-700">
              <span className="text-green-500 mr-2">✓</span>
              Priority customer support
            </li>
            <li className="flex items-center text-gray-700">
              <span className="text-green-500 mr-2">✓</span>
              Advanced analytics
            </li>
          </ul>
          <button
            onClick={() => handleStripeSubscribe('yearly')}
            disabled={loading}
            className="w-full bg-green-500 hover:bg-green-600 text-white font-semibold py-3 px-4 rounded-lg transition duration-200 disabled:opacity-50"
          >
            {loading ? 'Processing...' : 'Subscribe Yearly - $74.99'}
          </button>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-blue-800 mb-2">🔒 Secure Payment Processing</h3>
        <p className="text-blue-700">
          All payments are processed securely through Stripe. Your payment information is never stored on our servers.
        </p>
      </div>
    </div>
  );
};

// Include all other existing components (HouseholdLogin, StoreLogin, etc.) with minimal changes
// Reusing existing components from previous version...

// Household Login Component (unchanged)
const HouseholdLogin = ({ onLoginSuccess, switchToRegister, onBack }) => {
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
      localStorage.setItem('userType', response.user_type);
      onLoginSuccess('household');
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
          <button
            onClick={onBack}
            className="text-gray-600 hover:text-gray-800 mb-4"
          >
            ← Back to Home
          </button>
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

// Household Register Component (unchanged)
const HouseholdRegister = ({ onRegisterSuccess, switchToLogin, onBack }) => {
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
      localStorage.setItem('userType', response.user_type);
      onRegisterSuccess('household');
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
          <button
            onClick={onBack}
            className="text-gray-600 hover:text-gray-800 mb-4"
          >
            ← Back to Home
          </button>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Join ShopSync</h1>
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

// Store Login Component (unchanged)
const StoreLogin = ({ onLoginSuccess, switchToRegister, onBack }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await apiCall('/api/store/auth/login', {
        method: 'POST',
        body: { email, password },
      });

      localStorage.setItem('token', response.access_token);
      localStorage.setItem('userType', response.user_type);
      onLoginSuccess('store');
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
          <button
            onClick={onBack}
            className="text-gray-600 hover:text-gray-800 mb-4"
          >
            ← Back to Home
          </button>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Store Login</h1>
          <p className="text-gray-600">Access your store dashboard</p>
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
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              placeholder="Enter your store email"
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
            className="w-full bg-green-500 hover:bg-green-600 text-white font-semibold py-3 px-4 rounded-lg transition duration-200 disabled:opacity-50"
          >
            {loading ? 'Signing In...' : 'Sign In'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-gray-600">
            New store?{' '}
            <button
              onClick={switchToRegister}
              className="text-green-500 hover:text-green-600 font-semibold"
            >
              Start free trial
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

// Store Register Component (unchanged)
const StoreRegister = ({ onRegisterSuccess, switchToLogin, onBack }) => {
  const [formData, setFormData] = useState({
    store_name: '',
    email: '',
    password: '',
    address: '',
    city: '',
    state: '',
    zip_code: '',
    phone: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await apiCall('/api/store/auth/register', {
        method: 'POST',
        body: formData,
      });

      localStorage.setItem('token', response.access_token);
      localStorage.setItem('userType', response.user_type);
      onRegisterSuccess('store');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-500 to-blue-600 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-white rounded-xl shadow-2xl p-8">
        <div className="text-center mb-8">
          <button
            onClick={onBack}
            className="text-gray-600 hover:text-gray-800 mb-4"
          >
            ← Back to Home
          </button>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Join as a Store</h1>
          <p className="text-gray-600">Start your 7-day free trial - Just $12/month!</p>
        </div>

        <form onSubmit={handleRegister} className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Store Name
              </label>
              <input
                type="text"
                name="store_name"
                value={formData.store_name}
                onChange={handleInputChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                placeholder="Your Store Name"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email Address
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                placeholder="store@example.com"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              placeholder="Create a password"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Address
            </label>
            <input
              type="text"
              name="address"
              value={formData.address}
              onChange={handleInputChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              placeholder="Store address"
              required
            />
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                City
              </label>
              <input
                type="text"
                name="city"
                value={formData.city}
                onChange={handleInputChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                placeholder="City"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                State
              </label>
              <input
                type="text"
                name="state"
                value={formData.state}
                onChange={handleInputChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                placeholder="State"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                ZIP Code
              </label>
              <input
                type="text"
                name="zip_code"
                value={formData.zip_code}
                onChange={handleInputChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                placeholder="ZIP"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Phone (Optional)
            </label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleInputChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              placeholder="Store phone number"
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
            {loading ? 'Creating Account...' : 'Start Free Trial'}
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

// Store Dashboard Component (updated pricing display)
const StoreDashboard = ({ onLogout }) => {
  const [storeInfo, setStoreInfo] = useState(null);
  const [subscription, setSubscription] = useState(null);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [showAddProduct, setShowAddProduct] = useState(false);

  useEffect(() => {
    fetchStoreData();
  }, []);

  const fetchStoreData = async () => {
    try {
      const [storeData, subscriptionData, productsData] = await Promise.all([
        apiCall('/api/store/auth/me'),
        apiCall('/api/store/subscription'),
        apiCall('/api/store/products')
      ]);

      setStoreInfo(storeData);
      setSubscription(subscriptionData);
      setProducts(productsData);
    } catch (err) {
      console.error('Failed to fetch store data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userType');
    onLogout();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading store dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">{storeInfo?.store_name}</h1>
            <p className="text-gray-600">
              {storeInfo?.subscription_status === 'trial' ? 'Free Trial Active' : 
               storeInfo?.subscription_status === 'active' ? 'Active Subscription' : 'Inactive'}
            </p>
          </div>
          <button
            onClick={handleLogout}
            className="text-gray-600 hover:text-gray-800 font-medium"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {['overview', 'products', 'subscription'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-2 px-1 border-b-2 font-medium text-sm capitalize ${
                  activeTab === tab
                    ? 'border-green-500 text-green-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {activeTab === 'overview' && (
          <StoreOverview storeInfo={storeInfo} subscription={subscription} products={products} />
        )}
        {activeTab === 'products' && (
          <StoreProducts 
            products={products} 
            onProductsChange={fetchStoreData}
            showAddProduct={showAddProduct}
            setShowAddProduct={setShowAddProduct}
          />
        )}
        {activeTab === 'subscription' && (
          <StoreSubscription subscription={subscription} onSubscriptionChange={fetchStoreData} />
        )}
      </main>
    </div>
  );
};

// Store Overview Component (updated pricing display)
const StoreOverview = ({ storeInfo, subscription, products }) => {
  return (
    <div className="space-y-8">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Products Listed</h3>
          <p className="text-3xl font-bold text-green-500">{products.length}</p>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Subscription Status</h3>
          <p className={`text-3xl font-bold capitalize ${
            storeInfo?.subscription_status === 'active' ? 'text-green-500' :
            storeInfo?.subscription_status === 'trial' ? 'text-blue-500' : 'text-red-500'
          }`}>
            {storeInfo?.subscription_status}
          </p>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Monthly Cost</h3>
          <p className="text-3xl font-bold text-gray-800">
            {subscription ? `$${subscription.monthly_price.toFixed(2)}` : 'No Plan'}
          </p>
        </div>
      </div>

      {/* Store Info */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Store Information</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <p className="text-gray-600 mb-2"><strong>Address:</strong> {storeInfo?.address}</p>
            <p className="text-gray-600 mb-2"><strong>City:</strong> {storeInfo?.city}, {storeInfo?.state}</p>
            <p className="text-gray-600 mb-2"><strong>ZIP:</strong> {storeInfo?.zip_code}</p>
          </div>
          <div>
            <p className="text-gray-600 mb-2"><strong>Email:</strong> {storeInfo?.email}</p>
            {storeInfo?.phone && (
              <p className="text-gray-600 mb-2"><strong>Phone:</strong> {storeInfo.phone}</p>
            )}
            <p className="text-gray-600 mb-2">
              <strong>Member since:</strong> {new Date(storeInfo?.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>
      </div>

      {/* Trial Notice */}
      {storeInfo?.subscription_status === 'trial' && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-blue-800 mb-2">🎉 Free Trial Active</h3>
          <p className="text-blue-700 mb-4">
            You're currently on a 7-day free trial. After your trial ends, choose a subscription plan to continue advertising your products.
          </p>
          <p className="text-blue-700">
            <strong>Trial expires:</strong> {new Date(storeInfo?.subscription_expires).toLocaleDateString()}
          </p>
        </div>
      )}
    </div>
  );
};

// Store Products Component (unchanged)
const StoreProducts = ({ products, onProductsChange, showAddProduct, setShowAddProduct }) => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-semibold text-gray-800">Your Products</h2>
        <button
          onClick={() => setShowAddProduct(true)}
          className="bg-green-500 hover:bg-green-600 text-white px-6 py-2 rounded-lg font-medium transition duration-200"
        >
          + Add Product
        </button>
      </div>

      {products.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-xl shadow-sm border">
          <div className="text-gray-400 text-6xl mb-4">📦</div>
          <h3 className="text-xl font-semibold text-gray-600 mb-2">No products yet</h3>
          <p className="text-gray-500 mb-6">Add your first product to start advertising to local customers</p>
          <button
            onClick={() => setShowAddProduct(true)}
            className="bg-green-500 hover:bg-green-600 text-white px-6 py-3 rounded-lg font-medium transition duration-200"
          >
            Add Your First Product
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {products.map((product) => (
            <div key={product.id} className="bg-white rounded-xl shadow-sm border p-6">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-800">{product.name}</h3>
                  <p className="text-gray-600 mb-2">{product.category}</p>
                  <p className="text-2xl font-bold text-green-500">${product.price.toFixed(2)}</p>
                  {product.description && (
                    <p className="text-gray-500 mt-2">{product.description}</p>
                  )}
                </div>
                <div className="flex items-center space-x-4">
                  <span className={`px-3 py-1 rounded-full text-sm ${
                    product.is_advertised 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {product.is_advertised ? 'Advertised' : 'Not Advertised'}
                  </span>
                  <button className="text-gray-400 hover:text-red-500">
                    🗑️
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Product Modal */}
      {showAddProduct && (
        <AddProductModal 
          onClose={() => setShowAddProduct(false)}
          onProductAdded={onProductsChange}
        />
      )}
    </div>
  );
};

// Add Product Modal Component (unchanged)
const AddProductModal = ({ onClose, onProductAdded }) => {
  const [formData, setFormData] = useState({
    name: '',
    category: '',
    price: '',
    description: '',
    is_advertised: true
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setFormData({
      ...formData,
      [e.target.name]: value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await apiCall('/api/store/products', {
        method: 'POST',
        body: {
          ...formData,
          price: parseFloat(formData.price)
        }
      });

      onProductAdded();
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl max-w-md w-full p-6">
        <h3 className="text-xl font-semibold text-gray-800 mb-4">Add New Product</h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Product Name
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              placeholder="e.g., Organic Bananas"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Category
            </label>
            <input
              type="text"
              name="category"
              value={formData.category}
              onChange={handleInputChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              placeholder="e.g., Produce, Dairy, Meat"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Price ($)
            </label>
            <input
              type="number"
              step="0.01"
              name="price"
              value={formData.price}
              onChange={handleInputChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              placeholder="0.00"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description (Optional)
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              rows="3"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              placeholder="Additional product details..."
            />
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              name="is_advertised"
              checked={formData.is_advertised}
              onChange={handleInputChange}
              className="h-4 w-4 text-green-500 focus:ring-green-500 border-gray-300 rounded"
            />
            <label className="ml-2 block text-sm text-gray-700">
              Advertise this product to local families
            </label>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="bg-green-500 hover:bg-green-600 text-white px-6 py-2 rounded-lg font-medium transition duration-200 disabled:opacity-50"
            >
              {loading ? 'Adding...' : 'Add Product'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Enhanced Shopping List View with Store Prices (unchanged from previous version)
const ShoppingListView = ({ list, onBack }) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newItemName, setNewItemName] = useState('');
  const [showShareModal, setShowShareModal] = useState(false);
  const [shareEmail, setShareEmail] = useState('');
  const [sharing, setSharing] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(null);
  const [showPrices, setShowPrices] = useState(false);
  const [storePrices, setStorePrices] = useState({});

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

  const fetchStorePrices = async (itemName) => {
    try {
      const prices = await apiCall(`/api/products/search?query=${encodeURIComponent(itemName)}&limit=3`);
      setStorePrices(prev => ({
        ...prev,
        [itemName]: prices
      }));
    } catch (err) {
      console.error('Failed to fetch store prices:', err);
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
      
      // Fetch store prices for the new item
      if (showPrices) {
        fetchStorePrices(newItemName.trim());
      }
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

  const toggleStorePrices = () => {
    const newShowPrices = !showPrices;
    setShowPrices(newShowPrices);
    
    if (newShowPrices) {
      // Fetch prices for all items
      items.forEach(item => {
        if (!item.is_purchased) {
          fetchStorePrices(item.name);
        }
      });
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
            <div className="flex space-x-3">
              <button
                onClick={toggleStorePrices}
                className={`px-4 py-2 rounded-lg font-medium transition duration-200 ${
                  showPrices 
                    ? 'bg-green-500 hover:bg-green-600 text-white' 
                    : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
                }`}
              >
                {showPrices ? '💰 Prices On' : '💰 Show Prices'}
              </button>
              <button
                onClick={() => setShowShareModal(true)}
                className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-medium transition duration-200"
              >
                Share List
              </button>
            </div>
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
                  <div key={item.id} className="p-4">
                    <div className="flex items-center justify-between hover:bg-gray-50">
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
                    
                    {/* Store Prices */}
                    {showPrices && storePrices[item.name] && (
                      <div className="mt-3 ml-9 bg-gray-50 rounded-lg p-3">
                        <p className="text-sm font-medium text-gray-700 mb-2">Local Store Prices:</p>
                        <div className="space-y-1">
                          {storePrices[item.name].slice(0, 3).map((result, index) => (
                            <div key={index} className="flex justify-between items-center text-sm">
                              <span className="text-gray-600">{result.store.store_name}</span>
                              <span className="font-medium text-green-600">${result.product.price.toFixed(2)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
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

// Household Dashboard Component (updated with new pricing references)
const HouseholdDashboard = ({ onSelectList, onLogout }) => {
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
    localStorage.removeItem('userType');
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
            <h1 className="text-2xl font-bold text-gray-800">ShopSync</h1>
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
          <h2 className="text-xl font-semibold text-gray-800">Your Shopping Lists</h2>
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
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">
                    👥 {list.shared_with.length + 1} member{list.shared_with.length === 0 ? '' : 's'}
                  </span>
                  <span className="text-sm text-blue-500 font-medium">
                    💰 Prices available
                  </span>
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

// Main App Component (updated with enhanced UX)
function App() {
  const [currentView, setCurrentView] = useState('landing'); // landing, household, store, admin
  const [authState, setAuthState] = useState('login'); // login, register
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userType, setUserType] = useState(null);
  const [selectedList, setSelectedList] = useState(null);
  const [loading, setLoading] = useState(true);
  const { toasts, removeToast, success, error, info } = useToast();

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('token');
    const savedUserType = localStorage.getItem('userType');
    
    if (token && savedUserType) {
      setIsAuthenticated(true);
      setUserType(savedUserType);
      setCurrentView(savedUserType);
      info(`Welcome back! You're logged in as ${savedUserType}.`);
    }
    setLoading(false);
  }, [info]);

  const handleAuthSuccess = (type) => {
    setIsAuthenticated(true);
    setUserType(type);
    setCurrentView(type);
    success(`Successfully logged in! Welcome to ShopSync.`);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setUserType(null);
    setSelectedList(null);
    setCurrentView('landing');
    info('You have been logged out successfully.');
  };

  const handleSelectList = (list) => {
    setSelectedList(list);
  };

  const handleBackToDashboard = () => {
    setSelectedList(null);
  };

  if (loading) {
    return (
      <ErrorBoundary>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <LoadingSpinner size="xl" message="Loading ShopSync..." />
        </div>
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary>
      <div className="app">
        <ToastContainer toasts={toasts} removeToast={removeToast} />
        
        {/* Show appropriate view based on authentication and user type */}
        {!isAuthenticated ? (
          <>
            {currentView === 'landing' && (
              <LandingPage 
                onHouseholdLogin={() => setCurrentView('household-login')}
                onStoreLogin={() => setCurrentView('store-login')}
                onAdminLogin={() => setCurrentView('admin-login')}
              />
            )}

            {currentView === 'admin-login' && (
              <AdminLogin
                onLoginSuccess={handleAuthSuccess}
                onBack={() => setCurrentView('landing')}
                showToast={{ success, error }}
              />
            )}

            {currentView === 'household-login' && (
              <>
                {authState === 'login' ? (
                  <HouseholdLogin
                    onLoginSuccess={handleAuthSuccess}
                    switchToRegister={() => setAuthState('register')}
                    onBack={() => setCurrentView('landing')}
                    showToast={{ success, error }}
                  />
                ) : (
                  <HouseholdRegister
                    onRegisterSuccess={handleAuthSuccess}
                    switchToLogin={() => setAuthState('login')}
                    onBack={() => setCurrentView('landing')}
                    showToast={{ success, error }}
                  />
                )}
              </>
            )}

            {currentView === 'store-login' && (
              <>
                {authState === 'login' ? (
                  <StoreLogin
                    onLoginSuccess={handleAuthSuccess}
                    switchToRegister={() => setAuthState('register')}
                    onBack={() => setCurrentView('landing')}
                    showToast={{ success, error }}
                  />
                ) : (
                  <StoreRegister
                    onRegisterSuccess={handleAuthSuccess}
                    switchToLogin={() => setAuthState('login')}
                    onBack={() => setCurrentView('landing')}
                    showToast={{ success, error }}
                  />
                )}
              </>
            )}
          </>
        ) : (
          <>
            {/* Authenticated views */}
            {userType === 'admin' && (
              <AdminDashboard 
                onLogout={handleLogout} 
                showToast={{ success, error, info }}
              />
            )}

            {userType === 'store' && (
              <StoreDashboard 
                onLogout={handleLogout}
                showToast={{ success, error, info }}
              />
            )}

            {userType === 'household' && (
              <>
                {selectedList ? (
                  <ShoppingListView
                    list={selectedList}
                    onBack={handleBackToDashboard}
                    showToast={{ success, error, info }}
                  />
                ) : (
                  <HouseholdDashboard
                    onSelectList={handleSelectList}
                    onLogout={handleLogout}
                    showToast={{ success, error, info }}
                  />
                )}
              </>
            )}
          </>
        )}
      </div>
    </ErrorBoundary>
  );
}

export default App;