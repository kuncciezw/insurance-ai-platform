// This file contains JSDoc type definitions for better IDE support
// You can delete this file if you don't need the type hints

/**
 * @typedef {Object} User
 * @property {number} id
 * @property {string} username
 * @property {string} email
 * @property {string} first_name
 * @property {string} last_name
 */

/**
 * @typedef {Object} Policyholder
 * @property {number} id
 * @property {string} first_name
 * @property {string} last_name
 * @property {string} id_number
 * @property {string} date_of_birth
 * @property {string} gender
 * @property {string} marital_status
 * @property {string} occupation
 * @property {string} email
 * @property {string} phone_number
 * @property {string} address
 * @property {string} city
 * @property {string} created_at
 */

/**
 * @typedef {Object} Vehicle
 * @property {number} id
 * @property {number} policyholder
 * @property {string} registration_number
 * @property {string} make
 * @property {string} model
 * @property {number} year
 * @property {string} color
 * @property {string} chassis_number
 * @property {string} engine_number
 * @property {string} vehicle_type
 * @property {number} seating_capacity
 * @property {string} fuel_type
 * @property {number} engine_capacity
 * @property {string} created_at
 */

/**
 * @typedef {Object} Policy
 * @property {number} id
 * @property {string} policy_number
 * @property {number} policyholder
 * @property {number} vehicle
 * @property {string} policy_type
 * @property {string} coverage_type
 * @property {string} start_date
 * @property {string} end_date
 * @property {string} premium_amount
 * @property {string} sum_insured
 * @property {string} status
 * @property {string} created_at
 */

/**
 * @typedef {Object} Claim
 * @property {number} id
 * @property {string} claim_number
 * @property {number} policy
 * @property {string} incident_date
 * @property {string} claim_date
 * @property {string} incident_type
 * @property {string} incident_location
 * @property {string} description
 * @property {string} claimed_amount
 * @property {string} approved_amount
 * @property {string} status
 * @property {number} fraud_score
 * @property {boolean} is_fraudulent
 * @property {string} created_at
 */

export {};