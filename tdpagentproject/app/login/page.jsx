'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const router = useRouter();

    const handleLogin = (e) => {
        e.preventDefault();
        if (email === 'admin@tdpagent.com' && password === 'tdpagent') {
            // Set simple auth cookie
            document.cookie = "auth_token=true; path=/; max-age=86400; SameSite=Strict";
            router.push('/dashboard');
        } else {
            alert('Invalid credentials.');
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 p-4">
            <div className="w-full max-w-md space-y-8 rounded-2xl bg-white/10 p-8 shadow-2xl backdrop-blur-md border border-white/20">
                <div className="text-center">
                    <h2 className="mt-6 text-3xl font-extrabold text-white">
                        Welcome Back
                    </h2>
                    <p className="mt-2 text-sm text-indigo-100">
                        Sign in to access your dashboard
                    </p>
                </div>
                <form className="mt-8 space-y-6" onSubmit={handleLogin}>
                    <div className="space-y-4">
                        <div>
                            <label htmlFor="email-address" className="sr-only">
                                Email address
                            </label>
                            <input
                                id="email-address"
                                name="email"
                                type="email"
                                autoComplete="email"
                                required
                                className="relative block w-full rounded-lg border-0 bg-white/20 py-3 px-4 text-white placeholder:text-gray-300 ring-1 ring-inset ring-white/30 focus:z-10 focus:ring-2 focus:ring-inset focus:ring-white sm:text-sm sm:leading-6 backdrop-blur-sm transition-all focus:bg-white/30"
                                placeholder="Email address"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                            />
                        </div>
                        <div>
                            <label htmlFor="password" className="sr-only">
                                Password
                            </label>
                            <input
                                id="password"
                                name="password"
                                type="password"
                                autoComplete="current-password"
                                required
                                className="relative block w-full rounded-lg border-0 bg-white/20 py-3 px-4 text-white placeholder:text-gray-300 ring-1 ring-inset ring-white/30 focus:z-10 focus:ring-2 focus:ring-inset focus:ring-white sm:text-sm sm:leading-6 backdrop-blur-sm transition-all focus:bg-white/30"
                                placeholder="Password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </div>
                    </div>

                    <div>
                        <button
                            type="submit"
                            className="group relative flex w-full justify-center rounded-lg bg-white px-4 py-3 text-sm font-bold text-indigo-600 shadow-md transition-all hover:bg-gray-100 hover:shadow-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
                        >
                            Sign in
                        </button>
                    </div>
                </form>
                <div className="text-center text-sm">
                    {/* <p className="text-gray-200">
                        Don't have an account?{' '}
                        <Link href="/signup" className="font-semibold text-white hover:text-indigo-100 underline decoration-indigo-200 underline-offset-4">
                            Sign up
                        </Link>
                    </p> */}
                    {/* <div className="mt-4 p-2 rounded bg-black/20 text-xs text-gray-300 inline-block">
                        Test with: <strong>user@example.com</strong> / <strong>password</strong>
                    </div> */}
                </div>
            </div>
        </div>
    );
}
