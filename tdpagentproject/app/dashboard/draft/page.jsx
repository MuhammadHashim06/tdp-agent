'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '../../../lib/api';
import { RefreshCw, FileText, ExternalLink, Eye, Hash, Activity, Clock, ArrowUp, ArrowDown } from 'lucide-react';

export default function DraftsPage() {
    const [drafts, setDrafts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [sortConfig, setSortConfig] = useState({ key: 'created_at', direction: 'desc' });

    useEffect(() => {
        fetchDrafts();
    }, []);

    const fetchDrafts = async () => {
        try {
            setLoading(true);
            const data = await api.getDrafts();
            setDrafts(data.items || []);
        } catch (err) {
            setError('Failed to fetch drafts');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleSort = (key) => {
        setSortConfig((current) => ({
            key,
            direction: current.key === key && current.direction === 'desc' ? 'asc' : 'desc',
        }));
    };

    const sortedDrafts = [...drafts].sort((a, b) => {
        if (sortConfig.key === 'created_at') {
            const dateA = new Date(a.created_at);
            const dateB = new Date(b.created_at);
            return sortConfig.direction === 'asc' ? dateA - dateB : dateB - dateA;
        }
        if (sortConfig.key === 'kind') {
            const valA = (a.kind || '').toLowerCase();
            const valB = (b.kind || '').toLowerCase();
            if (valA < valB) return sortConfig.direction === 'asc' ? -1 : 1;
            if (valA > valB) return sortConfig.direction === 'asc' ? 1 : -1;
            return 0;
        }
        return 0;
    });

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="text-center text-red-500 p-8">
                {error}
                <button
                    onClick={fetchDrafts}
                    className="ml-4 text-indigo-600 hover:underline"
                >
                    Retry
                </button>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-xl font-semibold text-gray-900 dark:text-white">Drafts</h1>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Manage and track generated drafts.</p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={fetchDrafts}
                        className="flex items-center gap-2 px-3 py-2 bg-white dark:bg-zinc-800 border border-gray-300 dark:border-zinc-700 rounded-lg text-sm font-medium hover:bg-gray-50 dark:hover:bg-zinc-700 transition-colors"
                        disabled={loading}
                    >
                        <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                        Refresh
                    </button>
                </div>
            </div>

            <div className="bg-white dark:bg-zinc-900 shadow-sm rounded-xl overflow-hidden border border-gray-200 dark:border-zinc-800">
                <div className="p-4 flex gap-4 items-center border-b border-gray-100 dark:border-zinc-800">
                    <span className="text-xs text-gray-500 font-medium uppercase tracking-wide">Sort by:</span>
                    <button
                        onClick={() => handleSort('created_at')}
                        className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors border ${sortConfig.key === 'created_at'
                            ? 'bg-indigo-50 border-indigo-200 text-indigo-700 dark:bg-indigo-900/30 dark:border-indigo-800 dark:text-indigo-300 shadow-sm'
                            : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50 dark:bg-zinc-800 dark:border-zinc-700 dark:text-gray-300'}`}
                    >
                        <Clock size={12} />
                        Date
                        {sortConfig.key === 'created_at' && (sortConfig.direction === 'asc' ? <ArrowUp size={12} /> : <ArrowDown size={12} />)}
                    </button>
                    <button
                        onClick={() => handleSort('kind')}
                        className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors border ${sortConfig.key === 'kind'
                            ? 'bg-indigo-50 border-indigo-200 text-indigo-700 dark:bg-indigo-900/30 dark:border-indigo-800 dark:text-indigo-300 shadow-sm'
                            : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50 dark:bg-zinc-800 dark:border-zinc-700 dark:text-gray-300'}`}
                    >
                        <FileText size={12} />
                        Kind
                        {sortConfig.key === 'kind' && (sortConfig.direction === 'asc' ? <ArrowUp size={12} /> : <ArrowDown size={12} />)}
                    </button>
                </div>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-zinc-800">
                        <thead className="bg-gray-50/80 dark:bg-zinc-800/80 backend-blur-sm">
                            <tr>
                                <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider w-20">
                                    <div className="flex items-center gap-1"><Hash size={12} /> ID</div>
                                </th>
                                <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                    <div className="flex items-center gap-1"><FileText size={12} /> Kind / Tone</div>
                                </th>
                                <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider w-32">
                                    <div className="flex items-center gap-1"><Activity size={12} /> Status</div>
                                </th>
                                <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider w-32">
                                    <div className="flex items-center gap-1"><Clock size={12} /> Created</div>
                                </th>
                                <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider w-24">
                                    Action
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-zinc-900 divide-y divide-gray-200 dark:divide-zinc-800">
                            {sortedDrafts.map((draft) => (
                                <tr key={draft.id} className="hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors group">
                                    <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 align-top">
                                        <span className="font-mono text-xs">#{draft.id}</span>
                                    </td>
                                    <td className="px-4 py-3 text-sm align-top">
                                        <div className="font-medium text-gray-900 dark:text-white capitalize flex items-center gap-2">
                                            {draft.kind}
                                        </div>
                                        <div className="text-xs text-gray-500 dark:text-gray-400 capitalize mt-0.5 px-1.5 py-0.5 bg-gray-100 dark:bg-zinc-800 rounded inline-block">
                                            {draft.tone}
                                        </div>
                                    </td>
                                    <td className="px-4 py-3 align-top">
                                        <span className="px-2 py-1 inline-flex text-xs leading-4 font-semibold rounded-md bg-yellow-50 text-yellow-700 border border-yellow-100 dark:bg-yellow-900/30 dark:text-yellow-400 dark:border-yellow-900/50 capitalize">
                                            {draft.status}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 align-top">
                                        <div className="flex flex-col">
                                            <span>{new Date(draft.created_at).toLocaleDateString()}</span>
                                            <span className="text-xs text-gray-400">{new Date(draft.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3 text-sm font-medium align-top">
                                        <div className="flex items-center gap-2">
                                            <Link
                                                href={`/dashboard/draft/${draft.id}`}
                                                className="p-1.5 text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 dark:text-gray-400 dark:hover:text-indigo-400 dark:hover:bg-indigo-900/30 rounded-md transition-colors"
                                                title="View Draft"
                                            >
                                                <Eye size={16} />
                                            </Link>
                                            {draft.graph_draft_web_link && (
                                                <a
                                                    href={draft.graph_draft_web_link}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 dark:text-gray-400 dark:hover:text-blue-400 dark:hover:bg-blue-900/30 rounded-md transition-colors"
                                                    title="Open in Outlook"
                                                >
                                                    <ExternalLink size={16} />
                                                </a>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                <div className="px-4 py-3 border-t border-gray-100 dark:border-zinc-800 flex justify-between items-center bg-gray-50/50 dark:bg-zinc-800/10">
                    <span className="text-xs text-gray-500">Showing {sortedDrafts.length} records</span>
                    <div className="flex gap-2">
                        <button className="px-2.5 py-1.5 border border-gray-300 dark:border-zinc-700 rounded-md text-xs hover:bg-white dark:hover:bg-zinc-700 disabled:opacity-50 transition-colors" disabled>Previous</button>
                        <button className="px-2.5 py-1.5 border border-gray-300 dark:border-zinc-700 rounded-md text-xs hover:bg-white dark:hover:bg-zinc-700 disabled:opacity-50 transition-colors" disabled>Next</button>
                    </div>
                </div>
            </div>
        </div>
    );
}
