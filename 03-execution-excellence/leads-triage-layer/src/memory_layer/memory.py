import os
import json
import numpy as np
from typing import List, Dict, Any, Optional
from .models import PastProject, AggregateStats, MemorySearchRequest, MemorySearchResult
import ollama
from utils.env_loader import init_env
from collections import Counter

init_env()

class ProjectMemory:
    def __init__(self, data_path: Optional[str] = None, model_name: str = "gemma3:4b"):
        # Try multiple common paths for the data file
        if data_path:
            self.data_path = data_path
        else:
            possible_paths = [
                "data/past_projects.jsonl",
                "../data/past_projects.jsonl",
                "/Users/jimmypang/AntigravityProjects/PROJECT-casestudy-BAI-leads-triage-layer/data/past_projects.jsonl"
            ]
            self.data_path = next((p for p in possible_paths if os.path.exists(p)), possible_paths[0])
            
        self.model_name = model_name
        self.embed_model = "nomic-embed-text" # Standard embedding model
        self.projects: List[PastProject] = []
        self.project_embeddings: List[np.ndarray] = []
        
        # Initialize Ollama client
        api_key = os.getenv("OLLAMA_API_KEY")
        local_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        if api_key:
            self.client = ollama.Client(host="https://ollama.com", headers={"Authorization": f"Bearer {api_key}"})
        else:
            self.client = ollama.Client(host=local_host)

    def load_projects(self):
        """Loads projects from the JSONL file."""
        if not os.path.exists(self.data_path):
            print(f"WARNING: Data path {self.data_path} not found.")
            return
        
        self.projects = []
        with open(self.data_path, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    self.projects.append(PastProject.model_validate(data))
                except Exception as e:
                    print(f"Error loading line: {e}")
        print(f"INFO: Loaded {len(self.projects)} projects from {self.data_path}.")

    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Fetches embedding for a given text from Ollama."""
        try:
            # Try with the dedicated embedding model first, then fallback to gemma3
            try:
                response = self.client.embeddings(model=self.embed_model, prompt=text)
            except:
                response = self.client.embeddings(model=self.model_name, prompt=text)
            return np.array(response['embedding'])
        except Exception as e:
            print(f"Error fetching embedding: {e}")
            return None

    def index_projects(self, limit: int = 100):
        """
        Computes embeddings for project summaries. 
        Limit is used for development to avoid long wait times.
        """
        print(f"INFO: Indexing {min(len(self.projects), limit)} projects...")
        self.project_embeddings = []
        # For now, we only index the first 'limit' projects to save time/resources
        for project in self.projects[:limit]:
            emb = self._get_embedding(project.sales_call_summary)
            self.project_embeddings.append(emb)
        print("INFO: Indexing complete.")

    def search(self, request: MemorySearchRequest) -> MemorySearchResult:
        """Finds top-k similar projects based on features and transcript."""
        if not self.projects:
            self.load_projects()

        query_emb = None
        if request.transcript_text:
            query_emb = self._get_embedding(request.transcript_text)

        scores = []
        # Calculate similarity for each indexed project
        # If not indexed (due to limit), we only use categorical/numerical similarity
        for i, project in enumerate(self.projects):
            score = 0.0
            
            # 1. Categorical Similarity (Exact matches)
            cat_score = 0.0
            if request.region and project.region == request.region:
                cat_score += 1.0
            if request.product and project.product == request.product:
                cat_score += 1.0
            if request.fassaden_typ and project.fassaden_typ == request.fassaden_typ:
                cat_score += 1.0
            
            # Normalize cat score to [0, 1]
            cat_score /= 3.0
            score += 0.4 * cat_score

            # 2. Numerical Similarity (Building Year)
            num_score = 0.0
            if request.building_year and project.building_year:
                year_diff = abs(request.building_year - project.building_year)
                num_score = max(0, 1.0 - (year_diff / 50.0))
            score += 0.2 * num_score

            # 3. Vector Similarity (Embeddings)
            vec_score = 0.0
            if query_emb is not None and i < len(self.project_embeddings) and self.project_embeddings[i] is not None:
                proj_emb = self.project_embeddings[i]
                # Cosine similarity
                dot_product = np.dot(query_emb, proj_emb)
                norm_q = np.linalg.norm(query_emb)
                norm_p = np.linalg.norm(proj_emb)
                if norm_q > 0 and norm_p > 0:
                    vec_score = dot_product / (norm_q * norm_p)
            
            score += 0.4 * vec_score
            scores.append((score, project))

        # Sort by score descending
        scores.sort(key=lambda x: x[0], reverse=True)
        top_projects = [p for s, p in scores[:request.top_k]]
        
        # Calculate Stats
        stats = self.calculate_stats(top_projects)
        
        return MemorySearchResult(
            query=request,
            similar_projects=[p.model_dump() for p in top_projects],
            stats=stats
        )

    def calculate_stats(self, projects: List[PastProject]) -> AggregateStats:
        """Calculates aggregate statistics for a list of projects."""
        if not projects:
            return AggregateStats(total_similar=0, close_rate=0.0, avg_overrun_eur=0.0, common_issues=[])
        
        total = len(projects)
        closed = sum(1 for p in projects if p.stage in ["signed_installed", "completed"])
        
        overruns = []
        for p in projects:
            if p.initial_quote_eur and p.final_quote_eur:
                overruns.append(p.final_quote_eur - p.initial_quote_eur)
        
        avg_overrun = sum(overruns) / len(overruns) if overruns else 0.0
        
        # Common issues
        all_issues = []
        for p in projects:
            for issue in p.on_site_issues:
                category = issue.get("category")
                if category:
                    all_issues.append(category)
        
        common_issues = [item for item, count in Counter(all_issues).most_common(3)]
        
        return AggregateStats(
            total_similar=total,
            close_rate=closed / total,
            avg_overrun_eur=avg_overrun,
            common_issues=common_issues
        )
