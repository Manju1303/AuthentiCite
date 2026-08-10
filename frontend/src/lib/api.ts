export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export interface Paper {
  id: string;
  filename: string;
  original_format: string;
  status: string;
  overall_similarity: number;
  created_at: string;
}

export interface Section {
  id: string;
  paper_id: string;
  section_name: string | null;
  original_text: string;
  rewritten_text: string | null;
  similarity_score: number;
  is_flagged: boolean;
  layout_metadata: {
    type: string;
    image_name?: string;
    alignment?: string;
    style?: string;
    quality_warnings?: string[];
    similarity_source?: {
      filename: string;
      matching_text: string;
      score: number;
    };
  };
}

export interface Reference {
  id: string;
  paper_id: string;
  raw_reference: string;
  citation_key: string | null;
}

export interface PaperAnalysis {
  paper: Paper;
  sections: Section[];
  references: Reference[];
}

export async function uploadPaper(file: File): Promise<Paper> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/v1/papers/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Failed to upload paper');
  }

  return response.json();
}

export async function getPapers(): Promise<Paper[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/papers`);
  if (!response.ok) throw new Error('Failed to fetch papers list');
  return response.json();
}

export async function getPaperDetails(paperId: string): Promise<PaperAnalysis> {
  const response = await fetch(`${API_BASE_URL}/api/v1/papers/${paperId}`);
  if (!response.ok) throw new Error('Failed to fetch paper details');
  return response.json();
}

export async function analyzePaper(paperId: string): Promise<{ overall_similarity: number; flagged_count: number }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/papers/${paperId}/analyze`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to run similarity analysis');
  return response.json();
}

export async function rewriteSection(sectionId: string, rewrittenText: string): Promise<Section> {
  const response = await fetch(`${API_BASE_URL}/api/v1/sections/${sectionId}/rewrite`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ rewritten_text: rewrittenText }),
  });
  if (!response.ok) throw new Error('Failed to rewrite section');
  return response.json();
}

export async function rewriteAll(paperId: string): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/papers/${paperId}/rewrite-all`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to trigger bulk rewrite');
  return response.json();
}

export async function rebuildPaper(paperId: string, format: string): Promise<{ filename: string; format: string }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/papers/${paperId}/rebuild`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ journal_format: format }),
  });
  if (!response.ok) throw new Error('Failed to rebuild paper');
  return response.json();
}

export function getDownloadUrl(paperId: string, format: string): string {
  return `${API_BASE_URL}/api/v1/papers/${paperId}/download?file_format=${format}`;
}

export interface RAGCitation {
  citation_id: string;
  section_id: string;
  paper_id: string;
  page_number: number;
  snippet: string;
  score: number;
}

export interface RAGResponse {
  query: string;
  answer: string;
  citations: RAGCitation[];
  context_used: string[];
}

export async function queryRAG(query: string, paperId?: string): Promise<RAGResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/rag/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, paper_id: paperId, top_k: 4 }),
  });
  if (!response.ok) throw new Error('Failed to query RAG assistant');
  return response.json();
}

export async function uploadOCR(file: File): Promise<any> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/v1/rag/ocr`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) throw new Error('Failed to run OCR on document');
  return response.json();
}

export interface PlagiarismRecommendation {
  section_id: string;
  section_name: string;
  similarity_score: number;
  match_source_file: string;
  recommended_action: string;
  tactics: string[];
  snippet: string;
}

export interface PlagiarismAdviceResponse {
  paper_id: string;
  filename: string;
  overall_similarity: number;
  flagged_count: number;
  strategy_summary: string;
  recommendations: PlagiarismRecommendation[];
}

export async function generatePaper(topic: string, journalTier: string = 'q1_ieee', journalFormat: string = 'ieee'): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/v1/generator/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic, journal_tier: journalTier, journal_format: journalFormat }),
  });
  if (!response.ok) throw new Error('Failed to generate research paper');
  return response.json();
}

export async function getJournalTiers(): Promise<Record<string, { name: string; style: string; citation_style: string }>> {
  const response = await fetch(`${API_BASE_URL}/api/v1/generator/tiers`);
  if (!response.ok) throw new Error('Failed to fetch journal tiers');
  return response.json();
}

export async function getPlagiarismAdvice(paperId: string): Promise<PlagiarismAdviceResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/advisor/${paperId}`);
  if (!response.ok) throw new Error('Failed to fetch plagiarism reduction advice');
  return response.json();
}


