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
} from "lucide-react"
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

// Utility for tailwind classes
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Types matching the expected API response
interface ClaimResponse {
  status: string
  file_processed: string
  extracted_data: {
    total_amount?: number
    diagnosis?: string
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
    decision: "APPROVED" | "REJECTED" | "MANUAL_REVIEW"
    approved_amount: number
    reasons: string[]
    confidence?: number
  }
}

export default function ClaimDashboard() {
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<ClaimResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Handle Drag Events
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }, [])

  // Handle Drop Event
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0])
    }
  }, [])

  // Handle Manual File Selection
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0])
    }
  }

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile)
    setResult(null) // Reset previous results
    setError(null)

    // Create preview URL for images
    if (selectedFile.type.startsWith("image/")) {
      const reader = new FileReader()
      reader.onloadend = () => {
        setPreviewUrl(reader.result as string)
      }
      reader.readAsDataURL(selectedFile)
    } else {
      setPreviewUrl(null) // No preview for non-images (like PDFs) for this demo
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setIsLoading(true)
    setError(null)

    const formData = new FormData()
    formData.append("file", file)

    try {
      // --- REAL BACKEND CONNECTION ---
      const response = await fetch("http://localhost:8000/v1/claims/upload", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        // Parse the error message from the backend (if available)
        const errorText = await response.text()
        let errorMessage = `Server error: ${response.status}`
        try {
            const errorJson = JSON.parse(errorText)
            if (errorJson.detail) errorMessage = errorJson.detail
        } catch (e) {
            // If text isn't JSON, just use the raw text
            if (errorText) errorMessage = errorText
        }
        throw new Error(errorMessage)
      }

      const data = await response.json()
      setResult(data)

    } catch (err) {
      console.error(err)
      // Show the real error in the UI
      setError(err instanceof Error ? err.message : "An unknown error occurred. Check backend console.")
    } finally {
      setIsLoading(false)
    }
  }

  const reset = () => {
    setFile(null)
    setPreviewUrl(null)
    setResult(null)
    setError(null)
  }

  // Render helper for status badge
  const renderStatusBadge = (status: string) => {
    switch (status) {
      case "APPROVED":
        return (
          <div className="flex items-center gap-2 px-6 py-2 rounded-full bg-green-100 text-green-700 border border-green-200 shadow-sm animate-in fade-in zoom-in duration-300">
            <CheckCircle className="w-5 h-5" />
            <span className="font-bold tracking-wide text-sm">APPROVED</span>
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

  // Render helper for icons in analysis list
  const renderReasonIcon = (status: string) => {
    if (status === "APPROVED") return <CheckCircle className="w-5 h-5 text-green-500 shrink-0" />
    if (status === "REJECTED") return <XCircle className="w-5 h-5 text-red-500 shrink-0" />
    return <Activity className="w-5 h-5 text-amber-500 shrink-0" />
  }

  return (
    <div className="w-full max-w-6xl bg-white rounded-2xl shadow-xl overflow-hidden flex flex-col lg:flex-row min-h-[600px]">
      {/* Left Panel: Upload & Preview */}
      <div className="w-full lg:w-1/2 p-8 border-b lg:border-b-0 lg:border-r border-gray-100 flex flex-col">
        <h2 className="text-2xl font-bold text-gray-800 mb-1 flex items-center gap-2">
          <span className="w-2 h-8 bg-fuchsia-600 rounded-full block"></span>
          Upload Medical Bill
        </h2>
        <p className="text-gray-500 mb-8 pl-4 text-sm">Drag and drop your claim documents here</p>

        {/* Upload Area */}
        <div className="flex-1 flex flex-col">
          {!file ? (
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
                onChange={handleChange}
                accept="image/*,application/pdf"
              />
              <div
                className={cn(
                  "w-20 h-20 rounded-full flex items-center justify-center mb-4 transition-colors",
                  dragActive
                    ? "bg-white text-fuchsia-600"
                    : "bg-fuchsia-100 text-fuchsia-600 group-hover:scale-110 group-hover:shadow-lg duration-300",
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

              <div className="flex-1 flex items-center justify-center p-4 bg-gray-100/50">
                {previewUrl ? (
                  <img
                    src={previewUrl || "/placeholder.svg"}
                    alt="Preview"
                    className="max-h-[400px] object-contain rounded shadow-sm"
                  />
                ) : (
                  <div className="text-center p-8">
                    <FileText className="w-20 h-20 text-fuchsia-300 mx-auto mb-4" />
                    <p className="text-gray-600 font-medium">{file.name}</p>
                    <p className="text-sm text-gray-400 mt-1">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Action Button */}
          <div className="mt-8">
            <button
              onClick={handleUpload}
              disabled={!file || isLoading}
              className={cn(
                "w-full py-4 rounded-xl font-bold text-lg text-white shadow-lg transition-all transform duration-200 flex items-center justify-center gap-2",
                !file || isLoading
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
                <>
                  Adjudicate Claim
                  <ArrowRight className="w-5 h-5" />
                </>
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
            <h3 className="text-xl font-semibold text-gray-600 mb-2">Waiting for document...</h3>
            <p className="max-w-xs mx-auto text-sm text-gray-400">
              Upload a medical bill to receive an instant AI adjudication decision.
            </p>
          </div>
        ) : (
          <div className="flex-1 flex flex-col animate-in slide-in-from-right-4 duration-500 fade-in">
            {/* Header Section */}
            <div className="flex flex-col items-center mb-8">
              {renderStatusBadge(result.decision.decision)}
              <p className="text-gray-400 text-xs font-medium uppercase tracking-widest mt-4">Confidence Score</p>
              <div className="mt-2 flex items-center gap-2">
                <div className="h-2 w-24 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-fuchsia-500 rounded-full transition-all duration-1000 ease-out"
                    style={{ width: `${(result.decision.confidence || 0) * 100}%` }}
                  ></div>
                </div>
                <span className="text-fuchsia-600 font-bold">
                  {Math.round((result.decision.confidence || 0) * 100)}%
                </span>
              </div>
            </div>

            {/* Financial Card */}
            <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 mb-8 transform transition-all hover:shadow-xl">
              <div className="grid grid-cols-2 gap-8">
                <div className="flex flex-col border-r border-gray-100">
                  <span className="text-xs text-gray-400 uppercase tracking-wider font-semibold mb-1">
                    Total Claimed
                  </span>
                  <div className="text-2xl text-gray-600 flex items-baseline gap-1">
                    <span className="text-lg text-gray-400">$</span>
                    {result.extracted_data.total_amount?.toLocaleString(undefined, { minimumFractionDigits: 2 }) ||
                      "0.00"}
                  </div>
                </div>
                <div className="flex flex-col">
                  <span className="text-xs text-fuchsia-600 uppercase tracking-wider font-semibold mb-1">
                    Approved Amount
                  </span>
                  <div className="text-3xl font-bold text-gray-900 flex items-baseline gap-1">
                    <span className="text-xl text-gray-400">$</span>
                    {result.decision.approved_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </div>
                </div>
              </div>
            </div>

            {/* Analysis List */}
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-4 flex items-center gap-2">
                <FileText className="w-4 h-4 text-gray-400" />
                AI Analysis & Reasons
              </h4>
              <div className="space-y-3">
                {result.decision.reasons.map((reason, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-3 p-4 bg-white rounded-lg border border-gray-100 shadow-sm"
                  >
                    <div className="mt-0.5">{renderReasonIcon(result.decision.decision)}</div>
                    <p className="text-gray-700 text-sm leading-relaxed">{reason}</p>
                  </div>
                ))}

                {result.extracted_data.diagnosis && (
                  <div className="flex items-start gap-3 p-4 bg-blue-50/50 rounded-lg border border-blue-100 shadow-sm mt-2">
                    <Activity className="w-5 h-5 text-blue-500 mt-0.5 shrink-0" />
                    <div>
                      <span className="block text-xs text-blue-600 font-semibold uppercase mb-0.5">
                        Diagnosis Detected
                      </span>
                      <p className="text-gray-700 text-sm">{result.extracted_data.diagnosis}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Reset Button for Result View */}
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