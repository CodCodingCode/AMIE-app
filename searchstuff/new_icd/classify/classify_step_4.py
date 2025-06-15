import polars as pl
import os
import asyncio
import json
import csv
from typing import List, Dict, Optional, Tuple
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from tavily import TavilyClient
import random
from datetime import datetime, timedelta

class ImprovedKeyRotationVerifier:
    def __init__(self, max_workers: int = 3):  # Further reduced for quota management
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Multiple Tavily API keys for rotation
        self.tavily_keys = [
            "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",
            "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",
            "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",
            "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",
            "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",
            "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",
        ]
        
        # API key management
        self.current_key_index = 0
        self.exhausted_keys = set()  # Track permanently exhausted keys
        self.key_cooldowns = {}  # Track temporary cooldowns
        self.key_usage_count = {key: 0 for key in self.tavily_keys}  # Track usage per key
        self.key_lock = threading.Lock()  # Thread-safe key rotation
        
        # Rate limiting
        self.max_workers = max_workers
        self.request_delay = 3.0  # Increased delay to be more conservative
        self.last_request_times = {}
        self.worker_locks = {}
        
        # Statistics
        self.api_calls_made = 0
        self.key_switches = 0
        self.exhausted_key_count = 0
        self.successful_calls = 0
        self.failed_calls = 0
        
        print(f"🚀 Initialized improved key rotation verifier:")
        print(f"   • {max_workers} workers (conservative for quota limits)")
        print(f"   • {len(self.tavily_keys)} Tavily API keys available")
        print(f"   • {self.request_delay}s delay between requests")
        print(f"   • Enhanced usage limit detection")
        print(f"   • Automatic key exhaustion handling")
    
    def is_usage_limit_error(self, error_msg: str) -> bool:
        """
        Detect various types of usage/quota limit errors.
        """
        error_lower = error_msg.lower()
        usage_indicators = [
            "usage limit",
            "quota",
            "exceeded",
            "plan limit",
            "upgrade your plan",
            "contact support",
            "limit reached",
            "monthly limit",
            "api limit"
        ]
        return any(indicator in error_lower for indicator in usage_indicators)
    
    def is_rate_limit_error(self, error_msg: str) -> bool:
        """
        Detect rate limiting errors (temporary).
        """
        error_lower = error_msg.lower()
        rate_indicators = [
            "rate limit",
            "too many requests",
            "429",
            "slow down",
            "retry after"
        ]
        return any(indicator in error_lower for indicator in rate_indicators)
    
    def get_next_available_key(self, worker_id: str) -> Optional[str]:
        """
        Get the next available API key, skipping exhausted ones.
        """
        with self.key_lock:
            now = datetime.now()
            
            # Check all keys to find an available one
            available_keys = []
            for i, key in enumerate(self.tavily_keys):
                if key in self.exhausted_keys:
                    continue  # Skip permanently exhausted keys
                
                if key in self.key_cooldowns and now < self.key_cooldowns[key]:
                    continue  # Skip keys on temporary cooldown
                
                available_keys.append((i, key))
            
            if not available_keys:
                print(f"💥 {worker_id}: All API keys are either exhausted or on cooldown!")
                return None
            
            # Use the key with lowest usage count
            available_keys.sort(key=lambda x: self.key_usage_count[x[1]])
            best_index, best_key = available_keys[0]
            
            if best_index != self.current_key_index:
                print(f"🔄 {worker_id}: Switched to API key {best_index + 1} (usage: {self.key_usage_count[best_key]})")
                self.current_key_index = best_index
                self.key_switches += 1
            
            return best_key
    
    def handle_key_exhaustion(self, worker_id: str, exhausted_key: str):
        """
        Mark a key as permanently exhausted (usage limit exceeded).
        """
        with self.key_lock:
            if exhausted_key not in self.exhausted_keys:
                self.exhausted_keys.add(exhausted_key)
                self.exhausted_key_count += 1
                key_index = self.tavily_keys.index(exhausted_key) + 1
                
                print(f"🚫 {worker_id}: API key {key_index} EXHAUSTED (usage limit exceeded)")
                print(f"💡 {worker_id}: Marked key as permanently unavailable")
                print(f"📊 {worker_id}: {len(self.exhausted_keys)}/{len(self.tavily_keys)} keys exhausted")
                
                if len(self.exhausted_keys) >= len(self.tavily_keys):
                    print(f"💥 {worker_id}: ALL API KEYS EXHAUSTED! No more searches possible.")
                    return False
            
            return True
    
    def handle_rate_limit(self, worker_id: str, rate_limited_key: str):
        """
        Handle temporary rate limiting.
        """
        with self.key_lock:
            now = datetime.now()
            # Put key on temporary cooldown
            self.key_cooldowns[rate_limited_key] = now + timedelta(minutes=2)
            
            key_index = self.tavily_keys.index(rate_limited_key) + 1
            print(f"⏳ {worker_id}: API key {key_index} rate limited - cooldown for 2 minutes")
    
    def create_tavily_client(self, api_key: str) -> Optional[TavilyClient]:
        """
        Safely create a Tavily client.
        """
        try:
            return TavilyClient(api_key=api_key)
        except Exception as e:
            print(f"❌ Failed to create Tavily client: {e}")
            return None
    
    def enforce_rate_limit(self, worker_id: str):
        """
        Enforce conservative rate limiting.
        """
        if worker_id not in self.worker_locks:
            self.worker_locks[worker_id] = threading.Lock()
        
        with self.worker_locks[worker_id]:
            now = time.time()
            
            if worker_id in self.last_request_times:
                time_since_last = now - self.last_request_times[worker_id]
                if time_since_last < self.request_delay:
                    sleep_time = self.request_delay - time_since_last
                    print(f"⏳ {worker_id}: Rate limiting - sleeping {sleep_time:.1f}s")
                    time.sleep(sleep_time)
            
            self.last_request_times[worker_id] = time.time()
    
    def search_disease_info(self, disease_name: str, worker_id: str, max_retries: int = 6) -> Dict:
        """
        Search with improved key rotation and error handling.
        """
        self.enforce_rate_limit(worker_id)
        
        for attempt in range(max_retries):
            try:
                # Get next available key
                api_key = self.get_next_available_key(worker_id)
                if not api_key:
                    print(f"💥 {worker_id}: No API keys available - all exhausted or on cooldown")
                    if len(self.exhausted_keys) >= len(self.tavily_keys):
                        print(f"🛑 {worker_id}: All keys permanently exhausted - stopping search")
                        return {"results": [], "answer": "", "error": "all_keys_exhausted"}
                    else:
                        print(f"⏳ {worker_id}: Waiting 60s for key cooldowns...")
                        time.sleep(60)
                        continue
                
                # Create client
                tavily_client = self.create_tavily_client(api_key)
                if not tavily_client:
                    continue
                
                print(f"🔍 {worker_id} searching: {disease_name} (attempt {attempt + 1}, key usage: {self.key_usage_count[api_key]})")
                
                # Make the search request
                search_query = f"{disease_name} medical condition prevalence common"
                
                response = tavily_client.search(
                    query=search_query,
                    search_depth="basic",
                    include_domains=["mayoclinic.org", "cdc.gov", "nih.gov", "webmd.com"],
                    max_results=2,  # Further reduced for quota conservation
                    include_answer=True,
                    include_raw_content=False
                )
                
                # Success!
                self.api_calls_made += 1
                self.successful_calls += 1
                self.key_usage_count[api_key] += 1
                
                print(f"   ✅ {worker_id}: Found {len(response['results'])} results")
                return response
                
            except Exception as e:
                error_msg = str(e)
                self.failed_calls += 1
                
                print(f"❌ {worker_id}: Search error for {disease_name}: {error_msg}")
                
                # Handle different types of errors
                if self.is_usage_limit_error(error_msg):
                    print(f"🚫 {worker_id}: Usage limit detected - marking key as exhausted")
                    if api_key:
                        can_continue = self.handle_key_exhaustion(worker_id, api_key)
                        if not can_continue:
                            return {"results": [], "answer": "", "error": "all_keys_exhausted"}
                    # Try next key immediately
                    continue
                    
                elif self.is_rate_limit_error(error_msg):
                    print(f"⏳ {worker_id}: Rate limit detected - switching key")
                    if api_key:
                        self.handle_rate_limit(worker_id, api_key)
                    # Try next key after short delay
                    time.sleep(5)
                    continue
                    
                else:
                    print(f"❓ {worker_id}: Unknown error type - retrying")
                    if attempt < max_retries - 1:
                        wait_time = min(30, (attempt + 1) * 5)  # Cap wait time
                        print(f"⏳ {worker_id}: Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        continue
        
        print(f"💥 {worker_id}: Max retries reached for {disease_name}")
        return {"results": [], "answer": "", "error": "max_retries_exceeded"}
    
    def classify_disease_with_ai(self, disease_name: str, search_response: Dict, worker_id: str) -> Tuple[str, str, float]:
        """
        Classify with OpenAI - simplified for quota conservation.
        """
        # Handle search failures
        if search_response.get("error"):
            error_type = search_response["error"]
            if error_type == "all_keys_exhausted":
                return "unknown", "All API keys exhausted - cannot search", 0.0
            else:
                return "unknown", f"Search failed: {error_type}", 0.0
        
        # Small delay for OpenAI
        time.sleep(0.3)
        
        results = search_response.get("results", [])
        tavily_answer = search_response.get("answer", "")
        
        # Simplified content processing
        content_summary = f"AI Summary: {tavily_answer[:500]}"
        if results:
            content_summary += f"\nSource: {results[0].get('title', '')[:100]}"
            content_summary += f"\nContent: {results[0].get('content', '')[:300]}"
        
        prompt = f"""
        Classify "{disease_name}" based on this information:

        {content_summary}

        Choose ONE classification:
        1. common disease (affects >1% population)
        2. rare disease (affects <1 in 2000) 
        3. mental disease (psychiatric)
        4. emergency disease (life-threatening)
        5. not a valid entry (invalid)

        Respond ONLY with JSON:
        {{"classification": "your choice", "confidence": 0.8, "reasoning": "brief explanation"}}
        """
        
        try:
            print(f"🤖 {worker_id} analyzing: {disease_name}")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Clean response
            if "```" in result_text:
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                else:
                    result_text = result_text.split("```")[1].strip()
            
            try:
                result = json.loads(result_text)
                classification = result.get("classification", "unknown")
                confidence = float(result.get("confidence", 0.0))
                reasoning = result.get("reasoning", "No reasoning provided")
                
                print(f"   ✅ {worker_id}: {classification} (confidence: {confidence:.2f})")
                return classification, reasoning, confidence
                
            except json.JSONDecodeError:
                print(f"❌ {worker_id}: JSON parse error for {disease_name}")
                return "unknown", "Failed to parse AI response", 0.0
                
        except Exception as e:
            print(f"❌ {worker_id}: OpenAI error for {disease_name}: {e}")
            return "unknown", f"OpenAI error: {e}", 0.0
    
    def verify_single_disease_worker(self, disease_data: Dict) -> Dict:
        """
        Worker function with enhanced error handling.
        """
        code = disease_data['code']
        disease_name = disease_data['description']
        current_classification = disease_data['classification']
        
        worker_id = threading.current_thread().name
        print(f"\n🔬 {worker_id} processing: {code} - {disease_name}")
        
        start_time = time.time()
        
        # Check if we can still make searches
        if len(self.exhausted_keys) >= len(self.tavily_keys):
            print(f"🛑 {worker_id}: All API keys exhausted - skipping search")
            return {
                "code": code,
                "disease": disease_name,
                "current_classification": current_classification,
                "verified_classification": "unknown",
                "reasoning": "All API keys exhausted",
                "confidence": 0.0,
                "sources": [],
                "matches_current": False,
                "processing_time": time.time() - start_time,
                "worker_id": worker_id,
                "status": "keys_exhausted"
            }
        
        # Search with improved error handling
        search_response = self.search_disease_info(disease_name, worker_id)
        
        # Classify with AI
        classification, reasoning, confidence = self.classify_disease_with_ai(
            disease_name, search_response, worker_id
        )
        
        # Extract sources
        sources = []
        for result in search_response.get("results", []):
            sources.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("content", "")[:150] + "..."
            })
        
        matches_current = classification == current_classification
        match_symbol = "✅" if matches_current else "❌"
        processing_time = time.time() - start_time
        
        result = {
            "code": code,
            "disease": disease_name,
            "current_classification": current_classification,
            "verified_classification": classification,
            "reasoning": reasoning,
            "confidence": confidence,
            "sources": sources,
            "matches_current": matches_current,
            "tavily_answer": search_response.get("answer", ""),
            "processing_time": processing_time,
            "worker_id": worker_id,
            "status": "completed"
        }
        
        print(f"   {match_symbol} {worker_id} completed: {current_classification} → {classification} ({processing_time:.1f}s)")
        
        return result
    
    def verify_diseases_with_quota_management(self, diseases_df: pl.DataFrame) -> List[Dict]:
        """
        Verify diseases with smart quota management.
        """
        total_diseases = len(diseases_df)
        diseases_list = diseases_df.to_dicts()
        
        print(f"🚀 Starting quota-aware parallel verification:")
        print(f"   • {total_diseases} diseases to process")
        print(f"   • {self.max_workers} workers (conservative)")
        print(f"   • {len(self.tavily_keys)} API keys available")
        print(f"   • Smart key exhaustion detection")
        
        results = []
        completed_count = 0
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="QuotaAwareWorker") as executor:
            print(f"\n🎯 Submitting diseases to quota-aware worker pool...")
            
            future_to_disease = {
                executor.submit(self.verify_single_disease_worker, disease_data): disease_data 
                for disease_data in diseases_list
            }
            
            print(f"✅ {len(future_to_disease)} diseases submitted")
            
            # Process results
            for future in as_completed(future_to_disease):
                disease_data = future_to_disease[future]
                
                try:
                    result = future.result()
                    results.append(result)
                    completed_count += 1
                    
                    # Check if we should stop early
                    if len(self.exhausted_keys) >= len(self.tavily_keys):
                        remaining_futures = [f for f in future_to_disease if not f.done()]
                        if remaining_futures:
                            print(f"🛑 All API keys exhausted - cancelling {len(remaining_futures)} remaining tasks")
                            for f in remaining_futures:
                                f.cancel()
                    
                    # Progress updates
                    if completed_count % max(1, total_diseases // 10) == 0 or completed_count == total_diseases:
                        elapsed_time = time.time() - start_time
                        progress = (completed_count / total_diseases) * 100
                        
                        print(f"\n📊 PROGRESS UPDATE:")
                        print(f"   • Completed: {completed_count}/{total_diseases} ({progress:.1f}%)")
                        print(f"   • Successful calls: {self.successful_calls}")
                        print(f"   • Failed calls: {self.failed_calls}")
                        print(f"   • Keys exhausted: {len(self.exhausted_keys)}/{len(self.tavily_keys)}")
                        print(f"   • Key switches: {self.key_switches}")
                        
                        if len(self.exhausted_keys) >= len(self.tavily_keys):
                            print(f"   🛑 ALL KEYS EXHAUSTED - processing remaining without search")
                
                except Exception as e:
                    print(f"❌ Worker error: {e}")
                    error_result = {
                        "code": disease_data.get('code', 'ERROR'),
                        "disease": disease_data.get('description', 'Unknown'),
                        "current_classification": disease_data.get('classification', 'unknown'),
                        "verified_classification": "error",
                        "reasoning": f"Worker error: {e}",
                        "confidence": 0.0,
                        "sources": [],
                        "matches_current": False,
                        "processing_time": 0,
                        "worker_id": "Error",
                        "status": "error"
                    }
                    results.append(error_result)
                    completed_count += 1
        
        total_time = time.time() - start_time
        
        print(f"\n🎉 QUOTA-AWARE PROCESSING COMPLETE!")
        print(f"📊 FINAL STATISTICS:")
        print(f"   • Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
        print(f"   • Diseases processed: {completed_count}")
        print(f"   • Successful API calls: {self.successful_calls}")
        print(f"   • Failed API calls: {self.failed_calls}")
        print(f"   • Keys exhausted: {len(self.exhausted_keys)}/{len(self.tavily_keys)}")
        print(f"   • Key rotations: {self.key_switches}")
        
        # Show key usage statistics
        print(f"\n🔑 KEY USAGE STATISTICS:")
        for i, key in enumerate(self.tavily_keys):
            usage = self.key_usage_count[key]
            status = "EXHAUSTED" if key in self.exhausted_keys else "Available"
            print(f"   Key {i+1}: {usage} calls - {status}")
        
        return results
    
    def save_results_with_quota_info(self, results: List[Dict], output_file: str):
        """Save results with quota management information."""
        try:
            flattened_results = []
            for result in results:
                flat_result = {
                    "code": result["code"],
                    "disease": result["disease"],
                    "current_classification": result["current_classification"],
                    "verified_classification": result["verified_classification"],
                    "matches_current": result["matches_current"],
                    "confidence": result["confidence"],
                    "reasoning": result["reasoning"],
                    "processing_time": result.get("processing_time", 0),
                    "worker_id": result.get("worker_id", "Unknown"),
                    "status": result.get("status", "unknown")
                }
                flattened_results.append(flat_result)
            
            df_results = pl.DataFrame(flattened_results)
            df_results.write_csv(output_file)
            print(f"✅ Results saved to: {output_file}")
            
        except Exception as e:
            print(f"⚠️ Save failed: {e}")
        
        # Save detailed JSON with quota information
        try:
            json_file = output_file.replace('.csv', '_detailed.json')
            detailed_data = {
                "results": results,
                "quota_statistics": {
                    "total_api_calls": self.api_calls_made,
                    "successful_calls": self.successful_calls,
                    "failed_calls": self.failed_calls,
                    "keys_exhausted": len(self.exhausted_keys),
                    "total_keys": len(self.tavily_keys),
                    "key_switches": self.key_switches,
                    "key_usage": self.key_usage_count,
                    "exhausted_keys": list(self.exhausted_keys)
                }
            }
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(detailed_data, f, indent=2, ensure_ascii=False)
            print(f"📁 Detailed results with quota info saved to: {json_file}")
        except Exception as e:
            print(f"⚠️ JSON save failed: {e}")

def main():
    """Main function with quota management."""
    input_file = "true2.csv"
    output_file = "disease_verification_results.csv"
    
    try:
        df = pl.read_csv(input_file)
        print(f"📂 Loaded {len(df)} diseases from {input_file}")
        
        # Initialize quota-aware verifier
        verifier = ImprovedKeyRotationVerifier(max_workers=3)
        
        print(f"\n🎯 Processing {len(df)} diseases with quota management...")
        
        # Run verification
        results = verifier.verify_diseases_with_quota_management(df)
        
        # Save results
        verifier.save_results_with_quota_info(results, output_file)
        
        print(f"\n🎉 QUOTA-AWARE PROCESSING COMPLETE!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()