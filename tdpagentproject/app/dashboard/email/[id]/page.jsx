


'use client';

import { useState, useEffect, use } from 'react';
import Link from 'next/link';
import { api } from '../../../../lib/api';

export default function EmailDetailPage(props) {
    // Unwrap params using React.use()
    const params = use(props.params);
    const id = params.id;

    const [email, setEmail] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showDraftsList, setShowDraftsList] = useState(false);
    const [relatedDrafts, setRelatedDrafts] = useState([]);

    useEffect(() => {
        if (id) {
            fetchEmailDetails(id);
        }
    }, [id]);

    const fetchEmailDetails = async (emailId) => {
        try {
            setLoading(true);
            // Fetch the email data
            const emailData = await api.getEmailById(emailId);

            // Assuming emailData contains the response structure you provided
            let attachmentsData = { attachments: [] };
            try {
                attachmentsData = await api.getAttachments(emailId);
            } catch (e) {
                console.warn('Failed to fetch attachments', e);
            }

            setEmail({
                id: emailData.id,
                subject: emailData.subject || 'No Subject',
                sender: emailData.sender_name || 'Unknown Sender',
                senderEmail: emailData.sender || 'No Sender Email',
                receiver: emailData.to_list,
                cc: emailData.cc_list || 'No CC',
                received_at: emailData.received_datetime ? new Date(emailData.received_datetime).toLocaleString() : 'No Date Provided',
                body_html: emailData.body_html || emailData.body || 'No body content available', // Fallback to body if html missing
                message_id: emailData.message_id || 'No Message ID',
                internet_message_id: emailData.internet_message_id || 'No Internet Message ID',
                conversation_id: emailData.conversation_id || 'No Conversation ID',
                internet_message_id: emailData.internet_message_id || 'No Internet Message ID',
                conversation_id: emailData.conversation_id || 'No Conversation ID',
                attachments: attachmentsData.attachments,
            });

            // Related drafts are fetched separately in my mental model or part of the email data?
            // The previous code had a separate call. I need to restore that logic or use what I have.
            // Wait, I replaced the whole file content previously and might have lost the separate fetch if I didn't verify carefully.
            // Let's re-add the fetch logic properly.

            let draftsData = { items: [] };
            try {
                draftsData = await api.getDraftsByEmailId(emailId);
            } catch (e) {
                // simple fallback
            }
            setRelatedDrafts(draftsData.items || []);

        } catch (err) {
            setError('Failed to load email details');
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

    if (error || !email) {
        return (
            <div className="text-center p-8">
                <div className="text-red-500 mb-4">{error || 'Email not found'}</div>
                <Link href="/dashboard/email" className="text-indigo-600 hover:underline">
                    Back to Inbox
                </Link>
            </div>
        );
    }

    return (
        <div className="bg-white dark:bg-zinc-900 shadow rounded-lg overflow-hidden min-h-[500px] flex flex-col">
            {/* Email Header */}
            <div className="p-6 border-b border-gray-200 dark:border-zinc-800">
                <div className="flex justify-between items-start mb-4">
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{email.subject}</h1>
                    <div className="flex gap-2">
                        <Link href="/dashboard/email" className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 rounded text-gray-700 dark:text-gray-300 transition-colors">
                            &larr; Back
                        </Link>
                    </div>
                </div>
                <div className="flex items-center justify-between text-sm">
                    <div className="flex flex-col gap-1">
                        <p>
                            <span className="text-gray-500 dark:text-gray-400">From:</span>{' '}
                            <span className="font-semibold text-gray-900 dark:text-white">{email.sender}</span> ({email.senderEmail})
                        </p>
                        <p>
                            <span className="text-gray-500 dark:text-gray-400">To:</span>{' '}
                            <span className="text-gray-900 dark:text-white">{email.receiver}</span>
                        </p>
                        {email.cc && (
                            <p>
                                <span className="text-gray-500 dark:text-gray-400">CC:</span>{' '}
                                <span className="text-gray-900 dark:text-white">{email.cc}</span>
                            </p>
                        )}
                    </div>
                    <div className="text-gray-500 dark:text-gray-400">
                        {email.received_at}
                    </div>
                </div>
            </div>

            {/* Email Body */}
            <div className="p-6 flex-1 overflow-y-auto whitespace-pre-wrap text-gray-800 dark:text-gray-200 leading-relaxed font-sans">
                <div dangerouslySetInnerHTML={{ __html: email.body_html }} />
            </div>

            {/* Attachments */}
            {email.attachments && email.attachments.length > 0 && (
                <div className="p-6 bg-gray-50 dark:bg-zinc-900/50 border-t border-gray-200 dark:border-zinc-800">
                    <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-3 uppercase tracking-wider">
                        Attachments ({email.attachments.length})
                    </h3>
                    <ul className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {email.attachments.map((att) => (
                            <li key={att.attachment_id} className="flex items-center justify-between p-3 bg-white dark:bg-zinc-800 border dark:border-zinc-700 rounded-lg shadow-sm">
                                <div className="flex items-center gap-3 overflow-hidden">
                                    <span className="text-2xl">📄</span>
                                    <div className="min-w-0">
                                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate" title={att.file_name}>
                                            {att.file_name}
                                        </p>
                                        <p className="text-xs text-gray-500 dark:text-gray-400">
                                            {att.file_size}
                                        </p>
                                    </div>
                                </div>
                                <a
                                    href={api.getAttachmentDownloadUrl(email.id, att.attachment_id)}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="ml-2 text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 scroll-smooth"
                                >
                                    ⬇️
                                </a>
                            </li>
                        ))}
                    </ul>
                </div>
            )}


            {/* Related Drafts Section - Toggleable */}
            {
                relatedDrafts.length > 0 && (
                    <div className="border-t border-gray-200 dark:border-zinc-800 p-6 bg-gray-50 dark:bg-zinc-800/50">
                        <button
                            onClick={() => setShowDraftsList(!showDraftsList)}
                            className="flex items-center gap-2 text-sm font-semibold text-indigo-600 hover:text-indigo-500 mb-3"
                        >
                            {showDraftsList ? '▼' : '▶'} View Related Drafts ({relatedDrafts.length})
                        </button>

                        {showDraftsList && (
                            <div className="space-y-2 animate-in fade-in slide-in-from-top-2 duration-200">
                                {relatedDrafts.map(draft => (
                                    <div key={draft.id} className="flex items-center justify-between bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-md p-3">
                                        <div className="flex items-center gap-3">
                                            <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${draft.status === 'draft' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'
                                                }`}>
                                                {draft.status}
                                            </span>
                                            <div className="flex flex-col">
                                                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                                    {draft.kind ? `Kind: ${draft.kind}` : `Draft #${draft.id}`}
                                                </span>
                                                <span className="text-xs text-gray-500">
                                                    tone: {draft.tone || 'N/A'} &bull; model: {draft.model}
                                                </span>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-3">
                                            <span className="text-xs text-gray-500 hidden sm:inline">
                                                {new Date(draft.created_at).toLocaleString()}
                                            </span>
                                            <Link
                                                href={`/dashboard/draft/${draft.id}`}
                                                className="px-3 py-1.5 bg-white border border-gray-300 text-gray-700 rounded hover:bg-gray-50 text-xs font-medium dark:bg-zinc-800 dark:border-zinc-700 dark:text-gray-200 dark:hover:bg-zinc-700"
                                            >
                                                Edit
                                            </Link>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )
            }
        </div >
    );
}
