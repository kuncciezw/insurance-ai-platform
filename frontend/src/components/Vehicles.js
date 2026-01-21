import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/api';
import Sidebar from './Sidebar';
import { useNotification } from './notifications/useNotification';
import { useConfirm } from './notifications/useConfirm';
import {
  Search,
  Plus,
  Edit,
  Trash2,
  X,
} from 'lucide-react';

export default function Vehicles() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { showNotification, NotificationContainer } = useNotification();
  const { showConfirm, ConfirmDialog } = useConfirm();
  
  const [vehicles, setVehicles] = useState([]);
  const [policyholders, setPolicyholders] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    policyholder: '',
    registration_number: '',
    make: '',
    model: '',
    year: new Date().getFullYear(),
    color: '',
    vin: '',
    vehicle_id: '',
    vehicle_type: 'SEDAN',
    seating_capacity: 5,
    fuel_type: 'PETROL',
    engine_capacity: 1500,
    market_value: 0,
    odometer_reading: 0,
    has_anti_theft: false,
    has_airbags: true,
    has_abs: true,
    is_modified: false,
  });

  useEffect(() => {
    fetchVehicles();
    fetchPolicyholders();
  }, []);

  const fetchVehicles = async () => {
    try {
      setIsLoading(true);
      const data = await api.getVehicles();
      setVehicles(data.results || data);
    } catch (err) {
      console.error('Failed to fetch vehicles:', err);
      showNotification('Failed to load vehicles', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchPolicyholders = async () => {
    try {
      const data = await api.getPolicyholders();
      setPolicyholders(data.results || data);
    } catch (err) {
      console.error('Failed to fetch policyholders:', err);
      showNotification('Failed to load policyholders', 'error');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingId) {
        await api.updateVehicle(editingId, formData);
        showNotification('Vehicle updated successfully', 'success');
      } else {
        await api.createVehicle(formData);
        showNotification('Vehicle created successfully', 'success');
      }
      setShowModal(false);
      resetForm();
      fetchVehicles();
    } catch (err) {
      console.error('Failed to save vehicle:', err);
      showNotification(
        err.message || 'Failed to save vehicle. Please check all required fields.',
        'error'
      );
    }
  };

  const handleEdit = (vehicle) => {
    setEditingId(vehicle.id);
    setFormData({
      policyholder: vehicle.policyholder,
      registration_number: vehicle.registration_number,
      make: vehicle.make,
      model: vehicle.model,
      year: vehicle.year,
      color: vehicle.color,
      vin: vehicle.vin,
      vehicle_id: vehicle.vehicle_id,
      vehicle_type: vehicle.vehicle_type,
      seating_capacity: vehicle.seating_capacity,
      fuel_type: vehicle.fuel_type,
      engine_capacity: vehicle.engine_capacity,
      market_value: vehicle.market_value,
      odometer_reading: vehicle.odometer_reading,
      has_anti_theft: vehicle.has_anti_theft,
      has_airbags: vehicle.has_airbags,
      has_abs: vehicle.has_abs,
      is_modified: vehicle.is_modified,
    });
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    const confirmed = await showConfirm({
      title: 'Delete Vehicle',
      message: 'Are you sure you want to delete this vehicle? This action cannot be undone.',
      type: 'danger',
    });

    if (confirmed) {
      try {
        await api.deleteVehicle(id);
        showNotification('Vehicle deleted successfully', 'success');
        fetchVehicles();
      } catch (err) {
        console.error('Failed to delete vehicle:', err);
        showNotification(err.message || 'Failed to delete vehicle', 'error');
      }
    }
  };

  const resetForm = () => {
    setEditingId(null);
    setFormData({
      policyholder: '',
      registration_number: '',
      make: '',
      model: '',
      year: new Date().getFullYear(),
      color: '',
      vin: '',
      vehicle_id: '',
      vehicle_type: 'SEDAN',
      seating_capacity: 5,
      fuel_type: 'PETROL',
      engine_capacity: 1500,
      market_value: 0,
      odometer_reading: 0,
      has_anti_theft: false,
      has_airbags: true,
      has_abs: true,
      is_modified: false,
    });
  };

  const filteredVehicles = vehicles.filter((v) =>
    `${v.make} ${v.model} ${v.registration_number} ${v.policyholder_name || 'Unknown'}`
      .toLowerCase()
      .includes(searchTerm.toLowerCase())
  );

  return (
    <div className="flex h-screen overflow-hidden" style={{ backgroundColor: '#F8F9FA' }}>
      <Sidebar />
      <NotificationContainer />
      <ConfirmDialog />

      {/* Main Content */}
      <div className="flex-1 p-8 overflow-y-auto">
        <div className="mb-8">
          <h2 className="text-3xl font-bold" style={{ color: '#2C3E50' }}>
            Vehicles
          </h2>
          <p className="mt-2" style={{ color: '#7F8C8D' }}>
            Manage vehicle information
          </p>
        </div>

        {/* Search and Add */}
        <div className="bg-white p-6 rounded-lg shadow-lg mb-6">
          <div className="flex items-center justify-between gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5" style={{ color: '#7F8C8D' }} />
              <input
                type="text"
                placeholder="Search vehicles..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-3 rounded-lg border focus:outline-none focus:ring-2"
                style={{ borderColor: '#E5E7EB', backgroundColor: '#F8F9FA' }}
                onFocus={(e) => {
                  e.target.style.borderColor = '#FF6B4A';
                  e.target.style.backgroundColor = 'white';
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = '#E5E7EB';
                  e.target.style.backgroundColor = '#F8F9FA';
                }}
              />
            </div>
            <button
              onClick={() => {
                resetForm();
                setShowModal(true);
              }}
              className="flex items-center px-6 py-3 rounded-lg text-white font-medium transition-colors"
              style={{ backgroundColor: '#FF6B4A' }}
              onMouseEnter={(e) => {
                e.target.style.backgroundColor = '#E55A3A';
              }}
              onMouseLeave={(e) => {
                e.target.style.backgroundColor = '#FF6B4A';
              }}
            >
              <Plus className="w-5 h-5 mr-2" />
              Add Vehicle
            </button>
          </div>
        </div>

        {/* Table */}
        {isLoading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2" style={{ borderColor: '#FF6B4A' }}></div>
            <p className="mt-4" style={{ color: '#7F8C8D' }}>Loading vehicles...</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead style={{ backgroundColor: '#F8F9FA' }}>
                  <tr>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>Registration</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>Make & Model</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>Year</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>Type</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>Value</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>Owner</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold" style={{ color: '#2C3E50' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredVehicles.length === 0 ? (
                    <tr>
                      <td colSpan="7" className="px-6 py-8 text-center" style={{ color: '#7F8C8D' }}>
                        No vehicles found
                      </td>
                    </tr>
                  ) : (
                    filteredVehicles.map((vehicle) => (
                      <tr key={vehicle.id} className="border-t" style={{ borderColor: '#E5E7EB' }}>
                        <td className="px-6 py-4" style={{ color: '#2C3E50' }}>
                          {vehicle.registration_number}
                        </td>
                        <td className="px-6 py-4" style={{ color: '#7F8C8D' }}>
                          {vehicle.make} {vehicle.model}
                        </td>
                        <td className="px-6 py-4" style={{ color: '#7F8C8D' }}>{vehicle.year}</td>
                        <td className="px-6 py-4" style={{ color: '#7F8C8D' }}>
                          {vehicle.vehicle_type?.replace('_', ' ')}
                        </td>
                        <td className="px-6 py-4" style={{ color: '#7F8C8D' }}>
                          ${(vehicle.market_value || 0).toLocaleString()}
                        </td>
                        <td className="px-6 py-4" style={{ color: '#7F8C8D' }}>{vehicle.policyholder_name || 'Unknown'}</td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleEdit(vehicle)}
                              className="p-2 rounded-lg transition-colors"
                              style={{ backgroundColor: '#EBF5FF', color: '#3B82F6' }}
                              onMouseEnter={(e) => {
                                e.target.style.backgroundColor = '#3B82F6';
                                e.target.style.color = 'white';
                              }}
                              onMouseLeave={(e) => {
                                e.target.style.backgroundColor = '#EBF5FF';
                                e.target.style.color = '#3B82F6';
                              }}
                            >
                              <Edit className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDelete(vehicle.id)}
                              className="p-2 rounded-lg transition-colors"
                              style={{ backgroundColor: '#FEE2E2', color: '#EF4444' }}
                              onMouseEnter={(e) => {
                                e.target.style.backgroundColor = '#EF4444';
                                e.target.style.color = 'white';
                              }}
                              onMouseLeave={(e) => {
                                e.target.style.backgroundColor = '#FEE2E2';
                                e.target.style.color = '#EF4444';
                              }}
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Modal */}
        {showModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b" style={{ borderColor: '#E5E7EB' }}>
                <div className="flex items-center justify-between">
                  <h3 className="text-2xl font-bold" style={{ color: '#2C3E50' }}>
                    {editingId ? 'Edit Vehicle' : 'Add Vehicle'}
                  </h3>
                  <button
                    onClick={() => {
                      setShowModal(false);
                      resetForm();
                    }}
                    className="p-2 rounded-lg transition-colors"
                    style={{ backgroundColor: '#F8F9FA', color: '#7F8C8D' }}
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              <div className="p-6">
                {/* Policyholder */}
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                    Policyholder *
                  </label>
                  <select
                    required
                    value={formData.policyholder}
                    onChange={(e) => setFormData({ ...formData, policyholder: e.target.value })}
                    className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                    style={{ borderColor: '#E5E7EB' }}
                  >
                    <option value="">Select Policyholder</option>
                    {policyholders.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.full_name || `${p.first_name} ${p.last_name}`} ({p.policy_holder_id || p.id_number})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Vehicle ID and Year */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Vehicle ID *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.vehicle_id}
                      onChange={(e) => setFormData({ ...formData, vehicle_id: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                      placeholder="e.g., VEH-12345"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Year *
                    </label>
                    <input
                      type="number"
                      required
                      value={formData.year}
                      onChange={(e) => setFormData({ ...formData, year: parseInt(e.target.value) })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                      min="1900"
                      max={new Date().getFullYear() + 1}
                    />
                  </div>
                </div>

                {/* Registration and VIN */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Registration Number *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.registration_number}
                      onChange={(e) => setFormData({ ...formData, registration_number: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                      placeholder="e.g., ABZ-1234"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      VIN (Chassis Number) *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.vin}
                      onChange={(e) => setFormData({ ...formData, vin: e.target.value.toUpperCase() })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                      placeholder="17-character VIN"
                      maxLength="17"
                    />
                  </div>
                </div>

                {/* Make and Model */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Make *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.make}
                      onChange={(e) => setFormData({ ...formData, make: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                      placeholder="e.g., Toyota"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Model *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.model}
                      onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                      placeholder="e.g., Corolla"
                    />
                  </div>
                </div>

                {/* Vehicle Type and Fuel Type */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Vehicle Type *
                    </label>
                    <select
                      required
                      value={formData.vehicle_type}
                      onChange={(e) => setFormData({ ...formData, vehicle_type: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                    >
                      <option value="SEDAN">Sedan</option>
                      <option value="SUV">SUV</option>
                      <option value="TRUCK">Truck</option>
                      <option value="HATCHBACK">Hatchback</option>
                      <option value="COUPE">Coupe</option>
                      <option value="VAN">Van</option>
                      <option value="MOTORCYCLE">Motorcycle</option>
                      <option value="SPORTS_CAR">Sports Car</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Fuel Type *
                    </label>
                    <select
                      required
                      value={formData.fuel_type}
                      onChange={(e) => setFormData({ ...formData, fuel_type: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                    >
                      <option value="PETROL">Petrol</option>
                      <option value="DIESEL">Diesel</option>
                      <option value="ELECTRIC">Electric</option>
                      <option value="HYBRID">Hybrid</option>
                      <option value="CNG">CNG</option>
                    </select>
                  </div>
                </div>

                {/* Market Value and Odometer */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Market Value ($) *
                    </label>
                    <input
                      type="number"
                      required
                      value={formData.market_value}
                      onChange={(e) => setFormData({ ...formData, market_value: parseFloat(e.target.value) })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                      min="0"
                      step="100"
                      placeholder="e.g., 25000"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Odometer (km) *
                    </label>
                    <input
                      type="number"
                      required
                      value={formData.odometer_reading}
                      onChange={(e) => setFormData({ ...formData, odometer_reading: parseInt(e.target.value) })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                      min="0"
                      placeholder="e.g., 50000"
                    />
                  </div>
                </div>

                {/* Color and Seating Capacity */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Color *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.color}
                      onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                      placeholder="e.g., Silver"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                      Seating Capacity *
                    </label>
                    <input
                      type="number"
                      required
                      value={formData.seating_capacity}
                      onChange={(e) => setFormData({ ...formData, seating_capacity: parseInt(e.target.value) })}
                      className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                      style={{ borderColor: '#E5E7EB' }}
                      min="1"
                      max="50"
                      placeholder="e.g., 5"
                    />
                  </div>
                </div>

                {/* Engine Capacity */}
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-2" style={{ color: '#2C3E50' }}>
                    Engine Capacity (cc) *
                  </label>
                  <input
                    type="number"
                    required
                    value={formData.engine_capacity}
                    onChange={(e) => setFormData({ ...formData, engine_capacity: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
                    style={{ borderColor: '#E5E7EB' }}
                    min="500"
                    max="10000"
                    placeholder="e.g., 1500"
                  />
                </div>

                {/* Safety Features */}
                <div className="mb-6">
                  <label className="block text-sm font-medium mb-3" style={{ color: '#2C3E50' }}>
                    Safety & Features
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.has_anti_theft}
                        onChange={(e) => setFormData({ ...formData, has_anti_theft: e.target.checked })}
                        className="w-4 h-4 rounded"
                        style={{ accentColor: '#FF6B4A' }}
                      />
                      <span style={{ color: '#7F8C8D' }}>Anti-theft System</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.has_airbags}
                        onChange={(e) => setFormData({ ...formData, has_airbags: e.target.checked })}
                        className="w-4 h-4 rounded"
                        style={{ accentColor: '#FF6B4A' }}
                      />
                      <span style={{ color: '#7F8C8D' }}>Airbags</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.has_abs}
                        onChange={(e) => setFormData({ ...formData, has_abs: e.target.checked })}
                        className="w-4 h-4 rounded"
                        style={{ accentColor: '#FF6B4A' }}
                      />
                      <span style={{ color: '#7F8C8D' }}>ABS Brakes</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.is_modified}
                        onChange={(e) => setFormData({ ...formData, is_modified: e.target.checked })}
                        className="w-4 h-4 rounded"
                        style={{ accentColor: '#FF6B4A' }}
                      />
                      <span style={{ color: '#7F8C8D' }}>Modified Vehicle</span>
                    </label>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex justify-end gap-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowModal(false);
                      resetForm();
                    }}
                    className="px-6 py-2 rounded-lg font-medium transition-colors"
                    style={{ backgroundColor: '#F8F9FA', color: '#7F8C8D' }}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSubmit}
                    className="px-6 py-2 rounded-lg text-white font-medium transition-colors"
                    style={{ backgroundColor: '#FF6B4A' }}
                    onMouseEnter={(e) => {
                      e.target.style.backgroundColor = '#E55A3A';
                    }}
                    onMouseLeave={(e) => {
                      e.target.style.backgroundColor = '#FF6B4A';
                    }}
                  >
                    {editingId ? 'Update' : 'Create'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}