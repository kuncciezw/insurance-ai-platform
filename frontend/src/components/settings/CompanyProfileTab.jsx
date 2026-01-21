import { Save, Loader2 } from 'lucide-react';

export default function CompanyProfileTab({ 
  companyProfile, 
  setCompanyProfile,
  profileChanged,
  loading,
  onSave,
  onReset 
}) {
  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold" style={{ color: companyProfile.secondary_color }}>
          Company Information
        </h2>
        <div className="flex space-x-3">
          {profileChanged && (
            <button
              onClick={onReset}
              className="px-4 py-2 rounded-lg font-medium transition-colors"
              style={{ backgroundColor: '#F3F4F6', color: '#6B7280' }}
            >
              Reset Changes
            </button>
          )}
          <button
            onClick={onSave}
            disabled={!profileChanged || loading}
            className="px-6 py-2 rounded-lg font-medium transition-colors flex items-center"
            style={{
              backgroundColor: profileChanged && !loading ? companyProfile.primary_color : '#E5E7EB',
              color: 'white',
              opacity: profileChanged && !loading ? 1 : 0.6,
              cursor: profileChanged && !loading ? 'pointer' : 'not-allowed',
            }}
          >
            {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
            Save Changes
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Basic Information */}
        <div className="col-span-2">
          <h3 className="text-lg font-semibold mb-4" style={{ color: companyProfile.secondary_color }}>
            Basic Information
          </h3>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: '#4B5563' }}>
            Company Name *
          </label>
          <input
            type="text"
            value={companyProfile.company_name}
            onChange={(e) => setCompanyProfile({ ...companyProfile, company_name: e.target.value })}
            className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
            style={{ borderColor: '#E0E0E0' }}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: '#4B5563' }}>
            Tagline
          </label>
          <input
            type="text"
            value={companyProfile.company_tagline}
            onChange={(e) => setCompanyProfile({ ...companyProfile, company_tagline: e.target.value })}
            className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
            style={{ borderColor: '#E0E0E0' }}
            placeholder="Admin Portal"
          />
        </div>

        {/* Contact Information */}
        <div className="col-span-2 mt-6">
          <h3 className="text-lg font-semibold mb-4" style={{ color: companyProfile.secondary_color }}>
            Contact Information
          </h3>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: '#4B5563' }}>
            Email
          </label>
          <input
            type="email"
            value={companyProfile.email}
            onChange={(e) => setCompanyProfile({ ...companyProfile, email: e.target.value })}
            className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
            style={{ borderColor: '#E0E0E0' }}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: '#4B5563' }}>
            Phone
          </label>
          <input
            type="tel"
            value={companyProfile.phone}
            onChange={(e) => setCompanyProfile({ ...companyProfile, phone: e.target.value })}
            className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
            style={{ borderColor: '#E0E0E0' }}
          />
        </div>

        <div className="col-span-2">
          <label className="block text-sm font-medium mb-2" style={{ color: '#4B5563' }}>
            Website
          </label>
          <input
            type="url"
            value={companyProfile.website}
            onChange={(e) => setCompanyProfile({ ...companyProfile, website: e.target.value })}
            className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
            style={{ borderColor: '#E0E0E0' }}
            placeholder="https://"
          />
        </div>

        {/* Address */}
        <div className="col-span-2 mt-6">
          <h3 className="text-lg font-semibold mb-4" style={{ color: companyProfile.secondary_color }}>
            Address
          </h3>
        </div>

        <div className="col-span-2">
          <label className="block text-sm font-medium mb-2" style={{ color: '#4B5563' }}>
            Address Line 1
          </label>
          <input
            type="text"
            value={companyProfile.address_line1}
            onChange={(e) => setCompanyProfile({ ...companyProfile, address_line1: e.target.value })}
            className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
            style={{ borderColor: '#E0E0E0' }}
          />
        </div>

        <div className="col-span-2">
          <label className="block text-sm font-medium mb-2" style={{ color: '#4B5563' }}>
            Address Line 2
          </label>
          <input
            type="text"
            value={companyProfile.address_line2}
            onChange={(e) => setCompanyProfile({ ...companyProfile, address_line2: e.target.value })}
            className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
            style={{ borderColor: '#E0E0E0' }}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: '#4B5563' }}>
            City
          </label>
          <input
            type="text"
            value={companyProfile.city}
            onChange={(e) => setCompanyProfile({ ...companyProfile, city: e.target.value })}
            className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
            style={{ borderColor: '#E0E0E0' }}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: '#4B5563' }}>
            State / Province
          </label>
          <input
            type="text"
            value={companyProfile.state}
            onChange={(e) => setCompanyProfile({ ...companyProfile, state: e.target.value })}
            className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
            style={{ borderColor: '#E0E0E0' }}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: '#4B5563' }}>
            Postal Code
          </label>
          <input
            type="text"
            value={companyProfile.postal_code}
            onChange={(e) => setCompanyProfile({ ...companyProfile, postal_code: e.target.value })}
            className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
            style={{ borderColor: '#E0E0E0' }}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: '#4B5563' }}>
            Country
          </label>
          <input
            type="text"
            value={companyProfile.country}
            onChange={(e) => setCompanyProfile({ ...companyProfile, country: e.target.value })}
            className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
            style={{ borderColor: '#E0E0E0' }}
          />
        </div>

        {/* Business Details */}
        <div className="col-span-2 mt-6">
          <h3 className="text-lg font-semibold mb-4" style={{ color: companyProfile.secondary_color }}>
            Business Details
          </h3>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: '#4B5563' }}>
            Tax ID / EIN
          </label>
          <input
            type="text"
            value={companyProfile.tax_id}
            onChange={(e) => setCompanyProfile({ ...companyProfile, tax_id: e.target.value })}
            className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
            style={{ borderColor: '#E0E0E0' }}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: '#4B5563' }}>
            License Number
          </label>
          <input
            type="text"
            value={companyProfile.license_number}
            onChange={(e) => setCompanyProfile({ ...companyProfile, license_number: e.target.value })}
            className="w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
            style={{ borderColor: '#E0E0E0' }}
          />
        </div>

        {/* Branding */}
        <div className="col-span-2 mt-6">
          <h3 className="text-lg font-semibold mb-4" style={{ color: companyProfile.secondary_color }}>
            Branding Colors
          </h3>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: '#4B5563' }}>
            Primary Color
          </label>
          <div className="flex items-center space-x-3">
            <input
              type="color"
              value={companyProfile.primary_color}
              onChange={(e) => setCompanyProfile({ ...companyProfile, primary_color: e.target.value })}
              className="w-12 h-10 rounded border cursor-pointer"
              style={{ borderColor: '#E0E0E0' }}
            />
            <input
              type="text"
              value={companyProfile.primary_color}
              onChange={(e) => setCompanyProfile({ ...companyProfile, primary_color: e.target.value })}
              className="flex-1 px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
              style={{ borderColor: '#E0E0E0' }}
              placeholder="#FF6B4A"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: '#4B5563' }}>
            Secondary Color
          </label>
          <div className="flex items-center space-x-3">
            <input
              type="color"
              value={companyProfile.secondary_color}
              onChange={(e) => setCompanyProfile({ ...companyProfile, secondary_color: e.target.value })}
              className="w-12 h-10 rounded border cursor-pointer"
              style={{ borderColor: '#E0E0E0' }}
            />
            <input
              type="text"
              value={companyProfile.secondary_color}
              onChange={(e) => setCompanyProfile({ ...companyProfile, secondary_color: e.target.value })}
              className="flex-1 px-4 py-2 rounded-lg border focus:outline-none focus:ring-2"
              style={{ borderColor: '#E0E0E0' }}
              placeholder="#2C3E50"
            />
          </div>
        </div>
      </div>
    </div>
  );
}