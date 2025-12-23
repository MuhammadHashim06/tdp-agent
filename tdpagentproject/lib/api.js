// const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// export interface Email {
//     id: string;
//     subject: string;
//     sender: string;
//     sender_name?: string;
//     received_datetime: string;
//     status?: string;
// }

// export interface EmailDetail extends Email {
//     body: string;
//     receiver: string;
//     attachments: Attachment[];
// }

// export interface Attachment {
//     attachment_id: string;
//     file_name: string;
//     file_size: string;
//     content_type?: string;
//     download_url?: string;
// }

// export const api = {
//     getEmails: async (limit: number = 10, skip: number = 0): Promise<{ emails: Email[] }> => {
//         const response = await fetch(`${API_BASE_URL}/emails?limit=${limit}&skip=${skip}`);
//         if (!response.ok) {
//             throw new Error('Failed to fetch emails');
//         }
//         return response.json();
//     },

//     getEmailById: async (id: string): Promise<EmailDetail> => {
//         const response = await fetch(`${API_BASE_URL}/emails/${id}`);
//         if (!response.ok) {
//             throw new Error('Failed to fetch email details');
//         }
//         return response.json();
//     },

//     getAttachments: async (emailId: string): Promise<{ attachments: Attachment[] }> => {
//         const response = await fetch(`${API_BASE_URL}/attachments/emails/${emailId}`);
//         if (!response.ok) {
//             throw new Error('Failed to fetch attachments');
//         }
//         return response.json();
//     },

//     getAttachmentDownloadUrl: (emailId: string, attachmentRowId: string) => {
//         // Since the API returns the file directly or a URL, we can construct the URL if it's a GET request
//         // But typically we might fetch a presigned URL or just link to the endpoint.
//         // Based on spec: GET /attachments/emails/{email_id}/{attachment_row_id}/download
//         return `${API_BASE_URL}/attachments/emails/${emailId}/${attachmentRowId}/download`;
//     }
// };



const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export const api = {
    getEmails: async (limit = 100, skip = 0) => {
        const response = await fetch(`${API_BASE_URL}/emails?limit=${limit}&skip=${skip}`);
        if (!response.ok) {
            throw new Error('Failed to fetch emails');
        }
        return response.json();
    },

    getEmailById: async (id) => {
        const response = await fetch(`${API_BASE_URL}/emails/${id}`);
        if (!response.ok) {
            throw new Error('Failed to fetch email details');
        }
        return response.json();
    },

    getAttachments: async (emailId) => {
        const response = await fetch(`${API_BASE_URL}/attachments/emails/${emailId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch attachments');
        }
        return response.json();
    },

    getAttachmentDownloadUrl: (emailId, attachmentRowId) => {
        // Since the API returns the file directly or a URL, we can construct the URL if it's a GET request
        // But typically we might fetch a presigned URL or just link to the endpoint.
        // Based on spec: GET /attachments/emails/{email_id}/{attachment_row_id}/download
        return `${API_BASE_URL}/attachments/emails/${emailId}/${attachmentRowId}/download`;
    },

    getCases: async (limit = 50, skip = 0) => {
        const response = await fetch(`${API_BASE_URL}/cases?limit=${limit}&skip=${skip}`);
        if (!response.ok) {
            throw new Error('Failed to fetch cases');
        }
        return response.json();
    },

    getCaseById: async (id) => {
        const response = await fetch(`${API_BASE_URL}/cases/${id}`);
        if (!response.ok) {
            throw new Error('Failed to fetch case details');
        }
        return response.json();
    },

    getCaseTimeline: async (id, limit = 200) => {
        const response = await fetch(`${API_BASE_URL}/cases/${id}/timeline?limit=${limit}`);
        if (!response.ok) {
            throw new Error('Failed to fetch case timeline');
        }
        return response.json();
    },

    confirmStaffing: async (caseId, data) => {
        const response = await fetch(`${API_BASE_URL}/cases/${caseId}/staffing/confirm`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Failed to confirm staffing');
        }
        return response.json();
    },

    createAcceptanceDraft: async (caseId) => {
        const response = await fetch(`${API_BASE_URL}/cases/${caseId}/drafts/acceptance`, {
            method: 'POST',
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Failed to create acceptance draft');
        }
        return response.json();
    },

    updateCase: async (caseId, data) => {
        const response = await fetch(`${API_BASE_URL}/cases/${caseId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Failed to update case');
        }
        return response.json();
    },

    getDrafts: async (limit = 100, skip = 0) => {
        const response = await fetch(`${API_BASE_URL}/drafts/emails?limit=${limit}&skip=${skip}`);
        if (!response.ok) {
            throw new Error('Failed to fetch drafts');
        }
        return response.json();
    },

    getDraftById: async (id) => {
        const response = await fetch(`${API_BASE_URL}/drafts/${id}`);
        if (!response.ok) {
            throw new Error('Failed to fetch draft details');
        }
        return response.json();
    },

    updateDraft: async (id, data) => {
        const response = await fetch(`${API_BASE_URL}/drafts/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Failed to update draft');
        }
        return response.json();
    },

    getDraftsByEmailId: async (emailId) => {
        const response = await fetch(`${API_BASE_URL}/drafts/emails/${emailId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch drafts for email');
        }
        return response.json();
    },

    // Notifications
    checkStalledCases: async () => {
        const response = await fetch(`${API_BASE_URL}/notifications/check_stalled_cases/`, {
            method: 'POST',
        });
        if (!response.ok) throw new Error('Failed to check stalled cases');
        return response.json();
    },

    getNotifications: async () => {
        const response = await fetch(`${API_BASE_URL}/notifications/notifications/`);
        if (!response.ok) throw new Error('Failed to fetch notifications');
        return response.json();
    },

    markNotificationsRead: async () => {
        const response = await fetch(`${API_BASE_URL}/notifications/mark_notifications_read/`, {
            method: 'POST',
        });
        if (!response.ok) throw new Error('Failed to mark notifications as read');
        return response.json();
    }
};
