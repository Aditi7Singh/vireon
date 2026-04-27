"use client";

import { useState, useRef } from "react";
import TopBar from "@/components/TopBar";
import { cn } from "@/lib/utils";
import {
  Upload, FileText, CheckCircle2, AlertCircle, X, Download,
  Table, ArrowRight, RefreshCw, Sparkles, ChevronDown,
  FileSpreadsheet, Database, CreditCard, Users, Receipt,
} from "lucide-react";

type ImportType = "bank_statement" | "invoices" | "expenses" | "contacts" | "payroll" | "gl_entries";
type ImportStatus = "idle" | "uploading" | "mapping" | "preview" | "importing" | "done" | "error";

const IMPORT_TYPES: { id: ImportType; label: string; icon: React.ElementType; desc: string; formats: string[] }[] = [
  { id: "bank_statement", label: "Bank Statement", icon: CreditCard, desc: "Import transactions from bank CSV/OFX/QFX", formats: ["CSV", "OFX", "QFX", "XLSX"] },
  { id: "invoices", label: "Invoices / AR", icon: FileText, desc: "Bulk import customer invoices", formats: ["CSV", "XLSX"] },
  { id: "expenses", label: "Expenses", icon: Receipt, desc: "Upload expense records from any source", formats: ["CSV", "XLSX"] },
  { id: "contacts", label: "Customers & Vendors", icon: Users, desc: "Import contact directory", formats: ["CSV", "XLSX", "VCF"] },
  { id: "payroll", label: "Payroll Data", icon: Users, desc: "Import salary and payroll records", formats: ["CSV", "XLSX"] },
  { id: "gl_entries", label: "GL / Journal Entries", icon: Database, desc: "Import general ledger entries", formats: ["CSV", "XLSX"] },
];

const SAMPLE_BANK_PREVIEW = [
  { date: "2026-04-27", description: "AWS Cloud Services", amount: "-48,500", category: "Infrastructure", status: "new" },
  { date: "2026-04-26", description: "Client Payment - Acme Corp", amount: "1,85,000", category: "Revenue", status: "new" },
  { date: "2026-04-25", description: "Office Rent April", amount: "-1,25,000", category: "Rent", status: "duplicate" },
  { date: "2026-04-25", description: "Payroll - Engineering Team", amount: "-8,40,000", category: "Payroll", status: "new" },
  { date: "2026-04-24", description: "Zoom Pro Annual", amount: "-14,999", category: "Software", status: "new" },
  { date: "2026-04-23", description: "Google Workspace 20 seats", amount: "-18,000", category: "Software", status: "new" },
];

const FIELD_MAPPINGS: Record<ImportType, { field: string; mapTo: string }[]> = {
  bank_statement: [
    { field: "Date", mapTo: "transaction_date" },
    { field: "Description", mapTo: "description" },
    { field: "Amount", mapTo: "amount" },
    { field: "Balance", mapTo: "running_balance" },
  ],
  invoices: [
    { field: "Invoice #", mapTo: "invoice_number" },
    { field: "Customer", mapTo: "contact_name" },
    { field: "Amount", mapTo: "total_amount" },
    { field: "Due Date", mapTo: "due_date" },
  ],
  expenses: [
    { field: "Date", mapTo: "expense_date" },
    { field: "Merchant", mapTo: "vendor_name" },
    { field: "Amount", mapTo: "amount" },
    { field: "Category", mapTo: "category" },
  ],
  contacts: [
    { field: "Name", mapTo: "contact_name" },
    { field: "Email", mapTo: "email" },
    { field: "Phone", mapTo: "phone" },
    { field: "Type", mapTo: "contact_type" },
  ],
  payroll: [
    { field: "Employee", mapTo: "employee_name" },
    { field: "Gross Pay", mapTo: "gross_pay" },
    { field: "Net Pay", mapTo: "net_pay" },
    { field: "Pay Date", mapTo: "pay_date" },
  ],
  gl_entries: [
    { field: "Date", mapTo: "entry_date" },
    { field: "Account", mapTo: "account_code" },
    { field: "Debit", mapTo: "debit_amount" },
    { field: "Credit", mapTo: "credit_amount" },
  ],
};

const RECENT_IMPORTS = [
  { name: "HDFC_Statement_Apr2026.csv", type: "bank_statement", date: "2026-04-27", rows: 142, status: "success" },
  { name: "Invoices_Q1_2026.xlsx", type: "invoices", date: "2026-04-15", rows: 38, status: "success" },
  { name: "Expenses_Mar2026.csv", type: "expenses", date: "2026-04-01", rows: 67, status: "success" },
  { name: "Payroll_Mar2026.xlsx", type: "payroll", date: "2026-03-31", rows: 18, status: "partial" },
  { name: "Vendors_Master.csv", type: "contacts", date: "2026-03-15", rows: 24, status: "success" },
];

export default function DataImportPage() {
  const [selectedType, setSelectedType] = useState<ImportType>("bank_statement");
  const [status, setStatus] = useState<ImportStatus>("idle");
  const [isDragging, setIsDragging] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = () => setIsDragging(false);
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) simulateUpload(file.name);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) simulateUpload(file.name);
  };

  const simulateUpload = (name: string) => {
    setFileName(name);
    setStatus("uploading");
    setProgress(0);
    const interval = setInterval(() => {
      setProgress(p => {
        if (p >= 100) {
          clearInterval(interval);
          setStatus("mapping");
          return 100;
        }
        return p + 20;
      });
    }, 200);
  };

  const handleImport = () => {
    setStatus("importing");
    setProgress(0);
    const interval = setInterval(() => {
      setProgress(p => {
        if (p >= 100) {
          clearInterval(interval);
          setStatus("done");
          return 100;
        }
        return p + 10;
      });
    }, 150);
  };

  const handleReset = () => {
    setStatus("idle");
    setFileName(null);
    setProgress(0);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const selectedConfig = IMPORT_TYPES.find(t => t.id === selectedType)!;
  const mappings = FIELD_MAPPINGS[selectedType];

  return (
    <div className="min-h-screen bg-[#f6f3ee] pb-14 text-[#1d1b17]">
      <TopBar title="Import Data" />

      <div className="mx-auto max-w-6xl space-y-6 px-4 pt-6 sm:px-6 lg:px-8">

        {/* Hero */}
        <section className="rounded-3xl border border-[#d9cdbc] bg-[linear-gradient(145deg,#fff8ec_0%,#f3eadb_100%)] p-6 shadow-[0_18px_48px_rgba(63,45,24,0.1)] sm:p-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-[#d9c29a] bg-[#fff4dd] px-3 py-1 text-xs font-semibold text-[#8c5c19]">
                <Upload className="h-3.5 w-3.5" /> Data Import
              </p>
              <h1 className="mt-2 text-2xl font-bold text-[#2c2013]">Import Financial Data</h1>
              <p className="mt-1 text-sm text-[#5f5344]">
                Upload CSV, Excel, OFX or QFX files. Auto-map columns, detect duplicates, and import with one click.
              </p>
            </div>
            <button className="inline-flex items-center gap-2 rounded-xl border border-[#d9c29a] bg-white/80 px-4 py-2.5 text-sm font-medium text-[#6b4c1e] hover:bg-white w-fit">
              <Download className="h-4 w-4" /> Download Templates
            </button>
          </div>
        </section>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Left: Type Selector */}
          <div className="space-y-3 lg:col-span-1">
            <h2 className="text-sm font-bold text-[#2a2017] uppercase tracking-wider">What are you importing?</h2>
            {IMPORT_TYPES.map((type) => {
              const Icon = type.icon;
              return (
                <button
                  key={type.id}
                  onClick={() => { setSelectedType(type.id); handleReset(); }}
                  className={cn(
                    "w-full text-left rounded-2xl border p-4 transition-all",
                    selectedType === type.id
                      ? "border-[#b3622d] bg-[#fff8ec] shadow-sm"
                      : "border-[#ddd2c2] bg-[#fffdf8] hover:border-[#c4a882]"
                  )}
                >
                  <div className="flex items-center gap-3">
                    <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center",
                      selectedType === type.id ? "bg-[#b3622d]/15" : "bg-[#f0e8dc]"
                    )}>
                      <Icon className={cn("h-4 w-4", selectedType === type.id ? "text-[#8d4f27]" : "text-[#87602a]")} />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-[#2a2017]">{type.label}</p>
                      <p className="text-[10px] text-[#9a8872]">{type.formats.join(" · ")}</p>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Right: Upload + Steps */}
          <div className="lg:col-span-2 space-y-5">
            {status === "idle" && (
              <>
                <div
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className={cn(
                    "rounded-2xl border-2 border-dashed p-10 text-center cursor-pointer transition-all",
                    isDragging
                      ? "border-[#b3622d] bg-[#fff8ec]"
                      : "border-[#d4c3ae] bg-[#fffdf8] hover:border-[#b3622d] hover:bg-[#fff8ec]"
                  )}
                >
                  <input ref={fileInputRef} type="file" accept=".csv,.xlsx,.xls,.ofx,.qfx" className="hidden" onChange={handleFileSelect} />
                  <Upload className="h-10 w-10 text-[#9a8872] mx-auto mb-3" />
                  <p className="text-base font-bold text-[#2a2017]">Drop your file here, or click to browse</p>
                  <p className="text-sm text-[#9a8872] mt-1">
                    Supports {selectedConfig.formats.join(", ")} · Max 50MB
                  </p>
                  <button className="mt-4 inline-flex items-center gap-2 rounded-xl bg-[#231c15] px-5 py-2.5 text-sm font-medium text-[#fff7eb]">
                    <Upload className="h-4 w-4" /> Choose File
                  </button>
                </div>

                {/* Field mapping preview */}
                <div className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Table className="h-4 w-4 text-[#87602a]" />
                    <h3 className="text-sm font-bold text-[#2a2017]">Expected Column Mapping</h3>
                  </div>
                  <div className="space-y-2">
                    {mappings.map((m, i) => (
                      <div key={i} className="flex items-center gap-3 text-sm">
                        <span className="flex-1 rounded-lg bg-[#f0e8dc] px-3 py-1.5 text-xs font-mono font-semibold text-[#5f5344]">{m.field}</span>
                        <ArrowRight className="h-3.5 w-3.5 text-[#9a8872] shrink-0" />
                        <span className="flex-1 rounded-lg bg-blue-50 border border-blue-100 px-3 py-1.5 text-xs font-mono font-semibold text-blue-700">{m.mapTo}</span>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-[#9a8872] mt-3">Column names are auto-detected. You can remap them in the next step.</p>
                </div>
              </>
            )}

            {status === "uploading" && (
              <div className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-8 text-center">
                <RefreshCw className="h-10 w-10 text-[#87602a] mx-auto mb-3 animate-spin" />
                <p className="text-base font-bold text-[#2a2017]">Uploading {fileName}…</p>
                <div className="mt-4 h-2 rounded-full bg-[#f0e8dc] overflow-hidden">
                  <div className="h-2 rounded-full bg-[#b3622d] transition-all duration-300" style={{ width: `${progress}%` }} />
                </div>
                <p className="text-xs text-[#9a8872] mt-2">{progress}% uploaded</p>
              </div>
            )}

            {status === "mapping" && (
              <div className="space-y-4">
                <div className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-5">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-sm font-bold text-[#2a2017]">Column Mapping — {fileName}</h3>
                      <p className="text-xs text-[#9a8872] mt-0.5">Auto-detected from file headers. Adjust if needed.</p>
                    </div>
                    <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-1 rounded-full flex items-center gap-1">
                      <CheckCircle2 className="h-3 w-3" /> All columns matched
                    </span>
                  </div>
                  <div className="space-y-2">
                    {mappings.map((m, i) => (
                      <div key={i} className="flex items-center gap-3">
                        <span className="flex-1 rounded-lg bg-[#f0e8dc] px-3 py-2 text-xs font-mono font-semibold text-[#5f5344]">{m.field}</span>
                        <ArrowRight className="h-3.5 w-3.5 text-[#9a8872] shrink-0" />
                        <select className="flex-1 rounded-lg border border-[#ddd2c2] bg-[#faf7f3] px-2 py-2 text-xs outline-none">
                          <option>{m.mapTo}</option>
                        </select>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Preview table */}
                <div className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] overflow-hidden">
                  <div className="px-5 py-3 border-b border-[#ede8e0]">
                    <h3 className="text-sm font-bold text-[#2a2017]">Data Preview (first 6 rows)</h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead className="bg-[#f9f5ef] text-[#776b5a]">
                        <tr>
                          <th className="px-4 py-2.5 text-left font-bold">Date</th>
                          <th className="px-4 py-2.5 text-left font-bold">Description</th>
                          <th className="px-4 py-2.5 text-right font-bold">Amount</th>
                          <th className="px-4 py-2.5 text-left font-bold">Category</th>
                          <th className="px-4 py-2.5 text-left font-bold">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#f0ebe3]">
                        {SAMPLE_BANK_PREVIEW.map((row, i) => (
                          <tr key={i} className={cn("hover:bg-[#fdf9f4]", row.status === "duplicate" && "bg-amber-50/60")}>
                            <td className="px-4 py-2.5 font-mono text-[11px]">{row.date}</td>
                            <td className="px-4 py-2.5 text-[#2a2017]">{row.description}</td>
                            <td className={cn("px-4 py-2.5 text-right font-semibold", row.amount.startsWith("-") ? "text-red-600" : "text-emerald-700")}>
                              {row.amount.startsWith("-") ? "" : "+"}{row.amount}
                            </td>
                            <td className="px-4 py-2.5">
                              <span className="px-2 py-0.5 bg-[#f0e8dc] text-[#6b4c1e] rounded-md text-[10px] font-semibold">{row.category}</span>
                            </td>
                            <td className="px-4 py-2.5">
                              {row.status === "duplicate" ? (
                                <span className="flex items-center gap-1 text-amber-600 font-semibold text-[10px]">
                                  <AlertCircle className="h-3 w-3" /> Duplicate
                                </span>
                              ) : (
                                <span className="flex items-center gap-1 text-emerald-600 font-semibold text-[10px]">
                                  <CheckCircle2 className="h-3 w-3" /> New
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="px-5 py-3 border-t border-[#ede8e0] bg-[#faf7f3] flex items-center justify-between">
                    <p className="text-xs text-[#9a8872]">142 rows total · 1 duplicate detected · 141 new records</p>
                    <div className="flex gap-3">
                      <button onClick={handleReset} className="text-xs text-[#776b5a] hover:text-[#2a2017]">Cancel</button>
                      <button onClick={handleImport} className="rounded-xl bg-[#231c15] px-4 py-2 text-xs font-bold text-[#fff7eb] hover:bg-[#17120d] inline-flex items-center gap-2">
                        <Upload className="h-3.5 w-3.5" /> Import 141 Records
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {status === "importing" && (
              <div className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] p-8 text-center">
                <div className="w-14 h-14 rounded-2xl bg-[#f0e8dc] flex items-center justify-center mx-auto mb-3">
                  <Database className="h-7 w-7 text-[#87602a] animate-pulse" />
                </div>
                <p className="text-base font-bold text-[#2a2017]">Importing records…</p>
                <div className="mt-4 h-2 rounded-full bg-[#f0e8dc] overflow-hidden">
                  <div className="h-2 rounded-full bg-emerald-500 transition-all duration-300" style={{ width: `${progress}%` }} />
                </div>
                <p className="text-xs text-[#9a8872] mt-2">Processing {Math.floor(progress * 1.41)} of 141 records</p>
              </div>
            )}

            {status === "done" && (
              <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-8 text-center">
                <CheckCircle2 className="h-14 w-14 text-emerald-600 mx-auto mb-3" />
                <p className="text-xl font-black text-emerald-900">Import Complete!</p>
                <p className="text-sm text-emerald-700 mt-2">141 records imported successfully · 1 duplicate skipped</p>
                <div className="flex justify-center gap-3 mt-5">
                  <button onClick={handleReset} className="rounded-xl border border-emerald-300 px-4 py-2 text-sm font-medium text-emerald-700 hover:bg-emerald-100">
                    Import More
                  </button>
                  <button className="rounded-xl bg-[#231c15] px-4 py-2 text-sm font-medium text-[#fff7eb] hover:bg-[#17120d] inline-flex items-center gap-2">
                    <Sparkles className="h-4 w-4" /> Review with AI
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Recent Imports */}
        <section className="rounded-2xl border border-[#ddd2c2] bg-[#fffdf8] overflow-hidden">
          <div className="px-5 py-4 border-b border-[#ede8e0]">
            <h2 className="text-sm font-bold text-[#2a2017]">Recent Imports</h2>
          </div>
          <div className="divide-y divide-[#f0ebe3]">
            {RECENT_IMPORTS.map((imp, i) => {
              const typeConf = IMPORT_TYPES.find(t => t.id === imp.type)!;
              const Icon = typeConf?.icon || FileText;
              return (
                <div key={i} className="flex items-center gap-4 px-5 py-3.5 hover:bg-[#fdf9f4] transition-colors">
                  <div className="w-9 h-9 rounded-xl bg-[#f0e8dc] flex items-center justify-center shrink-0">
                    <Icon className="h-4.5 w-4.5 text-[#87602a]" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-[#2a2017] truncate">{imp.name}</p>
                    <p className="text-xs text-[#9a8872]">{typeConf?.label} · {imp.date} · {imp.rows} rows</p>
                  </div>
                  <span className={cn("text-[10px] font-black uppercase px-2.5 py-1 rounded-full",
                    imp.status === "success" ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"
                  )}>
                    {imp.status === "success" ? "✓ Success" : "⚠ Partial"}
                  </span>
                  <button className="text-xs text-[#776b5a] hover:text-[#2a2017]">
                    <Download className="h-4 w-4" />
                  </button>
                </div>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
}
