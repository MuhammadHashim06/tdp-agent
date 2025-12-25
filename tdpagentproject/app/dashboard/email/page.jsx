'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '../../../lib/api';
import { RefreshCw, Search, Hash, User, FileText, Clock, Eye, Filter, X } from 'lucide-react';

export default function EmailListPage() {
    const [emails, setEmails] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [activeFilters, setActiveFilters] = useState([]);

    const FILTER_OPTIONS = [
        { label: '@revivalhhc.org', value: 'revivalhhc.org', type: 'domain' },
        { label: '@primehhs.com', value: 'primehhs.com', type: 'domain' },
        { label: '@extendedhc.net', value: 'extendedhc.net', type: 'domain' },
        { label: '@ehcny.org', value: 'ehcny.org', type: 'domain' },
        { label: '@Americareny.com', value: 'Americareny.com', type: 'domain' },
        { label: 'schedulingtdp', value: 'schedulingtdp@therapydepotonline.com', type: 'email' },
        { label: 'services', value: 'services@therapydepotonline.com', type: 'email' },
        { label: 'staffing', value: 'staffing@therapydepotonline.com', type: 'email' },
    ];

    const toggleFilter = (filterValue) => {
        setActiveFilters(prev =>
            prev.includes(filterValue)
                ? prev.filter(f => f !== filterValue)
                : [...prev, filterValue]
        );
    };

    useEffect(() => {
        fetchEmails();
    }, []);

    const fetchEmails = async () => {
        try {
            setLoading(true);
            try {
                const data = await api.getEmails();
                console.log('Fetched emails:', data);
                setEmails(data.items || data || []);
            } catch (err) {
                console.warn('API failed, using mock data for demo', err);
                const mockEmails = [
                    {
                        "id": 30,
                        "subject": "RE: [External]Re: NOVICK, RITA",
                        "sender": "rdixon@revivalhhc.org",
                        "sender_name": "Rockell Dixon",
                        "received_datetime": "2025-12-22T19:34:59Z",
                        "message_id": "AQMkAGRlOTU4ZjE3LThkNjEtNDI4Yy1iNTBkLThkYjUxNzZiZGNmZQBGAAAD7fqkX7yfyEKUW_XunuYi2QcAQ4ScmgzzRkmKzjXyShrrUwAAAgEMAAAAQ4ScmgzzRkmKzjXyShrrUwABQeiXEAAAAA==",
                        "internet_message_id": "<PH7PR08MB8178A2D74D3F1B2DCBDED8A6B8B4A@PH7PR08MB8178.namprd08.prod.outlook.com>",
                        "conversation_id": "AAQkAGRlOTU4ZjE3LThkNjEtNDI4Yy1iNTBkLThkYjUxNzZiZGNmZQAQAPco0A3oziZKmfTDJYVL4sM="
                    },
                    {
                        "id": 29,
                        "subject": "RE: [External]Re: NOVICK, RITA",
                        "sender": "jbencomo@revivalhhc.org",
                        "sender_name": "Jeannette Bencomo",
                        "received_datetime": "2025-12-22T19:37:46Z",
                        "message_id": "AQMkAGRlOTU4ZjE3LThkNjEtNDI4Yy1iNTBkLThkYjUxNzZiZGNmZQBGAAAD7fqkX7yfyEKUW_XunuYi2QcAQ4ScmgzzRkmKzjXyShrrUwAAAgEMAAAAQ4ScmgzzRkmKzjXyShrrUwABQeiXEQAAAA==",
                        "internet_message_id": "<DM4PR08MB8247AA97D241E6A695A4E4B6B3B4A@DM4PR08MB8247.namprd08.prod.outlook.com>",
                        "conversation_id": "AAQkAGRlOTU4ZjE3LThkNjEtNDI4Yy1iNTBkLThkYjUxNzZiZGNmZQAQAPco0A3oziZKmfTDJYVL4sM="
                    },
                    {
                        "id": 28,
                        "subject": "RE: [External]Re: NOVICK, RITA",
                        "sender": "jbencomo@revivalhhc.org",
                        "sender_name": "Jeannette Bencomo",
                        "received_datetime": "2025-12-22T19:44:05Z",
                        "message_id": "AQMkAGRlOTU4ZjE3LThkNjEtNDI4Yy1iNTBkLThkYjUxNzZiZGNmZQBGAAAD7fqkX7yfyEKUW_XunuYi2QcAQ4ScmgzzRkmKzjXyShrrUwAAAgEMAAAAQ4ScmgzzRkmKzjXyShrrUwABQeiXEgAAAA==",
                        "internet_message_id": "<DM4PR08MB8247707D0781BEC981BA2DC0B3B4A@DM4PR08MB8247.namprd08.prod.outlook.com>",
                        "conversation_id": "AAQkAGRlOTU4ZjE3LThkNjEtNDI4Yy1iNTBkLThkYjUxNzZiZGNmZQAQAPco0A3oziZKmfTDJYVL4sM="
                    },
                    {
                        "id": 27,
                        "subject": "RE: [External]Re: NOVICK, RITA",
                        "sender": "rdixon@revivalhhc.org",
                        "sender_name": "Rockell Dixon",
                        "received_datetime": "2025-12-22T19:44:17Z",
                        "message_id": "AQMkAGRlOTU4ZjE3LThkNjEtNDI4Yy1iNTBkLThkYjUxNzZiZGNmZQBGAAAD7fqkX7yfyEKUW_XunuYi2QcAQ4ScmgzzRkmKzjXyShrrUwAAAgEMAAAAQ4ScmgzzRkmKzjXyShrrUwABQeiXEwAAAA==",
                        "internet_message_id": "<PH7PR08MB8178B1696A847D9BD24FE56EB8B4A@PH7PR08MB8178.namprd08.prod.outlook.com>",
                        "conversation_id": "AAQkAGRlOTU4ZjE3LThkNjEtNDI4Yy1iNTBkLThkYjUxNzZiZGNmZQAQAPco0A3oziZKmfTDJYVL4sM="
                    }
                ];
                setEmails(mockEmails);
            }
        } catch (err) {
            setError('Failed to load emails');
        } finally {
            setLoading(false);
        }
    };

    const filteredEmails = emails.filter(email => {
        const term = searchTerm.toLowerCase();
        const matchesSearch = (
            (email.sender_name && email.sender_name.toLowerCase().includes(term)) ||
            (email.sender && email.sender.toLowerCase().includes(term)) ||
            (email.subject && email.subject.toLowerCase().includes(term))
        );

        if (activeFilters.length > 0) {
            const matchesFilter = activeFilters.some(filter => {
                const isEmailFilter = filter.includes('@therapydepotonline.com');
                if (isEmailFilter) {
                    return email.sender === filter; // Exact match for specific mailboxes
                } else {
                    return email.sender && email.sender.endsWith(filter); // Domain match
                }
            });
            return matchesSearch && matchesFilter;
        }

        return matchesSearch;
    });

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
            </div>
        );
    }

    if (error) {
        return <div className="text-red-500 text-center p-4">{error}</div>;
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-xl font-semibold text-gray-900 dark:text-white">Emails</h1>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Manage and track emails.</p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={fetchEmails}
                        className="flex items-center gap-2 px-3 py-2 bg-white dark:bg-zinc-800 border border-gray-300 dark:border-zinc-700 rounded-lg text-sm font-medium hover:bg-gray-50 dark:hover:bg-zinc-700 transition-colors"
                        disabled={loading}
                    >
                        <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                        Refresh
                    </button>
                    {/* Optional Compose button if needed later */}
                    {/* <button className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700">
                        + Compose
                    </button> */}
                </div>
            </div>

            <div className="bg-white dark:bg-zinc-900 shadow-sm rounded-xl overflow-hidden border border-gray-200 dark:border-zinc-800">
                {/* Filters and Search Bar */}
                <div className="p-4 border-b border-gray-100 dark:border-zinc-800 flex flex-col gap-4">
                    {/* Search Bar */}
                    <div className="relative w-full">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <Search size={14} className="text-gray-400" />
                        </div>
                        <input
                            type="text"
                            placeholder="Search emails by sender or subject..."
                            className="block w-full pl-9 pr-3 py-2 border border-gray-300 dark:border-zinc-700 rounded-lg text-sm bg-gray-50 dark:bg-zinc-800/50 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>

                    {/* Filter Pills */}
                    <div className="flex flex-wrap gap-2 w-full">
                        {FILTER_OPTIONS.map(option => (
                            <button
                                key={option.value}
                                onClick={() => toggleFilter(option.value)}
                                className={`px-3 py-1.5 text-xs font-medium rounded-full transition-all border ${activeFilters.includes(option.value)
                                    ? 'bg-indigo-50 border-indigo-200 text-indigo-700 dark:bg-indigo-900/30 dark:border-indigo-800 dark:text-indigo-300 shadow-sm'
                                    : 'bg-transparent border-transparent text-gray-500 hover:bg-gray-50 hover:text-gray-700 dark:hover:bg-zinc-800 dark:text-gray-400'
                                    }`}
                            >
                                {option.label}
                            </button>
                        ))}
                        {activeFilters.length > 0 && (
                            <button
                                onClick={() => setActiveFilters([])}
                                className="px-3 py-1.5 rounded-full text-xs font-medium text-gray-500 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors flex items-center gap-1"
                            >
                                <X size={14} />
                                Clear
                            </button>
                        )}
                    </div>
                </div>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-zinc-800">
                        <thead className="bg-gray-50/80 dark:bg-zinc-800/80 backend-blur-sm">
                            <tr>
                                <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider w-20">
                                    <div className="flex items-center gap-1"><Hash size={12} /> ID</div>
                                </th>
                                <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider max-w-[200px]">
                                    <div className="flex items-center gap-1"><User size={12} /> Sender</div>
                                </th>
                                <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider max-w-[300px]">
                                    <div className="flex items-center gap-1"><FileText size={12} /> Subject</div>
                                </th>
                                <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider w-32">
                                    <div className="flex items-center gap-1"><Clock size={12} /> Received</div>
                                </th>
                                <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider w-20">
                                    Action
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-zinc-900 divide-y divide-gray-200 dark:divide-zinc-800">
                            {filteredEmails.map((email) => (
                                <tr key={email.id} className="hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors group">
                                    <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 align-top">
                                        <span className="font-mono text-xs">{email.id}</span>
                                    </td>
                                    <td className="px-4 py-3 text-sm text-gray-900 dark:text-white align-top max-w-[200px]">
                                        <div className="break-words font-medium">{email.sender_name}</div>
                                        <div className="text-xs text-gray-500 dark:text-gray-400 break-all">{email.sender}</div>
                                    </td>
                                    <td className="px-4 py-3 text-sm text-gray-900 dark:text-white align-top max-w-[300px]">
                                        <div className="break-words font-medium line-clamp-2" title={email.subject}>
                                            <Link href={`/dashboard/email/${email.id}`} className="hover:text-indigo-600 dark:hover:text-indigo-400">
                                                {email.subject}
                                            </Link>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 align-top">
                                        <div className="flex flex-col">
                                            <span>{new Date(email.received_datetime).toLocaleDateString()}</span>
                                            <span className="text-xs text-gray-400">{new Date(email.received_datetime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3 text-sm text-indigo-500 dark:text-indigo-400 align-top">
                                        <Link href={`/dashboard/email/${email.id}`} className="inline-flex items-center justify-center p-2 rounded-lg hover:bg-indigo-50 dark:hover:bg-indigo-900/30 transition-colors" title="View Email">
                                            <Eye size={16} />
                                        </Link>
                                    </td>
                                </tr>
                            ))}
                            {filteredEmails.length === 0 && (
                                <tr>
                                    <td colSpan="5" className="px-6 py-12 text-center text-gray-500 dark:text-gray-400">
                                        <div className="flex flex-col items-center gap-2">
                                            <Search size={32} className="text-gray-300" />
                                            <p>No emails found matching "{searchTerm}"</p>
                                        </div>
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
                <div className="px-4 py-3 border-t border-gray-100 dark:border-zinc-800 flex justify-between items-center bg-gray-50/50 dark:bg-zinc-800/10">
                    <span className="text-xs text-gray-500">Showing {filteredEmails.length} records</span>
                    <div className="flex gap-2">
                        <button className="px-2.5 py-1.5 border border-gray-300 dark:border-zinc-700 rounded-md text-xs hover:bg-white dark:hover:bg-zinc-700 disabled:opacity-50 transition-colors" disabled>Previous</button>
                        <button className="px-2.5 py-1.5 border border-gray-300 dark:border-zinc-700 rounded-md text-xs hover:bg-white dark:hover:bg-zinc-700 disabled:opacity-50 transition-colors" disabled>Next</button>
                    </div>
                </div>
            </div>
        </div>
    );
}
