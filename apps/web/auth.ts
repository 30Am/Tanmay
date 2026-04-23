import NextAuth, { type DefaultSession } from "next-auth";
import Credentials from "next-auth/providers/credentials";
import Google from "next-auth/providers/google";

/**
 * NextAuth v5 config.
 *
 * Two providers:
 *   • Google — real OAuth, active once GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET are set.
 *   • Credentials — dev-only demo login. Accepts:
 *        demo@withtanmay.com / demo
 *      Clearly marked as a demo: in production, swap for a real user store
 *      (Supabase / Postgres + bcrypt password hash, Clerk, etc.).
 *
 * Session strategy: JWT (no database required).
 */

// Extend the session type so TS knows about the fields we pass through.
declare module "next-auth" {
  interface Session {
    user: {
      id?: string;
      plan?: string;
    } & DefaultSession["user"];
  }
}

const DEMO_USERS: { id: string; email: string; name: string; password: string; plan: string }[] = [
  { id: "demo-1", email: "demo@withtanmay.com", name: "Demo User", password: "demo", plan: "Pro" },
  { id: "demo-2", email: "amlan@withtanmay.com", name: "Amlan", password: "amlan", plan: "Studio · Pro" },
];

const googleEnabled = !!(process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET);

export const { handlers, auth, signIn, signOut } = NextAuth({
  trustHost: true,
  session: { strategy: "jwt" },
  providers: [
    ...(googleEnabled
      ? [
          Google({
            clientId: process.env.GOOGLE_CLIENT_ID,
            clientSecret: process.env.GOOGLE_CLIENT_SECRET,
          }),
        ]
      : []),
    Credentials({
      name: "Email",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(c) {
        const email = String(c?.email || "").trim().toLowerCase();
        const password = String(c?.password || "");
        const found = DEMO_USERS.find((u) => u.email === email && u.password === password);
        if (!found) return null;
        return {
          id: found.id,
          email: found.email,
          name: found.name,
          // plan gets carried through via the jwt callback below
          plan: found.plan,
        } as unknown as { id: string; email: string; name: string; plan: string };
      },
    }),
  ],
  pages: {
    signIn: "/sign-in",
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = (user as { id?: string }).id ?? token.sub;
        token.plan = (user as { plan?: string }).plan ?? "Pro";
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        const id = typeof token.id === "string" ? token.id : (token.sub ?? "");
        session.user.id = id;
        session.user.plan = typeof token.plan === "string" ? token.plan : "Pro";
      }
      return session;
    },
  },
});
