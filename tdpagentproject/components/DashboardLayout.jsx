'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { api } from '../lib/api';

export default function DashboardLayout({ children }) {
    const pathname = usePathname();
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [showNotifications, setShowNotifications] = useState(false);
    const [notifications, setNotifications] = useState([]);

    useEffect(() => {
        // Initial fetch
        const init = async () => {
            try {
                // Trigger check for stalled cases (fire and forget)
                api.checkStalledCases().catch(e => console.warn('Stalled check failed', e));
                await fetchNotifications();
            } catch (e) {
                console.error(e);
            }
        };
        init();

        // Polling every 30 seconds
        const interval = setInterval(fetchNotifications, 30000);
        return () => clearInterval(interval);
    }, []);

    const fetchNotifications = async () => {
        try {
            const data = await api.getNotifications();
            // API returns { notifications: [case objects] }
            // We need to map them to { id, text, time, read }
            const mapped = (data.notifications || []).map(n => ({
                id: n.case_id || n.id,
                text: n.subject ? `Stalled Case: ${n.subject}` : `Stalled Case #${n.case_id || 'Unknown'}`,
                time: n.created_at ? new Date(n.created_at).toLocaleTimeString() : 'Just now',
                read: false // API only returns 'new' notifications
            }));
            setNotifications(mapped);
        } catch (e) {
            console.warn('Failed to fetch notifications', e);
        }
    };

    const handleMarkAllRead = async () => {
        try {
            await api.markNotificationsRead();
            // Optimistically mark local state or refetch
            setNotifications(prev => prev.map(n => ({ ...n, status: 'read' }))); // assuming 'status' field from API logic
            // The API response for getNotifications filters only 'new' ones? 
            // The user request says: "Get Notifications ... Filter the notifications that are marked as 'new'"
            // So if we mark read, they should disappear from the list on next fetch?
            // Or we just mark them read locally.
            // If the API only returns new ones, then clearing the list might be appropriate or fetching again.
            // Let's fetch again.
            fetchNotifications();
        } catch (e) {
            console.error('Failed to mark read', e);
        }
    };

    const navigation = [
        { name: 'Dashboard', href: '/dashboard', icon: '🏠' },
        { name: 'Draft', href: '/dashboard/draft', icon: '📝' },
        { name: 'Email', href: '/dashboard/email', icon: '📧' },
        { name: 'Cases', href: '/dashboard/cases', icon: '💼' },
    ];

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-zinc-950 flex flex-col md:flex-row">
            {/* Mobile Header */}
            <div className="md:hidden flex items-center justify-between p-4 bg-white dark:bg-zinc-900 shadow-sm z-20">
                <span className="text-xl font-bold dark:text-white">TDP Agent</span>
                <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="text-2xl">
                    ☰
                </button>
            </div>

            {/* Sidebar - Removed border-r, added shadow-lg for soft separation */}
            <aside
                className={`${isSidebarOpen ? 'block' : 'hidden'
                    } md:block w-full md:w-64 bg-white dark:bg-zinc-900 shadow-xl shadow-gray-200/50 dark:shadow-none z-20 flex-shrink-0 transition-all duration-300 md:h-screen sticky top-0`}
            >
                {/* Header in sidebar - removed border-b */}
                <div className="h-16 flex items-center px-6 hidden md:flex">
                    <h1 className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">TDP Agent</h1>
                </div>
                <nav className="p-4 space-y-2">
                    {navigation.map((item) => {
                        const isActive = item.href === '/dashboard'
                            ? pathname === '/dashboard'
                            : pathname === item.href || pathname?.startsWith(item.href + '/');
                        return (
                            <Link
                                key={item.name}
                                href={item.href}
                                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${isActive
                                    ? 'bg-indigo-50 text-indigo-600 shadow-sm dark:bg-indigo-900/20 dark:text-indigo-400'
                                    : 'text-gray-700 hover:bg-gray-50 hover:shadow-sm dark:text-gray-300 dark:hover:bg-zinc-800'
                                    }`}
                            >
                                <span>{item.icon}</span>
                                <span className="font-medium">{item.name}</span>
                            </Link>
                        );
                    })}
                </nav>
                {/* User section - removed border-t */}
                <div className="absolute bottom-0 w-full p-4">
                    <div className="flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-zinc-800 transition-colors cursor-pointer">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 flex items-center justify-center text-white font-bold shadow-md">
                            A
                        </div>
                        <div>
                            <p className="text-sm font-medium dark:text-white">Tdp Agent</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">admin@tdpagent.com</p>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto h-[calc(100vh-64px)] md:h-screen relative">
                {/* Header - Removed border-b, relying on shadow-sm which is already soft, maybe upgraded to md */}
                <header className="h-16 bg-white/80 backdrop-blur-md dark:bg-zinc-900/80 shadow-sm px-4 md:px-8 flex justify-between items-center sticky top-0 z-10 transition-shadow hover:shadow-md">
                    <h2 className="text-xl font-semibold text-gray-800 dark:text-white">
                        {navigation.find((n) => pathname === n.href || pathname?.startsWith(n.href + '/'))?.name || 'Dashboard'}
                    </h2>
                    <div className="flex items-center gap-4">
                        {/* Notification Bell */}
                        <div className="relative">
                            <button
                                onClick={() => setShowNotifications(!showNotifications)}
                                className="relative p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors rounded-full hover:bg-gray-100 dark:hover:bg-zinc-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
                                    <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
                                </svg>
                                {/* Notification Dot */}
                                {notifications && notifications.length > 0 && (
                                    <span className="absolute top-1.5 right-1.5 h-2.5 w-2.5 bg-red-500 rounded-full border-2 border-white dark:border-zinc-900 shadow-sm"></span>
                                )}
                            </button>

                            {/* Notification Dropdown */}
                            {showNotifications && (
                                <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-zinc-900 border-none rounded-xl shadow-xl z-50 animate-in fade-in zoom-in-95 duration-200 overflow-hidden ring-1 ring-black/5">
                                    <div className="p-3 flex justify-between items-center bg-gray-50/50 dark:bg-zinc-800/50">
                                        <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Notifications</h3>
                                        <span className="text-xs text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 px-2 py-0.5 rounded-full font-medium">
                                            {notifications.length} New
                                        </span>
                                    </div>
                                    <div className="max-h-96 overflow-y-auto">
                                        {notifications.length > 0 ? (
                                            <ul className="divide-y divide-gray-50 dark:divide-zinc-800/50">
                                                {notifications.map((notification) => (
                                                    <li
                                                        key={notification.id}
                                                        className={`p-3 hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors cursor-pointer ${!notification.read ? 'bg-indigo-50/30 dark:bg-indigo-900/10' : ''}`}
                                                    >
                                                        <div className="flex gap-3">
                                                            <div className={`mt-1 h-2 w-2 rounded-full flex-shrink-0 shadow-sm ${!notification.read ? 'bg-indigo-500' : 'bg-gray-300 dark:bg-zinc-600'}`}></div>
                                                            <div>
                                                                <p className={`text-sm ${!notification.read ? 'font-medium text-gray-900 dark:text-white' : 'text-gray-600 dark:text-gray-400'}`}>
                                                                    {notification.text}
                                                                </p>
                                                                <p className="text-xs text-gray-400 mt-1">{notification.time}</p>
                                                            </div>
                                                        </div>
                                                    </li>
                                                ))}
                                            </ul>
                                        ) : (
                                            <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                                                No notifications
                                            </div>
                                        )}
                                    </div>
                                    <div className="p-2 bg-gray-50/50 dark:bg-zinc-800/50 text-center">
                                        <button
                                            onClick={handleMarkAllRead}
                                            className="text-xs font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 transition-colors"
                                        >
                                            Mark all as read
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </header>
                <div className="p-4 md:p-8">
                    {children}
                </div>
            </main>
        </div>
    );
}
