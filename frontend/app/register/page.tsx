"use client";

import { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/input";
import { PasswordInput } from "@/components/ui/password-input";
import { Card } from "@/components/ui/card";
import { ApiError } from "@/lib/api";

export default function RegisterPage() {
  const { register } = useAuth();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await register(email, password, fullName);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-paper px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="postmark mx-auto mb-4 w-fit text-ledger">New Entry</div>
          <h1 className="font-display text-2xl font-bold text-ink">Create your account</h1>
          <p className="mt-1 text-sm text-ink-soft">Start logging applications in minutes.</p>
        </div>
        <Card className="p-6">
          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <Label htmlFor="fullName">Full name</Label>
              <Input id="fullName" required value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Jane Doe" />
            </div>
            <div>
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <PasswordInput id="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="At least 8 characters" />
            </div>
            {error && <p className="text-sm text-stamp-red">{error}</p>}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Creating account…" : "Create account"}
            </Button>
          </form>
        </Card>
        <p className="mt-4 text-center text-sm text-ink-soft">
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-ledger hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
