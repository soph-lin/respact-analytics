import os
import json
import argparse
from typing import Dict, List, Tuple
import re
from collections import defaultdict
import statistics
from pathlib import Path

class DialogueAnalyzer:
    def __init__(self):
        self.question_patterns = [
            r'\?$',
            r'where should',
            r'where do you suggest',
            r'what should',
            r'can you',
            r'should i'
        ]
        
        self.feedback_patterns = [
            r'^ok',
            r'^thank',
            r'^got it',
            r'^i understand',
            r'^alright'
        ]

    def count_tokens(self, text: str) -> int:
        """Simple token count estimation"""
        return len(text.split())

    def classify_speak_turn(self, text: str) -> str:
        """Classify a speak turn as question, feedback, or feedback+question"""
        text = text.lower()
        
        has_question = any(re.search(pattern, text, re.IGNORECASE) for pattern in self.question_patterns)
        has_feedback = any(re.search(pattern, text, re.IGNORECASE) for pattern in self.feedback_patterns)
        
        if has_question and has_feedback:
            return "feedback+question"
        elif has_question:
            return "question"
        elif has_feedback:
            return "feedback"
        return "other"

    def analyze_file(self, filepath: str) -> Dict:
        """Analyze a single conversation file"""
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()
            
            # Track task and success
            task = os.path.basename(filepath).split('trial')[0]
            success = not filepath.endswith('_failed_action_observation_pairs.txt')
            
            # Parse conversation
            speak_turns = []
            all_turns = []
            
            for line in lines:
                if ': Act ' in line:
                    turn_num, content = line.split(': Act ')[1].split(': ', 1)
                    action_type = content.split(':')[0] if ':' in content else content.strip()
                    
                    if action_type == 'speak':
                        speak_content = content.split(':', 1)[1].strip()
                        speak_turns.append(speak_content)
                    
                    all_turns.append(action_type)

            # Analyze speak turns
            speak_types = [self.classify_speak_turn(turn) for turn in speak_turns]
            token_counts = [self.count_tokens(turn) for turn in speak_turns]
            
            type_counts = defaultdict(int)
            for turn_type in speak_types:
                type_counts[turn_type] += 1

            return {
                "task": task,
                "success": success,
                "total_turns": len(all_turns),
                "speak_turns": len(speak_turns),
                "avg_tokens_per_speak": statistics.mean(token_counts) if token_counts else 0,
                "speak_type_counts": dict(type_counts),
                "filepath": filepath
            }
            
        except Exception as e:
            print(f"Error processing {filepath}: {str(e)}")
            return None

    def analyze_directory(self, directory: str) -> List[Dict]:
        """Analyze all conversation files in a directory"""
        results = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('_action_observation_pairs.txt'):
                    filepath = os.path.join(root, file)
                    result = self.analyze_file(filepath)
                    if result:
                        results.append(result)
        return results

    def aggregate_results(self, results: List[Dict]) -> Dict:
        """Aggregate results across multiple conversations"""
        if not results:
            return {}

        successful_dialogues = [r for r in results if r["success"]]
        
        # Calculate aggregate metrics
        metrics = {
            "total_conversations": len(results),
            "successful_conversations": len(successful_dialogues),
            "success_rate": len(successful_dialogues) / len(results) if results else 0,
            
            "avg_speak_turns_all": statistics.mean([r["speak_turns"] for r in results]),
            "avg_speak_turns_successful": statistics.mean([r["speak_turns"] for r in successful_dialogues]) if successful_dialogues else 0,
            
            "avg_tokens_per_speak_all": statistics.mean([r["avg_tokens_per_speak"] for r in results]),
            "avg_tokens_per_speak_successful": statistics.mean([r["avg_tokens_per_speak"] for r in successful_dialogues]) if successful_dialogues else 0,
            
            "speak_type_distribution": defaultdict(int)
        }

        # Aggregate speak type counts
        for result in results:
            for speak_type, count in result["speak_type_counts"].items():
                metrics["speak_type_distribution"][speak_type] += count

        return metrics

def main():
    parser = argparse.ArgumentParser(description='Analyze dialogue conversations')
    parser.add_argument('--path', type=str, help='Path to file or directory to analyze')
    args = parser.parse_args()

    analyzer = DialogueAnalyzer()
    
    # Determine path to analyze
    path = args.path if args.path else os.path.join(os.getcwd(), 'rollouts')
    
    if os.path.isfile(path):
        results = [analyzer.analyze_file(path)]
    else:
        results = analyzer.analyze_directory(path)
    
    # Aggregate and print results
    if results:
        aggregate_metrics = analyzer.aggregate_results(results)
        
        print("\n=== Analysis Results ===")
        print(f"Total conversations analyzed: {aggregate_metrics['total_conversations']}")
        print(f"Success rate: {aggregate_metrics['success_rate']:.2%}")
        print(f"\nAverage speak turns (all): {aggregate_metrics['avg_speak_turns_all']:.2f}")
        print(f"Average speak turns (successful): {aggregate_metrics['avg_speak_turns_successful']:.2f}")
        print(f"\nAverage tokens per speak (all): {aggregate_metrics['avg_tokens_per_speak_all']:.2f}")
        print(f"Average tokens per speak (successful): {aggregate_metrics['avg_tokens_per_speak_successful']:.2f}")
        
        print("\nSpeak turn type distribution:")
        for turn_type, count in aggregate_metrics['speak_type_distribution'].items():
            print(f"  {turn_type}: {count}")
            
        # Save results to JSON
        output_file = "analysis_results.json"
        with open(output_file, 'w') as f:
            json.dump(aggregate_metrics, f, indent=2)
        print(f"\nDetailed results saved to {output_file}")
    
    else:
        print("No valid conversations found to analyze.")

if __name__ == "__main__":
    main()
