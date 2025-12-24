'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '../../../lib/api';
import { RefreshCw, Search, Filter, Hash, FileText, Activity, User, Clock, Mail } from 'lucide-react';

export default function CasesListPage() {
    const [cases, setCases] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [activeTab, setActiveTab] = useState('All');

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

    const filteredCases = cases.filter(item => {
        // Filter by Tab
        if (activeTab !== 'All') {
            const statusMap = {
                'New': 'new',
                'Pending Staffing': 'pending staffing',
                'Staffed': 'staffed',
                'Acceptance Drafted': 'acceptance drafted',
                'Acceptance Sent': 'acceptance sent',
                'Evaluation Completed': 'evaluation completed',
                'Authorization Pending': 'authorization pending',
                'Authorized – Treatment Started': 'authorized – treatment started',
                'Closed': 'closed'
            };

            if (item.status !== statusMap[activeTab]) return false;
        }

        // Filter by Search
        if (searchQuery) {
            const query = searchQuery.toLowerCase();
            const title = (item.title || '').toString().toLowerCase();
            const patient = (item.metadata?.extracted?.patient_name || '').toString().toLowerCase();
            const id = formatCaseId(item.id).toLowerCase();
            const emailId = (item.metadata?.seed_email_id || '').toString();

            return title.includes(query) ||
                patient.includes(query) ||
                id.includes(query) ||
                emailId.includes(query);
        }

        return true;
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

    const tabs = [
        'All',
        'New',
        'Pending Staffing',
        'Staffed',
        'Acceptance Drafted',
        'Acceptance Sent',
        'Evaluation Completed',
        'Authorization Pending',
        'Authorized – Treatment Started',
        'Closed'
    ];

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-xl font-semibold text-gray-900 dark:text-white">Cases</h1>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Manage and track patient referrals.</p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={fetchCases}
                        className="flex items-center gap-2 px-3 py-2 bg-white dark:bg-zinc-800 border border-gray-300 dark:border-zinc-700 rounded-lg text-sm font-medium hover:bg-gray-50 dark:hover:bg-zinc-700 transition-colors"
                        disabled={loading}
                    >
                        <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                        Refresh
                    </button>
                    {/* New Case button removed as requested */}
                </div>
            </div>

            <div className="bg-white dark:bg-zinc-900 shadow-sm rounded-xl overflow-hidden border border-gray-200 dark:border-zinc-800">
                {/* Filters and Search Bar */}
                {/* Filters and Search Bar */}
                <div className="p-4 border-b border-gray-100 dark:border-zinc-800 flex flex-col gap-4">
                    {/* Search Bar - Top */}
                    <div className="relative w-full">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <Search size={14} className="text-gray-400" />
                        </div>
                        <input
                            type="text"
                            placeholder="Search cases..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="block w-full pl-9 pr-3 py-2 border border-gray-300 dark:border-zinc-700 rounded-lg text-sm bg-gray-50 dark:bg-zinc-800/50 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                        />
                    </div>

                    {/* Filter Tabs - Bottom, Wrapped */}
                    <div className="flex flex-wrap gap-2 w-full">
                        {tabs.map((tab) => (
                            <button
                                key={tab}
                                onClick={() => setActiveTab(tab)}
                                className={`px-3 py-1.5 text-xs font-medium rounded-full transition-all border ${activeTab === tab
                                    ? 'bg-indigo-50 border-indigo-200 text-indigo-700 dark:bg-indigo-900/30 dark:border-indigo-800 dark:text-indigo-300 shadow-sm'
                                    : 'bg-transparent border-transparent text-gray-500 hover:bg-gray-50 hover:text-gray-700 dark:hover:bg-zinc-800 dark:text-gray-400'
                                    }`}
                            >
                                {tab}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Responsive Table Wrapper */}
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-zinc-800">
                        <thead className="bg-gray-50/80 dark:bg-zinc-800/80 backend-blur-sm">
                            <tr>
                                <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider w-20">
                                    <div className="flex items-center gap-1"><Hash size={12} /> ID</div>
                                </th>
                                <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider max-w-[200px]">
                                    <div className="flex items-center gap-1"><FileText size={12} /> Title</div>
                                </th>
                                <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider w-32">
                                    <div className="flex items-center gap-1"><Activity size={12} /> Status</div>
                                </th>
                                <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider max-w-[150px]">
                                    <div className="flex items-center gap-1"><User size={12} /> Patient</div>
                                </th>
                                <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider w-24">
                                    Discipline
                                </th>
                                <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider w-28">
                                    <div className="flex items-center gap-1"><Clock size={12} /> Updated</div>
                                </th>
                                <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider w-20">
                                    <div className="flex items-center gap-1"><Mail size={12} /> Email</div>
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-zinc-900 divide-y divide-gray-200 dark:divide-zinc-800">
                            {filteredCases.map((item) => (
                                <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors group">
                                    <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 align-top">

                                        {/* <span className="font-mono text-xs">{formatCaseId(item.id)}</span> */}
                                        <div className="break-words line-clamp-2" title={item.title}>
                                            <Link href={`/dashboard/cases/${item.id}`} className="hover:text-indigo-600 dark:hover:text-indigo-400">
                                                {formatCaseId(item.id)}
                                            </Link>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white align-top max-w-[200px]">
                                        <div className="break-words line-clamp-2" title={item.title}>
                                            <Link href={`/dashboard/cases/${item.id}`} className="hover:text-indigo-600 dark:hover:text-indigo-400">
                                                {item.title.replace(/^RE:\s*/i, '').replace(/^\[External\]\s*/i, '')}
                                            </Link>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3 align-top">
                                        <span className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium capitalize border ${getStatusColor(item.status)}`}>
                                            {item.status}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-sm text-gray-900 dark:text-white align-top max-w-[150px]">
                                        <div className="break-words font-medium">
                                            {item.metadata?.extracted?.patient_name || <span className="text-gray-400 italic">Unknown</span>}
                                        </div>
                                    </td>
                                    <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 align-top">
                                        {item.metadata?.extracted?.discipline_requested || item.metadata?.staffing?.discipline || '-'}
                                    </td>
                                    <td className="px-4 py-3 text-xs text-gray-500 dark:text-gray-400 align-top">
                                        <div className="flex flex-col">
                                            <span>2025-12-23</span>
                                            <span className="text-gray-400 text-[10px]">07:37</span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3 text-sm text-indigo-500 dark:text-indigo-400 align-top">
                                        #{item.metadata?.seed_email_id || '-'}
                                    </td>
                                </tr>
                            ))}
                            {filteredCases.length === 0 && (
                                <tr>
                                    <td colSpan="7" className="px-6 py-12 text-center text-gray-500 dark:text-gray-400">
                                        <div className="flex flex-col items-center gap-2">
                                            <Search size={32} className="text-gray-300" />
                                            <p>No cases found matching your criteria</p>
                                        </div>
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>

                <div className="px-4 py-3 border-t border-gray-100 dark:border-zinc-800 flex justify-between items-center bg-gray-50/50 dark:bg-zinc-800/10">
                    <span className="text-xs text-gray-500">Showing {filteredCases.length} records</span>
                    <div className="flex gap-2">
                        <button className="px-2.5 py-1.5 border border-gray-300 dark:border-zinc-700 rounded-md text-xs hover:bg-white dark:hover:bg-zinc-700 disabled:opacity-50 transition-colors" disabled>Previous</button>
                        <button className="px-2.5 py-1.5 border border-gray-300 dark:border-zinc-700 rounded-md text-xs hover:bg-white dark:hover:bg-zinc-700 disabled:opacity-50 transition-colors" disabled>Next</button>
                    </div>
                </div>
            </div>
        </div>
    );
}
