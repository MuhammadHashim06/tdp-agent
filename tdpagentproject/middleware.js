import { NextResponse } from 'next/server';

export function middleware(request) {
    const token = request.cookies.get('auth_token');
    const isDashboard = request.nextUrl.pathname.startsWith('/dashboard');
    const isLoginPage = request.nextUrl.pathname === '/login';

    // If trying to access dashboard without token, redirect to login
    if (isDashboard && !token) {
        return NextResponse.redirect(new URL('/login', request.url));
    }

    // If trying to access login page WITH token, redirect to dashboard
    if (isLoginPage && token) {
        return NextResponse.redirect(new URL('/dashboard', request.url));
    }

    return NextResponse.next();
}

export const config = {
    matcher: ['/dashboard/:path*', '/login'],
};
