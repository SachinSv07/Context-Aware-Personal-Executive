/**
 * Get authorization headers for API requests
 * Includes the token from localStorage
 * 
 * @returns {Object} Headers object with Authorization
 */
export function getAuthHeaders() {
  const token = localStorage.getItem('token');
  
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
}

/**
 * Get current logged-in user from localStorage
 * 
 * @returns {Object|null} User object or null if not logged in
 */
export function getCurrentUser() {
  const userJson = localStorage.getItem('user');
  
  if (!userJson) {
    return null;
  }
  
  try {
    return JSON.parse(userJson);
  } catch (e) {
    console.error('Failed to parse user data:', e);
    return null;
  }
}

/**
 * Check if user is authenticated
 * 
 * @returns {boolean} True if user has valid token
 */
export function isAuthenticated() {
  const token = localStorage.getItem('token');
  const user = localStorage.getItem('user');
  
  return !!(token && user);
}

/**
 * Clear authentication data
 */
export function clearAuth() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
}
