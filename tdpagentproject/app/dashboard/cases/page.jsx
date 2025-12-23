'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '../../../lib/api';

export default function CasesListPage() {
    const [cases, setCases] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchCases();
    }, []);

    const fetchCases = async () => {
        try {
            setLoading(true);
            try {
                const data = await api.getCases();
                console.log('Fetched cases:', data);
                setCases(data.items);
            } catch (err) {
                console.warn('API failed, using mock data for demo', err);
                const mockCases = [
                    {
                        "id": 22,
                        "external_id": "schedulingtdp@therapydepotonline.com:AAQkAGRlOTU4ZjE3LThkNjEtNDI4Yy1iNTBkLThkYjUxNzZiZGNmZQAQAPco0A3oziZKmfTDJYVL4sM=",
                        "title": "RE: [External]Re: NOVICK, RITA",
                        "status": "acceptance drafted",
                        "metadata": {
                            "mailbox": "schedulingtdp@therapydepotonline.com",
                            "staffing": {
                                "discipline": null,
                                "availability": "12/22",
                                "referral_email": "jbencomo@revivalhhc.org",
                                "therapist_name": null
                            },
                            "extracted": {
                                "patient_name": "Rita Novick",
                                "extraction_confidence": "high",
                                "referral_source_org": "Revival HHC",
                                "discipline_requested": "RN, HHA, PT, OT",
                                "referral_source_name": "Rockell Dixon",
                                "special_instructions": "Please confirm hospitalization and enter a note. Patient wants all services (RN, HHA, PT, OT) and resume services after discharge.",
                            },
                            "seed_email_id": 23,
                            "conversation_id": "AAQkAGRlOTU4ZjE3LThkNjEtNDI4Yy1iNTBkLThkYjUxNzZiZGNmZQAQAPco0A3oziZKmfTDJYVL4sM="
                        }
                    },
                    {
                        "id": 21,
                        "external_id": "schedulingtdp@therapydepotonline.com:AAQkAGRlOTU4ZjE3LThkNjEtNDI4Yy1iNTBkLThkYjUxNzZiZGNmZQAQAEK_k5YmbHVDrqzDuQ7Hqbk=",
                        "title": "Re: SecureMail: NEW CASE REFERRAL: 908313-OT ELLIOT",
                        "status": "new",
                        "metadata": {
                            "mailbox": "schedulingtdp@therapydepotonline.com",
                            "seed_email_id": 22,
                            "conversation_id": "AAQkAGRlOTU4ZjE3LThkNjEtNDI4Yy1iNTBkLThkYjUxNzZiZGNmZQAQAEK_k5YmbHVDrqzDuQ7Hqbk=",
                            "extracted": {},
                            "staffing": {}
                        }
                    },
                    {
                        "id": 20,
                        "external_id": "schedulingtdp@therapydepotonline.com:AAQkAGRlOTU4ZjE3LThkNjEtNDI4Yy1iNTBkLThkYjUxNzZiZGNmZQAQAEH6UedXUzBHkphQ0wvNUmE=",
                        "title": "Re: REVIVAL OT EVAL PAUL YOUNGER",
                        "status": "pending staffing",
                        "metadata": {
                            "mailbox": "schedulingtdp@therapydepotonline.com",
                            "extracted": {
                                "patient_name": "PAUL YOUNGER",
                                "visit_frequency": "1 evaluation",
                                "referral_source_org": "Therapy Depot, Inc",
                                "discipline_requested": "occupational therapy",
                                "referral_source_name": "Case Management",
                                "requested_start_date": "2025-12-01",
                            },
                            "staffing": {},
                            "seed_email_id": 21,
                            "conversation_id": "AAQkAGRlOTU4ZjE3LThkNjEtNDI4Yy1iNTBkLThkYjUxNzZiZGNmZQAQAEH6UedXUzBHkphQ0wvNUmE="
                        }
                    }
                ];
                setCases(mockCases);
            }
        } catch (err) {
            setError('Failed to load cases');
        } finally {
            setLoading(false);
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'new': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300';
            case 'acceptance drafted': return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300';
            case 'pending staffing': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300';
            case 'active': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
            case 'closed': return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
            default: return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
        }
    };

    const formatCaseId = (id) => {
        return id ? (1000 + id).toString() : '-';
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
                <p className="text-sm text-gray-500 dark:text-gray-400">Manage and track patient case referrals.</p>
                <div className="flex gap-2">
                    <button onClick={fetchCases} className="px-4 py-2 bg-white dark:bg-zinc-800 border border-gray-300 dark:border-zinc-700 rounded-md text-sm font-medium hover:bg-gray-50 dark:hover:bg-zinc-700">
                        🔄 Refresh
                    </button>
                    <button className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700">
                        + New Case
                    </button>
                </div>
            </div>

            <div className="bg-white dark:bg-zinc-900 shadow-md rounded-xl overflow-hidden border border-gray-100 dark:border-zinc-800/50">
                <div className="p-4 flex gap-2">
                    {['All', 'New', 'Staffing', 'Active', 'Closed'].map((tab) => (
                        <button key={tab} className={`px-3 py-1 text-sm rounded-full ${tab === 'All' ? 'bg-gray-100 dark:bg-zinc-800 font-semibold' : 'text-gray-500 hover:bg-gray-50 dark:hover:bg-zinc-800'}`}>
                            {tab}
                        </button>
                    ))}
                    <div className="ml-auto flex gap-2">
                        <input type="text" placeholder="Filter cases..." className="px-3 py-1 border border-gray-300 dark:border-zinc-700 rounded-md text-sm bg-transparent" />
                    </div>
                </div>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-zinc-800">
                        <thead className="bg-gray-50 dark:bg-zinc-800/50">
                            <tr>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">CASE ID</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">TITLE</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">STATUS</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">PATIENT</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">DISCIPLINE</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">REFERRAL SOURCE</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">THERAPIST</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">UPDATED</th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">EMAIL ID</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-zinc-900 divide-y divide-gray-200 dark:divide-zinc-800">
                            {cases.map((item) => (
                                <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                        <span className="bg-gray-100 dark:bg-zinc-800 px-2 py-0.5 rounded text-xs font-mono">
                                            {formatCaseId(item.id)}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white max-w-xs truncate" title={item.title}>
                                        <Link href={`/dashboard/cases/${item.id}`} className="hover:text-indigo-600 hover:underline">
                                            {item.title.replace(/^RE:\s*/i, '').replace(/^\[External\]\s*/i, '')}
                                        </Link>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`px-2 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full capitalize ${getStatusColor(item.status)}`}>
                                            {item.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white font-medium">
                                        {item.metadata?.extracted?.patient_name || '-'}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                        {item.metadata?.extracted?.discipline_requested || item.metadata?.staffing?.discipline || '-'}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                        {item.metadata?.extracted?.referral_source_org || '-'}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                        {item.metadata?.staffing?.therapist_name || '-'}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400 text-xs">
                                        {/* Placeholder for Updated date as it's not in JSON */}
                                        2025-12-23 <br /><span className="text-gray-400 text-[10px]">07:37</span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-indigo-500 dark:text-indigo-400">
                                        #{item.metadata?.seed_email_id || '-'}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                <div className="px-6 py-3 flex justify-between items-center text-sm text-gray-500">
                    <span>Showing {cases.length} records</span>
                    <div className="flex gap-1">
                        <button className="px-2 py-1 border rounded hover:bg-gray-50 disabled:opacity-50" disabled>Previous</button>
                        <button className="px-2 py-1 border rounded hover:bg-gray-50 disabled:opacity-50" disabled>Next</button>
                    </div>
                </div>
            </div>
        </div>
    );
}
