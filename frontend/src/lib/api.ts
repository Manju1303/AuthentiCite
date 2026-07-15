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
