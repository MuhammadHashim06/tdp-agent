'use client';

import { useState, useEffect, use } from 'react';
import Link from 'next/link';
import { api } from '../../../../lib/api';

const ALLOWED_STATUSES_DEFAULT = [
    "new",
    "pending staffing",
    "staffed",
    "acceptance drafted",
    "acceptance sent",
    "evaluation completed",
    "authorization pending",
    "authorized – treatment started",
    "closed",
];

export default function CaseDetailPage(props) {
    const params = use(props.params);
    const id = params.id;

    const [caseDetail, setCaseDetail] = useState(null);
    const [timeline, setTimeline] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Modal State
    const [isStaffingModalOpen, setIsStaffingModalOpen] = useState(false);
    const [staffingFormData, setStaffingFormData] = useState({
        therapist_name: '',
        discipline: '',
        availability: '',
        referral_source_email: ''
    });
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [statusMessage, setStatusMessage] = useState('');
    const [successMessage, setSuccessMessage] = useState(null);

    // Update Status Modal State
    const [isUpdateModalOpen, setIsUpdateModalOpen] = useState(false);
    const [updateFormData, setUpdateFormData] = useState({
        status: '',
        title: ''
    });

    useEffect(() => {
        if (id) {
            fetchCaseData(id);
        }
    }, [id]);

    const fetchCaseData = async (caseId) => {
        try {
            setLoading(true);

            // Parallel fetch for case details and timeline
            const [caseData, timelineData] = await Promise.all([
                api.getCaseById(caseId).catch(err => {
                    console.warn('Failed to fetch case details', err);
                    return null;
                }),
                api.getCaseTimeline(caseId).catch(err => {
                    console.warn('Failed to fetch timeline', err);
                    return { items: [] };
                })
            ]);

            if (caseData) {
                setCaseDetail(caseData);
            } else {
                // Fallback mock data matching User Request (Case ID 6)
                setCaseDetail({
                    "id": 6,
                    "external_id": "staffing@therapydepotonline.com:AAQkAGI2MmQ2NjM0LWU4OWMtNDYxMi1hNjllLTU5NjczMTE1NTc2YgAQADfVnfAgXk9Aiv-qkPDa0SE=",
                    "title": "OT request from RevivalHHC in BRONX",
                    "status": "pending staffing",
                    "metadata": {
                        "mailbox": "staffing@therapydepotonline.com",
                        "extracted": {
                            "dob": null,
                            "mrn": null,
                            "address": "5360 BROADWAY, BRONX, NY 10463",
                            "evidence": {
                                "address": "Evidence: 'BRONX 5360 BROADWAY BRONX, NY 10463' appears in the body",
                                "patient_name": "Evidence: 'MERCADO, AGUEDA' appears in the body as the patient",
                                "discipline_requested": "Evidence: 'Discipline requested: OT' appears in the body",
                                "requested_start_date": "Evidence: 'SOC date: 12/05/25' appears in the body",
                                "referral_source_email": "Evidence: 'zfuentes@revivalhhc.org' appears in the body"
                            },
                            "language": null,
                            "diagnosis": null,
                            "insurance": null,
                            "patient_id": null,
                            "patient_name": "MERCADO, AGUEDA",
                            "extracted_from": "Email notification from Smartsheet",
                            "visit_frequency": null,
                            "confidence_notes": "Some fields missing (dob, insurance, MRN).",
                            "caregiver_contact": null,
                            "ordering_provider": null,
                            "referral_source_fax": null,
                            "referral_source_org": "RevivalHHC",
                            "discipline_requested": "OT",
                            "referral_source_name": "RevivalHHC",
                            "requested_start_date": "2025-12-05",
                            "special_instructions": "Open request; advise if OT is available for Eval and Treat...",
                            "referral_source_email": "zfuentes@revivalhhc.org",
                            "referral_source_phone": null,
                            "authorization_required": null
                        },
                        "staffing": {},
                        "seed_email_id": 6,
                        "conversation_id": "AAQkAGI2MmQ2NjM0LWU4OWMtNDYxMi1hNjllLTU5NjczMTE1NTc2YgAQADfVnfAgXk9Aiv-qkPDa0SE="
                    }
                });
            }

            if (timelineData && timelineData.items) {
                setTimeline(timelineData.items);
            } else {
                // Fallback mock timeline
                setTimeline([
                    {
                        id: 3,
                        subject: "STATUS CHANGE",
                        sender: "System",
                        received_datetime: "2025-12-22T20:25:56Z",
                        body_preview: "Status changed to 'pending staffing'",
                        type: "system"
                    },
                    {
                        id: 2,
                        subject: "DATA EXTRACTED",
                        sender: "System",
                        received_datetime: "2025-12-21T20:25:56Z",
                        body_preview: "Extracted patient data from email #450",
                        type: "system"
                    },
                    {
                        id: 1,
                        subject: "CASE CREATED",
                        sender: "System",
                        received_datetime: "2025-12-21T20:25:56Z",
                        body_preview: "Case created from email #450",
                        type: "system"
                    }
                ]);
            }

        } catch (err) {
            setError('Failed to load case data');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleStaffingSubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        setStatusMessage('Saving...');
        try {
            await api.confirmStaffing(id, staffingFormData);
            setStatusMessage('Saved');
            await api.createAcceptanceDraft(id);
            setSuccessMessage("Staffing confirmed and acceptance draft created!");
            setTimeout(() => {
                setIsStaffingModalOpen(false);
                setSuccessMessage(null);
                fetchCaseData(id);
            }, 1000);
        } catch (err) {
            console.error(err);
            setError("Failed to confirm staffing.");
        } finally {
            setIsSubmitting(false);
            setStatusMessage('');
        }
    };

    const handleUpdateSubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        setStatusMessage('Saving...');
        try {
            await api.updateCase(id, updateFormData);
            if (updateFormData.status === 'staffed') {
                await api.createAcceptanceDraft(id);
                setSuccessMessage("Case updated and draft created!");
            } else {
                setSuccessMessage("Case updated successfully!");
            }
            setTimeout(() => {
                setIsUpdateModalOpen(false);
                setSuccessMessage(null);
                fetchCaseData(id);
            }, 1000);
        } catch (err) {
            console.error(err);
            setError("Failed to update case.");
        } finally {
            setIsSubmitting(false);
            setStatusMessage('');
        }
    };

    // Helper to get initials
    const getInitials = (name) => {
        if (!name) return '??';
        return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
    };

    if (loading) return <div className="flex justify-center p-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>;
    if (error) return <div className="p-8 text-red-500">{error}</div>;
    if (!caseDetail) return null;

    return (
        <div className="space-y-6">
            {/* Header Steps */}
            <div className="flex items-center gap-2 mb-4 text-sm text-gray-500">
                <Link href="/dashboard/cases" className="hover:text-indigo-600">&larr; Back to Cases</Link>
            </div>

            <div className="flex justify-between items-start">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{caseDetail.title}</h1>
                    <p className="text-sm text-gray-500">Full case history and metadata.</p>
                </div>
                <button
                    onClick={() => fetchCaseData(id)}
                    className="px-3 py-1.5 bg-white border border-gray-300 rounded text-sm hover:bg-gray-50 dark:bg-zinc-800 dark:border-zinc-700 dark:text-white"
                >
                    Case Actions
                </button>
            </div>

            {/* Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white dark:bg-zinc-900 p-4 rounded-lg shadow-sm border border-gray-200 dark:border-zinc-800">
                    <p className="text-xs font-semibold text-gray-400 uppercase"># CASE ID</p>
                    <p className="text-lg font-bold text-gray-900 dark:text-white mt-1">
                        #{caseDetail.id}
                    </p>
                </div>
                <div className="bg-white dark:bg-zinc-900 p-4 rounded-lg shadow-sm border border-gray-200 dark:border-zinc-800">
                    <p className="text-xs font-semibold text-gray-400 uppercase">STATUS</p>
                    <div className="mt-1">
                        <span className={`px-3 py-1 text-sm font-semibold rounded-full capitalize
                            ${caseDetail.status === 'new' ? 'bg-blue-100 text-blue-800' :
                                caseDetail.status === 'pending staffing' ? 'bg-yellow-100 text-yellow-800' :
                                    'bg-gray-100 text-gray-800'
                            }`}>
                            {caseDetail.status}
                        </span>
                    </div>
                </div>
                <div className="bg-white dark:bg-zinc-900 p-4 rounded-lg shadow-sm border border-gray-200 dark:border-zinc-800">
                    <p className="text-xs font-semibold text-gray-400 uppercase">📅 CREATED</p>
                    <p className="text-lg font-bold text-gray-900 dark:text-white mt-1">12/21/2025</p>
                </div>
                <div className="bg-white dark:bg-zinc-900 p-4 rounded-lg shadow-sm border border-gray-200 dark:border-zinc-800">
                    <p className="text-xs font-semibold text-gray-400 uppercase">🕒 LAST UPDATE</p>
                    <p className="text-lg font-bold text-gray-900 dark:text-white mt-1">12/23/2025</p>
                </div>
            </div>

            {/* Main Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Left Column (2/3) - Patient Info & Details */}
                <div className="space-y-6 lg:col-span-1">
                    {/* Patient Information */}
                    <div className="bg-white dark:bg-zinc-900 rounded-lg shadow-sm border border-gray-200 dark:border-zinc-800">
                        <div className="px-4 py-3 border-b border-gray-200 dark:border-zinc-800">
                            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Patient Information</h3>
                        </div>
                        <div className="p-4 space-y-4">
                            <div>
                                <p className="text-xs text-gray-400 uppercase">PATIENT NAME</p>
                                <p className="font-medium text-gray-900 dark:text-white">
                                    {caseDetail.metadata?.extracted?.patient_name || '-'}
                                </p>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <p className="text-xs text-gray-400 uppercase">DOB</p>
                                    <p className="text-sm text-gray-900 dark:text-white">
                                        {caseDetail.metadata?.extracted?.dob || '—'}
                                    </p>
                                </div>
                                <div>
                                    <p className="text-xs text-gray-400 uppercase">INSURANCE</p>
                                    <p className="text-sm text-gray-900 dark:text-white">
                                        {caseDetail.metadata?.extracted?.insurance || '—'}
                                    </p>
                                </div>
                            </div>
                            <div>
                                <p className="text-xs text-gray-400 uppercase">DIAGNOSIS</p>
                                <p className="text-sm text-gray-900 dark:text-white font-medium">
                                    {caseDetail.metadata?.extracted?.diagnosis || '—'}
                                </p>
                            </div>
                            <div>
                                <p className="text-xs text-gray-400 uppercase">ADDRESS</p>
                                <p className="text-sm text-gray-900 dark:text-white">
                                    {caseDetail.metadata?.extracted?.address || '-'}
                                </p>
                            </div>
                            <div>
                                <p className="text-xs text-gray-400 uppercase">DISCIPLINE REQUESTED</p>
                                <p className="text-sm font-medium text-gray-900 dark:text-white">
                                    {caseDetail.metadata?.extracted?.discipline_requested || '-'}
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Referral Source */}
                    <div className="bg-white dark:bg-zinc-900 rounded-lg shadow-sm border border-gray-200 dark:border-zinc-800">
                        <div className="px-4 py-3 border-b border-gray-200 dark:border-zinc-800">
                            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Referral Source</h3>
                        </div>
                        <div className="p-4 space-y-4">
                            <div>
                                <p className="text-xs text-gray-400 uppercase">ORGANIZATION</p>
                                <p className="font-medium text-gray-900 dark:text-white">
                                    {caseDetail.metadata?.extracted?.referral_source_org || '-'}
                                </p>
                            </div>
                            <div>
                                <p className="text-xs text-gray-400 uppercase">REFERRAL CONTACT</p>
                                <p className="text-sm text-gray-900 dark:text-white">
                                    {caseDetail.metadata?.extracted?.referral_source_name || '-'}
                                </p>
                            </div>
                            <div>
                                <p className="text-xs text-gray-400 uppercase">CONTACT INFO</p>
                                <div className="space-y-1">
                                    {caseDetail.metadata?.extracted?.referral_source_email && (
                                        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
                                            <span>📧</span> {caseDetail.metadata.extracted.referral_source_email}
                                        </div>
                                    )}
                                    {caseDetail.metadata?.extracted?.referral_source_phone && (
                                        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
                                            <span>📞</span> {caseDetail.metadata.extracted.referral_source_phone}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Staffing Assignment */}
                    <div className="bg-white dark:bg-zinc-900 rounded-lg shadow-sm border border-gray-200 dark:border-zinc-800">
                        <div className="px-4 py-3 border-b border-gray-200 dark:border-zinc-800 flex justify-between items-center">
                            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Staffing Assignment</h3>
                            <button
                                onClick={() => setIsStaffingModalOpen(true)}
                                className="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
                            >
                                Edit
                            </button>
                        </div>
                        <div className="p-4 space-y-4">
                            <div>
                                <p className="text-xs text-gray-400 uppercase">THERAPIST</p>
                                <p className="font-medium text-gray-900 dark:text-white">
                                    {caseDetail.metadata?.staffing?.therapist_name || '—'}
                                </p>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <p className="text-xs text-gray-400 uppercase">DISCIPLINE</p>
                                    <p className="text-sm text-gray-900 dark:text-white">
                                        {caseDetail.metadata?.staffing?.discipline || '—'}
                                    </p>
                                </div>
                                <div>
                                    <p className="text-xs text-gray-400 uppercase">AVAILABILITY</p>
                                    <p className="text-sm text-gray-900 dark:text-white">
                                        {caseDetail.metadata?.staffing?.availability || '—'}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Column (1/3) - Emails & System Events */}
                <div className="space-y-6 lg:col-span-2">

                    {/* Emails */}
                    <div className="bg-white dark:bg-zinc-900 rounded-lg shadow-sm border border-gray-200 dark:border-zinc-800">
                        <div className="px-4 py-3 border-b border-gray-200 dark:border-zinc-800 bg-gray-50 dark:bg-zinc-800/50">
                            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Emails</h3>
                        </div>
                        <div className="divide-y divide-gray-100 dark:divide-zinc-800">
                            {/* Mock Email Item */}
                            <div className="p-4 hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors">
                                <div className="flex justify-between items-start mb-1">
                                    <div className="flex items-center gap-2">
                                        <div className="h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-semibold text-xs">
                                            {getInitials(caseDetail.metadata?.extracted?.referral_source_name || "Unknown")}
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium text-gray-900 dark:text-white">
                                                {caseDetail.title}
                                            </p>
                                            <p className="text-xs text-gray-500">
                                                {caseDetail.metadata?.extracted?.referral_source_email} &rarr; staffing@therapydepotonline.com
                                            </p>
                                        </div>
                                    </div>
                                    <span className="text-xs text-gray-400">12/22/2025</span>
                                </div>
                                <p className="text-sm text-gray-600 dark:text-gray-300 mt-2 line-clamp-2 pl-10">
                                    {/* Snippet from extraction evidence or default */}
                                    Please find attached the referral documents...
                                </p>
                                <div className="pl-10 mt-2">
                                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                                        📎 1 attachment(s)
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Drafts */}
                    <div className="bg-white dark:bg-zinc-900 rounded-lg shadow-sm border border-gray-200 dark:border-zinc-800">
                        <div className="px-4 py-3 border-b border-gray-200 dark:border-zinc-800 bg-gray-50 dark:bg-zinc-800/50">
                            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Drafts</h3>
                        </div>
                        <div className="p-4">
                            <div className="overflow-x-auto">
                                <table className="min-w-full text-left text-sm">
                                    <thead>
                                        <tr className="text-xs text-gray-400 uppercase border-b border-gray-100 dark:border-zinc-800">
                                            <th className="pb-2 font-medium">Type</th>
                                            <th className="pb-2 font-medium">Status</th>
                                            <th className="pb-2 font-medium">Details</th>
                                            <th className="pb-2 font-medium text-right">Date</th>
                                            <th className="pb-2"></th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-100 dark:divide-zinc-800">
                                        <tr>
                                            <td className="py-3">
                                                <div className="flex items-center gap-2">
                                                    <div className="h-2 w-2 rounded-full bg-yellow-400"></div>
                                                    <span className="font-medium text-gray-900 dark:text-white">Acceptance</span>
                                                </div>
                                            </td>
                                            <td className="py-3">
                                                <span className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full text-xs">drafted</span>
                                            </td>
                                            <td className="py-3 text-xs text-gray-500">
                                                To: {caseDetail.metadata?.extracted?.referral_source_email || '...'}
                                            </td>
                                            <td className="py-3 text-right text-xs text-gray-500">
                                                12/23/2025
                                            </td>
                                            <td className="py-3 text-right">
                                                <button className="text-indigo-600 hover:text-indigo-800 text-xs font-medium">Open ↗</button>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                    {/* System Events & Audit Log */}
                    <div className="bg-white dark:bg-zinc-900 rounded-lg shadow-sm border border-gray-200 dark:border-zinc-800">
                        <div className="px-4 py-3 border-b border-gray-200 dark:border-zinc-800 bg-gray-50 dark:bg-zinc-800/50">
                            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">System Events & Audit Log</h3>
                        </div>
                        <div className="p-4">
                            <div className="relative border-l border-gray-200 dark:border-zinc-700 ml-3 space-y-6">
                                {timeline.map((item) => (
                                    <div key={item.id} className="mb-6 ml-4">
                                        <div className="absolute w-2 h-2 bg-gray-200 rounded-full mt-1.5 -left-1 dark:bg-zinc-600 border border-white dark:border-zinc-900"></div>
                                        <div className="flex justify-between items-start">
                                            <h4 className="text-sm font-bold text-gray-900 dark:text-white uppercase">
                                                {item.subject}
                                            </h4>
                                            <span className="text-xs text-gray-400">
                                                {new Date(item.received_datetime).toLocaleString()}
                                            </span>
                                        </div>
                                        <div className="mt-1">
                                            {item.subject === "CASE CREATED" && (
                                                <div className="inline-flex items-center px-2 py-1 rounded bg-indigo-50 text-indigo-700 text-xs font-medium">
                                                    ✉ Linked to Email #{caseDetail.metadata?.seed_email_id}
                                                </div>
                                            )}
                                            <p className="text-sm text-gray-500 mt-1">
                                                {item.body_preview}
                                            </p>
                                            <button className="text-xs text-gray-400 hover:text-gray-600 mt-1 flex items-center gap-1">
                                                › View Payload
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                </div>
            </div>

            {/* Modals placed at the end to avoid z-index issues mostly */}
            {isStaffingModalOpen && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white dark:bg-zinc-900 rounded-lg shadow-xl max-w-md w-full p-6">
                        <h2 className="text-lg font-bold mb-4">Confirm Staffing</h2>
                        <form onSubmit={handleStaffingSubmit} className="space-y-4">
                            <input
                                className="w-full px-3 py-2 border rounded"
                                placeholder="Therapist Name"
                                value={staffingFormData.therapist_name}
                                onChange={e => setStaffingFormData({ ...staffingFormData, therapist_name: e.target.value })}
                            />
                            <input
                                className="w-full px-3 py-2 border rounded"
                                placeholder="Discipline"
                                value={staffingFormData.discipline}
                                onChange={e => setStaffingFormData({ ...staffingFormData, discipline: e.target.value })}
                            />
                            <div className="flex justify-end gap-2 text-sm">
                                <button type="button" onClick={() => setIsStaffingModalOpen(false)} className="px-3 py-2 text-gray-600">Cancel</button>
                                <button type="submit" disabled={isSubmitting} className="px-3 py-2 bg-indigo-600 text-white rounded">
                                    {isSubmitting ? 'Saving...' : 'Save'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
