/**
 * Validation Utility Library
 * Comprehensive validation functions for the Insurance AI Platform
 * Includes Zimbabwe-specific validations and international standards
 */

// ═══════════════════════════════════════════════════════════════════════════
// ZIMBABWE NATIONAL ID VALIDATION
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Validates and standardizes Zimbabwe National ID
 * Official format: XX-XXXXXXX L XX (e.g., 69-235489 C 67)
 * Handles various input formats with different separators
 * 
 * @param {string} nationalId - The national ID to validate
 * @returns {Object} { isValid: boolean, standardized: string, error: string }
 */
export const validateZimbabweNationalId = (nationalId) => {
  if (!nationalId) {
    return { isValid: false, standardized: '', error: 'National ID is required' };
  }

  // Remove all common separators and spaces
  const stripped = nationalId
    .replace(/[\s\-_/\\]/g, '')
    .toUpperCase()
    .trim();

  // Pattern: 2 digits, 4-7 digits, 1 letter, 2 digits
  // Example: 69235489C67
  const pattern = /^(\d{2})(\d{4,7})([A-Z])(\d{2})$/;
  const match = stripped.match(pattern);

  if (!match) {
    return {
      isValid: false,
      standardized: '',
      error: 'Invalid National ID format. Expected format: XX-XXXXXXX L XX'
    };
  }

  // Standardize to official format: XX-XXXXXXX L XX
  const [, part1, part2, letter, part3] = match;
  const standardized = `${part1}-${part2} ${letter} ${part3}`;

  return {
    isValid: true,
    standardized,
    error: ''
  };
};

// ═══════════════════════════════════════════════════════════════════════════
// PHONE NUMBER VALIDATION (ZIMBABWE)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Validates Zimbabwe phone numbers (mobile, landline, toll-free, etc.)
 * Mobile prefixes: 71 (NetOne), 73 (Telecel), 77/78 (Econet)
 * 
 * @param {string} phoneNumber - The phone number to validate
 * @returns {Object} { isValid: boolean, type: string, formatted: string, error: string }
 */
export const validateZimbabwePhoneNumber = (phoneNumber) => {
  if (!phoneNumber) {
    return { isValid: false, type: null, formatted: '', error: 'Phone number is required' };
  }

  // Clean the number
  const cleaned = phoneNumber.replace(/[\s\-\(\)]/g, '');

  // Mobile pattern: +263 or 0, followed by 7[1378], then 7 digits
  // Covers NetOne (71), Telecel (73), Econet (77, 78)
  const mobilePattern = /^(?:\+263|0)7[1378]\d{7}$/;
  
  // Landline pattern: geographic area codes
  const landlinePattern = /^(?:\+263|0)(?:2[0-9]|3[19]|5[4-5]|6[1678]|8[1-9])\d{6,7}$/;
  
  // Toll-free pattern
  const tollFreePattern = /^(?:\+263|0)080[0-8]\d{4}$/;
  
  // Premium rate services
  const premiumPattern = /^(?:\+263|0)3\d{4}$/;
  
  // VoIP services
  const voipPattern = /^(?:\+263|0)86\d{8}$/;

  // Format to international format
  let formatted = cleaned;
  if (cleaned.startsWith('0')) {
    formatted = '+263' + cleaned.substring(1);
  }

  if (mobilePattern.test(cleaned)) {
    return { isValid: true, type: 'mobile', formatted, error: '' };
  }
  if (landlinePattern.test(cleaned)) {
    return { isValid: true, type: 'landline', formatted, error: '' };
  }
  if (tollFreePattern.test(cleaned)) {
    return { isValid: true, type: 'toll-free', formatted, error: '' };
  }
  if (premiumPattern.test(cleaned)) {
    return { isValid: true, type: 'premium', formatted, error: '' };
  }
  if (voipPattern.test(cleaned)) {
    return { isValid: true, type: 'voip', formatted, error: '' };
  }

  return {
    isValid: false,
    type: null,
    formatted: '',
    error: 'Invalid Zimbabwe phone number format. Mobile numbers should start with 071, 073, 077, or 078'
  };
};

/**
 * Validates specifically mobile numbers only (stricter validation)
 */
export const validateZimbabweMobileNumber = (phoneNumber) => {
  const result = validateZimbabwePhoneNumber(phoneNumber);
  if (!result.isValid) return result;
  
  if (result.type !== 'mobile') {
    return {
      isValid: false,
      type: result.type,
      formatted: result.formatted,
      error: 'Only mobile numbers are accepted. Please provide a mobile number starting with 071, 073, 077, or 078'
    };
  }
  
  return result;
};

// ═══════════════════════════════════════════════════════════════════════════
// EMAIL VALIDATION
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Validates email address format
 * Uses RFC 5322 compliant regex pattern
 * 
 * @param {string} email - The email address to validate
 * @returns {Object} { isValid: boolean, error: string }
 */
export const validateEmail = (email) => {
  if (!email) {
    return { isValid: false, error: 'Email address is required' };
  }

  // RFC 5322 compliant email regex
  const emailPattern = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;

  if (!emailPattern.test(email.trim())) {
    return { isValid: false, error: 'Invalid email address format' };
  }

  return { isValid: true, error: '' };
};

// ═══════════════════════════════════════════════════════════════════════════
// DATE OF BIRTH VALIDATION (18+ REQUIREMENT)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Validates date of birth and ensures person is at least 18 years old
 * 
 * @param {string|Date} dateOfBirth - The date of birth to validate (ISO string or Date object)
 * @param {number} minAge - Minimum required age (default: 18)
 * @returns {Object} { isValid: boolean, age: number, error: string }
 */
export const validateDateOfBirth = (dateOfBirth, minAge = 18) => {
  if (!dateOfBirth) {
    return { isValid: false, age: null, error: 'Date of birth is required' };
  }

  const dob = new Date(dateOfBirth);
  const today = new Date();

  // Check if date is valid
  if (isNaN(dob.getTime())) {
    return { isValid: false, age: null, error: 'Invalid date format' };
  }

  // Check if date is not in the future
  if (dob > today) {
    return { isValid: false, age: null, error: 'Date of birth cannot be in the future' };
  }

  // Calculate age
  let age = today.getFullYear() - dob.getFullYear();
  const monthDiff = today.getMonth() - dob.getMonth();
  
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < dob.getDate())) {
    age--;
  }

  // Check minimum age requirement
  if (age < minAge) {
    return {
      isValid: false,
      age,
      error: `You must be at least ${minAge} years old. Current age: ${age}`
    };
  }

  // Check reasonable maximum age (e.g., 120 years)
  if (age > 120) {
    return {
      isValid: false,
      age,
      error: 'Date of birth appears to be invalid (age exceeds 120 years)'
    };
  }

  return { isValid: true, age, error: '' };
};

/**
 * Gets maximum allowed date for age requirement (useful for date input max attribute)
 */
export const getMaxDateForAge = (minAge = 18) => {
  const date = new Date();
  date.setFullYear(date.getFullYear() - minAge);
  return date.toISOString().split('T')[0];
};

// ═══════════════════════════════════════════════════════════════════════════
// MONEY/CURRENCY VALIDATION
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Validates monetary values
 * Ensures positive numbers with optional 2 decimal places
 * 
 * @param {string|number} amount - The amount to validate
 * @param {Object} options - Validation options
 * @returns {Object} { isValid: boolean, value: number, formatted: string, error: string }
 */
export const validateMoney = (amount, options = {}) => {
  const {
    min = 0,
    max = Infinity,
    required = true,
    allowZero = false
  } = options;

  if (!amount && amount !== 0) {
    if (required) {
      return { isValid: false, value: null, formatted: '', error: 'Amount is required' };
    }
    return { isValid: true, value: 0, formatted: '0.00', error: '' };
  }

  // Convert to number and validate
  const value = typeof amount === 'string' ? parseFloat(amount) : amount;

  if (isNaN(value)) {
    return { isValid: false, value: null, formatted: '', error: 'Invalid amount format' };
  }

  if (value < 0) {
    return { isValid: false, value, formatted: '', error: 'Amount cannot be negative' };
  }

  if (!allowZero && value === 0) {
    return { isValid: false, value, formatted: '', error: 'Amount must be greater than zero' };
  }

  if (value < min) {
    return { isValid: false, value, formatted: '', error: `Amount must be at least ${min}` };
  }

  if (value > max) {
    return { isValid: false, value, formatted: '', error: `Amount cannot exceed ${max}` };
  }

  // Format to 2 decimal places
  const formatted = value.toFixed(2);

  return { isValid: true, value, formatted, error: '' };
};

// ═══════════════════════════════════════════════════════════════════════════
// VEHICLE REGISTRATION VALIDATION
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Validates vehicle registration numbers (Zimbabwe and international formats)
 * 
 * @param {string} registrationNumber - The registration number to validate
 * @param {string} country - Country code for specific validation (default: 'ZW' for Zimbabwe)
 * @returns {Object} { isValid: boolean, formatted: string, country: string, error: string }
 */
export const validateVehicleRegistration = (registrationNumber, country = 'ZW') => {
  if (!registrationNumber) {
    return { isValid: false, formatted: '', country, error: 'Registration number is required' };
  }

  const cleaned = registrationNumber.trim().toUpperCase();

  // Zimbabwe format: 3 letters + space/hyphen (optional) + 4 digits
  // Current format (post-2006): ABC 1234 or ABC-1234
  // Old format (pre-2006): ABC 123 or ABC-123
  if (country === 'ZW') {
    const currentPattern = /^[A-Z]{3}[ -]?[0-9]{4}$/;
    const oldPattern = /^[A-Z]{3}[ -]?[0-9]{3}$/;

    if (currentPattern.test(cleaned)) {
      // Standardize format: ABC-1234
      const formatted = cleaned.replace(/[ -]?/, '-');
      return { isValid: true, formatted, country: 'ZW', error: '' };
    }

    if (oldPattern.test(cleaned)) {
      const formatted = cleaned.replace(/[ -]?/, '-');
      return { isValid: true, formatted, country: 'ZW', error: '' };
    }

    return {
      isValid: false,
      formatted: '',
      country: 'ZW',
      error: 'Invalid Zimbabwe registration format. Expected: ABC-1234 or ABC-123 (old format)'
    };
  }

  // International formats - basic validation
  // Most countries use alphanumeric combinations between 2-10 characters
  const internationalPattern = /^[A-Z0-9]{2,10}$/;
  
  if (internationalPattern.test(cleaned.replace(/[\s\-]/g, ''))) {
    return { isValid: true, formatted: cleaned, country, error: '' };
  }

  return {
    isValid: false,
    formatted: '',
    country,
    error: 'Invalid registration number format'
  };
};

// ═══════════════════════════════════════════════════════════════════════════
// VIN (VEHICLE IDENTIFICATION NUMBER) VALIDATION
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Validates Vehicle Identification Number (VIN)
 * Standard VIN is 17 characters (excludes I, O, Q to avoid confusion with 1, 0)
 * 
 * @param {string} vin - The VIN to validate
 * @returns {Object} { isValid: boolean, formatted: string, error: string }
 */
export const validateVIN = (vin) => {
  if (!vin) {
    return { isValid: false, formatted: '', error: 'VIN is required' };
  }

  const cleaned = vin.trim().toUpperCase().replace(/[\s\-]/g, '');

  // VIN must be exactly 17 characters
  if (cleaned.length !== 17) {
    return {
      isValid: false,
      formatted: '',
      error: `VIN must be exactly 17 characters (currently ${cleaned.length})`
    };
  }

  // VIN pattern: alphanumeric, no I, O, Q
  const vinPattern = /^[A-HJ-NPR-Z0-9]{17}$/;

  if (!vinPattern.test(cleaned)) {
    return {
      isValid: false,
      formatted: '',
      error: 'Invalid VIN format. VIN should contain only letters (except I, O, Q) and numbers'
    };
  }

  // Optional: VIN checksum validation (9th character is check digit)
  // This is a more advanced validation that can be added if needed

  return { isValid: true, formatted: cleaned, error: '' };
};

// ═══════════════════════════════════════════════════════════════════════════
// PASSWORD VALIDATION
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Validates password strength
 * Requirements: min 8 chars, uppercase, lowercase, number, special char
 * 
 * @param {string} password - The password to validate
 * @returns {Object} { isValid: boolean, checks: object, error: string }
 */
export const validatePassword = (password) => {
  if (!password) {
    return {
      isValid: false,
      checks: {},
      error: 'Password is required'
    };
  }

  const checks = {
    minLength: password.length >= 8,
    hasUpper: /[A-Z]/.test(password),
    hasLower: /[a-z]/.test(password),
    hasNumber: /[0-9]/.test(password),
    hasSpecial: /[!@#$%^&*(),.?":{}|<>]/.test(password),
  };

  const isValid = Object.values(checks).every(check => check);

  const errors = [];
  if (!checks.minLength) errors.push('at least 8 characters');
  if (!checks.hasUpper) errors.push('one uppercase letter');
  if (!checks.hasLower) errors.push('one lowercase letter');
  if (!checks.hasNumber) errors.push('one number');
  if (!checks.hasSpecial) errors.push('one special character');

  return {
    isValid,
    checks,
    error: isValid ? '' : `Password must contain: ${errors.join(', ')}`
  };
};

/**
 * Validates password confirmation match
 */
export const validatePasswordMatch = (password, confirmPassword) => {
  if (!confirmPassword) {
    return { isValid: false, error: 'Please confirm your password' };
  }

  if (password !== confirmPassword) {
    return { isValid: false, error: 'Passwords do not match' };
  }

  return { isValid: true, error: '' };
};

// ═══════════════════════════════════════════════════════════════════════════
// USERNAME VALIDATION
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Validates username
 * Requirements: 3-20 characters, alphanumeric and underscores only
 * 
 * @param {string} username - The username to validate
 * @returns {Object} { isValid: boolean, error: string }
 */
export const validateUsername = (username) => {
  if (!username) {
    return { isValid: false, error: 'Username is required' };
  }

  const cleaned = username.trim();

  if (cleaned.length < 3) {
    return { isValid: false, error: 'Username must be at least 3 characters long' };
  }

  if (cleaned.length > 20) {
    return { isValid: false, error: 'Username cannot exceed 20 characters' };
  }

  // Alphanumeric and underscores only
  const usernamePattern = /^[a-zA-Z0-9_]+$/;

  if (!usernamePattern.test(cleaned)) {
    return {
      isValid: false,
      error: 'Username can only contain letters, numbers, and underscores'
    };
  }

  return { isValid: true, error: '' };
};

// ═══════════════════════════════════════════════════════════════════════════
// NUMERIC RANGE VALIDATIONS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Validates credit score (300-850 range)
 */
export const validateCreditScore = (score) => {
  return validateNumericRange(score, 300, 850, 'Credit score');
};

/**
 * Validates age (18-120 range)
 */
export const validateAge = (age) => {
  return validateNumericRange(age, 18, 120, 'Age');
};

/**
 * Validates vehicle year (1900 to current year + 1)
 */
export const validateVehicleYear = (year) => {
  const currentYear = new Date().getFullYear();
  return validateNumericRange(year, 1900, currentYear + 1, 'Year');
};

/**
 * Generic numeric range validator
 */
export const validateNumericRange = (value, min, max, fieldName = 'Value') => {
  if (value === '' || value == null) {
    return { isValid: false, value: null, error: `${fieldName} is required` };
  }

  const numValue = typeof value === 'string' ? parseFloat(value) : value;

  if (isNaN(numValue)) {
    return { isValid: false, value: null, error: `${fieldName} must be a number` };
  }

  if (numValue < min) {
    return { isValid: false, value: numValue, error: `${fieldName} must be at least ${min}` };
  }

  if (numValue > max) {
    return { isValid: false, value: numValue, error: `${fieldName} cannot exceed ${max}` };
  }

  return { isValid: true, value: numValue, error: '' };
};

// ═══════════════════════════════════════════════════════════════════════════
// BATCH/FORM VALIDATION HELPERS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Validates multiple fields at once
 * Returns an object with field names as keys and error messages as values
 * 
 * @param {Object} validations - Object with field names and their validation results
 * @returns {Object} { isValid: boolean, errors: object }
 */
export const validateForm = (validations) => {
  const errors = {};
  let isValid = true;

  Object.entries(validations).forEach(([field, result]) => {
    if (result && !result.isValid && result.error) {
      errors[field] = result.error;
      isValid = false;
    }
  });

  return { isValid, errors };
};

/**
 * Validates required fields
 */
export const validateRequired = (value, fieldName = 'Field') => {
  if (!value || (typeof value === 'string' && !value.trim())) {
    return { isValid: false, error: `${fieldName} is required` };
  }
  return { isValid: true, error: '' };
};

// ═══════════════════════════════════════════════════════════════════════════
// EXPORT ALL VALIDATORS AS NAMED OBJECT
// ═══════════════════════════════════════════════════════════════════════════

export const validators = {
  // National ID & Identity
  zimbabweNationalId: validateZimbabweNationalId,
  
  // Phone Numbers
  zimbabwePhone: validateZimbabwePhoneNumber,
  zimbabweMobile: validateZimbabweMobileNumber,
  
  // Email & Authentication
  email: validateEmail,
  password: validatePassword,
  passwordMatch: validatePasswordMatch,
  username: validateUsername,
  
  // Dates
  dateOfBirth: validateDateOfBirth,
  getMaxDateForAge,
  
  // Money
  money: validateMoney,
  
  // Vehicle
  vehicleRegistration: validateVehicleRegistration,
  vin: validateVIN,
  vehicleYear: validateVehicleYear,
  
  // Numeric Ranges
  creditScore: validateCreditScore,
  age: validateAge,
  numericRange: validateNumericRange,
  
  // Form Helpers
  required: validateRequired,
  validateForm
};

export default validators;