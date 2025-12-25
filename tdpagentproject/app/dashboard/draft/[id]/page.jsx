'use client';

import { useState, useEffect, use } from 'react';
import Link from 'next/link';
import { api } from '../../../../lib/api';
import { ArrowLeft } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function DraftDetailPage(props) {
    const params = use(props.params);
    const id = params.id;
    const router = useRouter();

    const [draft, setDraft] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Modal State
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [saving, setSaving] = useState(false);
    const [modalError, setModalError] = useState(null);

    // Form Data for Modal
    const [formData, setFormData] = useState({
        draft: '',
        to: []
    });
    const [toInput, setToInput] = useState('');

    useEffect(() => {
        if (id) {
            fetchDraft(id);
        }
    }, [id]);

    const fetchDraft = async (draftId) => {
        try {
            setLoading(true);
            const data = await api.getDraftById(draftId);
            setDraft(data);
        } catch (err) {
            console.error(err);
            setError('Failed to load draft details');
        } finally {
            setLoading(false);
        }
    };

    const openEditModal = () => {
        // Pre-fill form data from current draft
        setFormData({
            draft: draft.draft || '',
            to: draft.to || []
        });
        if (draft.to && Array.isArray(draft.to)) {
            setToInput(draft.to.join(', '));
        }
        setModalError(null);
        setIsEditModalOpen(true);
    };

    const closeEditModal = () => {
        setIsEditModalOpen(false);
    };

    const handleSave = async (e) => {
        e.preventDefault();
        setSaving(true);
        setModalError(null);

        try {
            const toArray = toInput.split(',').map(s => s.trim()).filter(s => s);
            const payload = {
                draft: formData.draft,
                to: toArray
            };

            await api.updateDraft(id, payload);

            // Success: Refresh data and close modal
            await fetchDraft(id);
            closeEditModal();
        } catch (err) {
            console.error(err);
            setModalError(err.message || "Failed to save draft");
        } finally {
            setSaving(false);
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        if (name === 'toInput') {
            setToInput(value);
        } else {
            setFormData(prev => ({
                ...prev,
                [name]: value
            }));
        }
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
            </div>
        );
    }

    if (error && !draft) {
        return (
            <div className="text-center p-8">
                <div className="text-red-500 mb-4">{error}</div>
                <Link href="/dashboard/draft" className="text-indigo-600 hover:underline">
                    Back to Drafts
                </Link>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-4">
                    {/* <Link href="/dashboard/draft" className="text-indigo-600 hover:text-indigo-500">
                        &larr; Back
                    </Link> */}
                    <button
                        onClick={() => router.back()}
                        className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 rounded text-gray-700 dark:text-gray-300 transition-colors flex items-center gap-1"
                    >
                        <ArrowLeft size={16} /> Back
                    </button>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Draft #{id}</h1>
                </div>
                <div className="flex items-center gap-4">
                    {draft?.graph_draft_web_link && (
                        <a
                            href={draft.graph_draft_web_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-indigo-600 hover:underline flex items-center gap-1"
                        >
                            Open in Outlook &rarr;
                        </a>
                    )}
                    <button
                        onClick={openEditModal}
                        className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors font-medium text-sm"
                    >
                        Edit Draft
                    </button>
                </div>
            </div>

            {/* Read-Only Details */}
            <div className="space-y-6">
                {/* Metadata Card */}
                <div className="bg-gray-50 dark:bg-zinc-800 p-4 rounded-lg flex flex-wrap gap-4 text-sm border border-gray-200 dark:border-zinc-700">
                    <div>
                        <span className="text-gray-500 dark:text-gray-400">Status:</span>
                        <span className="ml-2 font-medium text-gray-900 dark:text-white capitalize">{draft?.status}</span>
                    </div>
                    <div>
                        <span className="text-gray-500 dark:text-gray-400">Kind:</span>
                        <span className="ml-2 font-medium text-gray-900 dark:text-white capitalize">{draft?.kind || '-'}</span>
                    </div>
                    <div>
                        <span className="text-gray-500 dark:text-gray-400">Tone:</span>
                        <span className="ml-2 font-medium text-gray-900 dark:text-white capitalize">{draft?.tone || '-'}</span>
                    </div>
                    <div>
                        <span className="text-gray-500 dark:text-gray-400">Created:</span>
                        <span className="ml-2 font-medium text-gray-900 dark:text-white">
                            {draft?.created_at ? new Date(draft.created_at).toLocaleString() : '-'}
                        </span>
                    </div>
                </div>

                {/* To Field */}
                <div className="bg-white dark:bg-zinc-900 shadow rounded-lg p-6">
                    <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wide">Recipients (To)</h3>
                    <div className="text-gray-900 dark:text-white font-mono text-sm">
                        {draft.to && draft.to.length > 0 ? (
                            draft.to.map((email, idx) => (
                                <span key={idx} className="inline-block bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded mr-2 mb-2">
                                    {email}
                                </span>
                            ))
                        ) : (
                            <span className="text-gray-400 italic">No recipients defined</span>
                        )}
                    </div>
                </div>

                {/* Body Content */}
                <div className="bg-white dark:bg-zinc-900 shadow rounded-lg p-6">
                    <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wide">Draft Content</h3>
                    <div className="whitespace-pre-wrap font-mono text-sm text-gray-800 dark:text-gray-200 bg-gray-50 dark:bg-black/20 p-4 rounded border border-gray-100 dark:border-zinc-800">
                        {draft.draft || <span className="text-gray-400 italic">No content</span>}
                    </div>
                </div>
            </div>

            {/* Edit Modal */}
            {isEditModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
                    <div
                        className="bg-white dark:bg-zinc-900 w-full max-w-3xl rounded-xl shadow-2xl border border-gray-200 dark:border-zinc-800 flex flex-col max-h-[90vh] animate-in zoom-in-95 duration-200"
                        role="dialog"
                        aria-modal="true"
                    >
                        {/* Modal Header */}
                        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-zinc-800">
                            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Edit Draft</h2>
                            <button
                                onClick={closeEditModal}
                                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18" /><path d="m6 6 18 18" /></svg>
                            </button>
                        </div>

                        {/* Modal Body */}
                        <div className="p-6 overflow-y-auto flex-1">
                            {modalError && (
                                <div className="mb-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
                                    {modalError}
                                </div>
                            )}

                            <form id="edit-draft-form" onSubmit={handleSave} className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        To (Recipients)
                                    </label>
                                    <input
                                        type="text"
                                        name="toInput"
                                        value={toInput}
                                        onChange={handleChange}
                                        placeholder="email@example.com, another@example.com"
                                        className="w-full px-3 py-2 border border-gray-300 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
                                    />
                                    <p className="mt-1 text-xs text-gray-500">Comma separated email addresses</p>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        Draft Content
                                    </label>
                                    <textarea
                                        name="draft"
                                        value={formData.draft}
                                        onChange={handleChange}
                                        rows={12}
                                        className="w-full px-3 py-2 border border-gray-300 dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 font-mono text-sm"
                                    />
                                </div>
                            </form>
                        </div>

                        {/* Modal Footer */}
                        <div className="p-4 border-t border-gray-200 dark:border-zinc-800 flex justify-end gap-3 bg-gray-50 dark:bg-zinc-800/50 rounded-b-xl">
                            <button
                                type="button"
                                onClick={closeEditModal}
                                disabled={saving}
                                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-zinc-800 border border-gray-300 dark:border-zinc-600 rounded-md hover:bg-gray-50 dark:hover:bg-zinc-700"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                form="edit-draft-form"
                                disabled={saving}
                                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
                            >
                                {saving ? (
                                    <>
                                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                                        Saving...
                                    </>
                                ) : 'Save Changes'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
