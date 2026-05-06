import { useState, useRef, useEffect, useCallback } from "react";
import { createPortal } from "react-dom";
import { useNavigate } from "react-router-dom";
import { useAuthContext } from "../../context/AuthContext";
import ChatMessage, { TypingIndicator } from "./ChatMessage";
import ChatInput from "./ChatInput";
import { sendChatMessage, sendMultimodalMessage, getChatHistory, getChatSummary } from "../../services/api";

// ── Constants ─────────────────────────────────────────────────────────────────
const MAX_RETRIES    = 2;
const RETRY_DELAY_MS = 1000;

const WIZARD_STEPS = [
  { key: "greeting",           label: "Start"      },
  { key: "claim_type",         label: "Claim Type" },
  { key: "incident_details",   label: "Incident"   },
  { key: "policy_number",      label: "Policy"     },
  { key: "document_collection",label: "Documents"  },
  { key: "contact_info",       label: "Contact"    },
  { key: "review",             label: "Review"     },
  { key: "summary_generated",  label: "Done"       },
];

const INITIAL_MSG = {
  id: 1, role: "agent",
  text: "Hello! I\u2019m your **ClaimFlow Insurance Assistant**.\n\nI can guide you through filing a claim step by step, check an existing claim\u2019s status, or answer policy questions.\n\nWhat would you like to do today?",
  time: new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
};

function formatTime(d) {
  return d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
}
function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

// ── Wizard progress bar ───────────────────────────────────────────────────────
function WizardProgress({ step }) {
  const idx = WIZARD_STEPS.findIndex((s) => s.key === step);
  if (idx < 1) return null;
  const pct = Math.round((idx / (WIZARD_STEPS.length - 1)) * 100);
  return (
    <div className="px-8 py-2 bg-white border-b border-slate-100 flex items-center gap-3">
      <div className="flex-grow bg-slate-100 rounded-full h-1.5 overflow-hidden">
        <div className="bg-[#fea619] h-full transition-all duration-500" style={{ width: `${pct}%` }} />
      </div>
      <span className="font-[Work_Sans] text-[11px] text-[#74777f] whitespace-nowrap">
        Step {idx + 1} of {WIZARD_STEPS.length} &mdash; {WIZARD_STEPS[idx]?.label}
      </span>
    </div>
  );
}

// ── Summary report modal — rendered via portal so it's never clipped ─────────
function SummaryModal({ report, onClose }) {
  if (!report) return null;

  const downloadTxt = () => {
    const lines = [
      "CLAIMFLOW SESSION SUMMARY REPORT",
      `Report ID: ${report.report_id}`,
      `Generated: ${report.generated_at}`,
      `Claim Type: ${report.claim_type}`,
      `Completeness: ${report.completeness_pct}%`,
      "",
      "--- EXTRACTED FIELDS ---",
      ...Object.entries(report.extracted_fields || {}).map(([k, v]) => `${k}: ${JSON.stringify(v)}`),
      "",
      "--- DOCUMENTS ---",
      ...(report.document_analysis || []).map((d) => `${d.filename} → ${d.detected_type} (conf: ${d.confidence})`),
      "",
      "--- CONVERSATION TRANSCRIPT ---",
      ...(report.transcript || []).map((t) => `[${t.timestamp}]\nUser: ${t.user}\nAgent: ${t.agent}\n`),
    ];
    const blob = new Blob([lines.join("\n")], { type: "text/plain" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href = url; a.download = `${report.report_id}.txt`; a.click();
    URL.revokeObjectURL(url);
  };

  const downloadJson = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href = url; a.download = `${report.report_id}.json`; a.click();
    URL.revokeObjectURL(url);
  };

  // Close on backdrop click
  const handleBackdrop = (e) => { if (e.target === e.currentTarget) onClose(); };

  const modal = (
    <div
      className="fixed inset-0 bg-black/50 z-[9999] flex items-center justify-center p-4"
      onClick={handleBackdrop}
    >
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 flex-shrink-0">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[#fea619]" style={{ fontVariationSettings: "'FILL' 1" }}>summarize</span>
            <h3 className="font-['Be_Vietnam_Pro'] font-semibold text-[#002045] text-[16px]">Session Summary Report</h3>
          </div>
          <button onClick={onClose} className="p-1 text-[#74777f] hover:text-[#002045] hover:bg-slate-100 rounded-full transition-colors">
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        {/* Body */}
        <div className="overflow-y-auto p-6 space-y-4 text-[13px] font-['Work_Sans']">
          {/* Stats grid */}
          <div className="grid grid-cols-3 gap-2">
            {[
              ["Claim Type",   report.claim_type?.toUpperCase() || "—"],
              ["Completeness", `${report.completeness_pct}%`],
              ["Turns",        report.conversation_turns],
              ["Documents",    report.document_analysis?.length ?? 0],
              ["Ready",        report.ready_for_pipeline ? "✅ Yes" : "⚠️ No"],
              ["Report ID",    report.report_id?.slice(-8)],
            ].map(([label, val]) => (
              <div key={label} className="bg-slate-50 rounded-xl p-3">
                <div className="text-[#74777f] text-[10px] uppercase tracking-wider mb-0.5">{label}</div>
                <div className="font-semibold text-[#002045] text-[13px]">{val}</div>
              </div>
            ))}
          </div>

          {/* Missing docs warning */}
          {report.missing_documents?.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-3">
              <div className="font-semibold text-amber-700 mb-1 flex items-center gap-1">
                <span className="material-symbols-outlined text-[16px]">warning</span>
                Missing Documents
              </div>
              {report.missing_documents.map((d) => (
                <div key={d} className="text-amber-600 text-[12px]">• {d}</div>
              ))}
            </div>
          )}

          {/* Extracted fields */}
          <div>
            <div className="font-semibold text-[#002045] mb-2">Extracted Fields</div>
            <div className="space-y-1">
              {Object.entries(report.extracted_fields || {})
                .filter(([, v]) => v && v !== "NOT_PROVIDED")
                .map(([k, v]) => (
                  <div key={k} className="flex gap-2 py-1.5 border-b border-slate-50 last:border-0">
                    <span className="text-[#74777f] w-40 flex-shrink-0 capitalize text-[12px]">
                      {k.replace(/_/g, " ")}
                    </span>
                    <span className="text-[#191c1e] font-medium text-[12px] break-all">
                      {typeof v === "object" ? JSON.stringify(v) : String(v)}
                    </span>
                  </div>
                ))}
            </div>
          </div>

          {/* Document analysis */}
          {report.document_analysis?.length > 0 && (
            <div>
              <div className="font-semibold text-[#002045] mb-2">Documents Analysed</div>
              {report.document_analysis.map((d, i) => (
                <div key={i} className="flex items-center gap-2 py-1.5 border-b border-slate-50 last:border-0">
                  <span className="material-symbols-outlined text-[16px] text-[#002045]">description</span>
                  <div>
                    <div className="font-medium text-[12px]">{d.filename}</div>
                    <div className="text-[#74777f] text-[11px]">
                      {d.detected_type}
                      {d.amount_found ? ` · ₹${Number(d.amount_found).toLocaleString()}` : ""}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-100 flex gap-2 flex-shrink-0">
          <button
            onClick={downloadTxt}
            className="flex-1 py-2.5 border-2 border-[#002045] text-[#002045] rounded-xl font-['Work_Sans'] text-[12px] font-semibold hover:bg-[#002045] hover:text-white transition-all"
          >
            Download TXT
          </button>
          <button
            onClick={downloadJson}
            className="flex-1 py-2.5 bg-[#002045] text-white rounded-xl font-['Work_Sans'] text-[12px] font-semibold hover:bg-[#1a365d] transition-all"
          >
            Download JSON
          </button>
        </div>
      </div>
    </div>
  );

  // Render into document.body so it's never clipped by parent overflow
  return createPortal(modal, document.body);
}

// ── Main component ────────────────────────────────────────────────────────────
export default function ChatWindow({ sessionId, onSessionIdChange }) {
  const { user, token } = useAuthContext();
  const navigate = useNavigate();

  const [messages,        setMessages]        = useState([INITIAL_MSG]);
  const [input,           setInput]           = useState("");
  const [isTyping,        setIsTyping]        = useState(false);
  const [error,           setError]           = useState(null);
  const [suggestedActions,setSuggestedActions] = useState(["File a new claim","Check claim status","Ask about coverage"]);
  const [wizardStep,      setWizardStep]      = useState("greeting");
  const [summaryReport,   setSummaryReport]   = useState(null);
  const [showSummary,     setShowSummary]     = useState(false);
  const [showMoreMenu,    setShowMoreMenu]    = useState(false);
  const [sessionLoaded,   setSessionLoaded]   = useState(false);

  const bottomRef  = useRef(null);
  const moreRef    = useRef(null);
  const initials   = user?.email ? user.email.slice(0, 2).toUpperCase() : "U";

  // ── Auto-scroll ───────────────────────────────────────────────────────────
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, isTyping]);

  // ── Close more-menu on outside click ─────────────────────────────────────
  useEffect(() => {
    const h = (e) => { if (moreRef.current && !moreRef.current.contains(e.target)) setShowMoreMenu(false); };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, []);

  // ── Restore session on mount / sessionId change ───────────────────────────
  useEffect(() => {
    if (!sessionId || !token || sessionLoaded) return;
    (async () => {
      try {
        const data = await getChatHistory(sessionId, token);
        const history = data.conversation_history || [];
        if (history.length === 0) { setSessionLoaded(true); return; }
        const restored = [INITIAL_MSG];
        history.forEach((h, i) => {
          restored.push({ id: i * 2 + 2, role: "user",  text: h.user_message, time: h.timestamp?.slice(11, 16) || "" });
          restored.push({ id: i * 2 + 3, role: "agent", text: h.bot_response,  time: h.timestamp?.slice(11, 16) || "" });
        });
        setMessages(restored);
        if (data.wizard_step) setWizardStep(data.wizard_step);
        if (data.context?.summary_report) setSummaryReport(data.context.summary_report);
      } catch (_) { /* session not found — start fresh */ }
      setSessionLoaded(true);
    })();
  }, [sessionId, token, sessionLoaded]);

  // ── New-conversation event from sidebar ───────────────────────────────────
  useEffect(() => {
    const h = () => {
      setMessages([INITIAL_MSG]);
      setInput(""); setError(null);
      setSuggestedActions(["File a new claim","Check claim status","Ask about coverage"]);
      setWizardStep("greeting");
      setSummaryReport(null);
      setSessionLoaded(false);
    };
    window.addEventListener("claimflow:new-conversation", h);
    return () => window.removeEventListener("claimflow:new-conversation", h);
  }, []);

  // ── Retry helper ──────────────────────────────────────────────────────────
  const callWithRetry = useCallback(async (fn, attempt = 0) => {
    try { return await fn(); }
    catch (err) {
      if (attempt < MAX_RETRIES) { await sleep(RETRY_DELAY_MS); return callWithRetry(fn, attempt + 1); }
      throw err;
    }
  }, []);

  // ── Core send ─────────────────────────────────────────────────────────────
  const handleSend = useCallback(async ({ text, files, audioBlob }) => {
    const msg = text.trim();
    if (!msg && files.length === 0 && !audioBlob) return;
    if (isTyping) return;

    const displayText = msg
      + (files.length ? "\n" + files.map((f) => `📎 ${f.name}`).join("\n") : "")
      + (audioBlob ? "\n🎙️ Voice message" : "");

    const userMsg = { id: Date.now(), role: "user", text: displayText, time: formatTime(new Date()) };
    setMessages((p) => [...p, userMsg]);
    setInput("");
    setIsTyping(true);
    setError(null);
    setSuggestedActions([]);

    try {
      let data;
      const sid = sessionId || undefined;

      if (files.length > 0 || audioBlob) {
        data = await callWithRetry(() =>
          sendMultimodalMessage({ message: msg, session_id: sid, files, audio: audioBlob }, token)
        );
      } else {
        data = await callWithRetry(() =>
          sendChatMessage({ message: msg, session_id: sid }, token)
        );
      }

      if (data.session_id && !sessionId) onSessionIdChange(data.session_id);
      if (data.wizard_step) setWizardStep(data.wizard_step);
      // Store report but DON'T auto-open modal — show the in-chat banner instead
      if (data.summary_report) setSummaryReport(data.summary_report);

      setMessages((p) => [...p, { id: Date.now() + 1, role: "agent", text: data.response, time: formatTime(new Date()) }]);
      if (data.suggested_actions?.length) setSuggestedActions(data.suggested_actions);
    } catch (_) {
      setError("Could not reach the server. Please check your connection and try again.");
      setMessages((p) => p.filter((m) => m.id !== userMsg.id));
      setInput(text);
    } finally {
      setIsTyping(false);
    }
  }, [isTyping, sessionId, token, callWithRetry, onSessionIdChange]);

  // ── Suggestion chip click ─────────────────────────────────────────────────
  const handleSuggestion = useCallback((action) => {
    handleSend({ text: action, files: [], audioBlob: null });
  }, [handleSend]);

  // ── Fetch summary report ──────────────────────────────────────────────────
  const handleFetchSummary = useCallback(async () => {
    if (!sessionId) return;
    try {
      const report = await getChatSummary(sessionId, token);
      setSummaryReport(report);
      setShowSummary(true);
    } catch (_) { setError("Could not generate summary report."); }
  }, [sessionId, token]);

  // ── Submit claim — sends "submit" message which triggers pipeline ─────────
  const handleSubmitClaim = useCallback(() => {
    handleSend({ text: "submit claim now", files: [], audioBlob: null });
  }, [handleSend]);

  // ── Export chat as text ───────────────────────────────────────────────────
  const exportChat = () => {
    const txt = messages.map((m) => `[${m.time}] ${m.role === "user" ? "You" : "Agent"}: ${m.text}`).join("\n");
    const blob = new Blob([txt], { type: "text/plain" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a"); a.href = url; a.download = "claimflow-chat.txt"; a.click();
    URL.revokeObjectURL(url);
    setShowMoreMenu(false);
  };

  const resetChat = () => {
    if (messages.length > 1 && !window.confirm("Start a new conversation? Current chat will be cleared.")) return;
    setMessages([INITIAL_MSG]); onSessionIdChange(null);
    setError(null); setSuggestedActions(["File a new claim","Check claim status","Ask about coverage"]);
    setWizardStep("greeting"); setSummaryReport(null); setSessionLoaded(false);
  };

  return (
    <>
      {/* Modal renders via portal into document.body — never clipped */}
      {showSummary && <SummaryModal report={summaryReport} onClose={() => setShowSummary(false)} />}

      <section className="flex-grow flex flex-col bg-white relative min-w-0 overflow-hidden">
        {/* Header */}
        <header className="h-20 border-b border-slate-100 flex items-center justify-between px-8 bg-white/80 backdrop-blur-md z-10 flex-shrink-0">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="w-11 h-11 rounded-full bg-[#002045] flex items-center justify-center text-white font-[Be_Vietnam_Pro] font-bold text-[16px]">CF</div>
              <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white rounded-full" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-[Be_Vietnam_Pro] text-[18px] font-semibold text-[#002045]">ClaimFlow Assistant</h3>
                <span className="bg-[#002045]/5 text-[#002045] text-[10px] px-2 py-0.5 rounded-full font-[Work_Sans] font-semibold uppercase border border-[#002045]/10">AI Agent</span>
              </div>
              <span className="font-[Work_Sans] text-[12px] text-green-600 flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-green-600 rounded-full inline-block" />Online
              </span>
            </div>
          </div>

          <div className="flex items-center gap-1">
            {summaryReport && (
              <button title="View summary report" onClick={() => setShowSummary(true)}
                className="flex items-center gap-1 px-3 py-1.5 bg-[#fea619]/10 text-[#684000] rounded-full text-[12px] font-[Work_Sans] font-semibold hover:bg-[#fea619]/20 transition-all">
                <span className="material-symbols-outlined text-[16px]">summarize</span>Report
              </button>
            )}
            <button title="New conversation" onClick={resetChat} className="p-2 hover:bg-slate-100 rounded-full transition-colors text-[#74777f]">
              <span className="material-symbols-outlined">refresh</span>
            </button>
            <div className="relative" ref={moreRef}>
              <button title="More options" onClick={() => setShowMoreMenu((v) => !v)} className="p-2 hover:bg-slate-100 rounded-full transition-colors text-[#74777f]">
                <span className="material-symbols-outlined">more_vert</span>
              </button>
              {showMoreMenu && (
                <div className="absolute right-0 top-full mt-1 w-52 bg-white border border-slate-200 rounded-xl shadow-lg z-20 overflow-hidden">
                  {[
                    { icon: "summarize",    label: "Generate report",   action: handleFetchSummary },
                    { icon: "download",     label: "Export chat (.txt)", action: exportChat },
                    { icon: "content_copy", label: "Copy last reply",   action: () => { const m = [...messages].reverse().find((m) => m.role === "agent"); if (m) navigator.clipboard.writeText(m.text); setShowMoreMenu(false); } },
                    { icon: "help",         label: "Help & FAQ",        action: () => { handleSend({ text: "What can you help me with?", files: [], audioBlob: null }); setShowMoreMenu(false); } },
                  ].map(({ icon, label, action }) => (
                    <button key={label} onClick={action} className="w-full flex items-center gap-3 px-4 py-3 text-left font-[Work_Sans] text-[13px] text-[#191c1e] hover:bg-slate-50 transition-colors">
                      <span className="material-symbols-outlined text-[18px] text-[#74777f]">{icon}</span>{label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Wizard progress */}
        <WizardProgress step={wizardStep} />

        {/* Error banner */}
        {error && (
          <div className="mx-6 mt-3 flex items-center gap-3 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl font-[Work_Sans] text-[13px]">
            <span className="material-symbols-outlined text-[18px] flex-shrink-0">error</span>
            <span className="flex-grow">{error}</span>
            <button onClick={() => setError(null)} className="flex-shrink-0 hover:text-red-900"><span className="material-symbols-outlined text-[16px]">close</span></button>
          </div>
        )}

        {/* Messages */}
        <div className="flex-grow overflow-y-auto p-8 space-y-6 bg-[#f8fafc]" style={{ scrollbarWidth: "none" }}>
          <div className="flex justify-center">
            <span className="font-[Work_Sans] text-[12px] text-[#74777f] bg-[#f2f4f6] px-4 py-1 rounded-full">
              Today, {new Date().toLocaleDateString("en-IN", { month: "long", day: "numeric" })}
            </span>
          </div>

          {messages.map((msg) => (
            <ChatMessage key={msg.id} role={msg.role} text={msg.text} time={msg.time} initials={initials} />
          ))}

          {isTyping && <TypingIndicator />}

          {/* Suggestion chips */}
          {!isTyping && suggestedActions.length > 0 && (
            <div className="flex flex-wrap gap-2 pl-12">
              {suggestedActions.map((a) => (
                <button key={a} onClick={() => handleSuggestion(a)}
                  className="px-3 py-1.5 bg-white border border-[#002045]/20 text-[#002045] rounded-full font-[Work_Sans] text-[12px] font-medium hover:bg-[#002045] hover:text-white transition-all shadow-sm">
                  {a}
                </button>
              ))}
            </div>
          )}

          {/* Summary ready banner — inline in chat, not a modal */}
          {summaryReport && (
            <div className="flex justify-center pt-2">
              <div className="bg-white border border-[#fea619]/40 rounded-2xl shadow-md px-6 py-4 flex flex-col items-center gap-3 max-w-sm w-full">
                <div className="flex items-center gap-2 text-[#002045]">
                  <span className="material-symbols-outlined text-[#fea619]" style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
                  <span className="font-['Be_Vietnam_Pro'] font-semibold text-[15px]">Summary Report Ready</span>
                </div>
                <p className="font-['Work_Sans'] text-[13px] text-[#43474e] text-center">
                  Completeness: <strong>{summaryReport.completeness_pct}%</strong>
                  {" · "}{summaryReport.conversation_turns} turns
                  {" · "}{summaryReport.document_analysis?.length ?? 0} docs
                </p>
                <div className="flex gap-2 w-full">
                  <button
                    onClick={() => setShowSummary(true)}
                    className="flex-1 flex items-center justify-center gap-1 border-2 border-[#002045] text-[#002045] py-2.5 rounded-xl font-['Work_Sans'] font-semibold text-[13px] hover:bg-[#002045] hover:text-white active:scale-95 transition-all"
                  >
                    <span className="material-symbols-outlined text-[16px]">summarize</span>
                    View Report
                  </button>
                  <button
                    onClick={handleSubmitClaim}
                    disabled={isTyping}
                    className="flex-1 flex items-center justify-center gap-1 bg-[#002045] text-white py-2.5 rounded-xl font-['Work_Sans'] font-semibold text-[13px] hover:bg-[#1a365d] active:scale-95 transition-all disabled:opacity-50"
                  >
                    Submit Claim
                    <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <ChatInput value={input} onChange={setInput} onSend={handleSend} disabled={isTyping} />
      </section>
    </>
  );
}
