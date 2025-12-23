'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '../../../lib/api';

export default function DraftsPage() {
    const [drafts, setDrafts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

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
                <p className="text-sm text-gray-500 dark:text-gray-400">Manage and track generated drafts.</p>
                <div className="flex gap-2">
                    <button onClick={fetchDrafts} className="px-4 py-2 bg-white dark:bg-zinc-800 border border-gray-300 dark:border-zinc-700 rounded-md text-sm font-medium hover:bg-gray-50 dark:hover:bg-zinc-700">
                        🔄 Refresh
                    </button>
                </div>
            </div>

            <div className="bg-white dark:bg-zinc-900 shadow-md rounded-xl overflow-hidden border border-gray-100 dark:border-zinc-800/50">
                <div className="p-4 flex gap-2">
                    {['All', 'Generated', 'Pending', 'Sent'].map((tab) => (
                        <button key={tab} className={`px-3 py-1 text-sm rounded-full ${tab === 'All' ? 'bg-gray-100 dark:bg-zinc-800 font-semibold' : 'text-gray-500 hover:bg-gray-50 dark:hover:bg-zinc-800'}`}>
                            {tab}
                        </button>
                    ))}
                    <div className="ml-auto flex gap-2">
                        <input type="text" placeholder="Search drafts..." className="px-3 py-1 border border-gray-300 dark:border-zinc-700 rounded-md text-sm bg-transparent" />
                    </div>
                </div>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-zinc-800">
                        <thead className="bg-gray-50 dark:bg-zinc-800/50">
                            <tr>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">ID</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">KIND / TONE</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">STATUS</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">CREATED AT</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">ACTION</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-zinc-900 divide-y divide-gray-200 dark:divide-zinc-800">
                            {drafts.map((draft) => (
                                <tr key={draft.id} className="hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                        <span className="bg-gray-100 dark:bg-zinc-800 px-2 py-0.5 rounded text-xs font-mono">
                                            #{draft.id}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                                        <div className="font-medium text-gray-900 dark:text-white capitalize">{draft.kind}</div>
                                        <div className="text-xs text-gray-500 dark:text-gray-400 capitalize">{draft.tone}</div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className="px-2 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300 capitalize">
                                            {draft.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                        {new Date(draft.created_at).toLocaleDateString()} <span className="text-xs text-gray-400">{new Date(draft.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                        <div className="flex gap-3">
                                            <Link href={`/dashboard/draft/${draft.id}`} className="text-indigo-600 hover:text-indigo-900 dark:text-indigo-400 dark:hover:text-indigo-300 hover:underline">
                                                View
                                            </Link>
                                            {draft.graph_draft_web_link && (
                                                <a
                                                    href={draft.graph_draft_web_link}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                                                    title="Open in Outlook"
                                                >
                                                    ↗ Outlook
                                                </a>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                <div className="px-6 py-3 flex justify-between items-center text-sm text-gray-500">
                    <span>Showing {drafts.length} records</span>
                    <div className="flex gap-1">
                        <button className="px-2 py-1 border rounded hover:bg-gray-50 disabled:opacity-50" disabled>Previous</button>
                        <button className="px-2 py-1 border rounded hover:bg-gray-50 disabled:opacity-50" disabled>Next</button>
                    </div>
                </div>
            </div>
        </div>
    );
}
