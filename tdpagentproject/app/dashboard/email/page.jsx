'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '../../../lib/api';

export default function EmailListPage() {
    const [emails, setEmails] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

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
                <p className="text-sm text-gray-500 dark:text-gray-400">Manage and track emails.</p>
                <div className="flex gap-2">
                    <button onClick={fetchEmails} className="px-4 py-2 bg-white dark:bg-zinc-800 border border-gray-300 dark:border-zinc-700 rounded-md text-sm font-medium hover:bg-gray-50 dark:hover:bg-zinc-700">
                        🔄 Refresh
                    </button>
                    {/* Optional Compose button if needed later */}
                    {/* <button className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700">
                        + Compose
                    </button> */}
                </div>
            </div>

            <div className="bg-white dark:bg-zinc-900 shadow-md rounded-xl overflow-hidden border border-gray-100 dark:border-zinc-800/50">
                <div className="p-4 flex gap-2">
                    {['All', 'Inbox', 'Sent', 'Drafts', 'Trash'].map((tab) => (
                        <button key={tab} className={`px-3 py-1 text-sm rounded-full ${tab === 'All' ? 'bg-gray-100 dark:bg-zinc-800 font-semibold' : 'text-gray-500 hover:bg-gray-50 dark:hover:bg-zinc-800'}`}>
                            {tab}
                        </button>
                    ))}
                    <div className="ml-auto flex gap-2">
                        <input type="text" placeholder="Search emails..." className="px-3 py-1 border border-gray-300 dark:border-zinc-700 rounded-md text-sm bg-transparent" />
                    </div>
                </div>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-zinc-800">
                        <thead className="bg-gray-50 dark:bg-zinc-800/50">
                            <tr>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">ID</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">SENDER</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">SUBJECT</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">RECEIVED</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">ACTION</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-zinc-900 divide-y divide-gray-200 dark:divide-zinc-800">
                            {emails.map((email) => (
                                <tr key={email.id} className="hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                        <span className="bg-gray-100 dark:bg-zinc-800 px-2 py-0.5 rounded text-xs font-mono">
                                            {email.id}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                                        <div className="font-medium">{email.sender_name}</div>
                                        <div className="text-xs text-gray-500 dark:text-gray-400">{email.sender}</div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white max-w-md truncate" title={email.subject}>
                                        <Link href={`/dashboard/email/${email.id}`} className="hover:text-indigo-600 hover:underline cursor-pointer font-medium">
                                            {email.subject}
                                        </Link>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                        {new Date(email.received_datetime).toLocaleDateString()} <span className="text-xs text-gray-400">{new Date(email.received_datetime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-indigo-500 dark:text-indigo-400">
                                        <Link href={`/dashboard/email/${email.id}`} className="hover:underline">
                                            View
                                        </Link>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                <div className="px-6 py-3 flex justify-between items-center text-sm text-gray-500">
                    <span>Showing {emails.length} records</span>
                    <div className="flex gap-1">
                        <button className="px-2 py-1 border rounded hover:bg-gray-50 disabled:opacity-50" disabled>Previous</button>
                        <button className="px-2 py-1 border rounded hover:bg-gray-50 disabled:opacity-50" disabled>Next</button>
                    </div>
                </div>
            </div>
        </div>
    );
}
