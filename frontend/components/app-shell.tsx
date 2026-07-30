"use client";

import { ReactNode, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LayoutDashboard, ListChecks, LogOut, BellRing, Trophy, Settings } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { getToken } from "@/lib/api";
import { cn } from "@/lib/cn";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/applications", label: "Applications", icon: ListChecks },
  { href: "/follow-ups", label: "Follow-ups", icon: BellRing },
  { href: "/offers", label: "Offers", icon: Trophy },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { logout } = useAuth();

  useEffect(() => {
    if (!getToken()) router.replace("/login");
  }, [router]);

  return (
    <div className="flex min-h-screen bg-paper">
      <aside className="flex w-56 flex-shrink-0 flex-col bg-ledger text-white">
        <div className="px-5 py-6">
          <div className="postmark w-fit border-white/50 text-white">Live Log</div>
          <h1 className="mt-3 font-display text-lg font-bold">JobTrack AI</h1>
        </div>
        <nav className="flex-1 space-y-1 px-3">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = pathname?.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                  active ? "bg-white/15 font-medium text-white" : "text-white/70 hover:bg-white/10 hover:text-white"
                )}
              >
                <Icon size={16} strokeWidth={2} />
                {label}
              </Link>
            );
          })}
        </nav>
        <div className="px-3 pb-6">
          <button
            onClick={logout}
            className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm text-white/70 transition-colors hover:bg-white/10 hover:text-white"
          >
            <LogOut size={16} strokeWidth={2} />
            Sign out
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto px-8 py-8">{children}</main>
    </div>
  );
}
