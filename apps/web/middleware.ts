import { auth } from "@/auth";
import { NextResponse } from "next/server";

/**
 * Protects /app/* — unauthenticated users get bounced to /sign-in with a
 * `next` query param so we can return them to where they were going.
 */
export default auth((req) => {
  const { pathname, search } = req.nextUrl;
  const isProtected = pathname.startsWith("/app");
  const isAuthed = !!req.auth;

  if (isProtected && !isAuthed) {
    const url = req.nextUrl.clone();
    url.pathname = "/sign-in";
    url.search = `?next=${encodeURIComponent(pathname + search)}`;
    return NextResponse.redirect(url);
  }

  // If a signed-in user hits /sign-in, bounce them to /app
  if (pathname === "/sign-in" && isAuthed) {
    const url = req.nextUrl.clone();
    url.pathname = "/app";
    url.search = "";
    return NextResponse.redirect(url);
  }
});

export const config = {
  matcher: ["/app/:path*", "/sign-in"],
};
