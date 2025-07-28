import os
import json
import time
import re
import pdfplumber
import numpy as np
from datetime import datetime
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import concurrent.futures
from functools import lru_cache
import multiprocessing

class PDFProcessor:
    def __init__(self, model_path='models/all-MiniLM-L6-v2', max_workers=None, batch_size=32):
        # Load the sentence transformer model
        self.model = SentenceTransformer(model_path)
        # Set the number of workers for parallel processing
        self.max_workers = max_workers if max_workers else max(1, multiprocessing.cpu_count() - 1)
        # Cache for embeddings
        self.embedding_cache = {}
        # Set batch size for encoding
        self.batch_size = batch_size
        print(f"Initialized PDFProcessor with {self.max_workers} workers and batch size {self.batch_size}")
        
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF with page numbers and section titles - optimized version"""
        sections = []
        all_text = ""
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                current_section = {"title": "Introduction", "text": "", "page": 1}
                
                # Process only the first 15 pages or all pages if less than 15 for better efficiency
                max_pages = min(15, len(pdf.pages))
                
                for page_num, page in enumerate(pdf.pages[:max_pages], 1):
                    text = page.extract_text()
                    if not text or len(text.strip()) < 10:  # Skip nearly empty pages
                        continue
                        
                    # Add to all text
                    all_text += text + "\n"
                    
                    # Look for section headers (usually in bold or larger font)
                    lines = text.split('\n')
                    for line in lines:
                        # Optimized heuristic for section headers
                        stripped_line = line.strip()
                        # Skip very long lines immediately
                        if len(stripped_line) >= 80:  # Reduced from 100 to 80 for better header detection
                            current_section["text"] += line + "\n"
                            continue
                            
                        # Enhanced header detection
                        if ((not stripped_line.endswith('.') and
                            len(stripped_line.split()) <= 8 and  # Reduced from 10 to 8
                            any(word[0].isupper() for word in stripped_line.split() if word)) or
                            (stripped_line.endswith(':')) or
                            (stripped_line[0].isdigit() and '.' in stripped_line[:5])):
                            
                            # Save previous section if it has content
                            if current_section["text"].strip():
                                sections.append(current_section)
                            
                            # Start new section
                            current_section = {"title": stripped_line, "text": "", "page": page_num}
                        else:
                            current_section["text"] += line + "\n"
                
                # Add the last section
                if current_section["text"].strip():
                    sections.append(current_section)
        
        except Exception as e:
            print(f"Error processing {pdf_path}: {str(e)}")
            return [], ""
        
        return sections, all_text
    
    @lru_cache(maxsize=256)
    def _get_embedding(self, text_key):
        """Get embedding for text with function-level caching"""
        # This method is optimized for single text embedding with lru_cache
        # text_key should be a hashable representation of the text
        return self.model.encode([text_key])[0]
    
    def _get_embeddings_batch(self, texts):
        """Get embeddings for multiple texts with optimized batching and caching"""
        # Use a more efficient approach for batch processing
        all_embeddings = [None] * len(texts)
        texts_to_encode = []
        indices_to_encode = []
        
        # First pass: check cache and prepare texts that need encoding
        for i, text in enumerate(texts):
            # Use a more reliable hash method for text
            text_key = text[:100]  # Use first 100 chars as key to avoid hash collisions
            
            if text_key in self.embedding_cache:
                all_embeddings[i] = self.embedding_cache[text_key]
            else:
                texts_to_encode.append(text)
                indices_to_encode.append(i)
        
        # Second pass: encode new texts in optimized batches
        if texts_to_encode:
            # Use smaller batches for better memory efficiency
            optimal_batch_size = min(self.batch_size, 16)  # Smaller batches process faster
            
            for i in range(0, len(texts_to_encode), optimal_batch_size):
                batch = texts_to_encode[i:i+optimal_batch_size]
                batch_indices = indices_to_encode[i:i+optimal_batch_size]
                
                # Encode the batch with show_progress_bar=False for speed
                batch_embeddings = self.model.encode(batch, show_progress_bar=False)
                
                # Update cache and result array
                for j, embedding in enumerate(batch_embeddings):
                    idx = batch_indices[j]
                    text_key = texts[idx][:100]  # Consistent key generation
                    
                    all_embeddings[idx] = embedding
                    self.embedding_cache[text_key] = embedding
        
        return all_embeddings
    
    def rank_sections(self, sections, persona, job_focus):
        """Rank sections based on relevance to persona and job focus - optimized version"""
        if not sections:
            return []
        
        # Create a query based on persona and job focus
        query = f"{persona['role']} with expertise in {persona['expertise']} needs to {job_focus['task']} "
        query += f"focusing on {', '.join(job_focus['focus'])}"
        
        # Get embedding for query
        query_embedding = self._get_embedding(query)
        
        # Prepare section texts for batch processing
        section_texts = [f"{section['title']}. {section['text'][:500]}" for section in sections]
        section_embeddings = self._get_embeddings_batch(section_texts)
        
        # Calculate similarities in one batch operation
        similarities = cosine_similarity([query_embedding], section_embeddings)[0]
        
        # Create ranked sections
        ranked_sections = []
        for i, (section, similarity) in enumerate(zip(sections, similarities)):
            ranked_sections.append({
                "section": section,
                "score": float(similarity),
                "index": i
            })
        
        # Sort by similarity score in descending order
        ranked_sections.sort(key=lambda x: x["score"], reverse=True)
        
        return ranked_sections
    
    def analyze_subsections(self, section_text, persona, job_focus):
        """Break down section text into smaller chunks and analyze relevance - optimized version"""
        # Split text into paragraphs
        paragraphs = re.split(r'\n\s*\n', section_text)
        
        # Filter out very short paragraphs and limit to 10 paragraphs for efficiency
        paragraphs = [p for p in paragraphs if len(p.split()) > 10][:10]
        
        if not paragraphs:
            return []
        
        # Create a query based on persona and job focus
        query = f"{persona['role']} with expertise in {persona['expertise']} needs to {job_focus['task']} "
        query += f"focusing on {', '.join(job_focus['focus'])}"
        
        # Get embeddings using optimized batch method
        query_embedding = self._get_embedding(query)
        paragraph_embeddings = self._get_embeddings_batch(paragraphs)
        
        # Calculate similarity scores
        similarities = cosine_similarity([query_embedding], paragraph_embeddings)[0]
        
        # Create subsection analysis - only process paragraphs with similarity > 0.3
        subsections = []
        for paragraph, similarity in zip(paragraphs, similarities):
            if similarity > 0.3:  # Only include relevant paragraphs
                subsections.append({
                    "refined_text": paragraph,
                    "relevance_score": float(similarity)
                })
        
        # Sort by relevance score in descending order
        subsections.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return subsections[:3]  # Return top 3 most relevant subsections for efficiency
    
    def _process_single_document(self, doc_data):
        """Process a single document and return its ranked sections"""
        file_name, file_path, persona, job_to_be_done = doc_data
        
        print(f"Processing document: {file_name}")
        
        if not os.path.exists(file_path):
            print(f"Warning: File not found: {file_path}")
            return None
            
        try:
            # Extract text from PDF
            sections, _ = self.extract_text_from_pdf(file_path)
            
            # Rank sections based on relevance
            ranked_sections = self.rank_sections(sections, persona, job_to_be_done)
            
            # Add document name to each ranked section
            for ranked_section in ranked_sections:
                ranked_section["document"] = file_name
            
            return {
                "document": file_name,
                "ranked_sections": ranked_sections,
                "success": True
            }
            
        except Exception as e:
            print(f"Error processing {file_name}: {str(e)}")
            return {
                "document": file_name,
                "ranked_sections": [],
                "success": False
            }
    
    def process_documents(self, input_scenario, input_dir, output_path):
        """Process all documents in parallel and generate the output JSON - optimized version"""
        start_time = time.time()
        
        # Extract information from input scenario
        document_collection = input_scenario["document_collection"]
        persona = input_scenario["persona"]
        job_to_be_done = input_scenario["job_to_be_done"]
        
        print(f"Total documents to process: {len(document_collection)}")
        
        # Prepare document processing tasks
        processing_tasks = []
        for doc in document_collection:
            file_name = doc["file_name"]
            file_path = os.path.join(input_dir, file_name)
            processing_tasks.append((file_name, file_path, persona, job_to_be_done))
        
        # Process documents in parallel
        all_ranked_sections = []
        document_info = []
        processed_docs = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_doc = {executor.submit(self._process_single_document, task): task[0] 
                            for task in processing_tasks}
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_doc):
                doc_name = future_to_doc[future]
                try:
                    result = future.result()
                    if result and result["success"]:
                        processed_docs.append(doc_name)
                        document_info.append({
                            "document": doc_name,
                            "sections": result["ranked_sections"]
                        })
                        all_ranked_sections.extend(result["ranked_sections"])
                except Exception as e:
                    print(f"Exception processing document {doc_name}: {str(e)}")
        
        # Sort all sections by score
        all_ranked_sections.sort(key=lambda x: x["score"], reverse=True)
        
        # Prepare extracted sections for output - limit to top 10
        extracted_sections = []
        for i, ranked_section in enumerate(all_ranked_sections[:10]):
            section = ranked_section["section"]
            extracted_sections.append({
                "document": ranked_section["document"],
                "page_number": section["page"],
                "section_title": section["title"],
                "importance_rank": i + 1
            })
        
        # Prepare subsection analysis - limit to top 3 sections for efficiency
        subsection_analysis = []
        for i, ranked_section in enumerate(all_ranked_sections[:3]):
            section = ranked_section["section"]
            subsections = self.analyze_subsections(section["text"], persona, job_to_be_done)
            
            for subsection in subsections:
                subsection_analysis.append({
                    "document": ranked_section["document"],
                    "section_title": section["title"],
                    "refined_text": subsection["refined_text"],
                    "page_number": section["page"]
                })
        
        # Prepare output JSON
        output = {
            "metadata": {
                "input_documents": processed_docs,
                "persona": persona,
                "job_to_be_done": job_to_be_done,
                "processing_timestamp": datetime.now().isoformat()
            },
            "extracted_sections": extracted_sections,
            "subsection_analysis": subsection_analysis
        }
        
        print(f"Successfully processed {len(processed_docs)} out of {len(document_collection)} documents")
        if len(processed_docs) < len(document_collection):
            print("Some documents could not be processed. Check the logs for details.")
        
        # Calculate processing time
        processing_time = time.time() - start_time
        print(f"Processing completed in {processing_time:.2f} seconds")
        
        # Write output to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        return output, processing_time