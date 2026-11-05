import React, { useEffect, useState } from 'react';
import './App.css';
import LoadingSpinner from './components/LoadingSpinner';
import { ToastContainer } from './components/NotificationToast';
import useToast from './hooks/useToast';
import ErrorBoundary from './components/ErrorBoundary';
import { apiCall } from './api';
import { subscribeToHouseholdEvents } from './realtime';

const PACKAGE_UNITS = ['oz', 'lb', 'g', 'kg', 'ml', 'l', 'floz', 'gal', 'pt', 'qt', 'count'];

const fieldClass =
  'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent';

const LandingPage = ({ onHouseholdLogin, onStoreLogin }) => (
  <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
    <div className="max-w-4xl w-full text-center">
      <div className="mb-8">
        <p className="inline-block bg-white/15 text-white text-sm rounded-full px-4 py-1 mb-4">
          Household pilot · not a public production service
        </p>
        <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4">ListSync</h1>
        <p className="text-lg sm:text-xl text-blue-100">
          A private shared shopping list for a household. Anyone in the household can add or check off items, and the others see it immediately.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto text-left">
        <div className="bg-white rounded-xl shadow-2xl p-6 sm:p-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-3">Households</h2>
          <p className="text-gray-600 mb-4">
            Free for the people using the list. Share it with your household, keep it private, and compare example prices only when the brand and package actually match.
          </p>
          <ul className="space-y-2 mb-6 text-gray-700">
            <li>Shared lists for more than one person</li>
            <li>Changes show up without reloading</li>
            <li>No consumer fee</li>
          </ul>
          <button
            type="button"
            data-testid="landing-household"
            onClick={onHouseholdLogin}
            className="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-3 px-4 rounded-lg"
          >
            Open a household list
          </button>
        </div>

        <div className="bg-white rounded-xl shadow-2xl p-6 sm:p-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-3">Retailers</h2>
          <p className="text-gray-600 mb-4">
            The retailer side is meant to be funded later by a monthly or yearly subscription. Those fee amounts are unset. This pilot does not bill anyone and does not take card details.
          </p>
          <ul className="space-y-2 mb-6 text-gray-700">
            <li>Enter local example prices yourself</li>
            <li>Prices are labeled example, not live shelf prices</li>
            <li>Retailers cannot browse household lists</li>
          </ul>
          <button
            type="button"
            data-testid="landing-retailer"
            onClick={onStoreLogin}
            className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-4 rounded-lg"
          >
            Retailer price account
          </button>
        </div>
      </div>
      <p className="mt-8 text-blue-100 text-sm">
        Admin console, payment processing, and outgoing email are turned off for this pilot.
      </p>
    </div>
  </div>
);

const AuthError = ({ error }) =>
  error ? (
    <div data-testid="form-error" className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
      {error}
    </div>
  ) : null;

const HouseholdLogin = ({ onLoginSuccess, switchToRegister, onBack }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (event) => {
    event.preventDefault();
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
      <div className="max-w-md w-full bg-white rounded-xl shadow-2xl p-6 sm:p-8">
        <button type="button" onClick={onBack} className="text-gray-600 hover:text-gray-800 mb-4">
          ← Back
        </button>
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Welcome back</h1>
        <p className="text-gray-600 mb-6">Sign in to your household lists</p>
        <form onSubmit={handleLogin} className="space-y-4">
          <input data-testid="auth-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} className={fieldClass} placeholder="Email" required />
          <input data-testid="auth-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} className={fieldClass} placeholder="Password" required />
          <AuthError error={error} />
          <button data-testid="auth-submit" type="submit" disabled={loading} className="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-3 rounded-lg disabled:opacity-50">
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
        <button data-testid="auth-switch" type="button" onClick={switchToRegister} className="mt-4 text-blue-600 font-semibold">
          Create a household account
        </button>
      </div>
    </div>
  );
};

const HouseholdRegister = ({ onRegisterSuccess, switchToLogin, onBack }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleRegister = async (event) => {
    event.preventDefault();
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
      <div className="max-w-md w-full bg-white rounded-xl shadow-2xl p-6 sm:p-8">
        <button type="button" onClick={onBack} className="text-gray-600 hover:text-gray-800 mb-4">
          ← Back
        </button>
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Join ListSync</h1>
        <p className="text-gray-600 mb-6">Household accounts are free. Password at least 8 characters.</p>
        <form onSubmit={handleRegister} className="space-y-4">
          <input data-testid="auth-name" type="text" value={name} onChange={(e) => setName(e.target.value)} className={fieldClass} placeholder="Your name" required />
          <input data-testid="auth-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} className={fieldClass} placeholder="Email" required />
          <input data-testid="auth-password" minLength={8} type="password" value={password} onChange={(e) => setPassword(e.target.value)} className={fieldClass} placeholder="Password" required />
          <AuthError error={error} />
          <button data-testid="auth-submit" type="submit" disabled={loading} className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 rounded-lg disabled:opacity-50">
            {loading ? 'Creating account...' : 'Create account'}
          </button>
        </form>
        <button data-testid="auth-switch" type="button" onClick={switchToLogin} className="mt-4 text-green-700 font-semibold">
          Already registered? Sign in
        </button>
      </div>
    </div>
  );
};

const StoreLogin = ({ onLoginSuccess, switchToRegister, onBack }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (event) => {
    event.preventDefault();
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
    <div className="min-h-screen bg-gradient-to-br from-green-600 to-emerald-800 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-2xl p-6 sm:p-8">
        <button type="button" onClick={onBack} className="text-gray-600 mb-4">← Back</button>
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Retailer sign in</h1>
        <form onSubmit={handleLogin} className="space-y-4">
          <input data-testid="auth-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} className={fieldClass} placeholder="Email" required />
          <input data-testid="auth-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} className={fieldClass} placeholder="Password" required />
          <AuthError error={error} />
          <button data-testid="auth-submit" type="submit" disabled={loading} className="w-full bg-green-600 text-white font-semibold py-3 rounded-lg disabled:opacity-50">
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
        <button data-testid="auth-switch" type="button" onClick={switchToRegister} className="mt-4 text-green-700 font-semibold">
          Create a retailer account
        </button>
      </div>
    </div>
  );
};

const StoreRegister = ({ onRegisterSuccess, switchToLogin, onBack }) => {
  const [formData, setFormData] = useState({
    store_name: '',
    email: '',
    password: '',
    address: '',
    city: '',
    state: '',
    zip_code: '',
    phone: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleRegister = async (event) => {
    event.preventDefault();
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

  const setField = (event) => {
    setFormData({ ...formData, [event.target.name]: event.target.value });
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-white rounded-xl shadow p-6 sm:p-8">
        <button type="button" onClick={onBack} className="text-gray-600 mb-4">← Back</button>
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Retailer account</h1>
        <p className="text-gray-600 mb-6">
          Monthly and yearly plans are future placeholders. The fee is unset, and this form does not start a trial charge.
        </p>
        <form onSubmit={handleRegister} className="space-y-4">
          <div className="grid sm:grid-cols-2 gap-4">
            <input data-testid="store-name" name="store_name" value={formData.store_name} onChange={setField} className={fieldClass} placeholder="Store name" required />
            <input data-testid="auth-email" name="email" type="email" value={formData.email} onChange={setField} className={fieldClass} placeholder="Email" required />
          </div>
          <input data-testid="auth-password" name="password" type="password" minLength={8} value={formData.password} onChange={setField} className={fieldClass} placeholder="Password (8+ characters)" required />
          <input data-testid="store-address" name="address" value={formData.address} onChange={setField} className={fieldClass} placeholder="Street address" required />
          <div className="grid sm:grid-cols-3 gap-4">
            <input data-testid="store-city" name="city" value={formData.city} onChange={setField} className={fieldClass} placeholder="City" required />
            <input data-testid="store-state" name="state" value={formData.state} onChange={setField} className={fieldClass} placeholder="State" required />
            <input data-testid="store-zip" name="zip_code" value={formData.zip_code} onChange={setField} className={fieldClass} placeholder="ZIP" required />
          </div>
          <AuthError error={error} />
          <button data-testid="auth-submit" type="submit" disabled={loading} className="w-full bg-green-600 text-white font-semibold py-3 rounded-lg disabled:opacity-50">
            {loading ? 'Creating account...' : 'Create retailer account'}
          </button>
        </form>
        <button data-testid="auth-switch" type="button" onClick={switchToLogin} className="mt-4 text-green-700 font-semibold">
          Already registered? Sign in
        </button>
      </div>
    </div>
  );
};

const localityText = {
  same_zip: 'Same ZIP as your household',
  same_city: 'Same city as your household',
  other_area: 'Different area from your household',
  household_location_unset: 'Household location is not set, so locality was not compared',
};

const ShoppingListView = ({ list, onBack }) => {
  const [items, setItems] = useState([]);
  const [members, setMembers] = useState([]);
  const [basket, setBasket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [liveStatus, setLiveStatus] = useState('connecting');
  const [form, setForm] = useState({
    name: '',
    brand: '',
    package_size: '',
    package_unit: '',
    quantity_count: '1',
  });
  const [showShare, setShowShare] = useState(false);
  const [shareEmail, setShareEmail] = useState('');
  const [shareError, setShareError] = useState('');
  const [formError, setFormError] = useState('');
  const [showPrices, setShowPrices] = useState(false);
  const [pricesByItem, setPricesByItem] = useState({});

  const loadItems = async () => {
    const [itemRows, memberRows, basketRow] = await Promise.all([
      apiCall(`/api/lists/${list.id}/items`),
      apiCall(`/api/lists/${list.id}/members`),
      apiCall(`/api/lists/${list.id}/basket-offer`),
    ]);
    setItems(itemRows);
    setMembers(memberRows);
    setBasket(basketRow);
    return itemRows;
  };

  const loadPrices = async (itemRows) => {
    const entries = await Promise.all(
      itemRows.filter((item) => !item.is_purchased).map(async (item) => {
        const prices = await apiCall(`/api/lists/${list.id}/items/${item.id}/example-prices`);
        return [item.id, prices];
      })
    );
    setPricesByItem(Object.fromEntries(entries));
  };

  useEffect(() => {
    let active = true;
    const refresh = async () => {
      try {
        const itemRows = await loadItems();
        if (!active) return;
        if (showPrices) {
          await loadPrices(itemRows);
        }
      } catch (err) {
        console.error(err);
      } finally {
        if (active) setLoading(false);
      }
    };
    refresh();
    const stop = subscribeToHouseholdEvents({
      onStatus: setLiveStatus,
      onEvent: (event) => {
        if (!active) return;
        if (event.type === 'items.changed' && event.list_id === list.id) {
          refresh();
        }
        if (event.type === 'lists.changed' && event.list_id === list.id) {
          refresh();
        }
      },
    });
    return () => {
      active = false;
      stop();
    };
  }, [list.id, showPrices]);

  const addItem = async (event) => {
    event.preventDefault();
    setFormError('');
    const body = {
      name: form.name,
      brand: form.brand || null,
      quantity_count: form.quantity_count ? Number(form.quantity_count) : 1,
    };
    if (form.package_size || form.package_unit) {
      body.package_size = form.package_size ? Number(form.package_size) : null;
      body.package_unit = form.package_unit || null;
    }
    try {
      await apiCall(`/api/lists/${list.id}/items`, { method: 'POST', body });
      setForm({ name: '', brand: '', package_size: '', package_unit: '', quantity_count: '1' });
    } catch (err) {
      setFormError(err.message);
    }
  };

  const toggleItem = async (item) => {
    await apiCall(`/api/items/${item.id}`, {
      method: 'PUT',
      body: { is_purchased: !item.is_purchased },
    });
  };

  const deleteItem = async (item) => {
    await apiCall(`/api/items/${item.id}`, { method: 'DELETE' });
  };

  const shareList = async (event) => {
    event.preventDefault();
    setShareError('');
    try {
      await apiCall(`/api/lists/${list.id}/share`, {
        method: 'POST',
        body: { email: shareEmail },
      });
      setShareEmail('');
      setShowShare(false);
      const memberRows = await apiCall(`/api/lists/${list.id}/members`);
      setMembers(memberRows);
    } catch (err) {
      setShareError(err.message);
    }
  };

  const remaining = items.filter((item) => !item.is_purchased);
  const purchased = items.filter((item) => item.is_purchased);

  const renderItem = (item) => {
    const prices = pricesByItem[item.id] || [];
    const detail = [
      item.brand,
      item.package_size && item.package_unit ? `${item.package_size} ${item.package_unit}` : null,
      `Qty ${item.quantity_count || item.quantity}`,
    ].filter(Boolean).join(' · ');
    return (
      <div key={item.id} data-testid="item-row" data-item-name={item.name} data-purchased={item.is_purchased ? 'true' : 'false'} className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <button
              type="button"
              data-testid="item-toggle"
              aria-label={item.is_purchased ? `Mark ${item.name} not purchased` : `Mark ${item.name} purchased`}
              onClick={() => toggleItem(item)}
              className={`mt-1 w-6 h-6 rounded-full border-2 flex items-center justify-center ${item.is_purchased ? 'bg-green-600 border-green-600 text-white' : 'border-gray-300'}`}
            >
              {item.is_purchased ? '✓' : ''}
            </button>
            <div>
              <p className={`font-medium text-gray-800 ${item.is_purchased ? 'line-through' : ''}`}>{item.name}</p>
              <p className="text-sm text-gray-500">{detail}</p>
              {item.added_by_name && <p className="text-xs text-gray-400">Added by {item.added_by_name}</p>}
            </div>
          </div>
          <button type="button" data-testid="item-delete" aria-label={`Delete ${item.name}`} onClick={() => deleteItem(item)} className="text-gray-400 hover:text-red-600">
            Delete
          </button>
        </div>
        {showPrices && !item.is_purchased && (
          <div className="mt-3 ml-0 sm:ml-9 space-y-2">
            {prices.length === 0 && (
              <p className="text-sm text-gray-500">No example prices with this exact item name.</p>
            )}
            {prices.map((price) => (
              <div key={price.product_id} data-testid="price-card" data-comparable={price.comparable ? 'true' : 'false'} className="rounded-lg border bg-gray-50 p-3 text-sm">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
                  <p className="font-medium text-gray-800">{price.store_name}</p>
                  <p className="font-semibold text-gray-900">
                    <span className="uppercase text-xs tracking-wide text-amber-700 mr-2">{price.price_label}</span>
                    ${price.price.toFixed(2)}
                  </p>
                </div>
                <p className="text-gray-600">
                  {price.brand || 'Brand not recorded'} · {price.package_size} {price.package_unit}
                  {' · '}{price.locality_city}, {price.locality_state} {price.locality_zip}
                </p>
                <p className={price.comparable ? 'text-green-700' : 'text-amber-800'}>
                  {price.comparable
                    ? 'Comparable example: brand, package size, and unit match. This is still not a live price or a stock check.'
                    : `Not the same product. ${price.comparability_reasons.join(', ')}.`}
                </p>
                <p className="text-gray-500">{localityText[price.locality_relation] || price.locality_relation}</p>
                <p className="text-gray-500">{price.validity_note}</p>
                <p className="text-gray-500">{price.availability_note}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner message="Loading the list..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 py-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <button type="button" onClick={onBack} className="text-gray-600 text-sm">← All lists</button>
            <h1 className="text-2xl font-bold text-gray-800">{list.name}</h1>
            <p className="text-sm text-gray-500">
              {remaining.length} remaining · {members.length} member{members.length === 1 ? '' : 's'} ·{' '}
              <span data-testid="live-status">{liveStatus === 'live' ? 'Live' : 'Reconnecting'}</span>
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              data-testid="show-prices"
              onClick={() => setShowPrices((value) => !value)}
              className={`px-4 py-2 rounded-lg font-medium ${showPrices ? 'bg-green-600 text-white' : 'bg-gray-200 text-gray-800'}`}
            >
              {showPrices ? 'Hide example prices' : 'Show example prices'}
            </button>
            <button type="button" data-testid="share-list" onClick={() => setShowShare(true)} className="px-4 py-2 rounded-lg bg-blue-600 text-white font-medium">
              Share
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        <section data-testid="basket-placeholder" className="rounded-xl border border-dashed border-gray-400 bg-white p-4">
          <h2 className="font-semibold text-gray-800">Whole-basket retailer offer</h2>
          <p className="text-sm text-gray-600 mt-1">{basket?.message}</p>
          <p className="text-sm text-gray-500 mt-1">Implemented: {basket?.implemented ? 'yes' : 'no'}. Offers: none.</p>
        </section>

        <form onSubmit={addItem} className="bg-white rounded-xl border p-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
          <input data-testid="item-name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className={fieldClass} placeholder="Item name, such as whole milk" required />
          <input data-testid="item-brand" value={form.brand} onChange={(e) => setForm({ ...form, brand: e.target.value })} className={fieldClass} placeholder="Brand" />
          <input data-testid="item-package-size" value={form.package_size} onChange={(e) => setForm({ ...form, package_size: e.target.value })} className={fieldClass} placeholder="Package size" inputMode="decimal" />
          <select data-testid="item-package-unit" value={form.package_unit} onChange={(e) => setForm({ ...form, package_unit: e.target.value })} className={fieldClass}>
            <option value="">Package unit</option>
            {PACKAGE_UNITS.map((unit) => (
              <option key={unit} value={unit}>{unit}</option>
            ))}
          </select>
          <input data-testid="item-quantity" value={form.quantity_count} onChange={(e) => setForm({ ...form, quantity_count: e.target.value })} className={fieldClass} placeholder="How many" inputMode="decimal" />
          <button data-testid="add-item" type="submit" className="bg-blue-600 text-white rounded-lg font-medium px-4 py-3">
            Add item
          </button>
          {formError && <p data-testid="form-error" className="sm:col-span-2 text-red-700 text-sm">{formError}</p>}
          <p className="sm:col-span-2 text-xs text-gray-500">
            Brand, package size, and unit are what make an example price comparable. A different size or unit is kept as a different product. Nothing here checks whether a store has it in stock.
          </p>
        </form>

        <section className="bg-white rounded-xl border divide-y">
          <div className="p-4 font-semibold text-gray-800">To buy</div>
          {remaining.length === 0 && <p className="p-4 text-gray-500">Nothing left to buy.</p>}
          {remaining.map(renderItem)}
        </section>

        {purchased.length > 0 && (
          <section className="bg-white rounded-xl border divide-y">
            <div className="p-4 font-semibold text-gray-800">Checked off</div>
            {purchased.map(renderItem)}
          </section>
        )}

        <section className="text-sm text-gray-500">
          Members: {members.map((member) => `${member.name} (${member.role})`).join(', ') || 'just you'}
        </section>
      </main>

      {showShare && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4">
          <form onSubmit={shareList} className="bg-white rounded-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-xl font-semibold">Share with a household member</h3>
            <p className="text-sm text-gray-600">They need a ListSync account already. Retailers are not added to household lists.</p>
            <input data-testid="share-email" type="email" value={shareEmail} onChange={(e) => setShareEmail(e.target.value)} className={fieldClass} placeholder="Their email" required />
            <AuthError error={shareError} />
            <div className="flex justify-end gap-3">
              <button type="button" onClick={() => setShowShare(false)} className="px-4 py-2 text-gray-600">Cancel</button>
              <button data-testid="share-submit" type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg">Share list</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

const HouseholdDashboard = ({ onSelectList, onLogout }) => {
  const [lists, setLists] = useState([]);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [liveStatus, setLiveStatus] = useState('connecting');
  const [showCreate, setShowCreate] = useState(false);
  const [newListName, setNewListName] = useState('');
  const [location, setLocation] = useState({ home_zip: '', home_city: '', home_state: '' });
  const [locationMessage, setLocationMessage] = useState('');

  useEffect(() => {
    let active = true;
    const refresh = async () => {
      const [userData, listData] = await Promise.all([
        apiCall('/api/auth/me'),
        apiCall('/api/lists'),
      ]);
      if (!active) return;
      setUser(userData);
      setLists(listData);
      setLocation({
        home_zip: userData.home_zip || '',
        home_city: userData.home_city || '',
        home_state: userData.home_state || '',
      });
      setLoading(false);
    };
    refresh().catch(() => active && setLoading(false));
    const stop = subscribeToHouseholdEvents({
      onStatus: setLiveStatus,
      onEvent: (event) => {
        if (event.type === 'lists.changed') refresh();
      },
    });
    return () => {
      active = false;
      stop();
    };
  }, []);

  const createList = async (event) => {
    event.preventDefault();
    await apiCall('/api/lists', { method: 'POST', body: { name: newListName } });
    setNewListName('');
    setShowCreate(false);
  };

  const saveLocation = async (event) => {
    event.preventDefault();
    const updated = await apiCall('/api/auth/me', {
      method: 'PATCH',
      body: {
        home_zip: location.home_zip,
        home_city: location.home_city,
        home_state: location.home_state,
      },
    });
    setUser(updated);
    setLocationMessage('Location saved. It is only used to label whether an example price is in your ZIP or city.');
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userType');
    onLogout();
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner message="Loading your lists..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="max-w-5xl mx-auto px-4 py-4 flex justify-between items-center gap-3">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">ListSync</h1>
            <p className="text-gray-600 text-sm">{user ? `Hello, ${user.name}` : 'Household'} · <span data-testid="live-status">{liveStatus === 'live' ? 'Live' : 'Reconnecting'}</span></p>
          </div>
          <button data-testid="logout" type="button" onClick={logout} className="text-gray-700 font-medium">Log out</button>
        </div>
      </header>
      <main className="max-w-5xl mx-auto px-4 py-6 space-y-6">
        <section className="bg-white rounded-xl border p-4">
          <h2 className="font-semibold text-gray-800 mb-2">Your place</h2>
          <p className="text-sm text-gray-500 mb-3">Optional. Used only to say whether a retailer example price is local. It is not shared with retailers as a shopping list.</p>
          <form onSubmit={saveLocation} className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <input data-testid="home-city" value={location.home_city} onChange={(e) => setLocation({ ...location, home_city: e.target.value })} className={fieldClass} placeholder="City" />
            <input data-testid="home-state" value={location.home_state} onChange={(e) => setLocation({ ...location, home_state: e.target.value })} className={fieldClass} placeholder="State" />
            <input data-testid="home-zip" value={location.home_zip} onChange={(e) => setLocation({ ...location, home_zip: e.target.value })} className={fieldClass} placeholder="ZIP" />
            <button data-testid="save-location" type="submit" className="bg-gray-800 text-white rounded-lg px-4 py-3">Save</button>
          </form>
          {locationMessage && <p className="text-sm text-green-700 mt-2">{locationMessage}</p>}
        </section>

        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-800">Lists</h2>
          <button data-testid="new-list" type="button" onClick={() => setShowCreate(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg">New list</button>
        </div>

        {lists.length === 0 ? (
          <div className="bg-white rounded-xl border p-8 text-center text-gray-600">No lists yet. Create one for this week.</div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {lists.map((row) => (
              <button
                type="button"
                key={row.id}
                data-testid="list-card"
                onClick={() => onSelectList(row)}
                className="text-left bg-white rounded-xl border p-5 hover:border-blue-400"
              >
                <h3 className="text-lg font-semibold text-gray-800">{row.name}</h3>
                <p className="text-sm text-gray-500 mt-2">{row.shared_with.length + 1} member{row.shared_with.length === 0 ? '' : 's'}</p>
              </button>
            ))}
          </div>
        )}
      </main>

      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4">
          <form onSubmit={createList} className="bg-white rounded-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-xl font-semibold">New list</h3>
            <input data-testid="list-name" value={newListName} onChange={(e) => setNewListName(e.target.value)} className={fieldClass} placeholder="Weekly groceries" required />
            <div className="flex justify-end gap-3">
              <button type="button" onClick={() => setShowCreate(false)} className="px-4 py-2 text-gray-600">Cancel</button>
              <button data-testid="create-list-submit" type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg">Create</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

const AddProductModal = ({ onClose, onProductAdded }) => {
  const [formData, setFormData] = useState({
    name: '',
    brand: '',
    category: 'Grocery',
    package_size: '',
    package_unit: 'oz',
    price: '',
    description: '',
    is_advertised: true,
    valid_from: '',
    valid_until: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const setField = (event) => {
    const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value;
    setFormData({ ...formData, [event.target.name]: value });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    const body = {
      name: formData.name,
      brand: formData.brand,
      category: formData.category,
      package_size: Number(formData.package_size),
      package_unit: formData.package_unit,
      price: Number(formData.price),
      description: formData.description || null,
      is_advertised: formData.is_advertised,
      provenance: 'example',
    };
    if (formData.valid_from) body.valid_from = new Date(formData.valid_from).toISOString();
    if (formData.valid_until) body.valid_until = new Date(formData.valid_until).toISOString();
    try {
      await apiCall('/api/store/products', { method: 'POST', body });
      onProductAdded();
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <form onSubmit={handleSubmit} className="bg-white rounded-xl max-w-lg w-full p-6 space-y-3 max-h-[90vh] overflow-y-auto">
        <h3 className="text-xl font-semibold">Example price</h3>
        <p className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-lg p-3">
          This is saved as an example price, not a live shelf price. Provenance is fixed to example. Stock is not recorded.
        </p>
        <input data-testid="product-name" name="name" value={formData.name} onChange={setField} className={fieldClass} placeholder="Product name" required />
        <input data-testid="product-brand" name="brand" value={formData.brand} onChange={setField} className={fieldClass} placeholder="Brand" required />
        <input data-testid="product-category" name="category" value={formData.category} onChange={setField} className={fieldClass} placeholder="Category" required />
        <div className="grid grid-cols-2 gap-3">
          <input data-testid="product-size" name="package_size" value={formData.package_size} onChange={setField} className={fieldClass} placeholder="Package size" required />
          <select data-testid="product-unit" name="package_unit" value={formData.package_unit} onChange={setField} className={fieldClass}>
            {PACKAGE_UNITS.map((unit) => <option key={unit} value={unit}>{unit}</option>)}
          </select>
        </div>
        <input data-testid="product-price" name="price" value={formData.price} onChange={setField} className={fieldClass} placeholder="Example price amount" required />
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <label className="text-sm text-gray-600">Valid from
            <input data-testid="product-valid-from" type="datetime-local" name="valid_from" value={formData.valid_from} onChange={setField} className={`${fieldClass} mt-1`} />
          </label>
          <label className="text-sm text-gray-600">Valid until
            <input data-testid="product-valid-until" type="datetime-local" name="valid_until" value={formData.valid_until} onChange={setField} className={`${fieldClass} mt-1`} />
          </label>
        </div>
        <textarea name="description" value={formData.description} onChange={setField} className={fieldClass} placeholder="Optional note. Do not claim this item is in stock." rows="2" />
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input type="checkbox" name="is_advertised" checked={formData.is_advertised} onChange={setField} />
          Show this example price to households
        </label>
        <AuthError error={error} />
        <div className="flex justify-end gap-3">
          <button type="button" onClick={onClose} className="px-4 py-2 text-gray-600">Cancel</button>
          <button data-testid="save-product" type="submit" disabled={loading} className="px-4 py-2 bg-green-600 text-white rounded-lg disabled:opacity-50">
            {loading ? 'Saving...' : 'Save example price'}
          </button>
        </div>
      </form>
    </div>
  );
};

const StoreDashboard = ({ onLogout }) => {
  const [storeInfo, setStoreInfo] = useState(null);
  const [subscription, setSubscription] = useState(null);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('products');
  const [showAddProduct, setShowAddProduct] = useState(false);
  const [error, setError] = useState('');

  const fetchStoreData = async () => {
    try {
      const [storeData, subscriptionData, productsData] = await Promise.all([
        apiCall('/api/store/auth/me'),
        apiCall('/api/store/subscription'),
        apiCall('/api/store/products'),
      ]);
      setStoreInfo(storeData);
      setSubscription(subscriptionData);
      setProducts(productsData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStoreData();
  }, []);

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userType');
    onLogout();
  };

  const deleteProduct = async (productId) => {
    await apiCall(`/api/store/products/${productId}`, { method: 'DELETE' });
    fetchStoreData();
  };

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center"><LoadingSpinner message="Loading retailer account..." /></div>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="max-w-5xl mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">{storeInfo?.store_name}</h1>
            <p className="text-sm text-gray-600">{storeInfo?.city}, {storeInfo?.state} {storeInfo?.zip_code} · pilot, not billed</p>
          </div>
          <button data-testid="logout" type="button" onClick={logout}>Log out</button>
        </div>
      </header>
      <div className="max-w-5xl mx-auto px-4 pt-4 flex gap-4 text-sm">
        {['products', 'subscription'].map((tab) => (
          <button key={tab} type="button" data-testid={`tab-${tab}`} onClick={() => setActiveTab(tab)} className={`pb-2 border-b-2 ${activeTab === tab ? 'border-green-600 text-green-700' : 'border-transparent text-gray-500'}`}>
            {tab}
          </button>
        ))}
      </div>
      <main className="max-w-5xl mx-auto px-4 py-6">
        {error && <p className="text-red-700 mb-4">{error}</p>}
        {activeTab === 'products' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold">Example prices</h2>
              <button data-testid="open-add-product" type="button" onClick={() => setShowAddProduct(true)} className="bg-green-600 text-white px-4 py-2 rounded-lg">Add example price</button>
            </div>
            {products.length === 0 && <p className="text-gray-500">No example prices yet.</p>}
            {products.map((product) => (
              <article key={product.id} data-testid="retailer-price" className="bg-white border rounded-xl p-4 flex justify-between gap-4">
                <div>
                  <h3 className="font-semibold">{product.name}</h3>
                  <p className="text-sm text-gray-600">{product.brand} · {product.package_size} {product.package_unit} · {product.category}</p>
                  <p className="mt-1"><span className="text-xs uppercase tracking-wide text-amber-700">Example price</span> <span className="font-semibold">${product.price.toFixed(2)}</span></p>
                  <p className="text-xs text-gray-500">{product.locality_city}, {product.locality_state} {product.locality_zip} · provenance {product.provenance}</p>
                </div>
                <button type="button" onClick={() => deleteProduct(product.id)} className="text-sm text-red-600">Delete</button>
              </article>
            ))}
          </div>
        )}
        {activeTab === 'subscription' && (
          <section data-testid="billing-placeholder" className="bg-white border rounded-xl p-6 space-y-3">
            <h2 className="text-xl font-semibold">Retailer subscription</h2>
            <p>{subscription?.message}</p>
            <dl className="grid sm:grid-cols-2 gap-3 text-sm">
              <div><dt className="text-gray-500">Billing implemented</dt><dd>{subscription?.billing_implemented ? 'yes' : 'no'}</dd></div>
              <div><dt className="text-gray-500">Account status</dt><dd>{subscription?.status}</dd></div>
              <div><dt className="text-gray-500">Monthly fee</dt><dd>{subscription?.monthly_fee == null ? 'Unset' : subscription.monthly_fee}</dd></div>
              <div><dt className="text-gray-500">Yearly fee</dt><dd>{subscription?.yearly_fee == null ? 'Unset' : subscription.yearly_fee}</dd></div>
              <div><dt className="text-gray-500">Plan options reserved</dt><dd>{(subscription?.plan_options || []).join(', ') || 'monthly, yearly'}</dd></div>
            </dl>
            <p className="text-sm text-gray-500">No checkout button is shown because taking payment is out of scope for this pilot.</p>
          </section>
        )}
      </main>
      {showAddProduct && (
        <AddProductModal onClose={() => setShowAddProduct(false)} onProductAdded={fetchStoreData} />
      )}
    </div>
  );
};

function App() {
  const [currentView, setCurrentView] = useState('landing');
  const [authState, setAuthState] = useState('login');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userType, setUserType] = useState(null);
  const [selectedList, setSelectedList] = useState(null);
  const [loading, setLoading] = useState(true);
  const { toasts, removeToast, success, info } = useToast();

  useEffect(() => {
    const token = localStorage.getItem('token');
    const savedUserType = localStorage.getItem('userType');
    if (token && savedUserType === 'household') {
      setIsAuthenticated(true);
      setUserType('household');
    } else if (token && savedUserType === 'store') {
      setIsAuthenticated(true);
      setUserType('store');
    } else if (savedUserType === 'admin') {
      localStorage.removeItem('token');
      localStorage.removeItem('userType');
    }
    setLoading(false);
  }, []);

  const handleAuthSuccess = (type) => {
    setIsAuthenticated(true);
    setUserType(type);
    setSelectedList(null);
    success('Signed in to ListSync.');
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setUserType(null);
    setSelectedList(null);
    setCurrentView('landing');
    setAuthState('login');
    info('Signed out.');
  };

  if (loading) {
    return (
      <ErrorBoundary>
        <div className="min-h-screen flex items-center justify-center">
          <LoadingSpinner size="xl" message="Loading ListSync..." />
        </div>
      </ErrorBoundary>
    );
  }

  let screen = null;
  if (!isAuthenticated && currentView === 'landing') {
    screen = (
      <LandingPage
        onHouseholdLogin={() => {
          setAuthState('login');
          setCurrentView('household-login');
        }}
        onStoreLogin={() => {
          setAuthState('login');
          setCurrentView('store-login');
        }}
      />
    );
  } else if (!isAuthenticated && currentView === 'household-login') {
    screen = authState === 'login' ? (
      <HouseholdLogin
        onLoginSuccess={handleAuthSuccess}
        switchToRegister={() => setAuthState('register')}
        onBack={() => setCurrentView('landing')}
      />
    ) : (
      <HouseholdRegister
        onRegisterSuccess={handleAuthSuccess}
        switchToLogin={() => setAuthState('login')}
        onBack={() => setCurrentView('landing')}
      />
    );
  } else if (!isAuthenticated && currentView === 'store-login') {
    screen = authState === 'login' ? (
      <StoreLogin
        onLoginSuccess={handleAuthSuccess}
        switchToRegister={() => setAuthState('register')}
        onBack={() => setCurrentView('landing')}
      />
    ) : (
      <StoreRegister
        onRegisterSuccess={handleAuthSuccess}
        switchToLogin={() => setAuthState('login')}
        onBack={() => setCurrentView('landing')}
      />
    );
  } else if (isAuthenticated && userType === 'store') {
    screen = <StoreDashboard onLogout={handleLogout} />;
  } else if (isAuthenticated && userType === 'household' && selectedList) {
    screen = <ShoppingListView list={selectedList} onBack={() => setSelectedList(null)} />;
  } else if (isAuthenticated && userType === 'household') {
    screen = <HouseholdDashboard onSelectList={setSelectedList} onLogout={handleLogout} />;
  }

  return (
    <ErrorBoundary>
      <div className="app">
        <ToastContainer toasts={toasts} removeToast={removeToast} />
        {screen}
      </div>
    </ErrorBoundary>
  );
}

export default App;
