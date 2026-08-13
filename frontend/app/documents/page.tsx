"use client";

import { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Upload, Trash2, FileText, ExternalLink } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Dialog } from "@/components/ui/dialog";
import { api, resolveAssetUrl, ApiError } from "@/lib/api";
import { DocumentType, DOCUMENT_TYPE_LABELS } from "@/lib/types";
import { formatDateShort } from "@/lib/dates";

const TYPE_OPTIONS = Object.entries(DOCUMENT_TYPE_LABELS) as [DocumentType, string][];

function formatFileSize(bytes: number | null): string {
  if (!bytes) return "";
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DocumentsPage() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [label, setLabel] = useState("");
  const [documentType, setDocumentType] = useState<DocumentType>("resume");
  const [error, setError] = useState<string | null>(null);

  const { data: documents, isLoading } = useQuery({
    queryKey: ["documents"],
    queryFn: () => api.listDocuments(),
  });

  const uploadMutation = useMutation({
    mutationFn: () => {
      if (!pendingFile) throw new Error("No file selected");
      return api.uploadDocument(pendingFile, label, documentType);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      setDialogOpen(false);
      setPendingFile(null);
      setLabel("");
      setError(null);
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Upload failed."),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteDocument(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents"] }),
  });

  const onFileSelected = (file: File) => {
    setPendingFile(file);
    if (!label) setLabel(file.name.replace(/\.[^/.]+$/, ""));
    setDialogOpen(true);
  };

  return (
    <AppShell>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <p className="postmark w-fit text-ledger">Documents</p>
          <h2 className="mt-2 font-display text-2xl font-bold text-ink">Resumes &amp; files</h2>
          <p className="mt-1 text-sm text-ink-soft">
            Upload resumes, cover letters, and portfolios once — attach the right version to each
            application from its detail page.
          </p>
        </div>
        <div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) onFileSelected(file);
            }}
          />
          <Button onClick={() => fileInputRef.current?.click()}>
            <Upload size={16} /> Upload document
          </Button>
        </div>
      </div>

      <Card>
        {isLoading ? (
          <p className="p-6 text-sm text-ink-soft">Loading…</p>
        ) : !documents || documents.length === 0 ? (
          <div className="p-10 text-center">
            <FileText size={28} className="mx-auto text-ink-soft" />
            <p className="mt-3 text-sm font-medium text-ink">No documents uploaded yet.</p>
            <p className="mt-1 text-sm text-ink-soft">Upload your resume to get started.</p>
          </div>
        ) : (
          <div>
            {documents.map((doc) => (
              <div key={doc.id} className="ledger-row flex items-center justify-between gap-3 px-5 py-4">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="truncate font-medium text-ink">{doc.label}</p>
                    <span className="postmark text-ledger">{DOCUMENT_TYPE_LABELS[doc.document_type]}</span>
                  </div>
                  <p className="mt-0.5 font-mono text-xs text-ink-soft">
                    {doc.original_filename} · {formatFileSize(doc.file_size)} · uploaded {formatDateShort(doc.created_at)}
                  </p>
                </div>
                <div className="flex flex-shrink-0 items-center gap-3">
                  <a
                    href={resolveAssetUrl(doc.file_path) || "#"}
                    target="_blank"
                    rel="noreferrer"
                    className="text-ink-soft hover:text-ledger"
                    aria-label="Open document"
                  >
                    <ExternalLink size={16} />
                  </a>
                  <button
                    onClick={() => {
                      if (confirm(`Delete "${doc.label}"?`)) deleteMutation.mutate(doc.id);
                    }}
                    className="text-ink-soft hover:text-stamp-red"
                    aria-label="Delete document"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Dialog
        open={dialogOpen}
        onClose={() => {
          setDialogOpen(false);
          setPendingFile(null);
          setError(null);
        }}
        title="Confirm upload"
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            uploadMutation.mutate();
          }}
          className="space-y-4"
        >
          <p className="text-sm text-ink-soft">{pendingFile?.name}</p>
          <div>
            <Label htmlFor="label">Label</Label>
            <Input id="label" required value={label} onChange={(e) => setLabel(e.target.value)} placeholder="e.g. Resume - Backend focus" />
          </div>
          <div>
            <Label htmlFor="document_type">Type</Label>
            <Select id="document_type" value={documentType} onChange={(e) => setDocumentType(e.target.value as DocumentType)}>
              {TYPE_OPTIONS.map(([value, text]) => (
                <option key={value} value={value}>
                  {text}
                </option>
              ))}
            </Select>
          </div>
          {error && <p className="text-sm text-stamp-red">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={uploadMutation.isPending}>
              {uploadMutation.isPending ? "Uploading…" : "Upload"}
            </Button>
          </div>
        </form>
      </Dialog>
    </AppShell>
  );
}
