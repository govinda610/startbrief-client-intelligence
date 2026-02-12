import React, { useState, useEffect, useRef } from 'react';
import { Send, Activity, Brain, Shield, ChevronDown, ChevronRight, Play, Terminal, ToggleLeft, ToggleRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// --- SVGs & Icons ---
const NexusLogo = () => (
  <div className="flex items-center gap-3 mb-8 px-2">
    <div className="w-10 h-10 bg-nexus-cyan rounded-md flex items-center justify-center shadow-[0_0_15px_rgba(34,211,238,0.3)]">
      <span className="text-nexus-bg font-extrabold text-2xl">N</span>
    </div>
    <div className="flex flex-col">
      <span className="text-white font-bold text-xl tracking-tight">Nexus</span>
      <span className="text-nexus-cyan text-xs font-bold uppercase tracking-widest">Strategic Advisor</span>
    </div>
  </div>
);

// --- Components ---

const MetricCard = ({ title, value, subtext, type = "neutral" }) => (
  <div className="bg-nexus-card/40 border border-nexus-border/50 p-4 flex flex-col items-center justify-center relative overflow-hidden group rounded-xl hover:bg-nexus-card/60 transition-all">
    <div className={`absolute top-0 left-0 w-full h-1 ${type === 'good' ? 'bg-nexus-cyan shadow-[0_0_10px_rgba(34,211,238,0.5)]' : type === 'risk' ? 'bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]' : 'bg-nexus-blue'}`} />
    <span className="text-nexus-slate text-xs uppercase font-bold mb-1 tracking-wider">{title}</span>
    <span className="text-3xl font-bold text-white mb-1 group-hover:scale-110 transition-transform duration-300 drop-shadow-md">{value}</span>
    <span className="text-[10px] text-white/70">{subtext}</span>
  </div>
);

const TraceLog = ({ traces }) => {
  const [expanded, setExpanded] = useState(true);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [traces]);

  if (!traces || traces.length === 0) return null;

  // Helper to safely extract displayable content from Anthropic content blocks
  const extractDisplayContent = (content) => {
    if (typeof content === "string") return content;
    if (Array.isArray(content)) {
      return content
        .map(block => {
          if (block.type === "text" && block.text) return block.text;
          if (block.type === "tool_use") return `[Tool: ${block.name}]`;
          return "";
        })
        .filter(Boolean)
        .join("\n");
    }
    if (typeof content === "object" && content !== null) {
      return JSON.stringify(content, null, 2);
    }
    return String(content || "");
  };

  return (
    <div className="bg-[#020617] mt-4 overflow-hidden border border-nexus-cyan/30 rounded-lg shadow-[0_0_15px_rgba(34,211,238,0.1)]">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-3 bg-nexus-cyan/5 hover:bg-nexus-cyan/10 transition-colors border-b border-nexus-cyan/20"
      >
        <div className="flex items-center gap-2 text-nexus-cyan text-sm font-bold">
          <Terminal size={14} />
          <span>Agent Reasoning Stream</span>
          <span className="bg-nexus-cyan text-nexus-bg px-2 py-0.5 rounded text-[10px] font-bold animate-pulse">LIVE</span>
        </div>
        {expanded ? <ChevronDown size={14} className="text-white" /> : <ChevronRight size={14} className="text-white" />}
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: "auto" }}
            exit={{ height: 0 }}
            className="overflow-hidden"
          >
            <div ref={scrollRef} className="p-3 max-h-60 overflow-y-auto font-mono text-xs space-y-2 bg-[#051020]">
              {traces.map((trace, idx) => (
                <div key={idx} className="border-l border-white/10 pl-2">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-[10px] px-1 py-0.5 rounded uppercase ${trace.node === "Supervisor" ? "bg-purple-500/20 text-purple-300" :
                      trace.node === "Critic" ? "bg-red-500/20 text-red-300" :
                        "bg-blue-500/20 text-blue-300"
                      }`}>
                      {trace.node}
                    </span>
                    <span className="text-nexus-slate/50 text-[10px]">{trace.type}</span>
                  </div>
                  <div className="text-nexus-slate whitespace-pre-wrap leading-relaxed">
                    {extractDisplayContent(trace.content)}
                  </div>

                  {/* Render Tool Call Details if present */}
                  {trace.tool_calls && trace.tool_calls.map((tc, i) => (
                    <div key={i} className="mt-2 bg-[#0a1a2f] border border-nexus-cyan/20 rounded-md p-2 overflow-hidden">
                      <div className="flex items-center gap-2 mb-1 border-b border-nexus-cyan/10 pb-1">
                        <Play size={10} className="text-nexus-cyan" />
                        <span className="text-nexus-cyan text-[10px] font-bold uppercase tracking-wider">{tc.tool_name}</span>
                      </div>

                      {tc.args?.code && (
                        <div className="relative group">
                          <Terminal size={10} className="absolute right-2 top-2 text-nexus-slate/30 group-hover:text-nexus-cyan transition-colors" />
                          <pre className="text-green-400 text-[10px] py-1 overflow-x-auto selection:bg-green-500/20">
                            <code>{tc.args.code}</code>
                          </pre>
                        </div>
                      )}

                      {/* For other tools, show summarized args if not too long */}
                      {!tc.args?.code && tc.args && Object.keys(tc.args).length > 0 && (
                        <div className="text-nexus-slate/70 text-[9px] italic">
                          Args: {JSON.stringify(tc.args)}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// --- Main Application ---

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [traces, setTraces] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [useMock, setUseMock] = useState(false);
  const [mode, setMode] = useState("frontline"); // "frontline" or "executive"
  // Initialize thread_id ONCE per session
  const [threadId] = useState(() => "demo_session_" + Date.now());
  const messagesEndRef = useRef(null);

  // Business Metrics (Mocked/Static for Demo)
  const metrics_data = [
    { name: 'Risk', value: 30, color: '#EF4444' },
    { name: 'Safe', value: 70, color: '#10B981' },
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const userMsg = input;
    setInput("");

    // Add User Message
    setMessages(prev => [
      ...prev,
      { role: 'user', content: userMsg }
    ]);

    setIsStreaming(true);

    try {
      let endpoint;
      if (useMock) {
        endpoint = 'http://localhost:8000/api/mock-chat-golden';
      } else {
        endpoint = mode === 'executive'
          ? 'http://localhost:8000/api/executive-chat'
          : 'http://localhost:8000/api/chat';
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg, thread_id: threadId })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      // Add initial empty AI message WITH empty traces array
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: "", traces: [] }
      ]);

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.replace('data: ', '');
            if (dataStr === '[DONE]') break;

            try {
              const data = JSON.parse(dataStr);

              // Update the LAST message (which is our assistant bubble)
              // Update the LAST message (which is our assistant bubble)
              setMessages(prev => {
                const newMsgs = [...prev];
                const lastMsgIndex = newMsgs.length - 1;
                // Create a shallow copy of the last message to avoid mutating immutable state
                // (though here we are mutating the copy)
                const lastMsg = { ...newMsgs[lastMsgIndex] };

                // Route: Supervisor Final Output -> Main Chat Bubble content
                const isSupervisorNode = data.node === "Supervisor" || data.node === "model";

                if (isSupervisorNode) {
                  // Extract text content
                  let textContent = "";
                  if (typeof data.content === "string") {
                    textContent = data.content;
                  } else if (Array.isArray(data.content)) {
                    textContent = data.content
                      .filter(block => block.type === "text" && block.text)
                      .map(block => block.text)
                      .join("\n");
                  }

                  if (textContent) {
                    lastMsg.content = textContent;
                  }

                  // If it ALSO has tool calls, log it to traces too
                  if (data.has_tool_calls) {
                    const currentTraces = lastMsg.traces || [];
                    const lastTrace = currentTraces[currentTraces.length - 1];
                    const isDuplicate = lastTrace && JSON.stringify(lastTrace) === JSON.stringify(data);

                    if (!isDuplicate) {
                      lastMsg.traces = [...currentTraces, data];
                    }
                  }
                }
                // Route: Tools/Thoughts/Critic -> Traces
                else {
                  const currentTraces = lastMsg.traces || [];
                  const lastTrace = currentTraces[currentTraces.length - 1];
                  const isDuplicate = lastTrace && JSON.stringify(lastTrace) === JSON.stringify(data);

                  if (!isDuplicate) {
                    lastMsg.traces = [...currentTraces, data];
                  }
                }

                newMsgs[lastMsgIndex] = lastMsg;
                return newMsgs;
              });

            } catch (e) {
              console.error("Parse error", e);
            }
          }
        }
      }
    } catch (error) {
      console.error("Stream failed", error);
      setMessages(prev => [...prev, { role: 'system', content: "Error: Connection to Nexus Brain failed." }]);
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className="flex h-[100dvh] overflow-hidden bg-nexus-bg text-nexus-slate selection:bg-nexus-cyan selection:text-nexus-bg">

      {/* Sidebar / Business Intelligence */}
      <div className="w-80 bg-[#0F172A] border-r border-nexus-border/50 p-6 flex flex-col hidden md:flex shadow-2xl z-20">
        <NexusLogo />

        <div className="mb-8">
          <h3 className="text-white text-sm font-bold mb-4 flex items-center gap-2 uppercase tracking-wider">
            <Activity size={16} className="text-nexus-cyan" />
            Engagement Health
          </h3>
          <div className="h-40 w-full bg-nexus-card/30 rounded-xl border border-nexus-border/30 flex items-center justify-center relative shadow-inner">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={metrics_data}
                  innerRadius={50}
                  outerRadius={70}
                  paddingAngle={5}
                  dataKey="value"
                  stroke="none"
                >
                  {metrics_data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#1E293B', borderColor: '#475569', color: '#fff' }}
                  itemStyle={{ color: '#fff' }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute text-center">
              <span className="text-3xl font-extrabold text-white drop-shadow-lg">92%</span>
              <span className="block text-[10px] text-nexus-slate uppercase font-bold tracking-wider">Retention</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-auto">
          <MetricCard title="Churn Risk" value="Low" type="good" subtext="-5% vs Last Q" />
          <MetricCard title="Upsell" value="$45k" type="neutral" subtext="Potential ARR" />
        </div>

        {/* Mode Toggle */}
        <div className="mb-6 p-1.5 bg-[#020617] rounded-xl flex items-center border border-white/10 shadow-inner">
          <button
            onClick={() => setMode("frontline")}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-xs font-bold rounded-lg transition-all duration-300 border ${mode === "frontline"
              ? "bg-nexus-cyan/10 text-nexus-cyan border-nexus-cyan shadow-[0_0_15px_rgba(34,211,238,0.4)] scale-[1.02]"
              : "border-transparent text-nexus-slate hover:text-white hover:bg-white/5"
              }`}
          >
            <Activity size={14} className={mode === "frontline" ? "stroke-[3px] drop-shadow-[0_0_8px_rgba(34,211,238,0.8)]" : ""} />
            Frontline
          </button>
          <button
            onClick={() => setMode("executive")}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-xs font-bold rounded-lg transition-all duration-300 border ${mode === "executive"
              ? "bg-nexus-blue/10 text-nexus-blue border-nexus-blue shadow-[0_0_15px_rgba(96,165,250,0.4)] scale-[1.02]"
              : "border-transparent text-nexus-slate hover:text-white hover:bg-white/5"
              }`}
          >
            <Shield size={14} className={mode === "executive" ? "stroke-[3px] drop-shadow-[0_0_8px_rgba(96,165,250,0.8)]" : ""} />
            Executive
          </button>
        </div>

        <div className="bg-nexus-card/40 border border-nexus-border/50 p-4 mt-4 rounded-xl">
          <h4 className="text-xs uppercase font-extrabold text-nexus-cyan mb-2 flex items-center gap-2 tracking-wide">
            <Brain size={14} />
            ZAI GLM-4.7
          </h4>
          <p className="text-[10px] leading-relaxed text-nexus-slate/80 font-medium">
            Running on Nexus Secure Cloud.
            Recursion Limit: 100.
            Context: 128k.
          </p>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative min-h-0">
        {/* Header */}
        {/* Header */}
        <div className="h-16 border-b border-nexus-border/50 flex items-center justify-between px-6 bg-nexus-bg/95 backdrop-blur-md z-10 sticky top-0 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(52,211,153,0.6)]"></div>
            <span className="text-sm font-bold text-white tracking-wide">Strategic Meeting Assistant</span>
          </div>
          <div className="flex gap-2 text-xs items-center">
            <button
              onClick={() => setUseMock(!useMock)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border transition-all font-semibold ${useMock
                ? 'bg-amber-500/10 border-amber-500/50 text-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.2)]'
                : 'bg-emerald-500/10 border-emerald-500/50 text-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.2)]'
                }`}
            >
              {useMock ? <ToggleRight size={16} /> : <ToggleLeft size={16} />}
              {useMock ? 'Mock Mode' : 'Live Mode'}
            </button>
            <button className="px-3 py-1.5 border border-white/10 rounded-lg hover:bg-white/5 hover:border-white/30 text-nexus-slate hover:text-white transition-all font-medium">Reset Session</button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center opacity-50">
              <Brain size={64} className="text-nexus-cyan mb-4 opacity-50" />
              <p className="text-lg">Ready to analyze client portfolio.</p>
            </div>
          )}

          {messages.map((msg, idx) => {
            // Logic: Render traces if the message has them
            const hasTraces = msg.role === 'assistant' && msg.traces && msg.traces.length > 0;

            return (
              <React.Fragment key={idx}>
                {hasTraces && (
                  <div className="mb-4">
                    <TraceLog traces={msg.traces} />
                  </div>
                )}

                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-[85%] rounded-2xl p-6 shadow-lg backdrop-blur-sm ${msg.role === 'user'
                    ? 'bg-nexus-cyan/10 border border-nexus-cyan/50 text-white rounded-tr-sm shadow-[0_0_15px_rgba(34,211,238,0.1)]'
                    : 'bg-nexus-cyan/5 border border-nexus-cyan/40 text-white rounded-tl-sm shadow-[0_0_10px_rgba(34,211,238,0.05)]'
                    }`}>
                    <div className="prose prose-sm max-w-none text-white">
                      {msg.role === 'user' ? (
                        <p className="whitespace-pre-wrap mb-0 text-base font-medium leading-relaxed">{msg.content}</p>
                      ) : (
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            p: ({ node, ...props }) => <p className="mb-3 last:mb-0 leading-relaxed text-nexus-slate/90 text-[13px]" {...props} />,
                            ul: ({ node, ...props }) => <ul className="list-disc ml-4 mb-3 text-nexus-slate/90" {...props} />,
                            ol: ({ node, ...props }) => <ol className="list-decimal ml-4 mb-3 text-nexus-slate/90" {...props} />,
                            li: ({ node, ...props }) => <li className="mb-1.5 pl-1" {...props} />,
                            h1: ({ node, ...props }) => <h1 className="text-lg font-extrabold mb-3 text-white border-b border-white/10 pb-2 mt-4 first:mt-0" {...props} />,
                            h2: ({ node, ...props }) => <h2 className="text-base font-bold mb-2 text-white mt-4 flex items-center gap-2" {...props} />,
                            h3: ({ node, ...props }) => <h3 className="text-sm font-bold mb-2 text-nexus-cyan mt-3 uppercase tracking-wide" {...props} />,
                            code: ({ node, inline, className, children, ...props }) => {
                              return inline ?
                                <code className="bg-white/5 px-1.5 py-0.5 rounded text-xs font-mono text-nexus-cyan border border-white/5" {...props}>{children}</code> :
                                <pre className="bg-[#020617] p-4 rounded-xl overflow-x-auto text-xs font-mono my-3 border border-nexus-border/50 shadow-inner" {...props}><code className="text-emerald-400">{children}</code></pre>
                            },
                            table: ({ node, ...props }) => <div className="overflow-x-auto my-4 rounded-lg border border-nexus-border/50 shadow-sm"><table className="min-w-full text-left text-xs bg-[#0F172A]" {...props} /></div>,
                            th: ({ node, ...props }) => <th className="bg-nexus-card p-3 font-bold border-b border-nexus-border text-nexus-cyan uppercase tracking-wider text-[10px]" {...props} />,
                            td: ({ node, ...props }) => <td className="p-3 border-b border-nexus-border/30 text-nexus-slate" {...props} />,
                            blockquote: ({ node, ...props }) => <blockquote className="border-l-4 border-nexus-cyan/50 pl-4 italic text-white/70 my-4 bg-white/5 p-3 rounded-r-lg" {...props} />
                          }}
                        >
                          {msg.content || ""}
                        </ReactMarkdown>
                      )}
                      {!msg.content && <div className="flex gap-1 items-center h-6"><span className="w-1.5 h-1.5 bg-nexus-cyan rounded-full animate-bounce"></span><span className="w-1.5 h-1.5 bg-nexus-cyan rounded-full animate-bounce delay-75"></span><span className="w-1.5 h-1.5 bg-nexus-cyan rounded-full animate-bounce delay-150"></span></div>}
                    </div>
                  </div>
                </motion.div>
              </React.Fragment>
            );
          })}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-6 bg-nexus-bg border-t border-nexus-border">
          <form onSubmit={handleSubmit} className="relative max-w-4xl mx-auto group">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about a client..."
              className="w-full bg-[#0F172A] border border-nexus-border text-white rounded-2xl pl-6 pr-14 py-4 focus:outline-none focus:ring-2 focus:ring-nexus-cyan/50 focus:border-nexus-cyan transition-all shadow-xl placeholder:text-nexus-slate/50 font-medium"
              disabled={isStreaming}
            />
            <button
              type="submit"
              disabled={isStreaming || !input.trim()}
              className="absolute right-2 top-2 p-2.5 bg-nexus-cyan text-[#0F172A] rounded-xl hover:bg-white transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_0_10px_rgba(34,211,238,0.4)] hover:shadow-[0_0_15px_rgba(255,255,255,0.6)]"
            >
              <Send size={20} className="stroke-[2.5px]" />
            </button>
          </form>
          <div className="text-center mt-3">
            <span className="text-[10px] text-nexus-slate/40 flex items-center justify-center gap-1 font-semibold uppercase tracking-wider">
              <Shield size={10} />
              Confidential. For Internal Use Only.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
