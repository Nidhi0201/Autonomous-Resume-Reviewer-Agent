"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { Loader2, CheckCircle2, AlertCircle, FileText, Sparkles, TrendingUp, Target, ArrowUpCircle } from "lucide-react"

// Auto-detect API URL: Use Netlify Functions in production, localhost in development
const getApiUrl = () => {
  if (typeof window !== 'undefined') {
    // Client-side: Use Netlify Functions if on Netlify domain, otherwise use env var or localhost
    const isNetlify = window.location.hostname.includes('netlify.app')
    if (isNetlify) {
      return `${window.location.origin}/.netlify/functions`
    }
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
}

const API_URL = getApiUrl()

interface ImprovedBullet {
  original: string
  improved: string
  explanation: string
  why_it_works: string
  self_critique: string
  is_supported_by_resume: boolean
  issues: string[]
  evidence_snippets: string[]
  relevance_score: number
  matched_jd_snippet: string
  relevance_improvements?: string  // Only present after iterative improvement
}

interface AnalyzeResponse {
  bullets: ImprovedBullet[]
  notes?: string
}

// Helper function to clean up error messages
const cleanErrorMessage = (message: string): string => {
  if (message.includes("API call failed")) {
    return "Unable to process with AI. Please try again or check your connection."
  }
  if (message.includes("model") && message.includes("decommissioned")) {
    return "Service temporarily unavailable. Please try again later."
  }
  return message
}

// Helper to check if explanation contains error
const isErrorExplanation = (text: string): boolean => {
  return text.includes("API call failed") || 
         text.includes("model") || 
         text.includes("Error code") ||
         text.includes("Groq API call failed") ||
         text.includes("Gemini API call failed")
}

// Helper to format issues for display
const formatIssue = (issue: string): string => {
  // Skip technical error codes
  if (issue.includes("_api_error") || issue.includes("critique_api_error")) {
    return ""
  }
  // Make user-friendly
  return issue.replace(/^The phrase /i, "").replace(/^Introduction of /i, "Added: ")
}

export default function Home() {
  const [resumeText, setResumeText] = useState("")
  const [jobDescription, setJobDescription] = useState("")
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<AnalyzeResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [improvingBullets, setImprovingBullets] = useState<Set<number>>(new Set())

  const handleAnalyze = async () => {
    if (!resumeText.trim() || !jobDescription.trim()) {
      setError("Please provide both resume text and job description")
      return
    }

    setLoading(true)
    setError(null)
    setResults(null)

    try {
      const endpoint = API_URL.endsWith('/functions') ? `${API_URL}/analyze` : `${API_URL}/analyze`
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          resume_text: resumeText,
          job_description: jobDescription,
        }),
      })

      if (!response.ok) {
        throw new Error(`Unable to connect to server. Please ensure the backend is running.`)
      }

      const data: AnalyzeResponse = await response.json()
      setResults(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze resume. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const handleImproveBullet = async (bulletIndex: number, bullet: ImprovedBullet, targetRelevance: number = 0.8) => {
    setImprovingBullets(prev => new Set(prev).add(bulletIndex))
    setError(null)

    try {
      const endpoint = API_URL.endsWith('/functions') ? `${API_URL}/improve-bullet` : `${API_URL}/improve-bullet`
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          current_bullet: bullet.improved,
          original_bullet: bullet.original,
          resume_text: resumeText,
          job_description: jobDescription,
          current_relevance: bullet.relevance_score,
          target_relevance: targetRelevance,
        }),
      })

      if (!response.ok) {
        throw new Error(`Unable to improve bullet. Please try again.`)
      }

      const improvedData = await response.json()
      
      // Update the specific bullet in results
      if (results) {
        const updatedBullets = [...results.bullets]
        updatedBullets[bulletIndex] = {
          ...bullet,
          improved: improvedData.improved,
          explanation: improvedData.explanation,
          why_it_works: improvedData.why_it_works || bullet.why_it_works,
          self_critique: improvedData.self_critique || bullet.self_critique,
          is_supported_by_resume: improvedData.is_supported_by_resume,
          issues: improvedData.issues || [],
          evidence_snippets: improvedData.evidence_snippets || [],
          relevance_score: improvedData.new_relevance_score || bullet.relevance_score,
          relevance_improvements: improvedData.relevance_improvements,
        }
        setResults({ ...results, bullets: updatedBullets })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to improve bullet. Please try again.")
    } finally {
      setImprovingBullets(prev => {
        const next = new Set(prev)
        next.delete(bulletIndex)
        return next
      })
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-4 md:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center space-y-3 pb-4">
          <div className="flex items-center justify-center gap-3">
            <Sparkles className="h-10 w-10 text-indigo-600" />
            <h1 className="text-5xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              Resume Reviewer Agent
            </h1>
          </div>
          <p className="text-gray-700 text-lg">
            AI-powered resume bullet improvement with self-critique and JD mapping
          </p>
        </div>

        {/* Input Section */}
        <div className="grid md:grid-cols-2 gap-6">
          <Card className="border-2 border-indigo-100 shadow-lg hover:shadow-xl transition-shadow">
            <CardHeader className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-t-lg">
              <CardTitle className="flex items-center gap-2 text-indigo-700">
                <FileText className="h-5 w-5" />
                Resume Text
              </CardTitle>
              <CardDescription className="text-gray-600">
                Paste your resume content here
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <Textarea
                placeholder="Example: Developed a web application using React and Node.js..."
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                className="min-h-[300px] font-mono text-sm border-indigo-200 focus:border-indigo-400"
              />
            </CardContent>
          </Card>

          <Card className="border-2 border-purple-100 shadow-lg hover:shadow-xl transition-shadow">
            <CardHeader className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-t-lg">
              <CardTitle className="flex items-center gap-2 text-purple-700">
                <Target className="h-5 w-5" />
                Job Description
              </CardTitle>
              <CardDescription className="text-gray-600">
                Paste the job description you're applying for
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <Textarea
                placeholder="Example: Looking for a React developer with 2+ years experience..."
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                className="min-h-[300px] font-mono text-sm border-purple-200 focus:border-purple-400"
              />
            </CardContent>
          </Card>
        </div>

        {/* Analyze Button */}
        <div className="flex justify-center">
          <Button
            onClick={handleAnalyze}
            disabled={loading || !resumeText.trim() || !jobDescription.trim()}
            size="lg"
            className="min-w-[220px] bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white text-lg py-6 shadow-lg hover:shadow-xl transition-all"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-5 w-5" />
                Analyze & Improve
              </>
            )}
          </Button>
        </div>

        {/* Error Message */}
        {error && (
          <Card className="border-2 border-red-300 bg-red-50 shadow-md">
            <CardContent className="pt-6">
              <div className="flex items-center gap-3 text-red-700">
                <AlertCircle className="h-5 w-5 flex-shrink-0" />
                <p className="font-medium">{error}</p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Results Section */}
        {results && (
          <Card className="border-2 border-indigo-200 shadow-xl">
            <CardHeader className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-t-lg">
              <CardTitle className="flex items-center gap-3 text-2xl">
                <TrendingUp className="h-6 w-6" />
                Improved Bullets
              </CardTitle>
              <CardDescription className="text-indigo-100">
                {results.bullets.length} bullet{results.bullets.length !== 1 ? 's' : ''} processed
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6 space-y-6">
              {results.bullets.map((bullet, idx) => {
                const hasRealIssues = bullet.issues.length > 0 && 
                  !bullet.issues.some(i => i.includes("_api_error") || i.includes("critique_api_error"))
                const isVerified = bullet.is_supported_by_resume && !hasRealIssues
                const relevancePercent = (bullet.relevance_score * 100).toFixed(0)
                
                return (
                  <Card 
                    key={idx} 
                    className={`border-l-4 ${
                      isVerified 
                        ? "border-l-green-500 bg-green-50/30" 
                        : "border-l-amber-500 bg-amber-50/30"
                    } shadow-md hover:shadow-lg transition-shadow`}
                  >
                    <CardContent className="pt-6">
                      <div className="space-y-5">
                        {/* Original vs Improved */}
                        <div className="grid md:grid-cols-2 gap-5">
                          <div className="space-y-2">
                            <h4 className="font-semibold text-sm text-gray-600 flex items-center gap-2">
                              <span className="w-2 h-2 rounded-full bg-gray-400"></span>
                              Original
                            </h4>
                            <p className="text-sm bg-gray-50 p-4 rounded-lg border border-gray-200 text-gray-800 leading-relaxed">
                              {bullet.original}
                            </p>
                          </div>
                          <div className="space-y-2">
                            <h4 className="font-semibold text-sm text-gray-600 flex items-center gap-2">
                              <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
                              Improved
                              {isVerified ? (
                                <Badge className="bg-green-600 text-white text-xs px-2 py-1">
                                  <CheckCircle2 className="h-3 w-3 mr-1" />
                                  Verified
                                </Badge>
                              ) : hasRealIssues ? (
                                <Badge className="bg-amber-600 text-white text-xs px-2 py-1">
                                  <AlertCircle className="h-3 w-3 mr-1" />
                                  Review Needed
                                </Badge>
                              ) : null}
                            </h4>
                            <p className={`text-sm p-4 rounded-lg border-2 leading-relaxed ${
                              isVerified 
                                ? "bg-green-50 border-green-200 text-green-900" 
                                : "bg-amber-50 border-amber-200 text-amber-900"
                            }`}>
                              {bullet.improved}
                            </p>
                          </div>
                        </div>

                        {/* Relevance Score - Better Visual */}
                        {bullet.relevance_score > 0 && (
                          <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                            <Target className="h-5 w-5 text-blue-600" />
                            <span className="text-sm font-medium text-blue-900">JD Match Score:</span>
                            <div className="flex-1 bg-blue-200 rounded-full h-3 relative overflow-hidden">
                              <div 
                                className={`h-full rounded-full transition-all ${
                                  parseFloat(relevancePercent) >= 70 
                                    ? "bg-green-500" 
                                    : parseFloat(relevancePercent) >= 40 
                                    ? "bg-blue-500" 
                                    : "bg-amber-500"
                                }`}
                                style={{ width: `${bullet.relevance_score * 100}%` }}
                              />
                            </div>
                            <Badge className={`font-bold ${
                              parseFloat(relevancePercent) >= 70 
                                ? "bg-green-600" 
                                : parseFloat(relevancePercent) >= 40 
                                ? "bg-blue-600" 
                                : "bg-amber-600"
                            } text-white`}>
                              {relevancePercent}%
                            </Badge>
                            {/* Improve Further Button - Show if relevance < 70% */}
                            {parseFloat(relevancePercent) < 70 && (
                              <Button
                                size="sm"
                                onClick={() => handleImproveBullet(idx, bullet, 0.8)}
                                disabled={improvingBullets.has(idx) || loading}
                                className="ml-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white text-xs"
                              >
                                {improvingBullets.has(idx) ? (
                                  <>
                                    <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                                    Improving...
                                  </>
                                ) : (
                                  <>
                                    <ArrowUpCircle className="mr-1 h-3 w-3" />
                                    Improve to ~80%
                                  </>
                                )}
                              </Button>
                            )}
                          </div>
                        )}

                        {/* Issues - Only show real issues, not technical errors */}
                        {hasRealIssues && (
                          <div className="space-y-2 p-4 bg-amber-50 rounded-lg border border-amber-200">
                            <h4 className="font-semibold text-sm text-amber-900 flex items-center gap-2">
                              <AlertCircle className="h-4 w-4" />
                              Areas to Review:
                            </h4>
                            <ul className="list-disc list-inside space-y-1.5 text-sm text-amber-800">
                              {bullet.issues
                                .filter(issue => !issue.includes("_api_error") && !issue.includes("critique_api_error"))
                                .map((issue, i) => {
                                  const formatted = formatIssue(issue)
                                  return formatted ? <li key={i}>{formatted}</li> : null
                                })
                                .filter(Boolean)}
                            </ul>
                          </div>
                        )}

                        {/* Accordion for Details - Only show if not an error */}
                        {!isErrorExplanation(bullet.explanation) && (
                          <Accordion type="single" collapsible>
                            <AccordionItem value={`explanation-${idx}`}>
                              <AccordionTrigger className="text-indigo-700 font-medium hover:text-indigo-900">
                                View Detailed Analysis
                              </AccordionTrigger>
                              <AccordionContent className="space-y-4 text-sm pt-4">
                                <div className="p-4 bg-indigo-50 rounded-lg border border-indigo-100">
                                  <h5 className="font-semibold mb-2 text-indigo-900 flex items-center gap-2">
                                    <Sparkles className="h-4 w-4" />
                                    Why Changes Were Made:
                                  </h5>
                                  <p className="text-gray-700 leading-relaxed">{bullet.explanation}</p>
                                </div>
                                <div className="p-4 bg-green-50 rounded-lg border border-green-100">
                                  <h5 className="font-semibold mb-2 text-green-900 flex items-center gap-2">
                                    <TrendingUp className="h-4 w-4" />
                                    Why It Works:
                                  </h5>
                                  <p className="text-gray-700 leading-relaxed">{bullet.why_it_works}</p>
                                </div>
                                {bullet.self_critique && !isErrorExplanation(bullet.self_critique) && (
                                  <div className="p-4 bg-blue-50 rounded-lg border border-blue-100">
                                    <h5 className="font-semibold mb-2 text-blue-900 flex items-center gap-2">
                                      <CheckCircle2 className="h-4 w-4" />
                                      Self-Critique:
                                    </h5>
                                    <p className="text-gray-700 leading-relaxed">{bullet.self_critique}</p>
                                  </div>
                                )}
                                {bullet.relevance_improvements && (
                                  <div className="p-4 bg-purple-50 rounded-lg border border-purple-100">
                                    <h5 className="font-semibold mb-2 text-purple-900 flex items-center gap-2">
                                      <ArrowUpCircle className="h-4 w-4" />
                                      JD Relevance Improvements:
                                    </h5>
                                    <p className="text-gray-700 leading-relaxed">{bullet.relevance_improvements}</p>
                                  </div>
                                )}
                                {bullet.matched_jd_snippet && (
                                  <div className="p-4 bg-purple-50 rounded-lg border border-purple-100">
                                    <h5 className="font-semibold mb-2 text-purple-900 flex items-center gap-2">
                                      <Target className="h-4 w-4" />
                                      Matched Job Description Section:
                                    </h5>
                                    <p className="text-gray-700 italic leading-relaxed">{bullet.matched_jd_snippet}</p>
                                  </div>
                                )}
                                {bullet.evidence_snippets.length > 0 && (
                                  <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                                    <h5 className="font-semibold mb-2 text-gray-900">Evidence from Resume:</h5>
                                    <ul className="list-disc list-inside space-y-1.5 text-gray-700">
                                      {bullet.evidence_snippets.map((evidence, i) => (
                                        <li key={i} className="leading-relaxed">{evidence}</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                              </AccordionContent>
                            </AccordionItem>
                          </Accordion>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
