/**
 * Utility module for logging functions across the application
 * Following the Single Responsibility Principle and DRY principles
 */

/**
 * Log color selection information for theme debugging
 *
 * @param {string} type - The type of color (primary, secondary, etc)
 * @param {string} value - The color value
 * @param {boolean} found - Whether the color was found in theme
 */
export function logColorSelection(type, value, found) {
  const status = found ? '✓' : '✗';
  const message = found
    ? `Using themed ${type} color: ${value}`
    : `Fallback to default ${type} color: themed color not found`;

  console.log(`%c Theme ${status} %c ${message}`,
    `background: ${found ? '#4CAF50' : '#F44336'}; color: white; padding: 2px;`,
    'background: transparent');
}

/**
 * Create a styled console logger for different message types
 *
 * @param {string} context - The context name to display in logs
 * @returns {Object} Logger methods (info, warn, error)
 */
export function createLogger(context) {
  return {
    info: (message, ...args) => console.log(
      `%c[${context}]%c ${message}`,
      'color: #2196F3; font-weight: bold',
      'color: inherit',
      ...args
    ),
    warn: (message, ...args) => console.warn(
      `%c[${context}]%c ${message}`,
      'color: #FF9800; font-weight: bold',
      'color: inherit',
      ...args
    ),
    error: (message, ...args) => console.error(
      `%c[${context}]%c ${message}`,
      'color: #F44336; font-weight: bold',
      'color: inherit',
      ...args
    )
  };
}
