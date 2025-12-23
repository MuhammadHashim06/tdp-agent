'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function SignupPage() {
    const router = useRouter();

    const handleSignup = (e) => {
        e.preventDefault();
        // Mock signup logic
        alert('Account created successfully! Redirecting to login...');
        router.push('/login');
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 p-4">
            <div className="w-full max-w-md space-y-8 rounded-2xl bg-white/10 p-8 shadow-2xl backdrop-blur-md border border-white/20">
                <div className="text-center">
                    <h2 className="mt-6 text-3xl font-extrabold text-white">
                        Create Account
                    </h2>
                    <p className="mt-2 text-sm text-indigo-100">
                        Join us to start managing your emails smarter
                    </p>
                </div>
                <form className="mt-8 space-y-4" onSubmit={handleSignup}>
                    <div className="space-y-4">
                        <div>
                            <label htmlFor="name" className="sr-only">
                                Full Name
                            </label>
                            <input
                                id="name"
                                name="name"
                                type="text"
                                autoComplete="name"
                                required
                                className="relative block w-full rounded-lg border-0 bg-white/20 py-3 px-4 text-white placeholder:text-gray-300 ring-1 ring-inset ring-white/30 focus:z-10 focus:ring-2 focus:ring-inset focus:ring-white sm:text-sm sm:leading-6 backdrop-blur-sm transition-all focus:bg-white/30"
                                placeholder="Full Name"
                            />
                        </div>
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
                                autoComplete="new-password"
                                required
                                className="relative block w-full rounded-lg border-0 bg-white/20 py-3 px-4 text-white placeholder:text-gray-300 ring-1 ring-inset ring-white/30 focus:z-10 focus:ring-2 focus:ring-inset focus:ring-white sm:text-sm sm:leading-6 backdrop-blur-sm transition-all focus:bg-white/30"
                                placeholder="Password"
                            />
                        </div>
                        <div>
                            <label htmlFor="confirm-password" className="sr-only">
                                Confirm Password
                            </label>
                            <input
                                id="confirm-password"
                                name="confirm-password"
                                type="password"
                                autoComplete="new-password"
                                required
                                className="relative block w-full rounded-lg border-0 bg-white/20 py-3 px-4 text-white placeholder:text-gray-300 ring-1 ring-inset ring-white/30 focus:z-10 focus:ring-2 focus:ring-inset focus:ring-white sm:text-sm sm:leading-6 backdrop-blur-sm transition-all focus:bg-white/30"
                                placeholder="Confirm Password"
                            />
                        </div>
                    </div>

                    <div>
                        <button
                            type="submit"
                            className="group relative flex w-full justify-center rounded-lg bg-white px-4 py-3 text-sm font-bold text-indigo-600 shadow-md transition-all hover:bg-gray-100 hover:shadow-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
                        >
                            Sign up
                        </button>
                    </div>
                </form>
                <div className="text-center text-sm">
                    <p className="text-gray-200">
                        Already have an account?{' '}
                        <Link href="/login" className="font-semibold text-white hover:text-indigo-100 underline decoration-indigo-200 underline-offset-4">
                            Sign in
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}
