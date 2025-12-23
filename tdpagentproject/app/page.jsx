import Link from "next/link";

export default function Home() {
    return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 text-white">
            <main className="flex flex-col items-center gap-8 text-center px-4">
                <h1 className="text-5xl font-extrabold tracking-tight sm:text-7xl drop-shadow-md">
                    Welcome to <br />
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-yellow-300 to-orange-400">
                        TDP Email Agent
                    </span>
                </h1>
                <p className="max-w-2xl text-lg sm:text-xl font-medium text-indigo-100 drop-shadow-sm">
                    Seamlessly manage your drafts, emails, and support cases in one powerful dashboard.
                    Experience the future of email management.
                </p>

                <div className="mt-8 flex gap-4">
                    <Link
                        href="/login"
                        className="rounded-full bg-white px-8 py-4 text-lg font-bold text-indigo-600 shadow-lg transition-all hover:scale-105 hover:bg-gray-100 focus:outline-none focus:ring-4 focus:ring-yellow-300"
                    >
                        Get Started
                    </Link>
                    {/* <Link
                        href="https://nextjs.org"
                        target="_blank"
                        className="rounded-full bg-indigo-700/50 px-8 py-4 text-lg font-bold text-white shadow-lg backdrop-blur-sm transition-all hover:bg-indigo-700/70 hover:scale-105 focus:outline-none focus:ring-4 focus:ring-indigo-300"
                    >
                        Learn More
                    </Link> */}
                </div>
            </main>

            <footer className="absolute bottom-4 text-sm text-indigo-200">
                &copy; {new Date().getFullYear()} TDP Email Agent. All rights reserved.
            </footer>
        </div>
    );
}
