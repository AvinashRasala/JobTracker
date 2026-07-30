"use client";

import { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/input";
import { PasswordInput } from "@/components/ui/password-input";
import { Card } from "@/components/ui/card";
import { api, ApiError } from "@/lib/api";

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [deactivated, setDeactivated] = useState(false);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setDeactivated(false);
    setLoading(true);
    try {
      await login(email, password);
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setDeactivated(true);
        setError(err.message);
      } else {
        setError(err instanceof ApiError ? err.message : "Something went wrong. Try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const onReactivate = async () => {
    setError(null);
    setLoading(true);
    try {
      await api.reactivate(email, password);
      await login(email, password);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reactivate this account.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-paper px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="postmark mx-auto mb-4 w-fit text-ledger">Waybill 001</div>
          <h1 className="font-display text-2xl font-bold text-ink">JobTrack AI</h1>
          <p className="mt-1 text-sm text-ink-soft">Sign in to your application log.</p>
        </div>
        <Card className="p-6">
          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <PasswordInput id="password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
            </div>
            {error && <p className="text-sm text-stamp-red">{error}</p>}
            {deactivated ? (
              <Button type="button" variant="secondary" className="w-full" onClick={onReactivate} disabled={loading}>
                {loading ? "Reactivating…" : "Reactivate my account"}
              </Button>
            ) : (
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "Signing in…" : "Sign in"}
              </Button>
            )}
          </form>
        </Card>
        <p className="mt-4 text-center text-sm text-ink-soft">
          No account yet?{" "}
          <Link href="/register" className="font-medium text-ledger hover:underline">
            Register
          </Link>
        </p>
      </div>
    </div>
  );
}
