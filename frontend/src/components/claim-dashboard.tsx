"use client"

import type React from "react"
import { useState, useCallback } from "react"
import {
  Upload,
  FileText,
  CheckCircle,
  XCircle,
  AlertTriangle,
  ArrowRight,
  Loader2,
  RefreshCw,
  Activity,
  Files,
  BookOpen,
  X,
  Info
} from "lucide-react"
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// --- CONSTANTS: MOCK POLICY FOR DISPLAY ---
const POLICY_PREVIEW = {
  "policy_id": "PLUM_OPD_2024",
  "policy_name": "Plum OPD Advantage",
  "coverage_details": {
    "annual_limit": 50000,
    "per_claim_limit": 5000,
    "consultation_fees": { "covered": true, "copay_percentage": 10 },
    "pharmacy": { "covered": true, "sub_limit": 15000 }
  },
  "exclusions": [
    "Cosmetic procedures",
    "Weight loss treatments",
    "Vitamins (unless deficiency)"
  ]
}

// --- INTERFACES ---
interface BreakdownItem {
    label: string
    amount: number
    type: "info" | "deduction" | "final"
}

interface ClaimResponse {
  status: string
  claim_id?: number
  files_processed?: string[]
  extracted_data: {
    total_amount?: number
    diagnosis?: string
    lab_results?: { test_name: string, result: string, normal_range: string }[]
    member?: {
      member_id?: string
      join_date?: string
    }
    hospital?: {
      name?: string
    }
    [key: string]: any
  }
  decision: {
    decision: "APPROVED" | "REJECTED" | "MANUAL_REVIEW" | "PARTIAL_APPROVAL" | "PARTIAL"
    approved_amount: number
    reasons: string[]
    confidence?: number
    breakdown?: BreakdownItem[]
    summary_text?: string
    medical_context?: string
  }
}

export default function ClaimDashboard() {
  const [files, setFiles] = useState<File[]>([])
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<ClaimResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  
  // Modal States
  const [showPolicy, setShowPolicy] = useState(false)
  const [showHealthModal, setShowHealthModal] = useState(false)

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFilesSelect(e.dataTransfer.files)
    }
  }, [])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()
    if (e.target.files && e.target.files.length > 0) {
      handleFilesSelect(e.target.files)
    }
  }

  const handleFilesSelect = (fileList: FileList) => {
    const selectedFiles = Array.from(fileList)
    setFiles(selectedFiles)
    setResult(null)
    setError(null)

    const firstFile = selectedFiles[0]
    if (firstFile.type.startsWith("image/")) {
      const reader = new FileReader()
      reader.onloadend = () => {
        setPreviewUrl(reader.result as string)
      }
      reader.readAsDataURL(firstFile)
    } else {
      setPreviewUrl(null)
    }
  }

  const handleUpload = async () => {
    if (files.length === 0) return

    setIsLoading(true)
    setError(null)

    const formData = new FormData()
    files.forEach((file) => {
        formData.append("files", file)
    })

    try {
      const response = await fetch("http://localhost:8000/v1/claims/upload", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        const errorText = await response.text()
        let errorMessage = `Server error: ${response.status}`
        try {
            const errorJson = JSON.parse(errorText)
            if (errorJson.detail) errorMessage = errorJson.detail
        } catch (e) {
            if (errorText) errorMessage = errorText
        }
        throw new Error(errorMessage)
      }

      const data = await response.json()
      setResult(data)

    } catch (err) {
      console.error(err)
      setError(err instanceof Error ? err.message : "Backend connection failed.")
    } finally {
      setIsLoading(false)
    }
  }

  const reset = () => {
    setFiles([])
    setPreviewUrl(null)
    setResult(null)
    setError(null)
  }

  const renderStatusBadge = (status: string) => {
    switch (status) {
      case "APPROVED":
        return (
          <div className="flex items-center gap-2 px-6 py-2 rounded-full bg-green-100 text-green-700 border border-green-200 shadow-sm animate-in fade-in zoom-in duration-300">
            <CheckCircle className="w-5 h-5" />
            <span className="font-bold tracking-wide text-sm">APPROVED</span>
          </div>
        )
      case "PARTIAL":
      case "PARTIAL_APPROVAL":
        return (
            <div className="flex items-center gap-2 px-6 py-2 rounded-full bg-blue-100 text-blue-700 border border-blue-200 shadow-sm animate-in fade-in zoom-in duration-300">
              <CheckCircle className="w-5 h-5" />
              <span className="font-bold tracking-wide text-sm">PARTIAL</span>
            </div>
          )
      case "REJECTED":
        return (
          <div className="flex items-center gap-2 px-6 py-2 rounded-full bg-red-100 text-red-700 border border-red-200 shadow-sm animate-in fade-in zoom-in duration-300">
            <XCircle className="w-5 h-5" />
            <span className="font-bold tracking-wide text-sm">REJECTED</span>
          </div>
        )
      case "MANUAL_REVIEW":
      default:
        return (
          <div className="flex items-center gap-2 px-6 py-2 rounded-full bg-amber-100 text-amber-700 border border-amber-200 shadow-sm animate-in fade-in zoom-in duration-300">
            <AlertTriangle className="w-5 h-5" />
            <span className="font-bold tracking-wide text-sm">MANUAL REVIEW</span>
          </div>
        )
    }
  }

  const renderReasonIcon = (status: string) => {
    if (status === "APPROVED" || status === "PARTIAL" || status === "PARTIAL_APPROVAL") return <CheckCircle className="w-5 h-5 text-green-500 shrink-0" />
    if (status === "REJECTED") return <XCircle className="w-5 h-5 text-red-500 shrink-0" />
    return <Activity className="w-5 h-5 text-amber-500 shrink-0" />
  }

  return (
    <div className="w-full max-w-6xl bg-white rounded-2xl shadow-xl overflow-hidden flex flex-col lg:flex-row min-h-[600px] relative">
      
      {/* --- POLICY MODAL --- */}
      {showPolicy && (
        <div className="absolute inset-0 z-50 bg-black/50 flex items-center justify-center p-4 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-white w-full max-w-md rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
                <div className="bg-fuchsia-50 p-4 border-b border-fuchsia-100 flex justify-between items-center">
                    <div className="flex items-center gap-2">
                        <BookOpen className="w-5 h-5 text-fuchsia-600" />
                        <h3 className="font-bold text-gray-800">Policy Lens: PLUM_OPD_2024</h3>
                    </div>
                    <button onClick={() => setShowPolicy(false)} className="text-gray-400 hover:text-gray-700">
                        <X className="w-5 h-5" />
                    </button>
                </div>
                <div className="p-6 max-h-[400px] overflow-y-auto bg-gray-50">
                    <div className="space-y-6 p-2">
                        {/* 1. Limits */}
                        <div>
                            <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Coverage Limits</h4>
                            <div className="grid grid-cols-2 gap-3">
                                <div className="bg-fuchsia-50 p-3 rounded-lg border border-fuchsia-100">
                                    <span className="block text-xs text-fuchsia-600 mb-1">Annual Limit</span>
                                    <span className="block text-lg font-bold text-gray-800">₹{POLICY_PREVIEW.coverage_details.annual_limit.toLocaleString()}</span>
                                </div>
                                <div className="bg-purple-50 p-3 rounded-lg border border-purple-100">
                                    <span className="block text-xs text-purple-600 mb-1">Per Claim Limit</span>
                                    <span className="block text-lg font-bold text-gray-800">₹{POLICY_PREVIEW.coverage_details.per_claim_limit.toLocaleString()}</span>
                                </div>
                            </div>
                        </div>

                        {/* 2. Rules */}
                        <div>
                            <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Key Rules</h4>
                            <div className="space-y-2">
                                <div className="flex justify-between items-center text-sm p-2 bg-gray-50 rounded">
                                    <span className="text-gray-600">Consultation Co-pay</span>
                                    <span className="font-semibold text-gray-900">{POLICY_PREVIEW.coverage_details.consultation_fees.copay_percentage}%</span>
                                </div>
                                <div className="flex justify-between items-center text-sm p-2 bg-gray-50 rounded">
                                    <span className="text-gray-600">Pharmacy Sub-limit</span>
                                    <span className="font-semibold text-gray-900">₹{POLICY_PREVIEW.coverage_details.pharmacy.sub_limit.toLocaleString()}</span>
                                </div>
                            </div>
                        </div>

                        {/* 3. Exclusions */}
                        <div>
                            <h4 className="text-xs font-bold text-red-400 uppercase tracking-wider mb-3">Exclusions</h4>
                            <ul className="list-disc pl-5 space-y-1">
                                {POLICY_PREVIEW.exclusions.map((ex, i) => (
                                    <li key={i} className="text-sm text-gray-600">{ex}</li>
                                ))}
                            </ul>
                        </div>
                    </div>
                </div>
                <div className="p-4 border-t border-gray-100 bg-white text-center">
                    <button onClick={() => setShowPolicy(false)} className="text-sm font-semibold text-fuchsia-600 hover:text-fuchsia-800">
                        Close Viewer
                    </button>
                </div>
            </div>
        </div>
      )}

      {/* --- HEALTH CONTEXT MODAL (Themed to match Adjudicate Button) --- */}
      {showHealthModal && result?.decision.medical_context && (
        <div className="absolute inset-0 z-50 bg-black/50 flex items-center justify-center p-4 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-white w-full max-w-md rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
                {/* GRADIENT HEADER TO MATCH BUTTON */}
                <div className="bg-gradient-to-r from-fuchsia-600 to-purple-600 p-4 flex justify-between items-center">
                    <div className="flex items-center gap-2 text-white">
                        <Activity className="w-5 h-5" />
                        <h3 className="font-bold">Health Insight</h3>
                    </div>
                    <button onClick={() => setShowHealthModal(false)} className="text-white/80 hover:text-white">
                        <X className="w-5 h-5" />
                    </button>
                </div>
                <div className="p-6">
                    <h4 className="text-lg font-bold text-gray-800 mb-2">
                        {result.extracted_data.diagnosis || result.extracted_data.lab_results?.[0]?.test_name || "Medical Analysis"}
                    </h4>
                    <p className="text-gray-600 text-sm leading-relaxed whitespace-pre-wrap">
                        {result.decision.medical_context}
                    </p>
                    <div className="mt-6 p-3 bg-amber-50 border border-amber-100 rounded text-xs text-amber-700 italic">
                        Disclaimer: This content is AI-generated for informational purposes only. It is not medical advice.
                    </div>
                </div>
            </div>
        </div>
      )}

      {/* Left Panel: Upload & Preview */}
      <div className="w-full lg:w-1/2 p-8 border-b lg:border-b-0 lg:border-r border-gray-100 flex flex-col">
        <h2 className="text-2xl font-bold text-gray-800 mb-1 flex items-center gap-2">
          <span className="w-2 h-8 bg-fuchsia-600 rounded-full block"></span>
          Upload Medical Bill
        </h2>
        <p className="text-gray-500 mb-8 pl-4 text-sm">Drag and drop your claim documents here</p>

        <div className="flex-1 flex flex-col">
          {files.length === 0 ? (
            <div
              className={cn(
                "flex-1 border-3 border-dashed rounded-xl transition-all duration-300 flex flex-col items-center justify-center p-8 cursor-pointer group bg-gray-50/50",
                dragActive
                  ? "border-fuchsia-500 bg-fuchsia-50 shadow-[0_0_30px_rgba(192,38,211,0.2)] scale-[1.02]"
                  : "border-gray-200 hover:border-fuchsia-300 hover:bg-gray-50",
              )}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => document.getElementById("file-upload")?.click()}
            >
              <input
                id="file-upload"
                type="file"
                className="hidden"
                multiple 
                onChange={handleChange}
                accept="image/*,application/pdf"
              />
              <div className={cn(
                  "w-20 h-20 rounded-full flex items-center justify-center mb-4 transition-colors",
                  dragActive ? "bg-white text-fuchsia-600" : "bg-fuchsia-100 text-fuchsia-600 group-hover:scale-110 group-hover:shadow-lg duration-300"
                )}
              >
                <Upload className="w-10 h-10" />
              </div>
              <p className="text-lg font-medium text-gray-700 mb-2">Click to upload or drag & drop</p>
              <p className="text-sm text-gray-400">PDF or Images (JPG, PNG)</p>
            </div>
          ) : (
            <div className="flex-1 relative rounded-xl overflow-hidden border border-gray-200 bg-gray-50 flex flex-col">
              <div className="absolute top-4 right-4 z-10">
                <button
                  onClick={reset}
                  className="bg-white/90 hover:bg-white text-gray-500 hover:text-red-500 p-2 rounded-full shadow-md transition-all backdrop-blur-sm"
                >
                  <XCircle className="w-5 h-5" />
                </button>
              </div>

              <div className="flex-1 flex flex-col items-center justify-center p-4 bg-gray-100/50">
                {previewUrl ? (
                  <img src={previewUrl || "/placeholder.svg"} alt="Preview" className="max-h-[300px] object-contain rounded shadow-sm mb-4" />
                ) : (
                   <div className="mb-4 text-fuchsia-300"><Files className="w-20 h-20 mx-auto" /></div>
                )}
                
                <div className="bg-white p-3 rounded-lg shadow-sm border border-gray-200 w-full max-w-sm">
                    <div className="text-sm font-semibold text-gray-700 mb-2 flex justify-between">
                        <span>Selected Documents</span>
                        <span className="bg-fuchsia-100 text-fuchsia-700 px-2 py-0.5 rounded-full text-xs">
                            {files.length}
                        </span>
                    </div>
                    <div className="max-h-32 overflow-y-auto space-y-1">
                        {files.map((f, i) => (
                            <div key={i} className="text-xs text-gray-500 flex items-center gap-2">
                                <FileText className="w-3 h-3" />
                                <span className="truncate">{f.name}</span>
                            </div>
                        ))}
                    </div>
                </div>
              </div>
            </div>
          )}

          <div className="mt-8">
            <button
              onClick={handleUpload}
              disabled={files.length === 0 || isLoading}
              className={cn(
                "w-full py-4 rounded-xl font-bold text-lg text-white shadow-lg transition-all transform duration-200 flex items-center justify-center gap-2",
                files.length === 0 || isLoading
                  ? "bg-gray-300 cursor-not-allowed shadow-none"
                  : "bg-gradient-to-r from-fuchsia-600 to-purple-600 hover:from-fuchsia-500 hover:to-purple-500 hover:shadow-fuchsia-200 hover:-translate-y-1 active:scale-[0.99]",
              )}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-6 h-6 animate-spin" />
                  Processing Claim...
                </>
              ) : (
                <>Adjudicate Claim<ArrowRight className="w-5 h-5" /></>
              )}
            </button>

            {error && (
              <div className="mt-4 p-4 bg-red-50 text-red-600 rounded-lg text-sm flex items-start gap-2">
                <AlertTriangle className="w-5 h-5 shrink-0" />
                <p>{error}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Right Panel: AI Results */}
      <div className="w-full lg:w-1/2 bg-gray-50/30 p-8 flex flex-col relative">
        {!result ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center text-gray-400">
            <div className="w-32 h-32 bg-gray-100 rounded-full flex items-center justify-center mb-6 animate-pulse">
              <Activity className="w-16 h-16 text-gray-300" />
            </div>
            <h3 className="text-xl font-semibold text-gray-600 mb-2">Waiting for documents...</h3>
            <p className="max-w-xs mx-auto text-sm text-gray-400">
              Upload bills and prescriptions to receive an instant AI adjudication decision.
            </p>
          </div>
        ) : (
          <div className="flex-1 flex flex-col animate-in slide-in-from-right-4 duration-500 fade-in overflow-y-auto max-h-[600px] pr-2">
            
            {/* Header Section */}
            <div className="flex flex-col items-center mb-8">
              <div className="flex items-center gap-3">
                  {renderStatusBadge(result.decision.decision)}
                  
                  <button 
                    onClick={() => setShowPolicy(true)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white border border-gray-200 shadow-sm hover:bg-gray-50 hover:border-fuchsia-200 transition-all group"
                  >
                    <BookOpen className="w-3.5 h-3.5 text-gray-400 group-hover:text-fuchsia-600" />
                    <span className="text-xs font-medium text-gray-500 group-hover:text-fuchsia-700">Policy Lens</span>
                  </button>
              </div>

              <div className="mt-4 flex items-center gap-2">
                <div className="h-2 w-24 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-fuchsia-500 rounded-full transition-all duration-1000 ease-out"
                    style={{ width: `${(result.decision.confidence || 0) * 100}%` }}
                  ></div>
                </div>
                <span className="text-xs font-bold text-gray-400 uppercase tracking-wide">
                  AI Confidence: <span className="text-fuchsia-600">{Math.round((result.decision.confidence || 0) * 100)}%</span>
                </span>
              </div>
            </div>

            {/* Missing Docs Alert */}
            {result.extracted_data.total_amount === 0 && result.decision.decision === "APPROVED" && (
                <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-3 shadow-sm">
                    <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                        <h4 className="text-sm font-bold text-amber-800 mb-1">Missing Financial Documents</h4>
                        <p className="text-xs text-amber-700 leading-relaxed">
                            We processed your Prescription successfully, but no Bill/Invoice was found. 
                            Please upload the Invoice to claim reimbursement.
                        </p>
                    </div>
                </div>
            )}

            {/* Financial Card */}
            <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 mb-8 transform transition-all hover:shadow-xl">
              <div className="grid grid-cols-2 gap-8">
                <div className="flex flex-col border-r border-gray-100">
                  <span className="text-xs text-gray-400 uppercase tracking-wider font-semibold mb-1">
                    Total Claimed
                  </span>
                  <div className="text-2xl text-gray-600 flex items-baseline gap-1">
                    <span className="text-lg text-gray-400">₹</span>
                    {result.extracted_data.total_amount?.toLocaleString(undefined, { minimumFractionDigits: 2 }) || "0.00"}
                  </div>
                </div>
                <div className="flex flex-col">
                  <span className="text-xs text-fuchsia-600 uppercase tracking-wider font-semibold mb-1">
                    Approved Amount
                  </span>
                  <div className="text-3xl font-bold text-gray-900 flex items-baseline gap-1">
                    <span className="text-xl text-gray-400">₹</span>
                    {result.decision.approved_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </div>
                </div>
              </div>
              
              {/* Cost Breakdown Ledger */}
              {result.decision.breakdown && result.decision.breakdown.length > 0 && (
                <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 mt-6">
                    <h4 className="text-xs font-bold text-gray-500 mb-3 uppercase tracking-wider">
                    Calculation Breakdown
                    </h4>
                    <div className="space-y-2">
                    {result.decision.breakdown.map((item, idx) => (
                        <div 
                        key={idx} 
                        className={cn(
                            "flex justify-between text-sm",
                            item.type === "final" ? "border-t border-gray-300 pt-2 font-bold text-gray-900 mt-2" : 
                            item.type === "deduction" ? "text-red-500" : "text-gray-600"
                        )}
                        >
                        <span>{item.label}</span>
                        <span>
                            {item.type === "deduction" ? "" : ""}
                            ₹{Math.abs(item.amount).toLocaleString(undefined, {minimumFractionDigits: 2})}
                        </span>
                        </div>
                    ))}
                    </div>
                </div>
              )}
            </div>

            {/* Analysis List */}
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-4 flex items-center gap-2">
                <FileText className="w-4 h-4 text-gray-400" />
                AI Analysis & Reasons
              </h4>
              
              {/* Summary Narrative */}
              {result.decision.summary_text && (
                  <div className="mb-4 p-3 bg-indigo-50 border border-indigo-100 rounded-lg text-sm text-indigo-900 leading-relaxed">
                      {result.decision.summary_text}
                  </div>
              )}

              <div className="space-y-3">
                {result.decision.reasons.map((reason, idx) => (
                  <div key={idx} className="flex items-start gap-3 p-4 bg-white rounded-lg border border-gray-100 shadow-sm">
                    <div className="mt-0.5">{renderReasonIcon(result.decision.decision)}</div>
                    <p className="text-gray-700 text-sm leading-relaxed">{reason}</p>
                  </div>
                ))}
                
                {/* Smart Clickable Diagnosis / Service (Themed) */}
                {(result.extracted_data.diagnosis || 
                  (result.extracted_data.lab_results && result.extracted_data.lab_results.length > 0) || 
                  result.decision.medical_context) && (
                  <div className="flex items-start gap-3 p-4 bg-fuchsia-50 rounded-lg border border-fuchsia-100 shadow-sm mt-2 transition-all hover:bg-fuchsia-100">
                    <Activity className="w-5 h-5 text-fuchsia-600 mt-0.5 shrink-0" />
                    <div className="flex-1">
                      <span className="block text-xs text-fuchsia-600 font-semibold uppercase mb-0.5">
                        {result.extracted_data.diagnosis ? "Diagnosis Detected" : "Medical Service"}
                      </span>
                      <div className="flex items-center gap-2 flex-wrap">
                          <p className="text-gray-700 text-sm font-medium">
                            {result.extracted_data.diagnosis || 
                             result.extracted_data.lab_results?.[0]?.test_name || 
                             "General Consultation"}
                          </p>
                          
                          {result.decision.medical_context && (
                            <button 
                              onClick={() => setShowHealthModal(true)}
                              className="text-xs flex items-center gap-1 text-fuchsia-600 hover:text-fuchsia-800 underline decoration-dotted underline-offset-2"
                            >
                              <Info className="w-3 h-3" />
                              Health Insights
                            </button>
                          )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="mt-8 pt-6 border-t border-gray-100 flex justify-end">
              <button
                onClick={reset}
                className="text-sm text-gray-500 hover:text-fuchsia-600 font-medium flex items-center gap-2 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Process Another Claim
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}