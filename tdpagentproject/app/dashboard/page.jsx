'use client';

import { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import Link from 'next/link';
import { Mail, Briefcase, FileText, Bell, TrendingUp, Activity, Clock, ArrowUpRight, CheckCircle, AlertCircle, Calendar } from 'lucide-react';

export default function DashboardPage() {
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState([
        { name: 'Total Emails', value: '-', change: '...', type: 'neutral', icon: Mail, color: 'blue' },
        { name: 'Active Cases', value: '-', change: '...', type: 'neutral', icon: Briefcase, color: 'purple' },
        { name: 'Pending Drafts', value: '-', change: '...', type: 'neutral', icon: FileText, color: 'amber' },
        { name: 'Notifications', value: '-', change: '...', type: 'neutral', icon: Bell, color: 'pink' },
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
                    { name: 'Total Emails', value: totalEmails.toString(), icon: Mail, color: 'blue' },
                    { name: 'Active Cases', value: activeCases.toString(), icon: Briefcase, color: 'purple' },
                    { name: 'Pending Drafts', value: pendingDrafts.toString(), icon: FileText, color: 'amber' },
                    { name: 'Alerts', value: newNotifications.toString(), icon: Bell, color: 'pink' },
                ]);

                // 2. Activity Graph (Last 7 Days)
                const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
                const activityMap = new Map();
                const now = new Date();
                const sevenDaysAgo = new Date(now);
                sevenDaysAgo.setDate(now.getDate() - 6);
                sevenDaysAgo.setHours(0, 0, 0, 0); // Start of the 7th day ago

                // Initialize last 7 days
                for (let i = 6; i >= 0; i--) {
                    const d = new Date(now);
                    d.setDate(d.getDate() - i);
                    const dayName = days[d.getDay()];
                    // Use a unique key like 'MM-DD-Day' to reliably map, but for simplicity with visual graph assuming 1 week:
                    // Reset counts
                    activityMap.set(dayName, { day: dayName, emails: 0, cases: 0 });
                }

                // Populate emails
                emails.forEach(e => {
                    const date = new Date(e.received_datetime);
                    if (date >= sevenDaysAgo) {
                        const dayName = days[date.getDay()];
                        if (activityMap.has(dayName)) {
                            activityMap.get(dayName).emails++;
                        }
                    }
                });

                // Populate cases
                cases.forEach(c => {
                    // Try to resolve date: created_at -> updated_at -> seed_email date
                    let dateStr = c.created_at || c.updated_at || c.received_datetime;

                    if (!dateStr && c.metadata?.seed_email_id) {
                        const seedId = c.metadata.seed_email_id;
                        // Note: emails array might be mix of strings/numbers for ID, handle safely
                        const foundEmail = emails.find(e => e.id == seedId);
                        if (foundEmail) {
                            dateStr = foundEmail.received_datetime;
                        }
                    }

                    if (dateStr) {
                        const date = new Date(dateStr);
                        if (date >= sevenDaysAgo) {
                            const dayName = days[date.getDay()];
                            if (activityMap.has(dayName)) {
                                activityMap.get(dayName).cases++;
                            }
                        }
                    }
                });

                setWeeklyActivity(Array.from(activityMap.values()));

                // 3. Recent Activity Feed (Merge sources)
                const activities = [
                    ...emails.map(e => ({ id: `e-${e.id}`, type: 'Email', message: `Email from ${e.sender_name || e.sender}`, time: e.received_datetime, icon: Mail, color: 'bg-blue-100 text-blue-600' })),
                    ...cases.map(c => ({ id: `c-${c.id}`, type: 'Case', message: `Case updated: ${c.title}`, time: c.created_at || c.updated_at || new Date().toISOString(), icon: Briefcase, color: 'bg-purple-100 text-purple-600' })),
                    ...drafts.map(d => ({ id: `d-${d.id}`, type: 'Draft', message: `Draft ${d.status}: ${d.kind}`, time: d.created_at, icon: FileText, color: 'bg-amber-100 text-amber-600' })),
                ];

                // Sort by time desc
                activities.sort((a, b) => new Date(b.time) - new Date(a.time));

                // Take top 5 and format time
                setRecentActivity(activities.slice(0, 5).map(a => ({
                    ...a,
                    time: new Date(a.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' ' + new Date(a.time).toLocaleDateString()
                })));

                // Helper: Resolve Case Date
                const resolveCaseDate = (c) => {
                    let dateStr = c.created_at || c.updated_at || c.received_datetime;
                    if (!dateStr && c.metadata?.seed_email_id) {
                        const foundEmail = emails.find(e => e.id == c.metadata.seed_email_id);
                        if (foundEmail) dateStr = foundEmail.received_datetime;
                    }
                    return dateStr;
                };

                // 4. Latest Cases
                setLatestCases(cases.slice(0, 5).map(c => {
                    const dateStr = resolveCaseDate(c);
                    return {
                        id: c.id,
                        title: c.title,
                        status: c.status,
                        date: dateStr ? new Date(dateStr).toLocaleDateString() : 'N/A'
                    };
                }));

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
            <div className="flex items-end justify-between h-52 gap-3 pt-6 px-2">
                {weeklyActivity.map((day) => (
                    <div key={day.day} className="flex flex-col items-center gap-3 w-full group cursor-pointer">
                        <div className="relative w-full flex gap-1.5 justify-center items-end h-40">
                            {/* Email Bar */}
                            <div
                                className="w-2.5 md:w-3 bg-blue-500 rounded-full transition-all duration-300 group-hover:bg-blue-600 group-hover:scale-y-110 origin-bottom relative shadow-sm"
                                style={{ height: `${(day.emails / maxVal) * 100}%` }}
                                title={`${day.emails} Emails`}
                            >
                            </div>
                            {/* Case Bar */}
                            <div
                                className="w-2.5 md:w-3 bg-purple-500 rounded-full transition-all duration-300 group-hover:bg-purple-600 group-hover:scale-y-110 origin-bottom relative shadow-sm opacity-80"
                                style={{ height: `${(day.cases / maxVal) * 100}%` }}
                                title={`${day.cases} Cases`}
                            >
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
        <div className="space-y-8">
            {/* Welcome Banner */}
            <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-8 text-white shadow-lg relative overflow-hidden">
                <div className="relative z-10">
                    <h1 className="text-3xl font-bold mb-2">Welcome back, Admin! 👋</h1>
                    <p className="text-indigo-100 max-w-xl">
                        Here's what's happening in your workspace today. You have <span className="font-semibold text-white">{stats.find(s => s.name === 'Pending Drafts')?.value} pending drafts</span> and <span className="font-semibold text-white">{stats.find(s => s.name === 'Active Cases')?.value} active cases</span> needing attention.
                    </p>
                </div>
                <div className="absolute right-0 top-0 h-full w-1/3 bg-white/5 skew-x-12 transform translate-x-12"></div>
                <div className="absolute right-20 bottom-0 h-32 w-32 bg-purple-500/20 rounded-full blur-2xl"></div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {stats.map((stat, idx) => {
                    const Icon = stat.icon;
                    const colors = {
                        blue: 'bg-blue-50 text-blue-600 border-blue-100 dark:bg-blue-900/20 dark:text-blue-400 dark:border-blue-900/50',
                        purple: 'bg-purple-50 text-purple-600 border-purple-100 dark:bg-purple-900/20 dark:text-purple-400 dark:border-purple-900/50',
                        amber: 'bg-amber-50 text-amber-600 border-amber-100 dark:bg-amber-900/20 dark:text-amber-400 dark:border-amber-900/50',
                        pink: 'bg-pink-50 text-pink-600 border-pink-100 dark:bg-pink-900/20 dark:text-pink-400 dark:border-pink-900/50',
                    };
                    const badgeColors = {
                        increase: 'text-green-600 bg-green-50 dark:bg-green-900/30 dark:text-green-400',
                        decrease: 'text-amber-600 bg-amber-50 dark:bg-amber-900/30 dark:text-amber-400',
                        neutral: 'text-gray-600 bg-gray-50 dark:bg-gray-800 dark:text-gray-400'
                    };

                    return (
                        <div key={stat.name} className="bg-white dark:bg-zinc-900 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-zinc-800 hover:shadow-md transition-all duration-300 group">
                            <div className="flex justify-between items-start mb-4">
                                <div className={`p-3 rounded-xl ${colors[stat.color]} transition-colors group-hover:scale-105 duration-300`}>
                                    <Icon size={24} />
                                </div>
                                {stat.change && stat.type && (
                                    <div className={`px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1 ${badgeColors[stat.type] || ''}`}>
                                        {stat.type === 'increase' && <TrendingUp size={12} />}
                                        {stat.change}
                                    </div>
                                )}
                            </div>
                            <div>
                                <h3 className="text-3xl font-bold text-gray-900 dark:text-white mb-1 tracking-tight">{stat.value}</h3>
                                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{stat.name}</p>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Content Grid: Graph & Activity */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Graph Section */}
                <div className="lg:col-span-2 bg-white dark:bg-zinc-900 p-8 rounded-2xl shadow-sm border border-gray-100 dark:border-zinc-800">
                    <div className="flex justify-between items-center mb-8">
                        <div>
                            <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                                <Activity size={20} className="text-indigo-500" />
                                Weekly Activity
                            </h3>
                            <p className="text-sm text-gray-500 mt-1">Incoming emails vs case processing</p>
                        </div>
                        <div className="flex gap-6 text-sm">
                            <div className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-full bg-blue-500 shadow-sm shadow-blue-500/50"></span>
                                <span className="font-medium text-gray-600 dark:text-gray-300">Emails</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-full bg-purple-500 shadow-sm shadow-purple-500/50"></span>
                                <span className="font-medium text-gray-600 dark:text-gray-300">Cases</span>
                            </div>
                        </div>
                    </div>
                    {weeklyActivity.length > 0 ? <ActivityGraph /> : <div className="h-52 flex items-center justify-center text-gray-400 text-sm italic">No activity data available</div>}
                </div>

                {/* Recent Activity Section */}
                <div className="bg-white dark:bg-zinc-900 p-8 rounded-2xl shadow-sm border border-gray-100 dark:border-zinc-800">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                            <Clock size={20} className="text-amber-500" />
                            Recent Activity
                        </h3>
                        <Link href="/dashboard/cases" className="text-xs font-semibold text-indigo-600 hover:text-indigo-500 uppercase tracking-wide">View All</Link>
                    </div>
                    <div className="flow-root">
                        <ul role="list" className="-my-5 divide-y divide-gray-100 dark:divide-zinc-800/50">
                            {recentActivity.map((activity) => {
                                const ItemIcon = activity.icon;
                                return (
                                    <li key={activity.id} className="py-5">
                                        <div className="flex items-start space-x-4">
                                            <div className={`flex-shrink-0 p-2 rounded-full ${activity.color}`}>
                                                <ItemIcon size={16} />
                                            </div>
                                            <div className="flex-1 min-w-0 pt-0.5">
                                                <p className="text-sm font-medium text-gray-900 dark:text-white truncate" title={activity.message}>
                                                    {activity.message}
                                                </p>
                                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                                                    {activity.time}
                                                </p>
                                            </div>
                                        </div>
                                    </li>
                                );
                            })}
                            {recentActivity.length === 0 && (
                                <li className="py-8 text-center text-gray-400 text-sm italic">No recent activity found</li>
                            )}
                        </ul>
                    </div>
                </div>
            </div>

            {/* Recent Cases Table */}
            <div className="bg-white dark:bg-zinc-900 rounded-2xl shadow-sm border border-gray-100 dark:border-zinc-800 overflow-hidden">
                <div className="p-6 border-b border-gray-100 dark:border-zinc-800 flex justify-between items-center bg-gray-50/50 dark:bg-zinc-800/20">
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                        <Briefcase size={20} className="text-gray-500" />
                        Latest Cases
                    </h3>
                    <Link href="/dashboard/cases" className="text-sm font-medium text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 flex items-center gap-1">
                        View all cases <ArrowUpRight size={16} />
                    </Link>
                </div>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-zinc-800">
                        <thead className="bg-gray-50 dark:bg-zinc-800/50">
                            <tr>
                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">ID</th>
                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Title / Patient</th>
                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Date</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-zinc-900 divide-y divide-gray-200 dark:divide-zinc-800">
                            {latestCases.map((item) => (
                                <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors group">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-indigo-600 dark:text-indigo-400">
                                        <Link href={`/dashboard/cases/${item.id}`} className="hover:underline flex items-center gap-1">
                                            #{item.id}
                                        </Link>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white max-w-xs truncate">
                                        {item.title}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full capitalize
                                            ${item.status === 'new' ? 'bg-blue-100 text-blue-800 border border-blue-200' :
                                                item.status === 'active' ? 'bg-green-100 text-green-800 border border-green-200' :
                                                    'bg-gray-100 text-gray-800 border border-gray-200'
                                            }`}>
                                            {item.status === 'active' && <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></div>}
                                            {item.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 flex items-center gap-2">
                                        <Calendar size={14} className="text-gray-400" />
                                        {item.date}
                                    </td>
                                </tr>
                            ))}
                            {latestCases.length === 0 && (
                                <tr>
                                    <td colSpan="4" className="px-6 py-8 text-center text-gray-500 text-sm flex flex-col items-center justify-center gap-2">
                                        <div className="p-3 bg-gray-100 rounded-full dark:bg-zinc-800">
                                            <Briefcase size={24} className="text-gray-400" />
                                        </div>
                                        <p>No recent cases found</p>
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
