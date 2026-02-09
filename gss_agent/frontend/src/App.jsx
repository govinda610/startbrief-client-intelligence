import React, { useState, useEffect, useRef } from 'react';
import { Send, Activity, Brain, Shield, ChevronDown, ChevronRight, Play, Terminal, ToggleLeft, ToggleRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// --- SVGs & Icons ---
const GartnerLogo = () => (
  <div className="flex items-center gap-2 mb-8">
    <div className="w-8 h-8 bg-gartner-cyan rounded-sm flex items-center justify-center">
      <span className="text-gartner-bg font-bold text-xl">G</span>
    </div>
    <div className="flex flex-col">
      <span className="text-gartner-light font-bold text-lg tracking-tight">Gartner</span>
      <span className="text-gartner-slate text-xs uppercase tracking-widest">Strategic Advisor</span>
    </div>
  </div>
);

// --- Components ---

const MetricCard = ({ title, value, subtext, type = "neutral" }) => (
  <div className="glass-panel p-4 flex flex-col items-center justify-center relative overflow-hidden group">
    <div className={`absolute top-0 left-0 w-full h-1 ${type === 'good' ? 'bg-gartner-cyan' : type === 'risk' ? 'bg-red-500' : 'bg-gartner-blue'}`} />
    <span className="text-gartner-slate text-xs uppercase font-semibold mb-1">{title}</span>
    <span className="text-3xl font-bold text-white mb-1 group-hover:scale-110 transition-transform duration-300">{value}</span>
    <span className="text-[10px] text-gartner-slate/70">{subtext}</span>
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

  return (
    <div className="glass-panel mt-4 overflow-hidden border-l-4 border-l-gartner-cyan">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-3 bg-gartner-card hover:bg-gartner-hover transition-colors"
      >
        <div className="flex items-center gap-2 text-gartner-cyan text-sm font-medium">
          <Terminal size={14} />
          <span>Agent Reasoning Stream</span>
          <span className="bg-gartner-cyan/10 px-2 py-0.5 rounded text-[10px] animate-pulse">LIVE</span>
        </div>
        {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
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
                    <span className="text-gartner-slate/50 text-[10px]">{trace.type}</span>
                  </div>
                  <div className="text-gartner-slate whitespace-pre-wrap leading-relaxed">
                    {trace.content}
                  </div>
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
  // Initialize thread_id ONCE per session
  const [threadId] = useState(() => "demo_session_" + Date.now());
  const messagesEndRef = useRef(null);

  // Business Metrics (Mocked for Demo, usually dynamic)
  const metrics_data = [
    { name: 'Risk', value: 30, color: '#EF4444' },
    { name: 'Safe', value: 70, color: '#10B981' },
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages, traces]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const userMsg = input;
    setInput("");
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setIsStreaming(true);
    setTraces([]); // Reset traces for new turn

    try {
      const endpoint = useMock ? 'http://localhost:8001/api/mock-chat-golden' : 'http://localhost:8001/api/chat';
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg, thread_id: threadId })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      // Add initial empty AI message
      setMessages(prev => [...prev, { role: 'assistant', content: "" }]);

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

              // Route: Supervisor Final Output -> Main Chat Bubble
              // DeepAgents emits "model" or "Supervisor" node names
              // CRITICAL: We accept these even if they have tool calls, because sometimes the final answer IS a tool call (save file) OR accompanies one.
              const isSupervisorNode = data.node === "Supervisor" || data.node === "model";

              if (isSupervisorNode) {
                // Update the LAST message (which is our assistant bubble)
                setMessages(prev => {
                  const newMsgs = [...prev];
                  if (newMsgs.length > 0) {
                    newMsgs[newMsgs.length - 1].content = data.content;
                  }
                  return newMsgs;
                });

                // If it ALSO has tool calls, log it to traces too so we see the action
                if (data.has_tool_calls) {
                  setTraces(prev => [...prev, data]);
                }
              }
              // Route: Tools/Thoughts/Critic -> Traces
              else {
                setTraces(prev => [...prev, data]);
              }

            } catch (e) {
              console.error("Parse error", e);
            }
          }
        }
      }
    } catch (error) {
      console.error("Stream failed", error);
      setMessages(prev => [...prev, { role: 'system', content: "Error: Connection to Gartner Brain failed." }]);
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className="flex h-screen bg-gartner-bg text-gartner-slate selection:bg-gartner-cyan selection:text-gartner-bg">

      {/* Sidebar / Business Intelligence */}
      <div className="w-80 bg-gartner-card/50 border-r border-gartner-border/30 p-6 flex flex-col hidden md:flex">
        <GartnerLogo />

        <div className="mb-8">
          <h3 className="text-gartner-light text-sm font-semibold mb-4 flex items-center gap-2">
            <Activity size={16} className="text-gartner-cyan" />
            Engagement Health
          </h3>
          <div className="h-40 w-full glass-panel flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={metrics_data}
                  innerRadius={40}
                  outerRadius={60}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {metrics_data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute text-center">
              <span className="text-2xl font-bold text-white">92%</span>
              <span className="block text-[10px]">Retention</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-auto">
          <MetricCard title="Churn Risk" value="Low" type="good" subtext="-5% vs Last Q" />
          <MetricCard title="Upsell" value="$45k" type="neutral" subtext="Potential ARR" />
        </div>

        <div className="glass-panel p-4 mt-4">
          <h4 className="text-xs uppercase font-bold text-gartner-cyan mb-2 flex items-center gap-2">
            <Shield size={12} />
            Minimax M2.1 Core
          </h4>
          <p className="text-[10px] leading-relaxed opacity-70">
            Running on Gartner Secure Cloud (OpenRouter).
            Recursion Limit: 50.
            Context: 128k.
          </p>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative">
        {/* Header */}
        <div className="h-16 border-b border-white/5 flex items-center justify-between px-6 bg-gartner-bg/80 backdrop-blur-sm z-10 sticky top-0">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
            <span className="text-sm font-medium text-gartner-light">Strategic Meeting Assistant</span>
          </div>
          <div className="flex gap-2 text-xs items-center">
            <button
              onClick={() => setUseMock(!useMock)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-full border transition-all ${useMock
                ? 'bg-amber-500/10 border-amber-500/50 text-amber-500'
                : 'bg-green-500/10 border-green-500/50 text-green-500'
                }`}
            >
              {useMock ? <ToggleRight size={16} /> : <ToggleLeft size={16} />}
              {useMock ? 'Mock Mode' : 'Live Mode'}
            </button>
            <button className="px-3 py-1.5 glass-panel hover:bg-white/5 transition">Reset Session</button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center opacity-50">
              <Brain size={64} className="text-gartner-cyan mb-4 opacity-50" />
              <p className="text-lg">Ready to analyze client portfolio.</p>
            </div>
          )}

          {messages.map((msg, idx) => {
            // Logic: If this is the LAST message AND it is from the assistant,
            // we render the TRACES (if any) BEFORE the message bubble.
            const isLastAssistantMessage = (idx === messages.length - 1) && (msg.role === 'assistant');

            return (
              <React.Fragment key={idx}>
                {isLastAssistantMessage && traces.length > 0 && (
                  <div className="mb-4">
                    <TraceLog traces={traces} />
                  </div>
                )}

                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-[80%] rounded-2xl p-5 ${msg.role === 'user'
                    ? 'bg-gartner-cyan text-gartner-bg font-medium rounded-tr-sm'
                    : 'glass-panel rounded-tl-sm prose prose-invert'
                    }`}>
                    <div className="prose prose-invert prose-sm max-w-none">
                      {msg.role === 'user' ? (
                        <p className="whitespace-pre-wrap mb-0">{msg.content}</p>
                      ) : (
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            p: ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />,
                            ul: ({ node, ...props }) => <ul className="list-disc ml-4 mb-2" {...props} />,
                            ol: ({ node, ...props }) => <ol className="list-decimal ml-4 mb-2" {...props} />,
                            li: ({ node, ...props }) => <li className="mb-1" {...props} />,
                            h1: ({ node, ...props }) => <h1 className="text-lg font-bold mb-2 text-white" {...props} />,
                            h2: ({ node, ...props }) => <h2 className="text-base font-bold mb-2 text-white" {...props} />,
                            h3: ({ node, ...props }) => <h3 className="text-sm font-bold mb-1 text-white" {...props} />,
                            code: ({ node, inline, className, children, ...props }) => {
                              return inline ?
                                <code className="bg-white/10 px-1 py-0.5 rounded text-xs font-mono" {...props}>{children}</code> :
                                <pre className="bg-[#051020] p-3 rounded-lg overflow-x-auto text-xs font-mono my-2 border border-white/10" {...props}><code>{children}</code></pre>
                            },
                            table: ({ node, ...props }) => <div className="overflow-x-auto my-4"><table className="min-w-full text-left text-xs border border-white/10" {...props} /></div>,
                            th: ({ node, ...props }) => <th className="bg-white/5 p-2 font-semibold border-b border-white/10 text-gartner-cyan" {...props} />,
                            td: ({ node, ...props }) => <td className="p-2 border-b border-white/5" {...props} />,
                            blockquote: ({ node, ...props }) => <blockquote className="border-l-2 border-gartner-cyan pl-4 italic text-gartner-slate/80 my-2" {...props} />
                          }}
                        >
                          {msg.content || ""}
                        </ReactMarkdown>
                      )}
                      {!msg.content && <span className="animate-pulse">...</span>}
                    </div>
                  </div>
                </motion.div>
              </React.Fragment>
            );
          })}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-6 bg-gartner-bg border-t border-white/5">
          <form onSubmit={handleSubmit} className="relative max-w-4xl mx-auto">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about a client..."
              className="w-full bg-gartner-card border border-gartner-border/50 text-gartner-light rounded-xl pl-6 pr-14 py-4 focus:outline-none focus:ring-2 focus:ring-gartner-cyan/50 focus:border-gartner-cyan transition-all shadow-lg placeholder:text-gartner-slate/30"
              disabled={isStreaming}
            />
            <button
              type="submit"
              disabled={isStreaming || !input.trim()}
              className="absolute right-3 top-3 p-2 bg-gartner-cyan text-gartner-bg rounded-lg hover:bg-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send size={18} />
            </button>
          </form>
          <div className="text-center mt-3">
            <span className="text-[10px] text-gartner-slate/40 flex items-center justify-center gap-1">
              <Shield size={8} />
              Confidential. For Internal Use Only.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
