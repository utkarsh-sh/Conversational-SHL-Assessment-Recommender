"""Test trace analyzer and evaluation utilities."""

import json
import os
from typing import List, Dict, Any, Tuple
from pathlib import Path


class TestTraceAnalyzer:
    """Analyze and manage test traces."""
    
    def __init__(self, traces_dir: str = "test_traces"):
        self.traces_dir = Path(traces_dir)
        self.traces: List[Dict[str, Any]] = []
    
    def load_traces(self) -> List[Dict[str, Any]]:
        """Load all test traces from directory."""
        if not self.traces_dir.exists():
            print(f"Traces directory not found: {self.traces_dir}")
            return []
        
        traces = []
        for trace_file in self.traces_dir.glob("*.json"):
            try:
                with open(trace_file, 'r') as f:
                    trace = json.load(f)
                    traces.append(trace)
                    print(f"Loaded trace: {trace_file.name}")
            except Exception as e:
                print(f"Error loading {trace_file}: {e}")
        
        self.traces = traces
        return traces
    
    def analyze_trace(self, trace: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single trace."""
        return {
            "name": trace.get("name", "Unknown"),
            "persona": trace.get("persona", {}),
            "facts": trace.get("facts", []),
            "expected_assessments": trace.get("expected_assessments", []),
            "conversation_turns": len(trace.get("conversation", [])) // 2,
            "required_test_types": trace.get("required_test_types", [])
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all loaded traces."""
        if not self.traces:
            return {"total_traces": 0}
        
        total_expected = sum(
            len(t.get("expected_assessments", []))
            for t in self.traces
        )
        
        test_types = set()
        for trace in self.traces:
            test_types.update(trace.get("required_test_types", []))
        
        return {
            "total_traces": len(self.traces),
            "total_expected_assessments": total_expected,
            "avg_expected_per_trace": total_expected / len(self.traces) if self.traces else 0,
            "test_types_covered": list(test_types),
            "traces": [self.analyze_trace(t) for t in self.traces]
        }


class EvaluationMetrics:
    """Calculate evaluation metrics for the agent."""
    
    @staticmethod
    def recall_at_k(relevant: List[str], recommended: List[str], k: int = 10) -> float:
        """
        Calculate Recall@K.
        
        Recall@K = (Number of relevant items in top K) / (Total relevant items)
        """
        if not relevant:
            return 1.0
        
        top_k = set(recommended[:k])
        relevant_set = set(relevant)
        
        intersection = len(top_k & relevant_set)
        return intersection / len(relevant_set)
    
    @staticmethod
    def mean_recall_at_k(traces: List[Dict[str, Any]], predictions: List[List[str]], k: int = 10) -> float:
        """Calculate Mean Recall@K across multiple traces."""
        if not traces or not predictions:
            return 0.0
        
        recalls = []
        for trace, pred in zip(traces, predictions):
            relevant = trace.get("expected_assessments", [])
            recall = EvaluationMetrics.recall_at_k(relevant, pred, k)
            recalls.append(recall)
        
        return sum(recalls) / len(recalls) if recalls else 0.0
    
    @staticmethod
    def precision_at_k(relevant: List[str], recommended: List[str], k: int = 10) -> float:
        """Calculate Precision@K."""
        if not recommended:
            return 0.0
        
        top_k = set(recommended[:k])
        relevant_set = set(relevant)
        
        intersection = len(top_k & relevant_set)
        return intersection / len(top_k)
    
    @staticmethod
    def evaluate_response(
        expected_assessments: List[str],
        recommended: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Evaluate a single agent response."""
        rec_names = [r["name"] for r in recommended]
        
        recall_10 = EvaluationMetrics.recall_at_k(expected_assessments, rec_names, 10)
        precision_10 = EvaluationMetrics.precision_at_k(expected_assessments, rec_names, 10)
        
        # Check if all expected assessments are in recommendations
        missing = set(expected_assessments) - set(rec_names)
        
        return {
            "recall@10": recall_10,
            "precision@10": precision_10,
            "coverage": 1.0 - (len(missing) / len(expected_assessments)) if expected_assessments else 1.0,
            "missing_assessments": list(missing),
            "extra_assessments": list(set(rec_names) - set(expected_assessments))
        }


class BehaviorProbes:
    """Define and run behavior probes for the agent."""
    
    PROBES = {
        "refuses_off_topic": {
            "description": "Agent refuses to answer off-topic questions",
            "test_query": "What are some good interview questions?",
            "should_have_recommendations": False,
            "should_refuse": True
        },
        "no_rec_on_vague_turn_1": {
            "description": "Agent does not recommend on turn 1 for vague queries",
            "test_query": "I need an assessment",
            "should_have_recommendations": False,
            "should_ask_clarification": True
        },
        "honors_constraints": {
            "description": "Agent updates recommendations when constraints change",
            "test_queries": [
                "I need a technical assessment for Java developers",
                "Actually, I need personality assessments instead"
            ],
            "should_change_recommendations": True
        },
        "no_hallucinations": {
            "description": "Agent never recommends non-existent assessments",
            "check_function": "validate_all_urls"
        },
        "respects_turn_limit": {
            "description": "Agent stops before exceeding 8-turn limit",
            "max_turns_allowed": 8
        }
    }
    
    @staticmethod
    def get_probe_descriptions() -> Dict[str, str]:
        """Get descriptions of all available probes."""
        return {
            name: probe["description"]
            for name, probe in BehaviorProbes.PROBES.items()
        }
