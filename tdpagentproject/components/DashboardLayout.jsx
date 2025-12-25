// 'use client';

// import { useState, useEffect } from 'react';
// import Link from 'next/link';
// import { usePathname } from 'next/navigation';
// import { api } from '../lib/api';
// import { Home, FileText, Mail, Briefcase, Bell } from 'lucide-react';

// export default function DashboardLayout({ children }) {
//     const pathname = usePathname();
//     const [isSidebarOpen, setIsSidebarOpen] = useState(false);
//     const [showNotifications, setShowNotifications] = useState(false);
//     const [notifications, setNotifications] = useState([]);

//     useEffect(() => {
//         // Initial fetch
//         const init = async () => {
//             try {
//                 // Trigger check for stalled cases (fire and forget)
//                 api.checkStalledCases().catch(e => console.warn('Stalled check failed', e));
//                 await fetchNotifications();
//             } catch (e) {
//                 console.error(e);
//             }
//         };
//         init();

//         // Polling every 30 seconds
//         const interval = setInterval(fetchNotifications, 30000);
//         return () => clearInterval(interval);
//     }, []);

//     const fetchNotifications = async () => {
//         try {
//             const data = await api.getNotifications();
//             // API returns { notifications: [case objects] }
//             // We need to map them to { id, text, time, read }
//             const mapped = (data.notifications || []).map(n => ({
//                 id: n.case_id || n.id,
//                 text: n.subject ? `Stalled Case: ${n.subject}` : `Stalled Case #${n.case_id || 'Unknown'}`,
//                 time: n.created_at ? new Date(n.created_at).toLocaleTimeString() : 'Just now',
//                 read: false // API only returns 'new' notifications
//             }));
//             setNotifications(mapped);
//         } catch (e) {
//             console.warn('Failed to fetch notifications', e);
//         }
//     };

//     const handleMarkAllRead = async () => {
//         try {
//             await api.markNotificationsRead();
//             // Optimistically mark local state or refetch
//             setNotifications(prev => prev.map(n => ({ ...n, status: 'read' }))); // assuming 'status' field from API logic
//             // The API response for getNotifications filters only 'new' ones? 
//             // The user request says: "Get Notifications ... Filter the notifications that are marked as 'new'"
//             // So if we mark read, they should disappear from the list on next fetch?
//             // Or we just mark them read locally.
//             // If the API only returns new ones, then clearing the list might be appropriate or fetching again.
//             // Let's fetch again.
//             fetchNotifications();
//         } catch (e) {
//             console.error('Failed to mark read', e);
//         }
//     };

//     const navigation = [
//         { name: 'Dashboard', href: '/dashboard', icon: <Home size={20} /> },
//         { name: 'Draft', href: '/dashboard/draft', icon: <FileText size={20} /> },
//         { name: 'Email', href: '/dashboard/email', icon: <Mail size={20} /> },
//         { name: 'Cases', href: '/dashboard/cases', icon: <Briefcase size={20} /> },
//     ];

//     return (
//         <div className="min-h-screen bg-gray-50 dark:bg-zinc-950 flex flex-col md:flex-row">
//             <div className="md:hidden flex items-center justify-between p-4 bg-white dark:bg-zinc-900 shadow-sm z-20">
//                 <span className="text-xl font-bold dark:text-white">TDP Agent</span>
//                 <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="text-2xl">
//                     ☰
//                 </button>
//             </div>

//             <aside
//                 className={`${isSidebarOpen ? 'block' : 'hidden'
//                     } md:block w-full md:w-64 bg-white dark:bg-zinc-900 shadow-xl shadow-gray-200/50 dark:shadow-none z-20 flex-shrink-0 transition-all duration-300 h-screen sticky top-0 flex flex-col justify-between`}
//             >
//                 <div className="h-16 flex items-center px-6 hidden md:flex">
//                     <h1 className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">TDP Agent</h1>
//                 </div>

//                 <nav className="p-4 space-y-2 flex-1 overflow-y-auto min-h-0">
//                     {navigation.map((item) => {
//                         const isActive = item.href === '/dashboard'
//                             ? pathname === '/dashboard'
//                             : pathname === item.href || pathname?.startsWith(item.href + '/');
//                         return (
//                             <Link
//                                 key={item.name}
//                                 href={item.href}
//                                 className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${isActive
//                                     ? 'bg-indigo-50 text-indigo-600 shadow-sm dark:bg-indigo-900/20 dark:text-indigo-400'
//                                     : 'text-gray-700 hover:bg-gray-50 hover:shadow-sm dark:text-gray-300 dark:hover:bg-zinc-800'
//                                     }`}
//                             >
//                                 <span>{item.icon}</span>
//                                 <span className="font-medium">{item.name}</span>
//                             </Link>
//                         );
//                     })}
//                 </nav>

//                 <div className="p-4 space-y-4 border-t border-gray-100 dark:border-zinc-800">
//                     <div className="relative">
//                         <button
//                             onClick={() => setShowNotifications(!showNotifications)}
//                             className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${showNotifications
//                                 ? 'bg-gray-100 text-gray-900 dark:bg-zinc-800 dark:text-white'
//                                 : 'text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-zinc-800'}`}
//                         >
//                             <div className="relative">
//                                 <Bell size={20} />
//                                 {notifications && notifications.length > 0 && (
//                                     <span className="absolute -top-1 -right-1 h-2.5 w-2.5 bg-red-500 rounded-full border-2 border-white dark:border-zinc-900"></span>
//                                 )}
//                             </div>
//                             <span className="font-medium">Notifications</span>
//                         </button>

//                         {showNotifications && (
//                             <div className="absolute bottom-full left-0 mb-2 w-full bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800 rounded-xl shadow-xl z-50 overflow-hidden ring-1 ring-black/5">
//                                 <div className="p-3 flex justify-between items-center bg-gray-50/50 dark:bg-zinc-800/50 border-b border-gray-100 dark:border-zinc-800">
//                                     <h3 className="text-xs font-semibold text-gray-900 dark:text-white uppercase tracking-wider">Recent Alerts</h3>
//                                     {notifications.length > 0 && (
//                                         <button
//                                             onClick={(e) => { e.stopPropagation(); handleMarkAllRead(); }}
//                                             className="text-[10px] text-indigo-600 hover:text-indigo-500 font-medium"
//                                         >
//                                             Mark read
//                                         </button>
//                                     )}
//                                 </div>
//                                 <div className="max-h-64 overflow-y-auto">
//                                     {notifications.length > 0 ? (
//                                         <ul className="divide-y divide-gray-50 dark:divide-zinc-800/50">
//                                             {notifications.map((notification) => (
//                                                 <li
//                                                     key={notification.id}
//                                                     className={`p-3 hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors cursor-pointer text-left ${!notification.read ? 'bg-indigo-50/30 dark:bg-indigo-900/10' : ''}`}
//                                                 >
//                                                     <div className="flex gap-3">
//                                                         <div className={`mt-1.5 h-1.5 w-1.5 rounded-full flex-shrink-0 ${!notification.read ? 'bg-indigo-500' : 'bg-gray-300 dark:bg-zinc-600'}`}></div>
//                                                         <div>
//                                                             <p className={`text-xs ${!notification.read ? 'font-medium text-gray-900 dark:text-white' : 'text-gray-600 dark:text-gray-400'}`}>
//                                                                 {notification.text}
//                                                             </p>
//                                                             <p className="text-[10px] text-gray-400 mt-0.5">{notification.time}</p>
//                                                         </div>
//                                                     </div>
//                                                 </li>
//                                             ))}
//                                         </ul>
//                                     ) : (
//                                         <div className="p-6 text-center text-gray-500 dark:text-gray-400 text-xs">
//                                             No new notifications
//                                         </div>
//                                     )}
//                                 </div>
//                             </div>
//                         )}
//                     </div>

//                     <div className="flex items-center gap-3 px-4 py-2 rounded-xl border border-gray-100 dark:border-zinc-800 bg-white dark:bg-zinc-900/50">
//                         <div className="w-8 h-8 rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 flex items-center justify-center text-white text-xs font-bold shadow-sm">
//                             A
//                         </div>
//                         <div className="overflow-hidden">
//                             <p className="text-xs font-medium dark:text-white truncate">Tdp Agent</p>
//                             <p className="text-[10px] text-gray-500 dark:text-gray-400 truncate">admin@tdpagent.com</p>
//                         </div>
//                     </div>
//                 </div>
//             </aside>

//             <main className="flex-1 overflow-y-auto h-[calc(100vh-64px)] md:h-screen relative p-4 md:p-8">
//                 {children}
//             </main>
//         </div>
//     );
// }




















'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { api } from '../lib/api';
import { Home, FileText, Mail, Briefcase, Bell, LogOut } from 'lucide-react';

export default function DashboardLayout({ children }) {
    const pathname = usePathname();
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [showNotifications, setShowNotifications] = useState(false);
    const [notifications, setNotifications] = useState([]);

    useEffect(() => {
        const init = async () => {
            try {
                api.checkStalledCases().catch(e => console.warn('Stalled check failed', e));
                await fetchNotifications();
            } catch (e) {
                console.error(e);
            }
        };
        init();
        const interval = setInterval(fetchNotifications, 30000);
        return () => clearInterval(interval);
    }, []);

    const fetchNotifications = async () => {
        try {
            const data = await api.getNotifications();
            const mapped = (data.notifications || []).map(n => ({
                id: n.case_id || n.id,
                text: n.subject ? `Stalled Case: ${n.subject}` : `Stalled Case #${n.case_id || 'Unknown'}`,
                time: n.created_at ? new Date(n.created_at).toLocaleTimeString() : 'Just now',
                read: false
            }));
            setNotifications(mapped);
        } catch (e) {
            console.warn('Failed to fetch notifications', e);
        }
    };

    const handleMarkAllRead = async () => {
        try {
            await api.markNotificationsRead();
            fetchNotifications();
        } catch (e) {
            console.error('Failed to mark read', e);
        }
    };

    const navigation = [
        { name: 'Dashboard', href: '/dashboard', icon: <Home size={20} /> },
        { name: 'Draft', href: '/dashboard/draft', icon: <FileText size={20} /> },
        { name: 'Email', href: '/dashboard/email', icon: <Mail size={20} /> },
        { name: 'Cases', href: '/dashboard/cases', icon: <Briefcase size={20} /> },
    ];

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-zinc-950 flex flex-col md:flex-row">
            {/* Mobile Header */}
            <div className="md:hidden flex items-center justify-between p-4 bg-white dark:bg-zinc-900 shadow-sm z-20">
                <span className="text-xl font-bold dark:text-white text-indigo-600">TDP Agent</span>
                <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="text-2xl">
                    ☰
                </button>
            </div>

            {/* Sidebar */}
            <aside
                className={`${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
                    } md:translate-x-0 fixed md:sticky top-0 left-0 w-64 h-screen bg-white dark:bg-zinc-900 border-r border-gray-100 dark:border-zinc-800 z-30 transition-transform duration-300 flex flex-col`}
            >
                {/* 1. Header Area */}
                <div className="h-20 flex items-center px-8">
                    <h1 className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">TDP Agent</h1>
                </div>

                {/* 2. Main Navigation - flex-1 pushes everything below it to the bottom */}
                <nav className="flex-1 px-4 py-2 space-y-1 overflow-y-auto">
                    {navigation.map((item) => {
                        const isActive = item.href === '/dashboard'
                            ? pathname === '/dashboard'
                            : pathname === item.href || pathname?.startsWith(item.href + '/');

                        return (
                            <Link
                                key={item.name}
                                href={item.href}
                                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${isActive
                                    ? 'bg-indigo-50 text-indigo-600 font-semibold dark:bg-indigo-900/20 dark:text-indigo-400'
                                    : 'text-gray-600 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-zinc-800'
                                    }`}
                            >
                                {item.icon}
                                <span>{item.name}</span>
                            </Link>
                        );
                    })}
                </nav>

                {/* 3. Bottom Utility & Profile Section */}
                <div className="p-4 border-t border-gray-100 dark:border-zinc-800 bg-white dark:bg-zinc-900">
                    <div className="relative mb-4">
                        <button
                            onClick={() => setShowNotifications(!showNotifications)}
                            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${showNotifications
                                ? 'bg-gray-100 dark:bg-zinc-800 text-gray-900 dark:text-white'
                                : 'text-gray-600 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-zinc-800'
                                }`}
                        >
                            <div className="relative">
                                <Bell size={20} />
                                {notifications.length > 0 && (
                                    <span className="absolute -top-0.5 -right-0.5 h-2 w-2 bg-red-500 rounded-full border-2 border-white dark:border-zinc-900"></span>
                                )}
                            </div>
                            <span className="font-medium">Notifications</span>
                        </button>

                        {/* Notification Dropup */}
                        {showNotifications && (
                            <div className="absolute bottom-full left-0 mb-2 w-full bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-2xl shadow-2xl z-50 overflow-hidden ring-1 ring-black/5">
                                <div className="p-3 flex justify-between items-center bg-gray-50 dark:bg-zinc-800/50 border-b dark:border-zinc-800">
                                    <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Alerts</h3>
                                    {notifications.length > 0 && (
                                        <button onClick={handleMarkAllRead} className="text-[10px] text-indigo-600 font-bold">Clear</button>
                                    )}
                                </div>
                                <div className="max-h-48 overflow-y-auto">
                                    {notifications.length > 0 ? (
                                        notifications.map(n => (
                                            <div key={n.id} className="p-3 border-b border-gray-50 dark:border-zinc-800 last:border-0 hover:bg-gray-50 dark:hover:bg-zinc-800 transition-colors cursor-pointer">
                                                <p className="text-xs text-gray-800 dark:text-gray-200 line-clamp-2">{n.text}</p>
                                                <p className="text-[9px] text-gray-400 mt-1">{n.time}</p>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="p-4 text-center text-[11px] text-gray-400">All caught up!</div>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* User Card */}
                    <div className="flex items-center gap-3 px-3 py-3 rounded-2xl border border-gray-100 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm">
                        <div className="w-10 h-10 rounded-full bg-indigo-500 flex items-center justify-center text-white font-bold text-sm shrink-0">
                            A
                        </div>
                        <div className="min-w-0 flex-1">
                            <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">Tdp Agent</p>
                            <p className="text-[10px] text-gray-500 dark:text-gray-400 truncate">admin@tdpagent.com</p>
                        </div>
                        <button
                            onClick={() => {
                                document.cookie = "auth_token=; path=/; max-age=0";
                                window.location.href = '/login';
                            }}
                            className="p-2 text-gray-500 hover:text-red-500 transition-colors"
                            title="Sign Out"
                        >
                            <LogOut size={18} />
                        </button>
                    </div>
                </div>
            </aside>

            {/* Main Content Area */}
            <main className="flex-1 min-w-0 bg-gray-50 dark:bg-zinc-950 p-6 md:p-10">
                {children}
            </main>

            {/* Overlay for mobile sidebar */}
            {isSidebarOpen && (
                <div
                    className="fixed inset-0 bg-black/20 backdrop-blur-sm z-20 md:hidden"
                    onClick={() => setIsSidebarOpen(false)}
                />
            )}
        </div>
    );
}