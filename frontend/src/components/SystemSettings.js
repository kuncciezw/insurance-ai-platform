import { useState, useEffect } from 'react';
import Sidebar from './Sidebar';
import { Settings, Building2, Users, Shield, UserCheck, DollarSign } from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from './notifications/useNotification';
import { useConfirm } from './notifications/useConfirm';

// Import modular components
import CompanyProfileTab from './settings/CompanyProfileTab';
import UsersTab from './settings/UsersTab';
import PendingUsersTab from './settings/PendingUsersTab';
import RolesTab from './settings/RolesTab';
import GlobalPricingSettingsTab from './settings/GlobalPricingSettingsTab';
import UserManagementModal from './settings/UserManagementModal';
import UserApprovalModal from './settings/UserApprovalModal';

export default function SystemSettings() {
  const { user } = useAuth();
  const { showNotification, NotificationContainer } = useNotification();
  const { showConfirm, ConfirmDialog } = useConfirm();

  const [activeTab, setActiveTab] = useState('company');
  const [users, setUsers] = useState([]);
  const [pendingUsers, setPendingUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showUserModal, setShowUserModal] = useState(false);
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [approvingUser, setApprovingUser] = useState(null);
  const [permissions, setPermissions] = useState({});

  // Company Profile State
  const [companyProfile, setCompanyProfile] = useState({
    company_name: 'Insurance AI',
    company_tagline: 'Admin Portal',
    email: '',
    phone: '',
    website: '',
    address_line1: '',
    address_line2: '',
    city: '',
    state: '',
    postal_code: '',
    country: '',
    tax_id: '',
    license_number: '',
    primary_color: '#FF6B4A',
    secondary_color: '#2C3E50',
  });
  const [originalProfile, setOriginalProfile] = useState({});
  const [profileChanged, setProfileChanged] = useState(false);

  const tabs = [
    { id: 'company',   label: 'Company Profile',     icon: Building2 },
    { id: 'pricing',  label: 'Pricing Settings',    icon: DollarSign },
    { id: 'pending',   label: 'Pending Users',        icon: UserCheck, badge: pendingUsers.length },
    { id: 'users',     label: 'Active Users',         icon: Users },
    { id: 'roles',     label: 'Roles & Permissions',  icon: Shield },
  ];

  const permissionsList = [
    { id: 'can_manage_users',         label: 'Manage Users' },
    { id: 'can_view_policyholders',   label: 'View Policyholders' },
    { id: 'can_create_policyholders', label: 'Create Policyholders' },
    { id: 'can_edit_policyholders',   label: 'Edit Policyholders' },
    { id: 'can_delete_policyholders', label: 'Delete Policyholders' },
    { id: 'can_view_policies',        label: 'View Policies' },
    { id: 'can_create_policies',      label: 'Create Policies' },
    { id: 'can_edit_policies',        label: 'Edit Policies' },
    { id: 'can_delete_policies',      label: 'Delete Policies' },
    { id: 'can_view_claims',          label: 'View Claims' },
    { id: 'can_process_claims',       label: 'Process Claims' },
    { id: 'can_approve_claims',       label: 'Approve Claims' },
    { id: 'can_delete_claims',        label: 'Delete Claims' },
    { id: 'can_use_fraud_detection',  label: 'Use Fraud Detection' },
    { id: 'can_flag_fraud',           label: 'Flag Fraud' },
    { id: 'can_calculate_premium',    label: 'Calculate Premium' },
    { id: 'can_estimate_claims',      label: 'Estimate Claims' },
    { id: 'can_export_reports',       label: 'Export Reports' },
  ];

  useEffect(() => {
    if (activeTab === 'company') {
      fetchCompanyProfile();
    } else if (activeTab === 'users') {
      fetchUsers();
    } else if (activeTab === 'pending') {
      fetchPendingUsers();
    } else if (activeTab === 'roles') {
      fetchRolesAndPermissions();
    }
    // 'currency' tab is self-contained — no fetch needed
  }, [activeTab]);

  // Auto-refresh pending users count every minute
  useEffect(() => {
    fetchPendingUsers();
    const interval = setInterval(fetchPendingUsers, 60000);
    return () => clearInterval(interval);
  }, []);

  // Detect unsaved company profile changes
  useEffect(() => {
    const changed = JSON.stringify(companyProfile) !== JSON.stringify(originalProfile);
    setProfileChanged(changed);
  }, [companyProfile, originalProfile]);

  // ── Data fetchers ──────────────────────────────────────────────────

  const fetchCompanyProfile = async () => {
    try {
      setLoading(true);
      const data = await api.getCompanyProfile();
      setCompanyProfile(data);
      setOriginalProfile(data);
    } catch (err) {
      showNotification('Failed to load company profile: ' + err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const data = await api.getUsers();
      const activeUsers = (data.results || data).filter((u) => u.is_active);
      setUsers(activeUsers);
    } catch (err) {
      showNotification('Failed to load users: ' + err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchPendingUsers = async () => {
    try {
      const data = await api.getUsers();
      const pending = (data.results || data).filter((u) => !u.is_active);
      setPendingUsers(pending);
    } catch (err) {
      console.error('Failed to load pending users:', err);
    }
  };

  const fetchRolesAndPermissions = async () => {
    try {
      setLoading(true);
      const data = await api.getRoles();
      if (data.roles) setPermissions(data.roles);
    } catch (err) {
      showNotification('Failed to load roles and permissions: ' + err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  // ── Handlers ──────────────────────────────────────────────────────

  const handleSaveCompanyProfile = async () => {
    try {
      setLoading(true);
      await api.updateCompanyProfile(companyProfile);
      showNotification('Company profile updated successfully', 'success');
      setOriginalProfile(companyProfile);
    } catch (err) {
      showNotification('Failed to update company profile: ' + err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleResetCompanyProfile = () => setCompanyProfile(originalProfile);

  const handleAddUser = () => {
    setEditingUser(null);
    setShowUserModal(true);
  };

  const handleEditUser = (user) => {
    setEditingUser(user);
    setShowUserModal(true);
  };

  const handleDeleteUser = async (userId) => {
    const confirmed = await showConfirm({
      title: 'Delete User',
      message: 'Are you sure you want to delete this user? This action cannot be undone.',
      type: 'danger',
      confirmText: 'Delete User',
      cancelText: 'Cancel',
    });
    if (!confirmed) return;

    try {
      await api.deleteUser(userId);
      showNotification('User deleted successfully', 'success');
      fetchUsers();
    } catch (err) {
      showNotification('Failed to delete user: ' + err.message, 'error');
    }
  };

  const handleSaveUser = async (formData) => {
    try {
      setLoading(true);
      if (editingUser) {
        const updateData = { ...formData };
        if (!updateData.password) {
          delete updateData.password;
          delete updateData.password_confirm;
        }
        await api.updateUser(editingUser.id, updateData);
        showNotification('User updated successfully', 'success');
      } else {
        await api.createUser(formData);
        showNotification('User created successfully', 'success');
      }
      setShowUserModal(false);
      fetchUsers();
    } catch (err) {
      const errorMessage =
        err.data?.password_confirm?.[0] ||
        err.data?.username?.[0] ||
        err.data?.email?.[0] ||
        err.message ||
        'Failed to save user';
      showNotification(errorMessage, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleApproveUser = (user) => {
    setApprovingUser(user);
    setShowApprovalModal(true);
  };

  const handleApproveConfirm = async (userId, role) => {
    try {
      setLoading(true);
      await api.updateUser(userId, { role, is_active: true });
      showNotification('User approved and activated successfully', 'success');
      setShowApprovalModal(false);
      fetchPendingUsers();
      fetchUsers();
    } catch (err) {
      showNotification('Failed to approve user: ' + err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleRejectUser = async (userId) => {
    const confirmed = await showConfirm({
      title: 'Reject User Application',
      message:
        'Are you sure you want to reject this application? This will permanently delete the user account.',
      type: 'danger',
      confirmText: 'Reject Application',
      cancelText: 'Cancel',
    });
    if (!confirmed) return;

    try {
      await api.deleteUser(userId);
      showNotification('User application rejected', 'success');
      fetchPendingUsers();
    } catch (err) {
      showNotification('Failed to reject user: ' + err.message, 'error');
    }
  };

  const handlePermissionsRefresh = () => fetchRolesAndPermissions();

  // ── Render ────────────────────────────────────────────────────────

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar activePath="/settings" />

      <NotificationContainer />
      <ConfirmDialog />

      <div className="flex-1 overflow-y-auto" style={{ backgroundColor: '#F8F9FA' }}>
        <div className="p-8">

          {/* Page Title */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center">
              <Settings className="w-8 h-8 mr-3" style={{ color: companyProfile.primary_color }} />
              <div>
                <h1 className="text-3xl font-bold" style={{ color: companyProfile.secondary_color }}>
                  System Settings
                </h1>
                <p className="mt-1" style={{ color: '#7F8C8D' }}>
                  Manage company profile, users, roles, and system permissions
                </p>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="bg-white rounded-xl shadow-sm">
            <div className="flex border-b" style={{ borderColor: '#E5E7EB' }}>
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className="px-6 py-4 font-medium transition-all relative flex items-center"
                    style={{
                      color: activeTab === tab.id ? companyProfile.secondary_color : '#7F8C8D',
                    }}
                  >
                    <Icon className="w-5 h-5 mr-2" />
                    {tab.label}
                    {tab.badge > 0 && (
                      <span
                        className="ml-2 px-2 py-0.5 rounded-full text-xs font-bold text-white"
                        style={{ backgroundColor: '#F59E0B' }}
                      >
                        {tab.badge}
                      </span>
                    )}
                    {activeTab === tab.id && (
                      <div
                        className="absolute bottom-0 left-0 right-0 h-0.5"
                        style={{ backgroundColor: companyProfile.primary_color }}
                      />
                    )}
                  </button>
                );
              })}
            </div>

            {/* Tab Content */}
            <div className="p-6">
              {activeTab === 'company' && (
                <CompanyProfileTab
                  companyProfile={companyProfile}
                  setCompanyProfile={setCompanyProfile}
                  profileChanged={profileChanged}
                  loading={loading}
                  onSave={handleSaveCompanyProfile}
                  onReset={handleResetCompanyProfile}
                />
              )}

              {activeTab === 'pricing' && (
                <GlobalPricingSettingsTab companyProfile={companyProfile} />
              )}

              {activeTab === 'pending' && (
                <PendingUsersTab
                  pendingUsers={pendingUsers}
                  searchQuery={searchQuery}
                  setSearchQuery={setSearchQuery}
                  loading={loading}
                  companyProfile={companyProfile}
                  onApprove={handleApproveUser}
                  onReject={handleRejectUser}
                />
              )}

              {activeTab === 'users' && (
                <UsersTab
                  users={users}
                  searchQuery={searchQuery}
                  setSearchQuery={setSearchQuery}
                  loading={loading}
                  companyProfile={companyProfile}
                  currentUser={user}
                  onAddUser={handleAddUser}
                  onEditUser={handleEditUser}
                  onDeleteUser={handleDeleteUser}
                />
              )}

              {activeTab === 'roles' && (
                <RolesTab
                  roles={roles}
                  permissions={permissions}
                  permissionsList={permissionsList}
                  companyProfile={companyProfile}
                  onPermissionToggle={handlePermissionsRefresh}
                />
              )}
            </div>
          </div>

        </div>
      </div>

      {/* Add/Edit User Modal */}
      <UserManagementModal
        show={showUserModal}
        onClose={() => setShowUserModal(false)}
        onSave={handleSaveUser}
        editingUser={editingUser}
        loading={loading}
        companyProfile={companyProfile}
      />

      {/* User Approval Modal */}
      <UserApprovalModal
        show={showApprovalModal}
        onClose={() => setShowApprovalModal(false)}
        onApprove={handleApproveConfirm}
        user={approvingUser}
        loading={loading}
        companyProfile={companyProfile}
      />
    </div>
  );
}