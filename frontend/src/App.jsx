import React, { useState, useEffect, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import {
    LayoutDashboard,
    UserPlus,
    ScanFace,
    History,
    Settings,
    Users,
    CheckCircle2,
    XCircle,
    LogOut,
    Clock,
    Fingerprint,
    ChevronRight,
    Menu,
    Camera,
    X,
    Loader2
} from 'lucide-react';

const API_BASE = '/api';

// History Page Component
const HistoryPage = () => {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [dateFrom, setDateFrom] = useState(() => {
        const d = new Date();
        d.setDate(d.getDate() - 7);
        return d.toISOString().split('T')[0];
    });
    const [dateTo, setDateTo] = useState(() => new Date().toISOString().split('T')[0]);

    useEffect(() => {
        fetchHistory();
    }, [dateFrom, dateTo]);

    const fetchHistory = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/attendance?date_from=${dateFrom}&date_to=${dateTo}`);
            const data = await res.json();
            setHistory(data);
        } catch (err) {
            console.error('Error fetching history:', err);
        }
        setLoading(false);
    };

    return (
        <div className="animate-fade-in">
            <div className="flex items-center space-x-2 mb-6">
                <History className="text-indigo-400" size={20} />
                <h2 className="text-xl font-semibold text-white">Attendance History</h2>
            </div>

            <div className="bg-slate-900/50 backdrop-blur-sm rounded-2xl p-6 border border-slate-800 mb-6">
                <div className="flex flex-wrap gap-4 items-end">
                    <div>
                        <label className="block text-sm font-medium text-slate-400 mb-2">From Date</label>
                        <input
                            type="date"
                            value={dateFrom}
                            onChange={(e) => setDateFrom(e.target.value)}
                            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-400 mb-2">To Date</label>
                        <input
                            type="date"
                            value={dateTo}
                            onChange={(e) => setDateTo(e.target.value)}
                            className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white"
                        />
                    </div>
                </div>
            </div>

            <div className="bg-slate-900/50 backdrop-blur-sm rounded-2xl border border-slate-800 overflow-hidden">
                {loading ? (
                    <div className="text-center py-12 text-slate-500">Loading...</div>
                ) : history.length === 0 ? (
                    <div className="text-center py-12 text-slate-500">No records found</div>
                ) : (
                    <table className="w-full">
                        <thead className="bg-slate-800/50">
                            <tr className="text-left text-xs font-semibold text-slate-400 uppercase">
                                <th className="px-6 py-4">Date</th>
                                <th className="px-6 py-4">Time</th>
                                <th className="px-6 py-4">Employee</th>
                                <th className="px-6 py-4">ID</th>
                                <th className="px-6 py-4">Type</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                            {history.map((record, idx) => {
                                const ts = new Date(record.timestamp);
                                return (
                                    <tr key={idx} className="hover:bg-slate-800/30">
                                        <td className="px-6 py-4 text-white">{ts.toLocaleDateString()}</td>
                                        <td className="px-6 py-4 text-slate-300 font-mono">{ts.toLocaleTimeString()}</td>
                                        <td className="px-6 py-4 text-white font-medium">{record.name}</td>
                                        <td className="px-6 py-4 text-slate-400">{record.employee_id}</td>
                                        <td className="px-6 py-4">
                                            <span className={`px-2 py-1 rounded-full text-xs font-semibold ${record.punch_type === 'IN'
                                                ? 'bg-emerald-900/30 text-emerald-400 border border-emerald-800'
                                                : 'bg-rose-900/30 text-rose-400 border border-rose-800'
                                                }`}>
                                                {record.punch_type}
                                            </span>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
};

const App = () => {
    const [activeTab, setActiveTab] = useState('dashboard');
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [stats, setStats] = useState({ totalUsers: 0, present: 0, absent: 0, checkedOut: 0 });
    const [usersData, setUsersData] = useState([]);
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState(null);

    // Register form state
    const [registerName, setRegisterName] = useState('');
    const [registerEmployeeId, setRegisterEmployeeId] = useState('');
    const [capturedImage, setCapturedImage] = useState(null);
    const webcamRef = useRef(null);

    // Recognition state
    const [recognitionResult, setRecognitionResult] = useState(null);
    const [isRecognizing, setIsRecognizing] = useState(false);

    // Fetch data on mount and tab change
    useEffect(() => {
        fetchStats();
        fetchTodayAttendance();
        fetchUsers();
    }, [activeTab]);

    const fetchStats = async () => {
        try {
            const res = await fetch(`${API_BASE}/stats`);
            const data = await res.json();
            setStats(data);
        } catch (err) {
            console.error('Error fetching stats:', err);
        }
    };

    const fetchTodayAttendance = async () => {
        try {
            const res = await fetch(`${API_BASE}/attendance/today`);
            const data = await res.json();
            setUsersData(data);
        } catch (err) {
            console.error('Error fetching attendance:', err);
        }
    };

    const fetchUsers = async () => {
        try {
            const res = await fetch(`${API_BASE}/users`);
            const data = await res.json();
            setUsers(data);
        } catch (err) {
            console.error('Error fetching users:', err);
        }
    };

    const showMessage = (text, type = 'info') => {
        setMessage({ text, type });
        setTimeout(() => setMessage(null), 4000);
    };

    // Camera capture
    const capturePhoto = useCallback(() => {
        const imageSrc = webcamRef.current?.getScreenshot();
        if (imageSrc) {
            setCapturedImage(imageSrc);
        }
    }, [webcamRef]);

    // Register user
    const handleRegister = async () => {
        if (!registerName || !registerEmployeeId || !capturedImage) {
            showMessage('Please fill all fields and capture a photo', 'error');
            return;
        }

        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/users`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: registerName,
                    employee_id: registerEmployeeId,
                    image: capturedImage
                })
            });

            const data = await res.json();

            if (data.success) {
                showMessage(`User ${registerName} registered successfully!`, 'success');
                setRegisterName('');
                setRegisterEmployeeId('');
                setCapturedImage(null);
                fetchUsers();
                fetchStats();
            } else {
                showMessage(data.error || 'Registration failed', 'error');
            }
        } catch (err) {
            showMessage('Error registering user', 'error');
        }
        setLoading(false);
    };

    // Recognize face
    const handleRecognize = async (logAttendance = false) => {
        const imageSrc = webcamRef.current?.getScreenshot();
        if (!imageSrc) {
            showMessage('Could not capture image', 'error');
            return;
        }

        setIsRecognizing(true);
        try {
            const res = await fetch(`${API_BASE}/recognize`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    image: imageSrc,
                    log_attendance: logAttendance
                })
            });

            const data = await res.json();
            setRecognitionResult(data);

            if (data.recognized) {
                if (logAttendance && data.attendance_logged) {
                    showMessage(`Punch ${data.punch_type} recorded for ${data.name}!`, 'success');
                    fetchTodayAttendance();
                    fetchStats();
                }
            } else {
                showMessage(data.error || 'Face not recognized', 'error');
            }
        } catch (err) {
            showMessage('Error recognizing face', 'error');
        }
        setIsRecognizing(false);
    };

    // Punch attendance using already recognized user
    const handlePunch = async (punchType) => {
        if (!recognitionResult?.user_id) {
            showMessage('Please recognize face first', 'error');
            return;
        }

        setIsRecognizing(true);
        try {
            const res = await fetch(`${API_BASE}/punch`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: recognitionResult.user_id,
                    punch_type: punchType
                })
            });

            const data = await res.json();

            if (data.success) {
                showMessage(`Punch ${data.punch_type} recorded for ${data.name}!`, 'success');
                // Update recognition result to show new next punch
                setRecognitionResult(prev => ({
                    ...prev,
                    last_punch: data.punch_type,
                    next_punch: data.punch_type === 'IN' ? 'OUT' : 'IN'
                }));
                fetchTodayAttendance();
                fetchStats();
            } else {
                showMessage(data.error || 'Failed to punch', 'error');
            }
        } catch (err) {
            showMessage('Error punching attendance', 'error');
        }
        setIsRecognizing(false);
    };

    // Delete user
    const handleDeleteUser = async (userId, userName) => {
        if (!confirm(`Delete user ${userName}?`)) return;

        try {
            const res = await fetch(`${API_BASE}/users/${userId}`, { method: 'DELETE' });
            const data = await res.json();

            if (data.success) {
                showMessage('User deleted', 'success');
                fetchUsers();
                fetchStats();
                fetchTodayAttendance();
            }
        } catch (err) {
            showMessage('Error deleting user', 'error');
        }
    };

    // Components
    const StatCard = ({ title, value, icon: Icon, colorClass, delay }) => (
        <div
            className="relative overflow-hidden bg-slate-800/50 backdrop-blur-md border border-slate-700/50 p-6 rounded-2xl shadow-xl transform transition-all hover:scale-[1.02] hover:border-slate-600 group animate-fade-in-up"
            style={{ animationDelay: delay }}
        >
            <div className={`absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity ${colorClass}`}>
                <Icon size={80} />
            </div>
            <div className="relative z-10 flex flex-col justify-between h-full">
                <div className="flex items-center space-x-3 mb-2">
                    <div className={`p-2 rounded-lg bg-slate-900/50`}>
                        <Icon size={20} className={colorClass} />
                    </div>
                    <h3 className="text-slate-400 text-sm font-medium tracking-wide uppercase">{title}</h3>
                </div>
                <p className="text-4xl font-bold text-white mt-1">{value}</p>
            </div>
            <div className={`absolute bottom-0 left-0 h-1 w-full ${colorClass.replace('text-', 'bg-')}`} />
        </div>
    );

    const AttendanceRow = ({ user }) => (
        <div className="group flex flex-col md:flex-row items-center justify-between p-4 mb-3 bg-slate-800/40 hover:bg-slate-700/50 border border-slate-700/30 hover:border-indigo-500/30 rounded-xl transition-all duration-300">
            <div className="flex items-center w-full md:w-1/3 mb-4 md:mb-0">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center text-white font-bold text-lg shadow-lg ${user.color}`}>
                    {user.avatar}
                </div>
                <div className="ml-4">
                    <h4 className="text-white font-semibold text-lg group-hover:text-indigo-400 transition-colors">{user.name}</h4>
                    <div className="flex items-center text-slate-400 text-xs space-x-2">
                        <span className="bg-slate-900/50 px-2 py-0.5 rounded border border-slate-700">ID: {user.id}</span>
                    </div>
                </div>
            </div>

            <div className="flex items-center justify-between w-full md:w-1/3 px-4 mb-4 md:mb-0 text-sm">
                <div className="flex flex-col items-center">
                    <span className="text-slate-500 text-xs uppercase mb-1">Clock In</span>
                    <span className="text-emerald-400 font-mono font-medium bg-emerald-900/20 px-2 py-1 rounded border border-emerald-900/30">
                        {user.inTime}
                    </span>
                </div>
                <div className="h-px w-8 bg-slate-700 mx-2"></div>
                <div className="flex flex-col items-center">
                    <span className="text-slate-500 text-xs uppercase mb-1">Clock Out</span>
                    <span className={`font-mono font-medium px-2 py-1 rounded border ${user.outTime !== '-'
                        ? 'text-rose-400 bg-rose-900/20 border-rose-900/30'
                        : 'text-slate-500 bg-slate-800 border-slate-700'
                        }`}>
                        {user.outTime}
                    </span>
                </div>
            </div>

            <div className="flex items-center justify-end w-full md:w-1/3 space-x-6">
                <div className="hidden md:flex flex-col items-end">
                    <span className="text-slate-500 text-xs uppercase mb-1">Duration</span>
                    <span className="text-white font-medium">{user.duration}</span>
                </div>
                <div>
                    {user.status === 'checked_out' ? (
                        <span className="flex items-center space-x-1 px-3 py-1 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-full text-xs font-semibold">
                            <CheckCircle2 size={14} />
                            <span>Complete</span>
                        </span>
                    ) : (
                        <span className="flex items-center space-x-1 px-3 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full text-xs font-semibold animate-pulse">
                            <Clock size={14} />
                            <span>Working</span>
                        </span>
                    )}
                </div>
            </div>
        </div>
    );

    const NavItem = ({ id, icon: Icon, label }) => (
        <button
            onClick={() => setActiveTab(id)}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 group ${activeTab === id
                ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-lg shadow-indigo-900/20'
                : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                }`}
        >
            <Icon size={20} className={activeTab === id ? 'text-white' : 'text-slate-500 group-hover:text-white transition-colors'} />
            <span className="font-medium">{label}</span>
            {activeTab === id && <ChevronRight size={16} className="ml-auto opacity-50" />}
        </button>
    );

    // Message toast
    const MessageToast = () => message && (
        <div className={`fixed top-4 right-4 z-50 px-6 py-3 rounded-xl shadow-2xl animate-fade-in ${message.type === 'success' ? 'bg-emerald-600' :
            message.type === 'error' ? 'bg-rose-600' : 'bg-indigo-600'
            } text-white font-medium`}>
            {message.text}
        </div>
    );

    return (
        <div className="flex h-screen bg-slate-950 text-slate-200 font-sans selection:bg-indigo-500/30">
            <MessageToast />

            {/* Mobile Menu Toggle */}
            <div className="fixed top-4 left-4 z-50 md:hidden">
                <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="p-2 bg-slate-800 rounded-lg text-white">
                    <Menu size={24} />
                </button>
            </div>

            {/* Sidebar */}
            <aside className={`
        fixed md:static inset-y-0 left-0 z-40 w-72 bg-slate-900 border-r border-slate-800 flex flex-col transition-transform duration-300 ease-in-out
        ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
      `}>
                <div className="p-6 border-b border-slate-800">
                    <div className="flex items-center space-x-3 text-indigo-400 mb-1">
                        <ScanFace size={28} />
                        <span className="font-bold text-lg tracking-tight text-white">Face <span className="text-indigo-500">Auth</span></span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">Attendance Management</p>
                </div>

                <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
                    <NavItem id="dashboard" icon={LayoutDashboard} label="Dashboard" />
                    <NavItem id="register" icon={UserPlus} label="Register User" />
                    <NavItem id="attendance" icon={CheckCircle2} label="Mark Attendance" />
                    <NavItem id="history" icon={History} label="Attendance History" />
                    <div className="pt-4 pb-2">
                        <div className="h-px bg-slate-800 mx-2"></div>
                    </div>
                    <NavItem id="settings" icon={Settings} label="Settings" />
                </nav>

                <div className="p-6 bg-slate-900/50 border-t border-slate-800">
                    <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">Quick Stats</h4>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="bg-slate-800 p-3 rounded-lg border border-slate-700">
                            <span className="block text-2xl font-bold text-white mb-1">{stats.totalUsers}</span>
                            <span className="text-xs text-slate-400">Total Users</span>
                        </div>
                        <div className="bg-slate-800 p-3 rounded-lg border border-slate-700">
                            <span className="block text-2xl font-bold text-emerald-400 mb-1">{stats.present}</span>
                            <span className="text-xs text-slate-400">Present</span>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto relative">
                <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
                    <div className="absolute top-[-10%] left-[20%] w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl"></div>
                    <div className="absolute bottom-[10%] right-[10%] w-80 h-80 bg-violet-600/10 rounded-full blur-3xl"></div>
                </div>

                <div className="relative z-10 max-w-6xl mx-auto p-6 md:p-10">

                    {/* Header */}
                    <header className="mb-10 flex flex-col md:flex-row md:items-center justify-between">
                        <div>
                            <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">
                                Hello! <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">Welcome Back.</span>
                            </h1>
                            <p className="text-slate-400">Here is today's attendance overview.</p>
                        </div>
                        <div className="mt-4 md:mt-0 flex items-center space-x-3 bg-slate-800/50 px-4 py-2 rounded-full border border-slate-700">
                            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                            <span className="text-sm font-medium text-emerald-400">System Active</span>
                        </div>
                    </header>

                    {/* Dashboard */}
                    {activeTab === 'dashboard' && (
                        <div className="space-y-8 animate-fade-in">
                            <section>
                                <div className="flex items-center space-x-2 mb-6">
                                    <LayoutDashboard className="text-indigo-400" size={20} />
                                    <h2 className="text-xl font-semibold text-white">Today's Overview</h2>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                                    <StatCard title="Total Users" value={stats.totalUsers} icon={Users} colorClass="text-violet-400" delay="0ms" />
                                    <StatCard title="Present" value={stats.present} icon={CheckCircle2} colorClass="text-emerald-400" delay="100ms" />
                                    <StatCard title="Absent" value={stats.absent} icon={XCircle} colorClass="text-rose-400" delay="200ms" />
                                    <StatCard title="Checked Out" value={stats.checkedOut} icon={LogOut} colorClass="text-blue-400" delay="300ms" />
                                </div>
                            </section>

                            <section>
                                <div className="flex items-center justify-between mb-6">
                                    <div className="flex items-center space-x-2">
                                        <Fingerprint className="text-indigo-400" size={20} />
                                        <h2 className="text-xl font-semibold text-white">Live Attendance Status</h2>
                                    </div>
                                </div>

                                <div className="bg-slate-900/50 backdrop-blur-sm rounded-2xl p-1 border border-slate-800">
                                    <div className="space-y-1">
                                        <div className="hidden md:flex px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                            <div className="w-1/3">Employee Profile</div>
                                            <div className="w-1/3 text-center">Timings</div>
                                            <div className="w-1/3 text-right">Status</div>
                                        </div>
                                        {usersData.length > 0 ? (
                                            usersData.map((user, index) => <AttendanceRow key={index} user={user} />)
                                        ) : (
                                            <div className="text-center py-12 text-slate-500">
                                                No attendance records today. Register users and mark attendance.
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </section>
                        </div>
                    )}

                    {/* Register User */}
                    {activeTab === 'register' && (
                        <div className="animate-fade-in">
                            <div className="flex items-center space-x-2 mb-6">
                                <UserPlus className="text-indigo-400" size={20} />
                                <h2 className="text-xl font-semibold text-white">Register New User</h2>
                            </div>

                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                                {/* Form */}
                                <div className="bg-slate-900/50 backdrop-blur-sm rounded-2xl p-6 border border-slate-800">
                                    <h3 className="text-lg font-semibold text-white mb-6">User Information</h3>

                                    <div className="space-y-4">
                                        <div>
                                            <label className="block text-sm font-medium text-slate-400 mb-2">Full Name</label>
                                            <input
                                                type="text"
                                                value={registerName}
                                                onChange={(e) => setRegisterName(e.target.value)}
                                                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition"
                                                placeholder="Enter full name"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-slate-400 mb-2">Employee ID</label>
                                            <input
                                                type="text"
                                                value={registerEmployeeId}
                                                onChange={(e) => setRegisterEmployeeId(e.target.value)}
                                                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition"
                                                placeholder="Enter employee ID"
                                            />
                                        </div>
                                    </div>

                                    <button
                                        onClick={handleRegister}
                                        disabled={loading}
                                        className="mt-6 w-full py-3 bg-gradient-to-r from-indigo-600 to-violet-600 text-white rounded-xl font-semibold hover:opacity-90 transition flex items-center justify-center space-x-2 disabled:opacity-50"
                                    >
                                        {loading ? <Loader2 className="animate-spin" size={20} /> : <UserPlus size={20} />}
                                        <span>{loading ? 'Registering...' : 'Register User'}</span>
                                    </button>
                                </div>

                                {/* Camera */}
                                <div className="bg-slate-900/50 backdrop-blur-sm rounded-2xl p-6 border border-slate-800">
                                    <h3 className="text-lg font-semibold text-white mb-6">Face Capture</h3>

                                    <div className="relative rounded-xl overflow-hidden bg-slate-800 aspect-video">
                                        {capturedImage ? (
                                            <img src={capturedImage} alt="Captured" className="w-full h-full object-cover" />
                                        ) : (
                                            <Webcam
                                                ref={webcamRef}
                                                screenshotFormat="image/jpeg"
                                                className="w-full h-full object-cover"
                                            />
                                        )}
                                    </div>

                                    <div className="flex space-x-3 mt-4">
                                        {capturedImage ? (
                                            <button
                                                onClick={() => setCapturedImage(null)}
                                                className="flex-1 py-3 bg-slate-700 text-white rounded-xl font-semibold hover:bg-slate-600 transition flex items-center justify-center space-x-2"
                                            >
                                                <X size={20} />
                                                <span>Retake</span>
                                            </button>
                                        ) : (
                                            <button
                                                onClick={capturePhoto}
                                                className="flex-1 py-3 bg-emerald-600 text-white rounded-xl font-semibold hover:bg-emerald-500 transition flex items-center justify-center space-x-2"
                                            >
                                                <Camera size={20} />
                                                <span>Capture Photo</span>
                                            </button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Mark Attendance */}
                    {activeTab === 'attendance' && (
                        <div className="animate-fade-in">
                            <div className="flex items-center space-x-2 mb-6">
                                <ScanFace className="text-indigo-400" size={20} />
                                <h2 className="text-xl font-semibold text-white">Mark Attendance</h2>
                            </div>

                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                                {/* Camera */}
                                <div className="bg-slate-900/50 backdrop-blur-sm rounded-2xl p-6 border border-slate-800">
                                    <h3 className="text-lg font-semibold text-white mb-6">Face Recognition</h3>

                                    <div className="relative rounded-xl overflow-hidden bg-slate-800 aspect-video">
                                        <Webcam
                                            ref={webcamRef}
                                            screenshotFormat="image/jpeg"
                                            className="w-full h-full object-cover"
                                        />
                                        {recognitionResult?.recognized && (
                                            <div className="absolute top-4 right-4 bg-emerald-600 text-white px-3 py-1 rounded-full text-sm font-semibold flex items-center space-x-1">
                                                <CheckCircle2 size={16} />
                                                <span>Verified</span>
                                            </div>
                                        )}
                                    </div>

                                    <button
                                        onClick={() => handleRecognize(false)}
                                        disabled={isRecognizing}
                                        className="mt-4 w-full py-3 bg-gradient-to-r from-indigo-600 to-violet-600 text-white rounded-xl font-semibold hover:opacity-90 transition flex items-center justify-center space-x-2 disabled:opacity-50"
                                    >
                                        {isRecognizing ? <Loader2 className="animate-spin" size={20} /> : <ScanFace size={20} />}
                                        <span>{isRecognizing ? 'Recognizing...' : 'Recognize Face'}</span>
                                    </button>
                                </div>

                                {/* Result */}
                                <div className="bg-slate-900/50 backdrop-blur-sm rounded-2xl p-6 border border-slate-800">
                                    <h3 className="text-lg font-semibold text-white mb-6">Recognition Result</h3>

                                    {recognitionResult?.recognized ? (
                                        <div className="text-center">
                                            <div className="w-20 h-20 mx-auto rounded-full bg-indigo-600 flex items-center justify-center text-white text-2xl font-bold mb-4">
                                                {recognitionResult.name?.split(' ').map(n => n[0]).join('').toUpperCase()}
                                            </div>
                                            <h4 className="text-2xl font-bold text-white mb-2">{recognitionResult.name}</h4>
                                            <p className="text-slate-400 mb-1">ID: {recognitionResult.employee_id}</p>
                                            <p className="text-emerald-400 mb-6">Confidence: {recognitionResult.confidence}%</p>

                                            <div className="bg-slate-800 rounded-xl p-4 mb-4">
                                                <p className="text-slate-400 text-sm mb-2">Last Punch: <span className="text-white">{recognitionResult.last_punch || 'None'}</span></p>
                                            </div>

                                            <div className="flex space-x-3">
                                                <button
                                                    onClick={() => handlePunch('IN')}
                                                    disabled={isRecognizing}
                                                    className="flex-1 py-3 bg-emerald-600 text-white rounded-xl font-semibold hover:bg-emerald-500 transition flex items-center justify-center space-x-2"
                                                >
                                                    <CheckCircle2 size={20} />
                                                    <span>Punch IN</span>
                                                </button>
                                                <button
                                                    onClick={() => handlePunch('OUT')}
                                                    disabled={isRecognizing}
                                                    className="flex-1 py-3 bg-rose-600 text-white rounded-xl font-semibold hover:bg-rose-500 transition flex items-center justify-center space-x-2"
                                                >
                                                    <LogOut size={20} />
                                                    <span>Punch OUT</span>
                                                </button>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="text-center py-12 text-slate-500">
                                            <ScanFace size={48} className="mx-auto mb-4 opacity-50" />
                                            <p>Look at the camera and click "Recognize Face"</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Settings */}
                    {activeTab === 'settings' && (
                        <div className="animate-fade-in">
                            <div className="flex items-center space-x-2 mb-6">
                                <Settings className="text-indigo-400" size={20} />
                                <h2 className="text-xl font-semibold text-white">Settings</h2>
                            </div>

                            <div className="bg-slate-900/50 backdrop-blur-sm rounded-2xl p-6 border border-slate-800">
                                <h3 className="text-lg font-semibold text-white mb-6">Registered Users</h3>

                                {users.length > 0 ? (
                                    <div className="space-y-3">
                                        {users.map((user) => (
                                            <div key={user.id} className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl border border-slate-700">
                                                <div>
                                                    <h4 className="text-white font-semibold">{user.name}</h4>
                                                    <p className="text-slate-400 text-sm">ID: {user.employee_id}</p>
                                                </div>
                                                <button
                                                    onClick={() => handleDeleteUser(user.id, user.name)}
                                                    className="px-4 py-2 bg-rose-600/20 text-rose-400 rounded-lg hover:bg-rose-600/30 transition text-sm font-medium"
                                                >
                                                    Delete
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-slate-500 text-center py-8">No users registered yet.</p>
                                )}
                            </div>
                        </div>
                    )}

                    {/* History */}
                    {activeTab === 'history' && (
                        <HistoryPage />
                    )}

                </div>
            </main>
        </div>
    );
};

export default App;
