import PropTypes from 'prop-types';
import { useState, useRef, useEffect } from "react";
import { askQuestion } from "../api";

const SUGGESTIONS = ["What are the payment terms?", "Can I end this contract early?", "Who owns the work I deliver?"];

export default function ChatBox({ documentId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const listRef = useRef(null);

  useEffect(() => {
    const el = listRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, loading]);

  const send = async (text) => {
    const q = (text ?? input).trim();
    if (!q || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: q }]);
    setLoading(true);
    try {
      const res = await askQuestion(documentId, q);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: res.data.answer, sources: res.data.sources },
      ]);
    } catch {
      setMessages((m) => [...m, { role: "assistant", content: "Sorry, something went wrong. Please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section data-tour="chat" className={`flex flex-col rounded-[4px] border border-rule bg-sheet ${messages.length || loading ? "h-[440px]" : ""}`}>
      <div className="px-5 pt-5 pb-3 sm:px-7">
        <h2 className="font-serif text-[21px] font-semibold text-ink">Ask about this contract</h2>
        <p className="mt-0.5 text-[13px] text-ink-3">Answers come from the contract’s own text only.</p>
      </div>

      <div ref={listRef} className="flex-1 overflow-y-auto border-t border-rule px-5 py-4 sm:px-7">
        {messages.length === 0 && !loading ? (
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => send(s)}
                className="rounded-[3px] border border-rule px-3 py-1.5 text-[13px] text-ink-2 hover:border-ink-3 hover:text-ink"
              >
                {s}
              </button>
            ))}
          </div>
        ) : (
          <dl className="space-y-4">
            {messages.map((msg, i) => (
              <div key={i} className="grid grid-cols-[22px_1fr] gap-2">
                <dt className={`num pt-0.5 text-[12px] font-semibold ${msg.role === "user" ? "text-ink-3" : "text-rev"}`}>
                  {msg.role === "user" ? "Q" : "A"}
                </dt>
                <dd className={`whitespace-pre-wrap leading-relaxed ${msg.role === "user" ? "text-[14px] font-medium text-ink" : "font-serif text-[15.5px] text-ink-2"}`}>
                  {msg.content}
                </dd>
              </div>
            ))}
            {loading && (
              <div className="grid grid-cols-[22px_1fr] gap-2">
                <dt className="num pt-0.5 text-[12px] font-semibold text-rev">A</dt>
                <dd className="text-[14px] text-ink-3">Reading the contract<span className="animate-pulse">…</span></dd>
              </div>
            )}
          </dl>
        )}
      </div>

      <form
        className="flex gap-2 border-t border-rule px-5 py-3 sm:px-7"
        onSubmit={(e) => { e.preventDefault(); send(); }}
      >
        <label htmlFor="qa-input" className="sr-only">Question about the contract</label>
        <input
          id="qa-input"
          className="min-w-0 flex-1 rounded-[3px] border border-rule bg-sheet px-3 py-2 text-[14px] text-ink placeholder:text-ink-3 focus:border-ink-2 focus:outline-none"
          placeholder="e.g. What happens if I deliver late?"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
        />
        <button
          type="submit"
          disabled={!input.trim() || loading}
          className="rounded-[3px] bg-ink px-4 py-2 text-[14px] font-medium text-sheet hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Ask
        </button>
      </form>
    </section>
  );
}

ChatBox.propTypes = { documentId: PropTypes.string };
