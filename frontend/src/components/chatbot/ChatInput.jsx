import { useRef, useCallback, useState } from "react";

/**
 * ChatInput — multimodal message bar
 * Supports: text, file attach, photo capture, voice recording (MediaRecorder)
 *
 * Props:
 *   value          string
 *   onChange       (val: string) => void
 *   onSend         (opts: { text, files, audioBlob }) => void
 *   disabled       boolean
 */
export default function ChatInput({ value, onChange, onSend, disabled = false }) {
  const textareaRef  = useRef(null);
  const fileInputRef = useRef(null);
  const photoInputRef = useRef(null);
  const mediaRecRef  = useRef(null);
  const chunksRef    = useRef([]);

  const [pendingFiles, setPendingFiles]   = useState([]);   // File[]
  const [isRecording, setIsRecording]     = useState(false);
  const [recordSecs, setRecordSecs]       = useState(0);
  const timerRef = useRef(null);

  // ── textarea auto-resize ──────────────────────────────────────────────────
  const handleInput = (e) => {
    const el = textareaRef.current;
    if (el) { el.style.height = "auto"; el.style.height = `${Math.min(el.scrollHeight, 120)}px`; }
    onChange(e.target.value);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); if (!disabled) triggerSend(); }
  };

  // ── send ──────────────────────────────────────────────────────────────────
  const triggerSend = useCallback(() => {
    if (disabled) return;
    if (!value.trim() && pendingFiles.length === 0) return;
    onSend({ text: value, files: pendingFiles, audioBlob: null });
    setPendingFiles([]);
  }, [disabled, value, pendingFiles, onSend]);

  // ── file attach ───────────────────────────────────────────────────────────
  const handleFileChange = (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    setPendingFiles((prev) => [...prev, ...files]);
    e.target.value = "";
  };

  const removeFile = (idx) => setPendingFiles((prev) => prev.filter((_, i) => i !== idx));

  // ── voice recording ───────────────────────────────────────────────────────
  const startRecording = useCallback(async () => {
    // Try MediaRecorder first (real audio blob)
    if (navigator.mediaDevices?.getUserMedia) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        chunksRef.current = [];
        const mr = new MediaRecorder(stream);
        mr.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
        mr.onstop = () => {
          const blob = new Blob(chunksRef.current, { type: "audio/webm" });
          stream.getTracks().forEach((t) => t.stop());
          // Also run Web Speech for transcript
          const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
          if (SR) {
            const rec = new SR();
            rec.lang = "en-IN";
            rec.onresult = (ev) => {
              const t = ev.results[0][0].transcript;
              onChange((prev) => (prev ? `${prev} ${t}` : t));
            };
            rec.start();
            setTimeout(() => { try { rec.stop(); } catch (_) {} }, 100);
          }
          onSend({ text: value, files: pendingFiles, audioBlob: blob });
          setPendingFiles([]);
          setIsRecording(false);
          clearInterval(timerRef.current);
          setRecordSecs(0);
        };
        mr.start();
        mediaRecRef.current = mr;
        setIsRecording(true);
        setRecordSecs(0);
        timerRef.current = setInterval(() => setRecordSecs((s) => s + 1), 1000);
        return;
      } catch (_) { /* fall through to Web Speech */ }
    }

    // Fallback: Web Speech API only
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { alert("Voice input not supported. Please use Chrome or Edge."); return; }
    const rec = new SR();
    rec.lang = "en-IN";
    rec.interimResults = true;
    rec.onresult = (ev) => {
      const t = Array.from(ev.results).map((r) => r[0].transcript).join(" ");
      onChange(t);
    };
    rec.onend = () => { setIsRecording(false); clearInterval(timerRef.current); setRecordSecs(0); };
    rec.start();
    mediaRecRef.current = { stop: () => rec.stop(), _isSpeech: true };
    setIsRecording(true);
    timerRef.current = setInterval(() => setRecordSecs((s) => s + 1), 1000);
  }, [value, pendingFiles, onSend, onChange]);

  const stopRecording = useCallback(() => {
    if (mediaRecRef.current) {
      mediaRecRef.current.stop();
      if (!mediaRecRef.current._isSpeech) {
        // onstop handler will call onSend
      } else {
        setIsRecording(false);
        clearInterval(timerRef.current);
        setRecordSecs(0);
      }
    }
  }, []);

  const canSend = (value.trim().length > 0 || pendingFiles.length > 0) && !disabled;

  return (
    <div className="bg-white border-t border-slate-100">
      {/* Pending files strip */}
      {pendingFiles.length > 0 && (
        <div className="px-6 pt-3 flex flex-wrap gap-2">
          {pendingFiles.map((f, i) => (
            <div key={i} className="flex items-center gap-1.5 bg-slate-100 border border-slate-200 rounded-lg px-2.5 py-1 text-[12px] font-[Work_Sans] text-[#002045]">
              <span className="material-symbols-outlined text-[14px]">
                {f.type.startsWith("image/") ? "image" : "description"}
              </span>
              <span className="max-w-[120px] truncate">{f.name}</span>
              <button onClick={() => removeFile(i)} className="text-[#74777f] hover:text-red-500">
                <span className="material-symbols-outlined text-[13px]">close</span>
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Recording indicator */}
      {isRecording && (
        <div className="px-6 pt-2 flex items-center gap-2 text-red-600 font-[Work_Sans] text-[12px]">
          <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
          Recording… {recordSecs}s — tap mic again to stop &amp; send
        </div>
      )}

      {/* Input row */}
      <div className="p-4 pb-5">
        <div className="max-w-4xl mx-auto flex items-end gap-2 bg-white border border-slate-200 p-2 rounded-2xl shadow-sm focus-within:border-[#002045] transition-all">
          {/* Hidden inputs */}
          <input ref={fileInputRef}  type="file" accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.webp" multiple className="hidden" onChange={handleFileChange} />
          <input ref={photoInputRef} type="file" accept="image/*" capture="environment" className="hidden" onChange={handleFileChange} />

          {/* Action buttons */}
          <div className="flex items-center gap-0.5 mb-1 px-1">
            <button type="button" title="Attach file" disabled={disabled}
              onClick={() => fileInputRef.current?.click()}
              className="p-2 text-[#74777f] hover:text-[#002045] hover:bg-slate-100 rounded-full transition-all disabled:opacity-40">
              <span className="material-symbols-outlined text-[20px]">attach_file</span>
            </button>
            <button type="button" title="Upload photo" disabled={disabled}
              onClick={() => photoInputRef.current?.click()}
              className="p-2 text-[#74777f] hover:text-[#002045] hover:bg-slate-100 rounded-full transition-all disabled:opacity-40">
              <span className="material-symbols-outlined text-[20px]">photo_camera</span>
            </button>
            <button type="button"
              title={isRecording ? "Stop recording" : "Voice input"}
              disabled={disabled}
              onClick={isRecording ? stopRecording : startRecording}
              className={`p-2 rounded-full transition-all disabled:opacity-40 ${
                isRecording
                  ? "text-red-500 bg-red-50 hover:bg-red-100 animate-pulse"
                  : "text-[#74777f] hover:text-[#002045] hover:bg-slate-100"
              }`}>
              <span className="material-symbols-outlined text-[20px]">
                {isRecording ? "stop_circle" : "mic"}
              </span>
            </button>
          </div>

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={value}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder={isRecording ? "Listening…" : "Type your message, upload a file, or use voice…"}
            rows={1}
            disabled={disabled || isRecording}
            className="flex-grow border-none focus:ring-0 font-[Work_Sans] text-[15px] py-3 bg-transparent resize-none min-h-[44px] placeholder:text-[#74777f] outline-none disabled:opacity-60"
            style={{ scrollbarWidth: "none" }}
          />

          {/* Send */}
          <button type="button" onClick={triggerSend} disabled={!canSend}
            className="bg-[#fea619] text-[#684000] h-11 w-11 flex items-center justify-center rounded-xl shadow-md hover:brightness-105 active:scale-95 transition-all disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0">
            {disabled
              ? <span className="w-4 h-4 border-2 border-[#684000] border-t-transparent rounded-full animate-spin" />
              : <span className="material-symbols-outlined text-[20px]">send</span>
            }
          </button>
        </div>

        <div className="flex justify-center mt-2">
          <span className="font-[Work_Sans] text-[10px] text-[#74777f] flex items-center gap-1">
            <span className="material-symbols-outlined text-[11px]">lock</span>
            End-to-end encrypted · Your data is secure with ClaimFlow
          </span>
        </div>
      </div>
    </div>
  );
}
