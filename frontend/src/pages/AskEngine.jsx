import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Search, Loader, Zap, Info, ShieldCheck } from 'lucide-react';

const AskEngine = () => {
  const [query, setQuery] = useState('');
  const [activeQuestion, setActiveQuestion] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const endRef = useRef(null);

  const suggestedQuestions = [
    "What kinds of old photos do users struggle to retrieve?",
    "What information do people actually remember about a photo?",
    "What information have they forgotten?",
    "How do users formulate searches when their memory is incomplete?"
  ];

  const handleAsk = async (q = query) => {
    if (!q.trim()) return;
    
    setActiveQuestion(q);
    setQuery('');
    setIsAsking(true);
    setError(null);
    setResult(null);

    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';
      const response = await fetch(`${API_BASE_URL}/ask/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q })
      });
      
      if (!response.ok) throw new Error('Failed to get answer from backend');
      
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsAsking(false);
      setTimeout(() => endRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 64px)' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '8px' }}>Ask AI</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Query to know more about photo retrieval experience of different users.</p>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', paddingRight: '16px', display: 'flex', flexDirection: 'column', gap: '24px', paddingBottom: '48px' }}>
        
        {/* Suggested Prompts (when empty) */}
        {!result && !isAsking && !error && (
          <div style={{ margin: 'auto', maxWidth: '600px', width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '24px' }}>
              <div style={{ background: 'var(--bg-secondary)', padding: '16px', borderRadius: '50%', boxShadow: 'var(--shadow-md)' }}>
                <Search size={32} color="var(--accent-primary)" />
              </div>
            </div>
            <h2 style={{ textAlign: 'center', marginBottom: '24px', fontWeight: 500 }}>What would you like to discover?</h2>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              {suggestedQuestions.map((sq, i) => (
                <div 
                  key={i} 
                  className="card" 
                  style={{ cursor: 'pointer', padding: '16px', fontSize: '0.9rem' }}
                  onClick={() => handleAsk(sq)}
                >
                  {sq}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Question Bubble */}
        {(result || isAsking || error) && (
          <div style={{ alignSelf: 'flex-end', background: 'var(--accent-gradient)', color: 'white', padding: '16px 24px', borderRadius: '24px 24px 4px 24px', maxWidth: '80%', boxShadow: 'var(--shadow-sm)' }}>
            {activeQuestion}
          </div>
        )}

        {/* Loading State */}
        {isAsking && (
          <div style={{ alignSelf: 'flex-start', background: 'var(--bg-secondary)', padding: '24px', borderRadius: '24px 24px 24px 4px', display: 'flex', alignItems: 'center', gap: '16px' }}>
            <Loader className="animate-spin" size={20} color="var(--accent-primary)" />
            <span style={{ color: 'var(--text-secondary)' }}>Searching vector database and synthesizing answer...</span>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div style={{ alignSelf: 'flex-start', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', padding: '24px', borderRadius: '24px 24px 24px 4px', color: '#EF4444' }}>
            {error}
          </div>
        )}

        {/* Result Bubble */}
        {result && (
          <div className="animate-slide-up" style={{ alignSelf: 'flex-start', maxWidth: '85%' }}>
            
            <div style={{ background: 'var(--bg-secondary)', padding: '32px', borderRadius: '24px 24px 24px 4px', border: '1px solid rgba(255,255,255,0.05)', boxShadow: 'var(--shadow-md)' }}>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '24px', paddingBottom: '16px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <Zap size={18} color="var(--accent-primary)" />
                <span style={{ fontWeight: 600, color: 'var(--accent-primary)' }}>AI Synthesis</span>
                
                <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', background: 'rgba(16, 185, 129, 0.1)', color: '#10B981', padding: '4px 10px', borderRadius: '12px' }}>
                  <ShieldCheck size={14} /> {result.confidence} Confidence ({result.evidence_count} sources)
                </div>
              </div>

              {/* Format markdown beautifully using ReactMarkdown */}
              <div className="markdown-body" style={{ fontSize: '1.05rem', lineHeight: 1.7, color: 'var(--text-primary)' }}>
                <ReactMarkdown>{result.answer.replace(/\\n/g, '\n')}</ReactMarkdown>
              </div>
            </div>

            {/* Citations */}
            {result.citations && result.citations.length > 0 && (
              <div style={{ marginTop: '24px' }}>
                <h3 style={{ fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-tertiary)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Info size={14} /> Grounding Evidence
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '12px', paddingBottom: '12px' }}>
                  {result.citations.slice(0, 5).map((citation, i) => (
                    <div key={i} className="card" style={{ padding: '16px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                        <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Source {citation.source_index}</span>
                        <span className={`badge badge-${citation.metadata.source || 'community'}`}>{citation.metadata.source || 'community'}</span>
                      </div>
                      <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: '-webkit-box', WebkitLineClamp: 6, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                        "{citation.text_snippet}"
                      </p>
                    </div>
                  ))}
                  {result.citations.length > 5 && (
                    <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent-primary)', fontWeight: 500, cursor: 'pointer', padding: '16px' }}>
                      +{result.citations.length - 5} more sources
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Input Area */}
      <div className="glass-panel" style={{ padding: '12px 16px', display: 'flex', gap: '12px', alignItems: 'center' }}>
        <input 
          type="text" 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about user pain points..."
          style={{ 
            flex: 1, 
            background: 'transparent', 
            border: 'none', 
            color: 'var(--text-primary)',
            fontSize: '1rem',
            outline: 'none',
            padding: '8px'
          }}
          disabled={isAsking}
        />
        <button 
          className="btn btn-primary" 
          style={{ borderRadius: '50%', width: '40px', height: '40px', padding: 0 }}
          onClick={() => handleAsk()}
          disabled={isAsking || !query.trim()}
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
};

export default AskEngine;
