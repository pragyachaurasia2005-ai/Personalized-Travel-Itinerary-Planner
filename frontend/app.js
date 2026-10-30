const { useState, useEffect, useMemo } = React;

// Category Badge Helper
const getCategoryBadge = (category) => {
  switch (category) {
    case 'attraction':
      return { label: 'Attraction', icon: '🏛️', bg: 'bg-indigo-50 text-indigo-700 border-indigo-200' };
    case 'dining':
      return { label: 'Dining', icon: '🍽️', bg: 'bg-amber-50 text-amber-700 border-amber-200' };
    case 'accommodation':
      return { label: 'Stay', icon: '🏨', bg: 'bg-emerald-50 text-emerald-700 border-emerald-200' };
    case 'transportation':
      return { label: 'Transit', icon: '🚆', bg: 'bg-blue-50 text-blue-700 border-blue-200' };
    case 'experience':
      return { label: 'Experience', icon: '🌿', bg: 'bg-teal-50 text-teal-700 border-teal-200' };
    case 'relaxation':
      return { label: 'Relaxation', icon: '🧘', bg: 'bg-purple-50 text-purple-700 border-purple-200' };
    default:
      return { label: 'Activity', icon: '📍', bg: 'bg-slate-50 text-slate-700 border-slate-200' };
  }
};

const CURRENCIES = [
  { code: 'USD', symbol: '$', name: 'USD ($) - US Dollar' },
  { code: 'INR', symbol: '₹', name: 'INR (₹) - Indian Rupee' },
  { code: 'EUR', symbol: '€', name: 'EUR (€) - Euro' },
  { code: 'GBP', symbol: '£', name: 'GBP (£) - British Pound' },
  { code: 'JPY', symbol: '¥', name: 'JPY (¥) - Japanese Yen' },
  { code: 'CAD', symbol: 'C$', name: 'CAD (C$) - Canadian Dollar' },
  { code: 'AUD', symbol: 'A$', name: 'AUD (A$) - Australian Dollar' },
];

function App() {
  const [activeTab, setActiveTab] = useState('builder'); // 'builder' | 'itinerary' | 'saved'
  const [health, setHealth] = useState(null);
  const [presets, setPresets] = useState([]);
  const [currentTrip, setCurrentTrip] = useState(null);
  const [savedTrips, setSavedTrips] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState('Consulting AI travel architects...');
  const [selectedDayIdx, setSelectedDayIdx] = useState(0);
  const [toast, setToast] = useState(null);

  // Modals
  const [regenDayModal, setRegenDayModal] = useState({ open: false, dayNumber: 1, instructions: '' });
  const [editingActivity, setEditingActivity] = useState(null);
  const [editingTitle, setEditingTitle] = useState(false);
  const [newTitleText, setNewTitleText] = useState('');
  const [storageHelpModal, setStorageHelpModal] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    destination: 'Tokyo, Japan',
    start_date: new Date(Date.now() + 86400000 * 7).toISOString().split('T')[0],
    end_date: new Date(Date.now() + 86400000 * 10).toISOString().split('T')[0],
    traveler_type: 'solo',
    group_size: 1,
    budget_tier: 'budget',
    currency: 'USD',
    custom_budget: '',
    pacing: 'packed',
    accommodation_pref: 'hostel',
    interests: ['food', 'sightseeing', 'culture', 'photography'],
    dietary_restrictions: 'Local street food & ramen enthusiast',
    special_requests: 'Solo-friendly dining, zero-backtracking routes, subway pass efficiency.'
  });

  // Calculate Duration
  const durationDays = useMemo(() => {
    try {
      const s = new Date(formData.start_date);
      const e = new Date(formData.end_date);
      const diff = Math.round((e - s) / (1000 * 60 * 60 * 24)) + 1;
      return diff > 0 ? diff : 1;
    } catch {
      return 1;
    }
  }, [formData.start_date, formData.end_date]);

  // Current Currency Symbol Helper
  const currentSymbol = useMemo(() => {
    if (currentTrip && currentTrip.currency_symbol) return currentTrip.currency_symbol;
    const found = CURRENCIES.find(c => c.code === formData.currency);
    return found ? found.symbol : '$';
  }, [currentTrip, formData.currency]);

  // Load Initial Data
  useEffect(() => {
    fetchHealth();
    fetchPresets();
    fetchSavedTrips();
  }, []);

  // Refresh Lucide Icons after render
  useEffect(() => {
    if (window.lucide) {
      window.lucide.createIcons();
    }
  });

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const fetchHealth = async () => {
    try {
      const res = await fetch('/api/health');
      if (res.ok) setHealth(await res.json());
    } catch (e) {
      console.warn('Health check unreachable:', e);
    }
  };

  const fetchPresets = async () => {
    try {
      const res = await fetch('/api/presets');
      if (res.ok) setPresets(await res.json());
    } catch (e) {
      console.warn('Presets unreachable:', e);
    }
  };

  const fetchSavedTrips = async () => {
    try {
      const res = await fetch('/api/trips');
      if (res.ok) setSavedTrips(await res.json());
    } catch (e) {
      console.warn('Saved trips fetch error:', e);
    }
  };

  // Preset Scenario Click
  const handleApplyScenario = (preset) => {
    const prefs = preset.preferences;
    setFormData({
      destination: prefs.destination,
      start_date: prefs.start_date,
      end_date: prefs.end_date,
      traveler_type: prefs.traveler_type,
      group_size: prefs.group_size || 1,
      budget_tier: prefs.budget_tier,
      currency: formData.currency, // preserve selected currency
      custom_budget: prefs.custom_budget || '',
      pacing: prefs.pacing,
      accommodation_pref: prefs.accommodation_pref,
      interests: prefs.interests || [],
      dietary_restrictions: prefs.dietary_restrictions || '',
      special_requests: prefs.special_requests || ''
    });
    showToast(`Loaded ${preset.badge} settings into builder!`, 'info');
    setActiveTab('builder');
  };

  // Quick Instant Generate Scenario
  const handleQuickRunScenario = async (scenarioKey) => {
    setLoading(true);
    setLoadingMsg(`Generating ${scenarioKey.replace('_', ' ')} with ${formData.currency} currency...`);
    try {
      const res = await fetch(`/api/trips/quick-scenario/${scenarioKey}?currency=${encodeURIComponent(formData.currency)}`, { method: 'POST' });
      if (!res.ok) throw new Error('Failed to generate scenario');
      const trip = await res.json();
      setCurrentTrip(trip);
      setSelectedDayIdx(0);
      setActiveTab('itinerary');
      fetchSavedTrips();
      fetchHealth();
      showToast('Scenario generated and saved!', 'success');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  // Generate Itinerary from Form
  const handleGenerateTrip = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setLoadingMsg(`Architecting personalized ${durationDays}-day itinerary for ${formData.destination} in ${formData.currency}...`);
    try {
      const payload = {
        ...formData,
        group_size: parseInt(formData.group_size) || 1,
        custom_budget: formData.custom_budget ? parseFloat(formData.custom_budget) : null
      };
      const res = await fetch('/api/trips/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error('Trip generation failed');
      const data = await res.json();
      setCurrentTrip(data);
      setSelectedDayIdx(0);
      setActiveTab('itinerary');
      fetchHealth();
      showToast('Itinerary successfully generated!', 'success');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  // Save Current Trip
  const handleSaveTrip = async () => {
    if (!currentTrip) return;
    try {
      const res = await fetch('/api/trips', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(currentTrip)
      });
      if (res.ok) {
        const saved = await res.json();
        setCurrentTrip(saved);
        fetchSavedTrips();
        fetchHealth();
        const mode = health?.storage?.supabase_connected ? 'Supabase Cloud' : 'Local SQLite Storage';
        showToast(`Trip saved to ${mode}!`, 'success');
      }
    } catch (err) {
      showToast('Failed to save trip', 'error');
    }
  };

  // Update Trip Title
  const handleSaveTitle = async () => {
    if (!currentTrip || !newTitleText.trim()) return;
    try {
      const res = await fetch(`/api/trips/${currentTrip.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTitleText.trim() })
      });
      if (res.ok) {
        const updated = await res.json();
        setCurrentTrip(updated);
        setEditingTitle(false);
        fetchSavedTrips();
        showToast('Trip title updated!', 'success');
      }
    } catch (err) {
      showToast('Failed to update title', 'error');
    }
  };

  // Delete Trip
  const handleDeleteTrip = async (tripId) => {
    if (!confirm('Are you sure you want to delete this trip?')) return;
    try {
      const res = await fetch(`/api/trips/${tripId}`, { method: 'DELETE' });
      if (res.ok) {
        if (currentTrip && currentTrip.id === tripId) {
          setCurrentTrip(null);
          setActiveTab('builder');
        }
        fetchSavedTrips();
        showToast('Trip deleted from storage', 'info');
      }
    } catch (err) {
      showToast('Failed to delete trip', 'error');
    }
  };

  // AI Regenerate Single Day
  const handleRegenerateDaySubmit = async () => {
    if (!currentTrip) return;
    setLoading(true);
    setLoadingMsg(`AI is reconstructing Day ${regenDayModal.dayNumber}...`);
    try {
      // Ensure trip is saved first
      await fetch('/api/trips', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(currentTrip)
      });

      const res = await fetch('/api/trips/regenerate-day', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trip_id: currentTrip.id,
          day_number: regenDayModal.dayNumber,
          custom_instructions: regenDayModal.instructions || 'Refine and improve activities'
        })
      });
      if (!res.ok) throw new Error('Regeneration failed');
      const updated = await res.json();
      setCurrentTrip(updated);
      setRegenDayModal({ open: false, dayNumber: 1, instructions: '' });
      fetchSavedTrips();
      showToast(`Day ${regenDayModal.dayNumber} successfully regenerated!`, 'success');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  // Toggle Interest Tag
  const toggleInterest = (tag) => {
    setFormData(prev => {
      const exists = prev.interests.includes(tag);
      return {
        ...prev,
        interests: exists ? prev.interests.filter(i => i !== tag) : [...prev.interests, tag]
      };
    });
  };

  // Quick Destination Pick
  const pickDestination = (city) => {
    setFormData(prev => ({ ...prev, destination: city }));
  };

  return (
    <div className="flex flex-col min-h-screen">
      {/* Toast Notification */}
      {toast && (
        <div className={`fixed bottom-5 right-5 z-50 flex items-center gap-3 px-5 py-3 rounded-xl shadow-xl text-white font-medium text-sm transition-all transform animate-bounce ${
          toast.type === 'error' ? 'bg-rose-600' : toast.type === 'info' ? 'bg-sky-600' : 'bg-emerald-600'
        }`}>
          <span>{toast.type === 'error' ? '⚠️' : '✅'}</span>
          <span>{toast.message}</span>
          <button onClick={() => setToast(null)} className="ml-2 hover:opacity-75 font-bold">✕</button>
        </div>
      )}

      {/* Global Navigation Header */}
      <header className="sticky top-0 z-40 glass-nav border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setActiveTab('builder')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-teal-500 flex items-center justify-center text-white shadow-md shadow-brand-500/20">
              <span className="text-xl">✈️</span>
            </div>
            <div>
              <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-slate-900 via-brand-800 to-teal-700 bg-clip-text text-transparent">
                TravelCraft AI
              </span>
              <span className="block text-[10px] text-slate-500 uppercase tracking-widest font-bold -mt-1">
                Itinerary Architect
              </span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center gap-1 sm:gap-2">
            <button
              onClick={() => setActiveTab('builder')}
              className={`px-3 py-1.5 sm:px-4 sm:py-2 rounded-lg font-semibold text-sm transition-all flex items-center gap-2 ${
                activeTab === 'builder'
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <span>🧭</span>
              <span className="hidden sm:inline">Smart Builder</span>
            </button>

            {currentTrip && (
              <button
                onClick={() => setActiveTab('itinerary')}
                className={`px-3 py-1.5 sm:px-4 sm:py-2 rounded-lg font-semibold text-sm transition-all flex items-center gap-2 ${
                  activeTab === 'itinerary'
                    ? 'bg-brand-600 text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <span>🗺️</span>
                <span className="hidden sm:inline">Active Trip</span>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              </button>
            )}

            <button
              onClick={() => { setActiveTab('saved'); fetchSavedTrips(); }}
              className={`px-3 py-1.5 sm:px-4 sm:py-2 rounded-lg font-semibold text-sm transition-all flex items-center gap-2 ${
                activeTab === 'saved'
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <span>📂</span>
              <span className="hidden sm:inline">Saved Trips</span>
              <span className="px-1.5 py-0.5 rounded-full text-[11px] bg-slate-200 text-slate-700 font-bold">
                {savedTrips.length}
              </span>
            </button>
          </nav>

          {/* Truthful Status Indicator */}
          <div className="hidden lg:flex items-center gap-2">
            {/* AI Status */}
            <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-medium ${
              health?.ai_engine?.gemini_connected
                ? 'bg-indigo-50 border-indigo-200 text-indigo-800'
                : 'bg-slate-100 border-slate-200 text-slate-700'
            }`}>
              <span className={`w-2 h-2 rounded-full ${health?.ai_engine?.gemini_connected ? 'bg-indigo-600 animate-pulse' : 'bg-slate-400'}`}></span>
              <span>AI: <strong>{health?.ai_engine?.gemini_connected ? 'Google Gemini 2.5' : 'Adaptive Local Engine'}</strong></span>
            </div>

            {/* Storage Status */}
            <button
              onClick={() => setStorageHelpModal(true)}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-medium transition cursor-pointer hover:opacity-80 ${
                health?.storage?.supabase_connected
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                  : 'bg-amber-50 border-amber-200 text-amber-800'
              }`}
              title="Click for storage connection details"
            >
              <span className={`w-2 h-2 rounded-full ${health?.storage?.supabase_connected ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`}></span>
              <span>Storage: <strong>{health?.storage?.supabase_connected ? 'Supabase Cloud' : 'Local SQLite'}</strong></span>
              <span className="text-[10px] text-slate-400">ℹ️</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        
        {/* Loading Overlay */}
        {loading && (
          <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full text-center border border-slate-100 animate-pulse-slow">
              <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-tr from-brand-600 to-teal-500 flex items-center justify-center text-white text-3xl shadow-lg shadow-brand-500/30">
                ✈️
              </div>
              <h3 className="text-xl font-bold text-slate-800 mb-2">Architecting Itinerary</h3>
              <p className="text-sm text-slate-600 mb-4">{loadingMsg}</p>
              <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                <div className="bg-gradient-to-r from-brand-500 to-teal-500 h-2 rounded-full w-2/3 animate-pulse"></div>
              </div>
              <div className="mt-4 text-[11px] text-slate-400">Verifying non-repetitive routes • Calculating exact currency budget • Curating dining</div>
            </div>
          </div>
        )}

        {/* TAB 1: SMART BUILDER */}
        {activeTab === 'builder' && (
          <div className="space-y-8">
            {/* Hero & Preset Scenarios Banner */}
            <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-900 via-brand-950 to-slate-900 text-white p-6 sm:p-10 shadow-2xl">
              <div className="relative z-10 max-w-3xl">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/20 text-brand-300 border border-brand-500/30 text-xs font-semibold uppercase tracking-wider mb-3">
                  <span>✨</span> Next-Gen Generative Travel Automation
                </div>
                <h1 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight text-white mb-3">
                  Tailored journeys, <span className="bg-gradient-to-r from-brand-400 to-teal-300 bg-clip-text text-transparent">zero planning friction.</span>
                </h1>
                <p className="text-slate-300 text-sm sm:text-base leading-relaxed mb-6">
                  Intelligent day-by-day scheduling for solo explorers, romantic couples, and multi-day group adventures. Built with React, FastAPI, Supabase, and Gemini AI.
                </p>

                {/* Scenarios Quick Launcher Bar */}
                <div className="pt-2">
                  <div className="text-xs uppercase tracking-wider font-bold text-brand-300 mb-3 flex items-center gap-2">
                    <span>⚡</span> <span>Explore 3 Core Persona Scenarios:</span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {presets.map(p => (
                      <div 
                        key={p.id}
                        className="bg-white/10 hover:bg-white/15 border border-white/10 hover:border-white/25 rounded-2xl p-4 transition-all flex flex-col justify-between group cursor-pointer"
                        onClick={() => handleApplyScenario(p)}
                      >
                        <div>
                          <div className="text-xs font-bold text-teal-300 mb-1">{p.badge}</div>
                          <div className="font-bold text-sm text-white group-hover:text-brand-300 transition-colors">{p.title}</div>
                          <p className="text-[12px] text-slate-300 line-clamp-2 mt-1 leading-snug">{p.tagline}</p>
                        </div>
                        <div className="mt-4 pt-3 border-t border-white/10 flex items-center justify-between">
                          <button
                            type="button"
                            onClick={(e) => { e.stopPropagation(); handleApplyScenario(p); }}
                            className="text-xs text-brand-200 hover:text-white font-medium"
                          >
                            Load Template →
                          </button>
                          <button
                            type="button"
                            onClick={(e) => { e.stopPropagation(); handleQuickRunScenario(p.id); }}
                            className="text-xs px-2.5 py-1 rounded-lg bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold transition-all shadow-sm"
                          >
                            Instant Run ⚡
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Smart Trip Builder Form */}
            <form onSubmit={handleGenerateTrip} className="glass-card rounded-3xl p-6 sm:p-10 shadow-xl border border-slate-200/80 space-y-8">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-6 border-b border-slate-200 gap-4">
                <div>
                  <h2 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
                    <span>⚙️</span> Trip Parameter Studio
                  </h2>
                  <p className="text-sm text-slate-500 mt-0.5">Customize constraints, currency, pacing, and preferences for AI optimization</p>
                </div>
                <div className="flex items-center gap-3">
                  {/* Currency Selector */}
                  <div className="flex items-center gap-2">
                    <label className="text-xs font-bold uppercase tracking-wider text-slate-600">Currency:</label>
                    <select
                      value={formData.currency}
                      onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                      className="px-3 py-1.5 rounded-xl border border-slate-300 bg-white text-xs font-bold text-slate-800 shadow-sm focus:ring-2 focus:ring-brand-500 outline-none"
                    >
                      {CURRENCIES.map(curr => (
                        <option key={curr.code} value={curr.code}>{curr.name}</option>
                      ))}
                    </select>
                  </div>

                  <span className="text-xs font-semibold px-3 py-1.5 bg-brand-50 text-brand-700 rounded-full border border-brand-200">
                    Duration: {durationDays} {durationDays === 1 ? 'Day' : 'Days'}
                  </span>
                </div>
              </div>

              {/* Grid 1: Destination & Dates */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="md:col-span-1 space-y-2">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                    Destination City or Region
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.destination}
                    onChange={(e) => setFormData({ ...formData, destination: e.target.value })}
                    placeholder="e.g. Tokyo, Paris, Amalfi Coast, Banff..."
                    className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition font-medium text-slate-800"
                  />
                  {/* Quick City Chips */}
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {['Tokyo', 'Amalfi Coast', 'Banff', 'Kyoto', 'Paris', 'New York', 'Bali', 'Goa'].map(city => (
                      <button
                        type="button"
                        key={city}
                        onClick={() => pickDestination(city)}
                        className="text-[11px] px-2 py-0.5 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-600 font-medium transition"
                      >
                        {city}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                    Start Date
                  </label>
                  <input
                    type="date"
                    required
                    value={formData.start_date}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition font-medium text-slate-800"
                  />
                </div>

                <div className="space-y-2">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                    End Date
                  </label>
                  <input
                    type="date"
                    required
                    value={formData.end_date}
                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition font-medium text-slate-800"
                  />
                </div>
              </div>

              {/* Grid 2: Traveler Type & Group Size */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6 pt-2">
                <div className="space-y-2">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                    Traveler Archetype
                  </label>
                  <select
                    value={formData.traveler_type}
                    onChange={(e) => {
                      const type = e.target.value;
                      setFormData(prev => ({
                        ...prev,
                        traveler_type: type,
                        group_size: type === 'solo' ? 1 : type === 'couple' ? 2 : prev.group_size < 3 ? 4 : prev.group_size
                      }));
                    }}
                    className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition font-medium text-slate-800 bg-white"
                  >
                    <option value="solo">👤 Solo Traveler (Efficiency & Walkability)</option>
                    <option value="couple">💑 Romantic Couple (Scenic & Curated)</option>
                    <option value="group">👥 Small Group (Adventure & Logistics)</option>
                    <option value="family">👨‍👩‍👧‍👦 Family Vacation (All-ages Friendly)</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                    Group Size
                  </label>
                  <div className="flex items-center">
                    <input
                      type="number"
                      min="1"
                      max="30"
                      value={formData.group_size}
                      onChange={(e) => setFormData({ ...formData, group_size: Math.max(1, parseInt(e.target.value) || 1) })}
                      className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition font-medium text-slate-800"
                    />
                    <span className="ml-3 text-xs text-slate-500 font-semibold whitespace-nowrap">
                      {formData.group_size === 1 ? 'Person' : 'People'}
                    </span>
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                    Budget Tier
                  </label>
                  <select
                    value={formData.budget_tier}
                    onChange={(e) => setFormData({ ...formData, budget_tier: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition font-medium text-slate-800 bg-white"
                  >
                    <option value="budget">💰 Budget (Hostels, street food, transit)</option>
                    <option value="moderate">💰💰 Moderate (Boutique, mid-tier dining)</option>
                    <option value="luxury">💎 Luxury (Fine dining, private transfers)</option>
                    <option value="custom">⚙️ Custom Budget Limit</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                    Daily Pacing
                  </label>
                  <select
                    value={formData.pacing}
                    onChange={(e) => setFormData({ ...formData, pacing: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition font-medium text-slate-800 bg-white"
                  >
                    <option value="relaxed">🧘 Relaxed (2 activities/day, slow mornings)</option>
                    <option value="moderate">⚖️ Balanced (3 activities/day, coffee breaks)</option>
                    <option value="packed">⚡ Packed (4 activities/day, see everything)</option>
                  </select>
                </div>
              </div>

              {/* Grid 3: Accommodation Style & Interests */}
              <div className="space-y-4 pt-2">
                <div className="flex items-center justify-between">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                    Primary Interests & Travel Vibes (Select all that apply)
                  </label>
                  <span className="text-xs text-slate-400 font-medium">Selected: {formData.interests.length}</span>
                </div>

                <div className="flex flex-wrap gap-2">
                  {[
                    { id: 'food', label: 'Food & Culinary', icon: '🍜' },
                    { id: 'sightseeing', label: 'Iconic Sights', icon: '🏛️' },
                    { id: 'culture', label: 'Art & Heritage', icon: '🎨' },
                    { id: 'adventure', label: 'Hikes & Adventure', icon: '🧗' },
                    { id: 'romantic', label: 'Romantic & Sunset', icon: '🌅' },
                    { id: 'nature', label: 'Nature & Parks', icon: '🌲' },
                    { id: 'relaxation', label: 'Spa & Wellness', icon: '💆' },
                    { id: 'photography', label: 'Photo Spots', icon: '📸' },
                    { id: 'nightlife', label: 'Bars & Nightlife', icon: '🌃' },
                    { id: 'shopping', label: 'Artisan & Shopping', icon: '🛍️' }
                  ].map(tag => {
                    const selected = formData.interests.includes(tag.id);
                    return (
                      <button
                        type="button"
                        key={tag.id}
                        onClick={() => toggleInterest(tag.id)}
                        className={`px-3 py-2 rounded-xl text-xs font-semibold transition flex items-center gap-1.5 border ${
                          selected
                            ? 'bg-brand-600 text-white border-brand-600 shadow-sm shadow-brand-500/20'
                            : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                        }`}
                      >
                        <span>{tag.icon}</span>
                        <span>{tag.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Special Requests & Dietary */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
                <div className="space-y-2">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                    Dietary Restrictions / Food Preferences
                  </label>
                  <input
                    type="text"
                    value={formData.dietary_restrictions}
                    onChange={(e) => setFormData({ ...formData, dietary_restrictions: e.target.value })}
                    placeholder="e.g. Vegetarian, Pescatarian, Halal, Gluten-free, none"
                    className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition font-medium text-slate-800"
                  />
                </div>

                <div className="space-y-2">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                    Special AI Instructions / Desires
                  </label>
                  <input
                    type="text"
                    value={formData.special_requests}
                    onChange={(e) => setFormData({ ...formData, special_requests: e.target.value })}
                    placeholder="e.g. Avoid tourist traps, include sunset views, minimize walking..."
                    className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition font-medium text-slate-800"
                  />
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-4 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-slate-200">
                <div className="text-xs text-slate-500">
                  ⚡ Generates {durationDays} unique, non-repeating days in <strong>{formData.currency}</strong> ({currentSymbol}).
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full sm:w-auto px-8 py-4 rounded-xl bg-gradient-to-r from-brand-600 via-brand-700 to-teal-600 hover:from-brand-500 hover:to-teal-500 text-white font-extrabold text-base shadow-xl shadow-brand-600/25 transition-all transform hover:-translate-y-0.5 flex items-center justify-center gap-3"
                >
                  <span>✨</span>
                  <span>Generate Personalized Itinerary</span>
                </button>
              </div>
            </form>
          </div>
        )}

        {/* TAB 2: ACTIVE ITINERARY VIEWER */}
        {activeTab === 'itinerary' && currentTrip && (
          <div className="space-y-8">
            {/* Header Title Card */}
            <div className="glass-card rounded-3xl p-6 sm:p-8 shadow-xl border border-slate-200 space-y-6">
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                <div>
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-brand-100 text-brand-800">
                      {currentTrip.traveler_type} Trip ({currentTrip.group_size} {currentTrip.group_size === 1 ? 'person' : 'people'})
                    </span>
                    <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-slate-100 text-slate-700">
                      {currentTrip.budget_tier} Tier
                    </span>
                    <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-100 text-emerald-800">
                      {currentTrip.duration_days} Days ({currentTrip.start_date} → {currentTrip.end_date})
                    </span>

                    {/* AI Engine Source Badge */}
                    <span className={`px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1.5 border ${
                      currentTrip.generation_source === 'gemini'
                        ? 'bg-indigo-100 border-indigo-300 text-indigo-900'
                        : 'bg-amber-100 border-amber-300 text-amber-900'
                    }`}>
                      <span>{currentTrip.generation_source === 'gemini' ? '✨' : '⚡'}</span>
                      <span>{currentTrip.generation_source === 'gemini' ? `Google Gemini (${currentTrip.generation_model})` : 'Adaptive Local Engine'}</span>
                    </span>
                  </div>

                  {/* Trip Title with inline edit */}
                  {editingTitle ? (
                    <div className="flex items-center gap-2 mt-2">
                      <input
                        type="text"
                        value={newTitleText}
                        onChange={(e) => setNewTitleText(e.target.value)}
                        className="px-3 py-1.5 border border-brand-500 rounded-xl text-xl font-black text-slate-900 w-full max-w-xl outline-none"
                      />
                      <button onClick={handleSaveTitle} className="px-3 py-1.5 bg-brand-600 text-white rounded-lg text-xs font-bold">Save</button>
                      <button onClick={() => setEditingTitle(false)} className="px-3 py-1.5 bg-slate-200 text-slate-700 rounded-lg text-xs font-bold">Cancel</button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-3">
                      <h1 className="text-2xl sm:text-4xl font-black text-slate-900 tracking-tight">
                        {currentTrip.title}
                      </h1>
                      <button
                        onClick={() => { setNewTitleText(currentTrip.title); setEditingTitle(true); }}
                        className="text-xs text-slate-400 hover:text-brand-600 font-semibold no-print"
                        title="Edit Trip Title"
                      >
                        ✏️
                      </button>
                    </div>
                  )}

                  <p className="text-sm text-slate-600 mt-2 max-w-3xl leading-relaxed">
                    💡 <strong>AI Rationale:</strong> {currentTrip.ai_rationale}
                  </p>
                </div>

                {/* Quick Action Buttons */}
                <div className="flex flex-wrap items-center gap-2">
                  <button
                    onClick={handleSaveTrip}
                    className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold shadow-md transition flex items-center gap-1.5"
                  >
                    <span>💾</span> <span>Save to Storage</span>
                  </button>
                  <a
                    href={`/api/trips/${currentTrip.id}/export/markdown`}
                    target="_blank"
                    className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold border border-slate-200 transition flex items-center gap-1.5"
                  >
                    <span>📥</span> <span>Export Markdown</span>
                  </a>
                  <button
                    onClick={() => window.print()}
                    className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold border border-slate-200 transition flex items-center gap-1.5 no-print"
                  >
                    <span>🖨️</span> <span>Print / PDF</span>
                  </button>
                </div>
              </div>

              {/* Persona Context Highlight Banner */}
              <div className="p-4 rounded-2xl bg-gradient-to-r from-brand-50 via-teal-50 to-blue-50 border border-brand-200/70 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">
                    {currentTrip.traveler_type === 'solo' ? '👤' : currentTrip.traveler_type === 'couple' ? '💑' : '👥'}
                  </span>
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-brand-900">
                      {currentTrip.traveler_type === 'solo' && 'Scenario 1: Solo Traveler Efficiency Mode'}
                      {currentTrip.traveler_type === 'couple' && 'Scenario 2: Romantic Couples Mode'}
                      {currentTrip.traveler_type === 'group' && 'Scenario 3: Small Group Logistics Coordination Mode'}
                      {currentTrip.traveler_type === 'family' && 'Family Pacing Mode'}
                    </h4>
                    <p className="text-xs text-slate-600 mt-0.5">
                      {currentTrip.traveler_type === 'solo' && 'Geographic clusters minimize backtracking; single-diner seating verified; safe transit paths.'}
                      {currentTrip.traveler_type === 'couple' && 'Atmospheric sunset viewpoints, boutique accommodations, and unhurried morning transitions.'}
                      {currentTrip.traveler_type === 'group' && 'Parks & vehicle passes calculated across group; table reservation windows; shared cabin cost savings.'}
                      {currentTrip.traveler_type === 'family' && 'Kid-friendly pauses, rest breaks, and diverse dining selections.'}
                    </p>
                  </div>
                </div>

                <div className="text-right sm:border-l sm:border-brand-200 sm:pl-4">
                  <div className="text-[11px] uppercase tracking-wider text-slate-500 font-bold">Estimated Total ({currentTrip.currency || 'USD'})</div>
                  <div className="text-xl font-black text-brand-900">
                    {currentTrip.currency_symbol || '$'} {currentTrip.cost_breakdown.total.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>
                  <div className="text-[11px] text-slate-500 font-medium">
                    ({currentTrip.currency_symbol || '$'} {currentTrip.cost_breakdown.per_person.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} / person)
                  </div>
                </div>
              </div>

              {/* Budget Visualizer Bar */}
              <div className="space-y-2 pt-2">
                <div className="flex items-center justify-between text-xs font-bold text-slate-700">
                  <span>Expense Allocation Breakdown ({currentTrip.currency || 'USD'})</span>
                  <span className="text-slate-400 font-normal">Real-time estimate for {currentTrip.group_size} travelers</span>
                </div>
                <div className="h-3 w-full bg-slate-100 rounded-full flex overflow-hidden">
                  <div style={{ width: '40%' }} className="bg-emerald-500" title={`Stay: ${currentTrip.currency_symbol}${currentTrip.cost_breakdown.stay}`}></div>
                  <div style={{ width: '30%' }} className="bg-amber-500" title={`Dining: ${currentTrip.currency_symbol}${currentTrip.cost_breakdown.dining}`}></div>
                  <div style={{ width: '18%' }} className="bg-indigo-500" title={`Attractions: ${currentTrip.currency_symbol}${currentTrip.cost_breakdown.attractions}`}></div>
                  <div style={{ width: '12%' }} className="bg-blue-500" title={`Transit: ${currentTrip.currency_symbol}${currentTrip.cost_breakdown.transport}`}></div>
                </div>
                <div className="flex flex-wrap gap-4 text-xs pt-1 text-slate-600 font-medium">
                  <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Stay ({currentTrip.currency_symbol}{currentTrip.cost_breakdown.stay.toLocaleString()})</span>
                  <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Dining ({currentTrip.currency_symbol}{currentTrip.cost_breakdown.dining.toLocaleString()})</span>
                  <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-indigo-500"></span> Sights ({currentTrip.currency_symbol}{currentTrip.cost_breakdown.attractions.toLocaleString()})</span>
                  <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span> Transit ({currentTrip.currency_symbol}{currentTrip.cost_breakdown.transport.toLocaleString()})</span>
                </div>
              </div>
            </div>

            {/* Day Selector Pills */}
            <div className="flex items-center gap-2 overflow-x-auto pb-2 no-print">
              {currentTrip.days.map((day, idx) => (
                <button
                  key={day.day_number}
                  onClick={() => setSelectedDayIdx(idx)}
                  className={`px-4 py-3 rounded-2xl font-bold text-xs whitespace-nowrap transition-all flex flex-col items-start ${
                    selectedDayIdx === idx
                      ? 'bg-slate-900 text-white shadow-lg shadow-slate-900/20'
                      : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200'
                  }`}
                >
                  <span className="text-[10px] uppercase tracking-wider opacity-75">Day {day.day_number}</span>
                  <span className="text-xs truncate max-w-[140px]">{day.theme}</span>
                </button>
              ))}
            </div>

            {/* Selected Day Details Card */}
            {currentTrip.days[selectedDayIdx] && (() => {
              const day = currentTrip.days[selectedDayIdx];
              return (
                <div className="glass-card rounded-3xl p-6 sm:p-8 shadow-xl border border-slate-200 space-y-6">
                  {/* Day Header */}
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-6 border-b border-slate-200 gap-4">
                    <div>
                      <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-brand-700 mb-1">
                        <span>Day {day.day_number}</span>
                        {day.date_str && <span>• {day.date_str}</span>}
                      </div>
                      <h3 className="text-xl sm:text-2xl font-black text-slate-900">{day.theme}</h3>
                      <p className="text-xs text-slate-600 mt-1 max-w-2xl">{day.summary}</p>
                    </div>

                    {/* AI Day Regenerator Button */}
                    <button
                      onClick={() => setRegenDayModal({ open: true, dayNumber: day.day_number, instructions: '' })}
                      className="px-4 py-2.5 rounded-xl bg-teal-50 hover:bg-teal-100 text-teal-800 border border-teal-200 text-xs font-bold transition flex items-center gap-2 shadow-sm"
                    >
                      <span>🔄</span>
                      <span>AI Re-roll Day {day.day_number}</span>
                    </button>
                  </div>

                  {/* Stay & Logistics Quick Ribbons */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {day.accommodation_suggestion && (
                      <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 flex items-start gap-3">
                        <span className="text-lg">🏨</span>
                        <div>
                          <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Stay Recommendation</div>
                          <div className="text-xs font-bold text-slate-800">{day.accommodation_suggestion}</div>
                        </div>
                      </div>
                    )}
                    {day.travel_logistics_note && (
                      <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 flex items-start gap-3">
                        <span className="text-lg">🚆</span>
                        <div>
                          <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Transit & Route Note</div>
                          <div className="text-xs text-slate-700">{day.travel_logistics_note}</div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Activity List Timeline */}
                  <div className="space-y-4 pt-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">Scheduled Activities & Timelines</h4>
                    <div className="space-y-4">
                      {day.activities.map((act) => {
                        const badge = getCategoryBadge(act.category);
                        return (
                          <div key={act.id} className="p-5 rounded-2xl bg-white border border-slate-200/90 shadow-sm hover:shadow-md transition-all flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
                            <div className="space-y-2 flex-1">
                              <div className="flex flex-wrap items-center gap-2">
                                <span className={`px-2.5 py-0.5 rounded-md text-[11px] font-bold border ${badge.bg} flex items-center gap-1`}>
                                  <span>{badge.icon}</span> <span>{badge.label}</span>
                                </span>
                                <span className="text-xs font-semibold text-slate-500">
                                  ⏰ {act.time_str}
                                </span>
                                <span className="text-xs font-bold text-slate-800">
                                  • 📍 {act.location_name}
                                </span>
                              </div>

                              <h5 className="text-base font-bold text-slate-900">{act.title}</h5>
                              <p className="text-xs text-slate-600 leading-relaxed">{act.description}</p>

                              {/* Pro tips & transit recommendation */}
                              <div className="flex flex-wrap gap-3 text-[11px] pt-1">
                                {act.booking_tip && (
                                  <span className="text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                                    💡 <strong>Tip:</strong> {act.booking_tip}
                                  </span>
                                )}
                                {act.transport_recommendation && (
                                  <span className="text-blue-800 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                                    🚆 <strong>Transit:</strong> {act.transport_recommendation}
                                  </span>
                                )}
                              </div>
                            </div>

                            {/* Cost & Edit */}
                            <div className="text-right md:border-l md:border-slate-100 md:pl-6 self-stretch flex md:flex-col justify-between items-end">
                              <div>
                                <div className="text-[10px] uppercase font-bold text-slate-400">Est. Activity Cost</div>
                                <div className="text-base font-extrabold text-slate-900">
                                  {currentTrip.currency_symbol || '$'}{act.estimated_cost.toFixed(2)}
                                </div>
                              </div>
                              <button
                                onClick={() => setEditingActivity({ ...act, day_number: day.day_number })}
                                className="text-xs text-brand-600 hover:text-brand-800 font-semibold mt-2"
                              >
                                Edit / Tweak ✏️
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* Checklist & Etiquette Side-by-Side */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Packing Checklist */}
              <div className="glass-card rounded-3xl p-6 shadow-lg border border-slate-200">
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-xl">🎒</span>
                  <h4 className="text-base font-bold text-slate-900">Recommended Packing Checklist</h4>
                </div>
                <ul className="space-y-2.5">
                  {currentTrip.packing_checklist.map((item, idx) => (
                    <li key={idx} className="flex items-center gap-2 text-xs text-slate-700">
                      <input type="checkbox" className="w-4 h-4 rounded text-brand-600 border-slate-300 focus:ring-brand-500" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Local Etiquette Tips */}
              <div className="glass-card rounded-3xl p-6 shadow-lg border border-slate-200">
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-xl">📌</span>
                  <h4 className="text-base font-bold text-slate-900">Local Etiquette & Pro Tips</h4>
                </div>
                <ul className="space-y-2.5">
                  {currentTrip.local_etiquette_tips.map((tip, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-xs text-slate-700">
                      <span className="text-brand-600 font-bold">•</span>
                      <span>{tip}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: SAVED TRIPS DASHBOARD */}
        {activeTab === 'saved' && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-200">
              <div>
                <h2 className="text-2xl font-black text-slate-900 tracking-tight">Saved Trips & Expeditions</h2>
                <p className="text-sm text-slate-500">
                  Storage Mode: <strong>{health?.storage?.storage_mode}</strong>
                </p>
              </div>
              <button
                onClick={() => setActiveTab('builder')}
                className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs shadow-md transition flex items-center gap-1.5 self-start sm:self-auto"
              >
                <span>➕</span> <span>Plan New Trip</span>
              </button>
            </div>

            {savedTrips.length === 0 ? (
              <div className="glass-card rounded-3xl p-12 text-center border border-slate-200 max-w-lg mx-auto">
                <div className="text-4xl mb-3">🗺️</div>
                <h4 className="text-lg font-bold text-slate-800 mb-1">No Saved Trips Yet</h4>
                <p className="text-xs text-slate-500 mb-6">Use the Smart Builder or run one of the three preset scenarios to create your first itinerary!</p>
                <button
                  onClick={() => setActiveTab('builder')}
                  className="px-5 py-2.5 rounded-xl bg-brand-600 text-white text-xs font-bold hover:bg-brand-500 transition"
                >
                  Open Trip Builder
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {savedTrips.map(trip => {
                  const sym = trip.currency_symbol || trip.cost_breakdown?.currency_symbol || '$';
                  const tot = trip.cost_breakdown?.total || trip.total_estimated_cost || 0;
                  return (
                    <div key={trip.id} className="glass-card rounded-2xl p-6 shadow-md hover:shadow-xl transition-all border border-slate-200 flex flex-col justify-between group">
                      <div>
                        <div className="flex items-center justify-between gap-2 mb-2">
                          <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-brand-100 text-brand-800">
                            {trip.traveler_type} ({trip.group_size}p)
                          </span>
                          <span className="text-[10px] font-semibold text-slate-400">
                            {trip.duration_days} Days
                          </span>
                        </div>
                        <h4 className="text-base font-bold text-slate-900 group-hover:text-brand-600 transition-colors line-clamp-1">
                          {trip.title}
                        </h4>
                        <p className="text-xs text-slate-500 mt-1 line-clamp-2">📍 {trip.destination}</p>
                        <div className="mt-3 text-xs font-semibold text-slate-700">
                          Est. {sym}{tot.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </div>
                      </div>

                      <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
                        <button
                          onClick={() => {
                            setCurrentTrip(trip);
                            setSelectedDayIdx(0);
                            setActiveTab('itinerary');
                          }}
                          className="text-xs font-bold text-brand-600 hover:text-brand-800"
                        >
                          View Itinerary →
                        </button>
                        <button
                          onClick={() => handleDeleteTrip(trip.id)}
                          className="text-xs font-medium text-rose-500 hover:text-rose-700"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

      </main>

      {/* MODAL: AI Day Regenerator */}
      {regenDayModal.open && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl shadow-2xl p-6 sm:p-8 max-w-lg w-full border border-slate-200 space-y-4 animate-in fade-in zoom-in duration-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <h3 className="text-lg font-black text-slate-900 flex items-center gap-2">
                <span>🔄</span> AI Re-roll Day {regenDayModal.dayNumber}
              </h3>
              <button
                onClick={() => setRegenDayModal({ open: false, dayNumber: 1, instructions: '' })}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-600">
              Tell the AI how you want to alter Day {regenDayModal.dayNumber}. The rest of your itinerary will remain untouched.
            </p>

            <textarea
              rows="3"
              value={regenDayModal.instructions}
              onChange={(e) => setRegenDayModal({ ...regenDayModal, instructions: e.target.value })}
              placeholder="e.g. Focus on outdoor nature hikes, replace the museum with an artisanal culinary tour, make the evening dinner more romantic..."
              className="w-full p-3 rounded-xl border border-slate-300 focus:ring-2 focus:ring-brand-500 outline-none text-xs text-slate-800 font-medium"
            />

            {/* Quick Prompt Chips */}
            <div className="flex flex-wrap gap-1.5">
              {[
                'Make it more relaxed & slower paced',
                'Add romantic sunset dinner',
                'Suggest indoor activities (rainy day)',
                'Include local craft beer / wine tasting',
                'Focus on budget street food'
              ].map(chip => (
                <button
                  type="button"
                  key={chip}
                  onClick={() => setRegenDayModal({ ...regenDayModal, instructions: chip })}
                  className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition"
                >
                  + {chip}
                </button>
              ))}
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setRegenDayModal({ open: false, dayNumber: 1, instructions: '' })}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleRegenerateDaySubmit}
                className="px-5 py-2 rounded-xl bg-teal-600 hover:bg-teal-500 text-white text-xs font-bold shadow-md transition"
              >
                Regenerate Day with AI ⚡
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Edit Activity Details */}
      {editingActivity && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl shadow-2xl p-6 sm:p-8 max-w-lg w-full border border-slate-200 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <h3 className="text-lg font-black text-slate-900 flex items-center gap-2">
                <span>✏️</span> Tweak Activity Details
              </h3>
              <button
                onClick={() => setEditingActivity(null)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-[11px] font-bold text-slate-600 uppercase">Activity Title</label>
                <input
                  type="text"
                  value={editingActivity.title}
                  onChange={(e) => setEditingActivity({ ...editingActivity, title: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs text-slate-800 font-semibold"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-bold text-slate-600 uppercase">Timing</label>
                  <input
                    type="text"
                    value={editingActivity.time_str}
                    onChange={(e) => setEditingActivity({ ...editingActivity, time_str: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs text-slate-800"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-bold text-slate-600 uppercase">
                    Est. Cost ({currentTrip.currency || 'USD'})
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={editingActivity.estimated_cost}
                    onChange={(e) => setEditingActivity({ ...editingActivity, estimated_cost: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs text-slate-800"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-600 uppercase">Description & Overview</label>
                <textarea
                  rows="2"
                  value={editingActivity.description}
                  onChange={(e) => setEditingActivity({ ...editingActivity, description: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs text-slate-800"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-600 uppercase">Booking / Insider Tip</label>
                <input
                  type="text"
                  value={editingActivity.booking_tip || ''}
                  onChange={(e) => setEditingActivity({ ...editingActivity, booking_tip: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs text-slate-800"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setEditingActivity(null)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={async () => {
                  const updatedDays = currentTrip.days.map(d => ({
                    ...d,
                    activities: d.activities.map(a => a.id === editingActivity.id ? editingActivity : a)
                  }));
                  const updatedTrip = { ...currentTrip, days: updatedDays };
                  setCurrentTrip(updatedTrip);
                  setEditingActivity(null);
                  
                  // Persist to backend
                  try {
                    await fetch(`/api/trips/${currentTrip.id}`, {
                      method: 'PUT',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ days: updatedDays })
                    });
                    fetchSavedTrips();
                    showToast('Activity updated and saved!', 'success');
                  } catch (e) {
                    showToast('Saved locally in view', 'info');
                  }
                }}
                className="px-5 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold transition"
              >
                Apply Changes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Storage Configuration & Details */}
      {storageHelpModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl shadow-2xl p-6 sm:p-8 max-w-lg w-full border border-slate-200 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <h3 className="text-lg font-black text-slate-900 flex items-center gap-2">
                <span>🗄️</span> Storage Engine Status
              </h3>
              <button onClick={() => setStorageHelpModal(false)} className="text-slate-400 hover:text-slate-600 font-bold">✕</button>
            </div>

            <div className="space-y-3 text-xs text-slate-700">
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                <div className="font-bold text-slate-900">Current Storage Status:</div>
                <div className="text-slate-600 mt-1">{health?.storage?.storage_mode}</div>
              </div>

              <div className="font-bold text-slate-800">How to configure Supabase Cloud Database:</div>
              <ol className="list-decimal list-inside space-y-1 text-slate-600 leading-relaxed">
                <li>Create a free Supabase project at <code className="bg-slate-100 px-1 py-0.5 rounded text-brand-600">supabase.com</code>.</li>
                <li>Run the SQL schema in <code className="bg-slate-100 px-1 py-0.5 rounded text-brand-600">backend/supabase_schema.sql</code> in the Supabase SQL editor.</li>
                <li>Add your credentials to <code className="bg-slate-100 px-1 py-0.5 rounded text-brand-600">.env</code>:
                  <pre className="p-2 bg-slate-900 text-teal-300 rounded-lg mt-1 font-mono text-[11px] overflow-x-auto">
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-key
                  </pre>
                </li>
                <li>The system will automatically detect the connection and switch to <strong>Supabase Cloud Active</strong>!</li>
              </ol>

              <div className="p-2.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800">
                ✓ <strong>Local SQLite Fallback</strong> is active and persistent in <code className="font-mono">travel_planner.db</code>.
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button onClick={() => setStorageHelpModal(false)} className="px-4 py-2 bg-brand-600 text-white rounded-xl text-xs font-bold">
                Got It
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Global Footer */}
      <footer className="glass-nav border-t border-slate-200 mt-12 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="font-extrabold text-slate-800">TravelCraft AI</span>
            <span>• React, FastAPI, Supabase & Gemini</span>
          </div>
          <div>
            AI Travel Itinerary Planner • Multi-Currency Support (USD, INR, EUR, GBP, JPY)
          </div>
        </div>
      </footer>
    </div>
  );
}

// Render React App
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
