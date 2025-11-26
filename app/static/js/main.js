const API_URL = '/api';

// State Management
const state = {
    token: localStorage.getItem('token'),
    user: null,
    accounts: []
};

// DOM Elements
const views = {
    auth: document.getElementById('auth-container'),
    dashboard: document.getElementById('dashboard-container'),
    loginForm: document.getElementById('login-form'),
    signupForm: document.getElementById('signup-form')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    if (state.token) {
        initDashboard();
    } else {
        showAuth();
    }

    setupEventListeners();
    updateDate();
});

function setupEventListeners() {
    // Switch Auth Forms
    document.getElementById('show-signup').addEventListener('click', (e) => {
        e.preventDefault();
        views.loginForm.classList.add('hidden');
        views.signupForm.classList.remove('hidden');
    });

    document.getElementById('show-login').addEventListener('click', (e) => {
        e.preventDefault();
        views.signupForm.classList.add('hidden');
        views.loginForm.classList.remove('hidden');
    });

    // Login
    views.loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;

        try {
            await login(email, password);
        } catch (error) {
            alert('Login failed: ' + error.message);
        }
    });

    // Signup
    views.signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('signup-email').value;
        const password = document.getElementById('signup-password').value;

        try {
            await signup(email, password);
        } catch (error) {
            alert('Signup failed: ' + error.message);
        }
    });

    // Logout
    document.getElementById('logout-btn').addEventListener('click', (e) => {
        e.preventDefault();
        logout();
    });
}

// Auth Functions
async function login(email, password) {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
    });

    if (!response.ok) throw new Error('Invalid credentials');

    const data = await response.json();
    state.token = data.access_token;
    localStorage.setItem('token', state.token);

    await initDashboard();
}

async function signup(email, password) {
    const response = await fetch(`${API_URL}/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
    });

    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Signup failed');
    }

    // Auto login after signup
    await login(email, password);
}

function logout() {
    state.token = null;
    state.user = null;
    localStorage.removeItem('token');
    showAuth();
}

// Navigation
function showAuth() {
    views.dashboard.classList.add('hidden');
    views.auth.classList.remove('hidden');
}

async function initDashboard() {
    views.auth.classList.add('hidden');
    views.dashboard.classList.remove('hidden');

    try {
        await fetchUserData();
        await loadDashboardData();
    } catch (error) {
        console.error('Dashboard load failed', error);
        if (error.status === 401) logout();
    }
}

// API Helpers
async function authenticatedFetch(endpoint, options = {}) {
    const headers = {
        'Authorization': `Bearer ${state.token}`,
        'Content-Type': 'application/json',
        ...options.headers
    };

    const response = await fetch(`${API_URL}${endpoint}`, { ...options, headers });

    if (response.status === 401) {
        logout();
        throw { status: 401, message: 'Unauthorized' };
    }

    return response;
}

async function fetchUserData() {
    const response = await authenticatedFetch('/auth/me');
    state.user = await response.json();
    document.getElementById('user-name').textContent = state.user.email.split('@')[0];
}

function updateDate() {
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    document.getElementById('current-date').textContent = new Date().toLocaleDateString('en-US', options);
}
