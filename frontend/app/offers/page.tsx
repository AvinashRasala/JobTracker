"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Trophy } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Card } from "@/components/ui/card";
import { api } from "@/lib/api";

function formatCtc(value: number | null, currency: string | null) {
  if (value == null) return "—";
  return `${currency || ""} ${value.toLocaleString()}`.trim();
}

export default function OffersPage() {
  const { data: offers, isLoading } = useQuery({
    queryKey: ["offers"],
    queryFn: api.compareOffers,
  });

  const best = offers && offers.length > 0 ? Math.max(...offers.map((o) => o.offered_ctc || 0)) : null;

  return (
    <AppShell>
      <div className="mb-6">
        <p className="postmark w-fit text-ledger">Comparison</p>
        <h2 className="mt-2 font-display text-2xl font-bold text-ink">Offers</h2>
        <p className="mt-1 text-sm text-ink-soft">
          Every application that reached an offer, side by side, so you can compare before deciding.
        </p>
      </div>

      {isLoading ? (
        <p className="text-sm text-ink-soft">Loading…</p>
      ) : !offers || offers.length === 0 ? (
        <Card className="p-10 text-center">
          <Trophy size={28} className="mx-auto text-ink-soft" />
          <p className="mt-3 text-sm font-medium text-ink">No offers yet.</p>
          <p className="mt-1 text-sm text-ink-soft">
            Once an application's status is set to "Offer Received", it'll show up here.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {offers.map((offer) => (
            <Card key={offer.id} className={`p-5 ${offer.offered_ctc === best && best ? "border-stamp-green" : ""}`}>
              {offer.offered_ctc === best && best ? (
                <p className="postmark mb-2 w-fit text-stamp-green">Highest offer</p>
              ) : null}
              <Link href={`/applications/${offer.id}`} className="font-display text-base font-semibold text-ink hover:text-ledger hover:underline">
                {offer.role_title}
              </Link>
              <p className="text-sm text-ink-soft">{offer.company_name || "—"}</p>

              <div className="mt-4 space-y-2 border-t border-hairline pt-4 text-sm">
                <div className="flex justify-between">
                  <span className="text-ink-soft">Offered CTC</span>
                  <span className="font-mono font-medium text-stamp-green">
                    {formatCtc(offer.offered_ctc, offer.salary_currency)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ink-soft">Expected CTC</span>
                  <span className="font-mono text-ink">{formatCtc(offer.expected_ctc, offer.salary_currency)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ink-soft">Notice period</span>
                  <span className="font-mono text-ink">
                    {offer.notice_period_days != null ? `${offer.notice_period_days} days` : "—"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ink-soft">Location</span>
                  <span className="text-ink">{offer.location || "—"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-ink-soft">Work type</span>
                  <span className="text-ink">{offer.work_type !== "unknown" ? offer.work_type : "—"}</span>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </AppShell>
  );
}
