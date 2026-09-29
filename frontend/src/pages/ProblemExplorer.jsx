import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate, useParams, Link } from 'react-router-dom';
import { Layers, ChevronRight, FileText, ArrowLeft, Users, Zap, ExternalLink } from 'lucide-react';

// --- MAIN EXPLORER VIEW ---
const ClusterGrid = () => {
  const [clusters, setClusters] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchClusters = async () => {
      try {
        const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';
        const response = await fetch(`${API_BASE_URL}/clusters/`);
        const data = await response.json();
        setClusters(data);
      } catch (err) {
        console.error("Failed to fetch clusters", err);
      } finally {
        setLoading(false);
      }
    };
    fetchClusters();
  }, []);

  if (loading) return <div className="animate-fade-in">Loading clusters...</div>;

  return (
    <div className="animate-fade-in">
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '8px' }}>Problem Explorer</h1>
        <p style={{ color: 'var(--text-secondary)' }}>AI-generated thematic clusters mapping the core user experience gaps.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '24px' }}>
        {clusters.map(cluster => (
          <div 
            key={cluster.id} 
            className="card" 
            style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column' }}
            onClick={() => navigate(`/explore/${cluster.id}`)}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
              <div style={{ background: 'rgba(59, 130, 246, 0.1)', padding: '8px', borderRadius: '8px' }}>
                <Layers size={24} color="var(--accent-primary)" />
              </div>
              <div style={{ background: 'var(--bg-tertiary)', padding: '4px 10px', borderRadius: '12px', fontSize: '0.8rem', fontWeight: 600 }}>
                {cluster.episode_count} episodes
              </div>
            </div>
            
            <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '8px', lineHeight: 1.3 }}>{cluster.label}</h3>
            
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '24px', flex: 1, display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
              {cluster.summary || 'No summary generated yet.'}
            </p>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '16px', color: 'var(--accent-primary)', fontSize: '0.9rem', fontWeight: 500 }}>
              <span>Analyze Cluster</span>
              <ChevronRight size={18} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// --- DETAILED CLUSTER VIEW ---
const ClusterDetail = () => {
  const { clusterId } = useParams();
  const [cluster, setCluster] = useState(null);
  const [episodes, setEpisodes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDetail = async () => {
      try {
        const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';
        const [clusterRes, episodesRes] = await Promise.all([
          fetch(`${API_BASE_URL}/clusters/${clusterId}`),
          fetch(`${API_BASE_URL}/clusters/${clusterId}/episodes`)
        ]);
        setCluster(await clusterRes.json());
        setEpisodes(await episodesRes.json());
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchDetail();
  }, [clusterId]);

  if (loading) return <div className="animate-fade-in">Loading cluster data...</div>;
  if (!cluster) return <div>Cluster not found</div>;

  return (
    <div className="animate-fade-in">
      <Link to="/explore" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)', textDecoration: 'none', marginBottom: '24px', fontSize: '0.9rem' }}>
        <ArrowLeft size={16} /> Back to Explorer
      </Link>
      
      <div className="card" style={{ marginBottom: '32px', background: 'var(--bg-secondary)', backgroundImage: 'radial-gradient(circle at top right, rgba(59, 130, 246, 0.05), transparent 40%)' }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '16px', color: 'var(--accent-primary)', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          <Layers size={16} /> Problem Cluster
        </div>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 800, marginBottom: '16px', lineHeight: 1.2 }}>{cluster.label}</h1>
        <p style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', maxWidth: '800px', lineHeight: 1.6, marginBottom: '24px' }}>
          {cluster.summary}
        </p>
        <div style={{ display: 'flex', gap: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileText size={18} color="var(--text-tertiary)" />
            <span style={{ fontWeight: 600 }}>{cluster.episode_count}</span> <span style={{ color: 'var(--text-secondary)' }}>Episodes</span>
          </div>
        </div>
      </div>

      <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '24px' }}>Pattern Breakdown</h2>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '48px' }}>
        <div className="card">
          <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '16px' }}>Dominant Failure Reasons</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {cluster.common_failure_reasons?.map((reason, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ width: '24px', height: '24px', borderRadius: '4px', background: 'rgba(239, 68, 68, 0.2)', color: '#EF4444', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem', fontWeight: 'bold' }}>{i+1}</div>
                <div style={{ flex: 1, textTransform: 'capitalize' }}>{reason.replace(/_/g, ' ')}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '16px' }}>What Users Attempted</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {cluster.common_retrieval_methods?.map((method, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ width: '24px', height: '24px', borderRadius: '4px', background: 'rgba(59, 130, 246, 0.2)', color: '#3B82F6', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem', fontWeight: 'bold' }}>{i+1}</div>
                <div style={{ flex: 1, textTransform: 'capitalize' }}>{method.replace(/_/g, ' ')}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '24px' }}>Extracted Episodes ({episodes.length})</h2>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {episodes.map(episode => (
          <div key={episode.id} className="card" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
              <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                <span className={`badge badge-${episode.source || 'reddit'}`}>{episode.source}</span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 600 }}>ID: {episode.id.split('-')[0]}</span>
              </div>
              {episode.source_url && (
                <a href={episode.source_url} target="_blank" rel="noreferrer" style={{ color: 'var(--accent-primary)' }}>
                  <ExternalLink size={16} />
                </a>
              )}
            </div>
            
            <h4 style={{ fontSize: '0.85rem', textTransform: 'uppercase', color: 'var(--text-tertiary)', fontWeight: 600, marginBottom: '8px' }}>User Goal</h4>
            <p style={{ fontSize: '1.1rem', marginBottom: '24px', fontWeight: 500 }}>{episode.user_goal}</p>

            <div style={{ background: 'var(--bg-primary)', padding: '16px', borderRadius: '8px', marginBottom: '24px', borderLeft: '3px solid var(--text-tertiary)' }}>
              <h4 style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-tertiary)', fontWeight: 600, marginBottom: '8px' }}>Original Feedback</h4>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', fontStyle: 'italic' }}>"{episode.supporting_evidence}"</p>
            </div>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '24px' }}>
              <div>
                <span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-tertiary)', marginBottom: '4px', textTransform: 'uppercase', fontWeight: 600 }}>Memory Type</span>
                <span style={{ background: 'var(--bg-tertiary)', padding: '4px 8px', borderRadius: '4px', fontSize: '0.85rem', textTransform: 'capitalize' }}>{episode.memory_type}</span>
              </div>
              
              <div>
                <span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-tertiary)', marginBottom: '4px', textTransform: 'uppercase', fontWeight: 600 }}>Clues Remembered</span>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  {episode.remembered_clues?.map(c => (
                    <span key={c} style={{ background: 'rgba(16, 185, 129, 0.1)', color: '#10B981', padding: '4px 8px', borderRadius: '4px', fontSize: '0.85rem' }}>{c}</span>
                  ))}
                </div>
              </div>
              
              <div>
                <span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-tertiary)', marginBottom: '4px', textTransform: 'uppercase', fontWeight: 600 }}>Why it failed</span>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  {episode.failure_reason?.map(f => (
                    <span key={f} style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#EF4444', padding: '4px 8px', borderRadius: '4px', fontSize: '0.85rem' }}>{f.replace(/_/g, ' ')}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// --- ROUTER OUTLET ---
const ProblemExplorer = () => {
  return (
    <Routes>
      <Route path="/" element={<ClusterGrid />} />
      <Route path="/:clusterId" element={<ClusterDetail />} />
    </Routes>
  );
};

export default ProblemExplorer;
