'use client';

import { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import Link from 'next/link';

export default function DashboardPage() {
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState([
        { name: 'Total Emails', value: '-', change: '...', type: 'neutral' },
        { name: 'Active Cases', value: '-', change: '...', type: 'neutral' },
        { name: 'Pending Drafts', value: '-', change: '...', type: 'neutral' },
        { name: 'Notifications', value: '-', change: '...', type: 'neutral' },
    ]);
    const [weeklyActivity, setWeeklyActivity] = useState([]);
    const [recentActivity, setRecentActivity] = useState([]);
    const [latestCases, setLatestCases] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const [emailsData, casesData, draftsData, notificationsData] = await Promise.allSettled([
                    api.getEmails(100), // Fetch enough for graph
                    api.getCases(100),
                    api.getDrafts(100),
                    api.getNotifications()
                ]);

                const emails = emailsData.status === 'fulfilled' ? (emailsData.value.items || []) : [];
                const cases = casesData.status === 'fulfilled' ? (casesData.value.items || []) : [];
                const drafts = draftsData.status === 'fulfilled' ? (draftsData.value.items || []) : [];
                const notifications = notificationsData.status === 'fulfilled' ? (notificationsData.value.notifications || []) : [];

                // 1. Calculate Stats
                const totalEmails = emails.length;
                const activeCases = cases.filter(c => c.status !== 'closed' && c.status !== 'Closed').length;
                const pendingDrafts = drafts.filter(d => d.status !== 'sent').length;
                const newNotifications = notifications.length;

                setStats([
                    { name: 'Total Emails', value: totalEmails.toString(), change: 'Fetched', type: 'increase' },
                    { name: 'Active Cases', value: activeCases.toString(), change: 'Current', type: 'increase' },
                    { name: 'Pending Drafts', value: pendingDrafts.toString(), change: 'Action needed', type: 'decrease' },
                    { name: 'Alerts', value: newNotifications.toString(), change: 'New updates', type: 'increase' },
                ]);

                // 2. Activity Graph (Last 7 Days)
                const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
                const activityMap = new Map();
                const now = new Date();

                // Initialize last 7 days
                for (let i = 6; i >= 0; i--) {
                    const d = new Date(now);
                    d.setDate(d.getDate() - i);
                    const dayName = days[d.getDay()];
                    activityMap.set(dayName, { day: dayName, emails: 0, cases: 0 });
                }

                // Populate emails
                emails.forEach(e => {
                    const date = new Date(e.received_datetime);
                    const dayName = days[date.getDay()];
                    if (activityMap.has(dayName)) {
                        activityMap.get(dayName).emails++;
                    }
                });

                // Populate cases
                cases.forEach(c => {
                    // Prefer created_at, fallback to updated_at or received_datetime
                    const dateStr = c.created_at || c.updated_at || c.received_datetime;
                    if (dateStr) {
                        const date = new Date(dateStr);
                        const dayName = days[date.getDay()];
                        if (activityMap.has(dayName)) {
                            activityMap.get(dayName).cases++;
                        }
                    }
                });

                setWeeklyActivity(Array.from(activityMap.values()));

                // 3. Recent Activity Feed (Merge sources)
                const activities = [
                    ...emails.map(e => ({ id: `e-${e.id}`, type: 'Email', message: `Email from ${e.sender_name || e.sender}`, time: e.received_datetime })),
                    ...cases.map(c => ({ id: `c-${c.id}`, type: 'Case', message: `Case updated: ${c.title}`, time: c.created_at || c.updated_at || new Date().toISOString() })),
                    ...drafts.map(d => ({ id: `d-${d.id}`, type: 'Draft', message: `Draft ${d.status}: ${d.kind}`, time: d.created_at })),
                ];

                // Sort by time desc
                activities.sort((a, b) => new Date(b.time) - new Date(a.time));

                // Take top 5 and format time
                setRecentActivity(activities.slice(0, 5).map(a => ({
                    ...a,
                    time: new Date(a.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' ' + new Date(a.time).toLocaleDateString()
                })));

                // 4. Latest Cases
                setLatestCases(cases.slice(0, 5).map(c => ({
                    id: c.id,
                    title: c.title,
                    status: c.status,
                    date: c.created_at ? new Date(c.created_at).toLocaleDateString() : 'N/A'
                })));

                setLoading(false);

            } catch (err) {
                console.error('Dashboard fetch failed', err);
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    // Simple Graph Component using CSS Heights
    const ActivityGraph = () => {
        // Find max value for scaling
        const maxVal = Math.max(...weeklyActivity.map(d => Math.max(d.emails, d.cases, 1)));

        return (
            <div className="flex items-end justify-between h-48 gap-2 pt-4">
                {weeklyActivity.map((day) => (
                    <div key={day.day} className="flex flex-col items-center gap-2 w-full group">
                        <div className="relative w-full flex gap-1 justify-center items-end h-32">
                            {/* Email Bar */}
                            <div
                                className="w-3 md:w-4 bg-indigo-500 rounded-t-sm transition-all duration-300 group-hover:bg-indigo-600 relative group/bar"
                                style={{ height: `${(day.emails / maxVal) * 100}%` }}
                            >
                                <div className="opacity-0 group-hover/bar:opacity-100 absolute bottom-full mb-1 left-1/2 -translate-x-1/2 bg-gray-800 text-white text-[10px] px-1 rounded pointer-events-none z-10 transition-opacity">
                                    {day.emails}
                                </div>
                            </div>
                            {/* Case Bar */}
                            <div
                                className="w-3 md:w-4 bg-purple-400 rounded-t-sm transition-all duration-300 group-hover:bg-purple-500 relative group/bar"
                                style={{ height: `${(day.cases / maxVal) * 100}%` }}
                            >
                                <div className="opacity-0 group-hover/bar:opacity-100 absolute bottom-full mb-1 left-1/2 -translate-x-1/2 bg-gray-800 text-white text-[10px] px-1 rounded pointer-events-none z-10 transition-opacity">
                                    {day.cases}
                                </div>
                            </div>
                        </div>
                        <span className="text-xs text-gray-400 font-medium">{day.day}</span>
                    </div>
                ))}
            </div>
        );
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-full min-h-[500px]">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Page Header */}
            <div>
                <h2 className="text-lg font-medium text-gray-900 dark:text-white">Overview</h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">Your daily activity summary.</p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {stats.map((stat) => (
                    <div key={stat.name} className="bg-white dark:bg-zinc-900 p-6 rounded-xl shadow-md border border-gray-100 dark:border-zinc-800/50 hover:shadow-lg transition-shadow">
                        <div className="flex justify-between items-start">
                            <div>
                                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{stat.name}</p>
                                <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">{stat.value}</p>
                            </div>
                            <span className={`px-2 py-1 text-xs font-semibold rounded-full ${stat.type === 'increase' ? 'bg-green-100 text-green-800 dark:bg-green-900/10 dark:text-green-400' : stat.type === 'decrease' ? 'bg-red-100 text-red-800 dark:bg-red-900/10 dark:text-red-400' : 'bg-gray-100 text-gray-800 dark:bg-zinc-800 dark:text-gray-300'
                                }`}>
                                {stat.change}
                            </span>
                        </div>
                    </div>
                ))}
            </div>

            {/* Content Grid: Graph & Activity */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Graph Section */}
                <div className="lg:col-span-2 bg-white dark:bg-zinc-900 p-6 rounded-xl shadow-md border border-gray-100 dark:border-zinc-800/50">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-base font-semibold text-gray-900 dark:text-white">Weekly Activity</h3>
                        <div className="flex gap-4 text-xs">
                            <div className="flex items-center gap-1">
                                <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
                                <span className="text-gray-500">Emails</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <span className="w-2 h-2 rounded-full bg-purple-400"></span>
                                <span className="text-gray-500">Cases</span>
                            </div>
                        </div>
                    </div>
                    {weeklyActivity.length > 0 ? <ActivityGraph /> : <div className="h-48 flex items-center justify-center text-gray-400 text-sm">No activity data</div>}
                    <div className="mt-4 flex justify-between items-center text-xs text-gray-400 border-t border-gray-100 dark:border-zinc-800 pt-4">
                        <span>Last updated: just now</span>
                    </div>
                </div>

                {/* Recent Activity Section */}
                <div className="bg-white dark:bg-zinc-900 p-6 rounded-xl shadow-md border border-gray-100 dark:border-zinc-800/50">
                    <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-4">Recent Activity</h3>
                    <div className="flow-root">
                        <ul role="list" className="-my-5 divide-y divide-gray-100 dark:divide-zinc-800">
                            {recentActivity.map((activity) => (
                                <li key={activity.id} className="py-4">
                                    <div className="flex items-center space-x-4">
                                        <div className="flex-shrink-0">
                                            {activity.type === 'Email' && <span className="text-xl">📧</span>}
                                            {activity.type === 'Case' && <span className="text-xl">💼</span>}
                                            {activity.type === 'Draft' && <span className="text-xl">📝</span>}
                                            {activity.type === 'System' && <span className="text-xl">⚙️</span>}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-medium text-gray-900 dark:text-white truncate" title={activity.message}>
                                                {activity.message}
                                            </p>
                                            <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                                                {activity.time}
                                            </p>
                                        </div>
                                        <div>
                                            <span className="inline-flex items-center shadow-sm px-2.5 py-0.5 border border-gray-300 dark:border-zinc-700 text-xs font-medium rounded-full text-gray-700 dark:text-gray-300 bg-white dark:bg-zinc-800">
                                                {activity.type}
                                            </span>
                                        </div>
                                    </div>
                                </li>
                            ))}
                            {recentActivity.length === 0 && (
                                <li className="py-4 text-center text-gray-500 text-sm">No recent activity</li>
                            )}
                        </ul>
                    </div>
                    <div className="mt-6">
                        <Link
                            href="/dashboard/cases" // fallback link
                            className="flex items-center justify-center w-full rounded-md bg-white dark:bg-zinc-800 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-white shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-zinc-700 hover:bg-gray-50 dark:hover:bg-zinc-700 sm:mt-0 sm:w-auto"
                        >
                            View all activity
                        </Link>
                    </div>
                </div>
            </div>

            {/* Recent Cases Table */}
            <div className="bg-white dark:bg-zinc-900 rounded-xl shadow-md border border-gray-100 dark:border-zinc-800/50 overflow-hidden">
                <div className="p-6 border-b border-gray-100 dark:border-zinc-800 flex justify-between items-center">
                    <h3 className="text-base font-semibold text-gray-900 dark:text-white">Latest Cases</h3>
                    <Link href="/dashboard/cases" className="text-sm text-indigo-600 hover:text-indigo-500 dark:text-indigo-400">View all</Link>
                </div>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-zinc-800">
                        <thead className="bg-gray-50 dark:bg-zinc-800/50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Title</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-zinc-900 divide-y divide-gray-200 dark:divide-zinc-800">
                            {latestCases.map((item) => (
                                <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        <Link href={`/dashboard/cases/${item.id}`} className="hover:underline">#{item.id}</Link>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white max-w-xs truncate">{item.title}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`px-2 py-1 text-xs rounded-full capitalize ${item.status === 'new' ? 'bg-blue-100 text-blue-800' :
                                                item.status === 'active' ? 'bg-green-100 text-green-800' :
                                                    'bg-gray-100 text-gray-800'
                                            }`}>{item.status}</span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.date}</td>
                                </tr>
                            ))}
                            {latestCases.length === 0 && (
                                <tr>
                                    <td colSpan="4" className="px-6 py-4 text-center text-gray-500 text-sm">No recent cases</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
