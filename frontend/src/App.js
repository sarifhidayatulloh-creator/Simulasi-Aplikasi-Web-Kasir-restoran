import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchProfile();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await axios.get(`${API}/auth/profile`);
      setUser(response.data);
    } catch (error) {
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
    }
    setLoading(false);
  };

  const login = async (username, password) => {
    try {
      console.log('Attempting login with:', username);
      console.log('API URL:', API);
      
      const response = await axios.post(`${API}/auth/login`, { 
        username, 
        password 
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      console.log('Login response:', response.data);
      
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(userData);
      
      console.log('Login successful, user set:', userData);
      return true;
    } catch (error) {
      console.error('Login error:', error.response?.data || error.message);
      throw new Error(error.response?.data?.detail || 'Login gagal');
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Login Component
const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      await login(username, password);
    } catch (error) {
      setError(error.message);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-600 via-red-700 to-red-800 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">🏪 KASIR INDONESIA</h1>
          <p className="text-gray-600">Sistem Kasir Restoran Terpadu</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-red-500 focus:outline-none transition-colors"
              placeholder="Masukkan username"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-red-500 focus:outline-none transition-colors"
              placeholder="Masukkan password"
              required
            />
          </div>
          
          {error && <div className="text-red-500 text-sm text-center">{error}</div>}
          
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-red-600 text-white py-3 px-4 rounded-lg font-semibold hover:bg-red-700 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Loading...' : 'Masuk'}
          </button>
        </form>
        
        <div className="mt-6 text-center text-sm text-gray-600">
          <p>Demo Login:</p>
          <p><strong>Admin:</strong> admin / admin123</p>
          <p><strong>Kasir:</strong> kasir / kasir123</p>
        </div>
        
        <div className="mt-8 text-center text-xs text-gray-500">
          By SARIF HIDAYATULLOH
        </div>
      </div>
    </div>
  );
};

// Main Dashboard Component
const Dashboard = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('kasir');
  const [menuItems, setMenuItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [cart, setCart] = useState([]);
  const [orders, setOrders] = useState([]);
  const [todayStats, setTodayStats] = useState(null);
  const [dashboardStats, setDashboardStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showReceipt, setShowReceipt] = useState(false);
  const [lastOrder, setLastOrder] = useState(null);

  useEffect(() => {
    fetchMenuItems();
    fetchCategories();
    if (activeTab === 'laporan') {
      fetchTodayStats();
      fetchDashboardStats();
      fetchRecentOrders();
    }
  }, [activeTab]);

  const fetchMenuItems = async () => {
    try {
      const response = await axios.get(`${API}/menu`);
      setMenuItems(response.data);
    } catch (error) {
      console.error('Error fetching menu:', error);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${API}/menu/categories`);
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const fetchTodayStats = async () => {
    try {
      const response = await axios.get(`${API}/orders/today`);
      setTodayStats(response.data);
    } catch (error) {
      console.error('Error fetching today stats:', error);
    }
  };

  const fetchDashboardStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      setDashboardStats(response.data);
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
    }
  };

  const fetchRecentOrders = async () => {
    try {
      const response = await axios.get(`${API}/orders?limit=20`);
      setOrders(response.data);
    } catch (error) {
      console.error('Error fetching orders:', error);
    }
  };

  const addToCart = (menuItem) => {
    const existingItem = cart.find(item => item.menu_item_id === menuItem.id);
    if (existingItem) {
      setCart(cart.map(item =>
        item.menu_item_id === menuItem.id
          ? { ...item, quantity: item.quantity + 1 }
          : item
      ));
    } else {
      setCart([...cart, {
        menu_item_id: menuItem.id,
        name: menuItem.name,
        price: menuItem.price,
        quantity: 1
      }]);
    }
  };

  const updateCartQuantity = (menuItemId, newQuantity) => {
    if (newQuantity <= 0) {
      setCart(cart.filter(item => item.menu_item_id !== menuItemId));
    } else {
      setCart(cart.map(item =>
        item.menu_item_id === menuItemId
          ? { ...item, quantity: newQuantity }
          : item
      ));
    }
  };

  const getTotalAmount = () => {
    return cart.reduce((total, item) => total + (item.price * item.quantity), 0);
  };

  const processPayment = async (cashReceived) => {
    if (cart.length === 0) {
      alert('Keranjang kosong!');
      return;
    }

    const totalAmount = getTotalAmount();
    if (cashReceived < totalAmount) {
      alert('Uang yang diterima kurang!');
      return;
    }

    setLoading(true);
    try {
      const orderData = {
        items: cart,
        total_amount: totalAmount,
        cash_received: parseFloat(cashReceived),
        cashier_id: user.id,
        cashier_name: user.name
      };

      const response = await axios.post(`${API}/orders`, orderData);
      setLastOrder(response.data);
      setCart([]);
      setShowReceipt(true);
      
      // Refresh stats if on report tab
      if (activeTab === 'laporan') {
        fetchTodayStats();
        fetchDashboardStats();
        fetchRecentOrders();
      }
    } catch (error) {
      alert('Error processing payment: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
  };

  const filteredMenuItems = selectedCategory
    ? menuItems.filter(item => item.category === selectedCategory)
    : menuItems;

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('id-ID');
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-red-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold">🏪 KASIR INDONESIA</h1>
              <span className="text-red-200">|</span>
              <span className="text-red-200">Halo, {user.name}</span>
            </div>
            <button
              onClick={logout}
              className="bg-red-700 hover:bg-red-800 px-4 py-2 rounded-lg transition-colors"
            >
              Keluar
            </button>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('kasir')}
              className={`py-4 px-2 border-b-2 font-medium text-sm ${
                activeTab === 'kasir'
                  ? 'border-red-500 text-red-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              💰 Kasir
            </button>
            <button
              onClick={() => setActiveTab('laporan')}
              className={`py-4 px-2 border-b-2 font-medium text-sm ${
                activeTab === 'laporan'
                  ? 'border-red-500 text-red-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              📊 Laporan
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'kasir' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Menu Items */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg shadow-sm p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold">Menu Makanan & Minuman</h2>
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
                  >
                    <option value="">Semua Kategori</option>
                    {categories.map(cat => (
                      <option key={cat.category} value={cat.category}>
                        {cat.category} ({cat.count})
                      </option>
                    ))}
                  </select>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {filteredMenuItems.map(item => (
                    <div key={item.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                      <img
                        src={item.image_url}
                        alt={item.name}
                        className="w-full h-32 object-cover rounded-lg mb-3"
                        onError={(e) => {
                          e.target.src = 'https://via.placeholder.com/300x200?text=No+Image';
                        }}
                      />
                      <h3 className="font-semibold text-lg mb-1">{item.name}</h3>
                      <p className="text-gray-600 text-sm mb-2">{item.description}</p>
                      <div className="flex justify-between items-center">
                        <span className="text-lg font-bold text-red-600">
                          {formatCurrency(item.price)}
                        </span>
                        <button
                          onClick={() => addToCart(item)}
                          className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
                        >
                          + Keranjang
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Cart */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow-sm p-6 sticky top-6">
                <h2 className="text-xl font-semibold mb-4">🛒 Keranjang Pesanan</h2>
                
                {cart.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">Keranjang kosong</p>
                ) : (
                  <>
                    <div className="space-y-3 mb-4 max-h-64 overflow-y-auto">
                      {cart.map(item => (
                        <div key={item.menu_item_id} className="flex justify-between items-center border-b pb-2">
                          <div className="flex-1">
                            <h4 className="font-medium text-sm">{item.name}</h4>
                            <p className="text-red-600 font-semibold">{formatCurrency(item.price)}</p>
                          </div>
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => updateCartQuantity(item.menu_item_id, item.quantity - 1)}
                              className="w-6 h-6 bg-gray-200 rounded text-sm hover:bg-gray-300"
                            >
                              -
                            </button>
                            <span className="w-8 text-center">{item.quantity}</span>
                            <button
                              onClick={() => updateCartQuantity(item.menu_item_id, item.quantity + 1)}
                              className="w-6 h-6 bg-gray-200 rounded text-sm hover:bg-gray-300"
                            >
                              +
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                    
                    <div className="border-t pt-4">
                      <div className="flex justify-between items-center mb-4">
                        <span className="text-lg font-semibold">Total:</span>
                        <span className="text-xl font-bold text-red-600">
                          {formatCurrency(getTotalAmount())}
                        </span>
                      </div>
                      
                      <PaymentModal
                        totalAmount={getTotalAmount()}
                        onPayment={processPayment}
                        loading={loading}
                      />
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'laporan' && (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="text-sm font-medium text-gray-500">Pesanan Hari Ini</h3>
                <p className="text-3xl font-bold text-gray-900">
                  {dashboardStats?.today?.orders || 0}
                </p>
              </div>
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="text-sm font-medium text-gray-500">Pendapatan Hari Ini</h3>
                <p className="text-3xl font-bold text-green-600">
                  {formatCurrency(dashboardStats?.today?.revenue || 0)}
                </p>
              </div>
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="text-sm font-medium text-gray-500">Total Pesanan</h3>
                <p className="text-3xl font-bold text-gray-900">
                  {dashboardStats?.all_time?.orders || 0}
                </p>
              </div>
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="text-sm font-medium text-gray-500">Total Pendapatan</h3>
                <p className="text-3xl font-bold text-green-600">
                  {formatCurrency(dashboardStats?.all_time?.revenue || 0)}
                </p>
              </div>
            </div>

            {/* Popular Items Today */}
            {todayStats?.popular_items && todayStats.popular_items.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h2 className="text-xl font-semibold mb-4">🔥 Menu Terpopuler Hari Ini</h2>
                <div className="space-y-2">
                  {todayStats.popular_items.map((item, index) => (
                    <div key={index} className="flex justify-between items-center py-2 border-b">
                      <span className="font-medium">{item.name}</span>
                      <span className="text-red-600 font-semibold">{item.quantity} porsi</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recent Orders */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold mb-4">📋 Pesanan Terakhir</h2>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Tanggal
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Kasir
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Items
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Total
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {orders.map((order) => (
                      <tr key={order.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatDate(order.order_date)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {order.cashier_name}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-900">
                          {order.items.map(item => `${item.name} (${item.quantity})`).join(', ')}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-green-600">
                          {formatCurrency(order.total_amount)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Receipt Modal */}
      {showReceipt && lastOrder && (
        <ReceiptModal
          order={lastOrder}
          onClose={() => setShowReceipt(false)}
          formatCurrency={formatCurrency}
          formatDate={formatDate}
        />
      )}

      {/* Footer */}
      <footer className="bg-gray-800 text-white text-center py-4 mt-12">
        <p className="text-sm">By SARIF HIDAYATULLOH</p>
      </footer>
    </div>
  );
};

// Payment Modal Component
const PaymentModal = ({ totalAmount, onPayment, loading }) => {
  const [showModal, setShowModal] = useState(false);
  const [cashReceived, setCashReceived] = useState('');

  const handlePayment = () => {
    onPayment(cashReceived);
    setShowModal(false);
    setCashReceived('');
  };

  const quickAmounts = [
    totalAmount,
    Math.ceil(totalAmount / 50000) * 50000,
    Math.ceil(totalAmount / 100000) * 100000,
  ].filter((amount, index, arr) => arr.indexOf(amount) === index);

  return (
    <>
      <button
        onClick={() => setShowModal(true)}
        disabled={loading}
        className="w-full bg-green-600 text-white py-3 px-4 rounded-lg font-semibold hover:bg-green-700 disabled:opacity-50 transition-colors"
      >
        {loading ? 'Processing...' : 'Bayar'}
      </button>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">💳 Pembayaran Cash</h3>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Total: {new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR' }).format(totalAmount)}
              </label>
              <input
                type="number"
                value={cashReceived}
                onChange={(e) => setCashReceived(e.target.value)}
                placeholder="Masukkan jumlah uang diterima"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
              />
            </div>

            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">Quick amounts:</p>
              <div className="flex flex-wrap gap-2">
                {quickAmounts.map(amount => (
                  <button
                    key={amount}
                    onClick={() => setCashReceived(amount.toString())}
                    className="px-3 py-1 bg-gray-200 text-gray-700 rounded text-sm hover:bg-gray-300"
                  >
                    {new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR' }).format(amount)}
                  </button>
                ))}
              </div>
            </div>

            {cashReceived && parseFloat(cashReceived) >= totalAmount && (
              <div className="mb-4 p-3 bg-green-50 rounded-lg">
                <p className="text-green-800 font-semibold">
                  Kembalian: {new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR' }).format(parseFloat(cashReceived) - totalAmount)}
                </p>
              </div>
            )}

            <div className="flex space-x-3">
              <button
                onClick={() => setShowModal(false)}
                className="flex-1 px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Batal
              </button>
              <button
                onClick={handlePayment}
                disabled={!cashReceived || parseFloat(cashReceived) < totalAmount}
                className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                Proses Bayar
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

// Receipt Modal Component
const ReceiptModal = ({ order, onClose, formatCurrency, formatDate }) => {
  const printReceipt = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-96 overflow-y-auto">
        <div className="text-center mb-4">
          <h2 className="text-xl font-bold">🏪 KASIR INDONESIA</h2>
          <p className="text-sm text-gray-600">Struk Pembayaran</p>
          <p className="text-xs text-gray-500">{formatDate(order.order_date)}</p>
        </div>

        <div className="border-t border-b py-4 mb-4">
          <div className="space-y-2">
            {order.items.map((item, index) => (
              <div key={index} className="flex justify-between text-sm">
                <span>{item.name} x{item.quantity}</span>
                <span>{formatCurrency(item.price * item.quantity)}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-2 text-sm">
          <div className="flex justify-between font-semibold">
            <span>Total:</span>
            <span>{formatCurrency(order.total_amount)}</span>
          </div>
          <div className="flex justify-between">
            <span>Tunai:</span>
            <span>{formatCurrency(order.cash_received)}</span>
          </div>
          <div className="flex justify-between">
            <span>Kembalian:</span>
            <span>{formatCurrency(order.change_amount)}</span>
          </div>
          <div className="flex justify-between text-xs text-gray-500">
            <span>Kasir:</span>
            <span>{order.cashier_name}</span>
          </div>
        </div>

        <div className="flex space-x-3 mt-6">
          <button
            onClick={printReceipt}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            🖨️ Print
          </button>
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            Tutup
          </button>
        </div>

        <div className="text-center mt-4 text-xs text-gray-500">
          By SARIF HIDAYATULLOH
        </div>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

const AppContent = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return user ? <Dashboard /> : <LoginPage />;
};

export default App;