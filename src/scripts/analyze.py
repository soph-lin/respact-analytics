import os
import json
import argparse
from typing import Dict, List, Tuple
import re
from collections import defaultdict
import statistics
from pathlib import Path
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.tasks import TASKS

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
        
        # Configuration for file length analysis
        self.min_lines = 10
        self.max_lines = 15

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
            filename = os.path.basename(filepath)
            # Find which task prefix matches the filename
            task = next((t for t in TASKS if filename.startswith(t)), None)
            if task is None:
                print(f"Warning: Could not identify task for file {filepath}")
                return None
                
            success = not filepath.endswith('_failed_action_observation_pairs.txt')
            
            # Parse conversation
            speak_turns = []
            all_turns = []
            speak_lines_with_numbers = []  # Store line numbers with speak content
            
            for i, line in enumerate(lines, 1):  # 1-based line numbering
                # Handle new format: "9: > speak: ..."
                if ': > ' in line:
                    parts = line.split(': > ')
                    if len(parts) >= 2:
                        content = parts[1].strip()
                        if content.startswith('speak:'):
                            speak_content = content[len('speak:'):].strip()
                            speak_turns.append(speak_content)
                            speak_lines_with_numbers.append({"line_number": i, "content": speak_content})
                            all_turns.append('speak')
                        elif any(content.startswith(t + ':') for t in ['think', 'act']):
                            all_turns.append(content.split(':')[0])
                    continue
                
                # Handle old format: "7: Act 7: speak: ..."
                if ': Act ' in line:
                    turn_num, content = line.split(': Act ')[1].split(': ', 1)
                    action_type = content.split(':')[0] if ':' in content else content.strip()
                    
                    if action_type == 'speak':
                        speak_content = content.split(':', 1)[1].strip()
                        speak_turns.append(speak_content)
                        speak_lines_with_numbers.append({"line_number": i, "content": speak_content})
                    
                    all_turns.append(action_type)
                    continue

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
                "total_lines": len(lines),
                "avg_tokens_per_speak": statistics.mean(token_counts) if token_counts else 0,
                "speak_type_counts": dict(type_counts),
                "filepath": filepath,
                "filename": filename,
                "speak_lines": speak_lines_with_numbers  # Add the speak lines with line numbers
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
        
        # Calculate general aggregate metrics
        metrics = {
            "total_conversations": len(results),
            "successful_conversations": len(successful_dialogues),
            "success_rate": len(successful_dialogues) / len(results) if results else 0,
            
            "avg_speak_turns_all": statistics.mean([r["speak_turns"] for r in results]),
            "avg_speak_turns_successful": statistics.mean([r["speak_turns"] for r in successful_dialogues]) if successful_dialogues else 0,
            
            "avg_tokens_per_speak_all": statistics.mean([r["avg_tokens_per_speak"] for r in results]),
            "avg_tokens_per_speak_successful": statistics.mean([r["avg_tokens_per_speak"] for r in successful_dialogues]) if successful_dialogues else 0,
            
            "speak_type_distribution": defaultdict(int),
            
            # New general statistics
            "total_files_analyzed": len(results),
            "avg_lines_per_file": statistics.mean([r["total_lines"] for r in results]),
            
            # Min/Max statistics for total lines
            "min_total_lines": min([r["total_lines"] for r in results]),
            "max_total_lines": max([r["total_lines"] for r in results]),
            "files_with_min_lines": len([r for r in results if r["total_lines"] == min([r["total_lines"] for r in results])]),
            "files_with_max_lines": len([r for r in results if r["total_lines"] == max([r["total_lines"] for r in results])]),
            
            # Min/Max statistics for speak lines
            "min_speak_lines": min([r["speak_turns"] for r in results]),
            "max_speak_lines": max([r["speak_turns"] for r in results]),
            "files_with_min_speak_lines": len([r for r in results if r["speak_turns"] == min([r["speak_turns"] for r in results])]),
            "files_with_max_speak_lines": len([r for r in results if r["speak_turns"] == max([r["speak_turns"] for r in results])]),
            
            # Task-specific analysis
            "task_analysis": {}
        }

        # Aggregate speak type counts
        for result in results:
            for speak_type, count in result["speak_type_counts"].items():
                metrics["speak_type_distribution"][speak_type] += count

        # Perform task-specific analysis
        for task in TASKS:
            task_results = [r for r in results if r["task"] == task]
            if not task_results:
                continue

            task_metrics = {
                "total_files": len(task_results),
                "successful_files": len([r for r in task_results if r["success"]]),
                "success_rate": len([r for r in task_results if r["success"]]) / len(task_results),
                "avg_speak_turns": statistics.mean([r["speak_turns"] for r in task_results]),
                "avg_tokens_per_speak": statistics.mean([r["avg_tokens_per_speak"] for r in task_results]),
                
                # Min/Max statistics for total lines
                "min_total_lines": min([r["total_lines"] for r in task_results]),
                "max_total_lines": max([r["total_lines"] for r in task_results]),
                "files_with_min_lines": len([r for r in task_results if r["total_lines"] == min([r["total_lines"] for r in task_results])]),
                "files_with_max_lines": len([r for r in task_results if r["total_lines"] == max([r["total_lines"] for r in task_results])]),
                
                # Min/Max statistics for speak lines
                "min_speak_lines": min([r["speak_turns"] for r in task_results]),
                "max_speak_lines": max([r["speak_turns"] for r in task_results]),
                "files_with_min_speak_lines": len([r for r in task_results if r["speak_turns"] == min([r["speak_turns"] for r in task_results])]),
                "files_with_max_speak_lines": len([r for r in task_results if r["speak_turns"] == max([r["speak_turns"] for r in task_results])]),
                
                "files_with_10_15_lines": []
            }

            # Find files with 10-15 lines
            for result in task_results:
                if self.min_lines <= result["total_lines"] <= self.max_lines:
                    task_metrics["files_with_10_15_lines"].append({
                        "filename": os.path.basename(result["filepath"]),
                        "total_lines": result["total_lines"],
                        "speak_lines": result["speak_turns"]
                    })

            metrics["task_analysis"][task] = task_metrics

        return metrics

    def get_filenames_from_results(self, results_file: str) -> Dict[str, set]:
        """Extract filenames by task from a results file"""
        task_files = defaultdict(set)
        try:
            with open(results_file, 'r') as f:
                data = json.load(f)
                
            # Extract filenames from task analysis
            for task, task_data in data["task_analysis"].items():
                # Get filenames from files_with_10_15_lines
                task_files[task].update(
                    result["filename"]
                    for result in task_data.get("files_with_10_15_lines", [])
                )
                # Get filenames from all_files if present
                task_files[task].update(
                    os.path.basename(filepath)
                    for filepath in task_data.get("all_files", [])
                )
        except Exception as e:
            print(f"Warning: Error processing {results_file}: {str(e)}")
        
        return task_files

    def select_representative_files(self, results: List[Dict], intersect_files: List[str] = None) -> Dict[str, List[Dict]]:
        """Select representative files for each task based on speak lines criteria, ensuring files are present in all intersect_files"""
        task_files = defaultdict(list)
        
        # Group files by task for current results
        for result in results:
            task_files[result["task"]].append(result)
            
        # If intersect files are provided, find common files across all datasets
        if intersect_files:
            # Get filenames from each results file
            all_task_files = [self.get_filenames_from_results(f) for f in intersect_files]
            
            # Find intersection of filenames for each task
            common_files = {}
            for task in task_files.keys():
                # Get sets of filenames for this task from all results
                task_file_sets = [files[task] for files in all_task_files if task in files]
                
                if task_file_sets:
                    # Find intersection of all sets
                    common_files[task] = set.intersection(*task_file_sets)
                    if not common_files[task]:
                        print(f"Warning: No common files found for task {task} across all datasets")
                else:
                    print(f"Warning: Task {task} not found in all datasets")
                    common_files[task] = set()
        
        selected_files = {}
        for task, files in task_files.items():
            # If we have intersect files, filter to only files that appear in all datasets
            if intersect_files:
                files = [f for f in files if f["filename"] in common_files.get(task, set())]
            
            if not files:
                print(f"Warning: No valid files found for task {task}")
                continue
                
            # Sort files by number of speak turns
            files_sorted = sorted(files, key=lambda x: (x["speak_turns"], x["total_lines"]))
            
            # Select 2 files with minimum speak lines
            min_speak_files = [f for f in files_sorted if f["speak_turns"] == files_sorted[0]["speak_turns"]]
            min_speak_selected = sorted(min_speak_files, key=lambda x: x["total_lines"])[:2]
            
            # Select 3 files with more speak lines
            more_speak_files = [f for f in files_sorted if f["speak_turns"] > files_sorted[0]["speak_turns"]]
            more_speak_selected = sorted(more_speak_files, key=lambda x: (-x["speak_turns"], x["total_lines"]))[:3]
            
            selected_files[task] = min_speak_selected + more_speak_selected
        
        return selected_files

    def create_speak_analysis(self, selected_files: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """Create speak analysis for selected files"""
        speak_analysis = {}
        
        for task, files in selected_files.items():
            speak_analysis[task] = []
            for file_data in files:
                for speak_line in file_data["speak_lines"]:
                    speak_analysis[task].append({
                        "filename": file_data["filename"],
                        "line": speak_line["line_number"],
                        "content": speak_line["content"]
                    })
        
        return speak_analysis

def main():
    parser = argparse.ArgumentParser(description='Analyze dialogue conversations')
    parser.add_argument('--path', type=str, help='Path to parent directory containing experiment folders')
    args = parser.parse_args()

    analyzer = DialogueAnalyzer()
    
    # Get the absolute path to the src directory
    src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(src_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # Determine parent path to analyze
    parent_path = args.path if args.path else os.path.join(os.getcwd(), 'rollouts')
    
    # Get all subdirectories in the parent path
    subdirs = [d for d in os.listdir(parent_path) if os.path.isdir(os.path.join(parent_path, d))]
    if not subdirs:
        print("No subdirectories found in parent directory")
        return
        
    print(f"\nFound {len(subdirs)} experiment directories:")
    for d in subdirs:
        print(f"  - {d}")
    
    # Analyze each subdirectory
    all_results = {}
    for subdir in subdirs:
        subdir_path = os.path.join(parent_path, subdir)
        results = analyzer.analyze_directory(subdir_path)
        results = [r for r in results if r is not None]
        if results:
            all_results[subdir] = results
    
    if not all_results:
        print("No valid conversations found in any subdirectory")
        return
    
    # Find common files across all subdirectories for each task
    task_files = defaultdict(lambda: defaultdict(list))
    for subdir, results in all_results.items():
        for result in results:
            task_files[result["task"]][subdir].append(result)
    
    # Select representative files that exist in all subdirectories
    selected_files = {}
    for task, subdir_files in task_files.items():
        # Only consider files that exist in all subdirectories
        common_filenames = set.intersection(*[
            {f["filename"] for f in files}
            for files in subdir_files.values()
        ])
        
        if not common_filenames:
            print(f"Warning: No common files found for task {task} across all subdirectories")
            continue
            
        # Get the full file data from any subdirectory (they should be identical)
        first_subdir = next(iter(subdir_files))
        common_files = [
            f for f in subdir_files[first_subdir]
            if f["filename"] in common_filenames
        ]
        
        # Sort and select files
        files_sorted = sorted(common_files, key=lambda x: (x["speak_turns"], x["total_lines"]))
        
        # Select 2 files with minimum speak lines
        min_speak_files = [f for f in files_sorted if f["speak_turns"] == files_sorted[0]["speak_turns"]]
        min_speak_selected = sorted(min_speak_files, key=lambda x: x["total_lines"])[:2]
        
        # Select 3 files with more speak lines
        more_speak_files = [f for f in files_sorted if f["speak_turns"] > files_sorted[0]["speak_turns"]]
        more_speak_selected = sorted(more_speak_files, key=lambda x: (-x["speak_turns"], x["total_lines"]))[:3]
        
        selected_files[task] = min_speak_selected + more_speak_selected
    
    # Create the intersection summary
    intersection_summary = {}
    for task, files in selected_files.items():
        intersection_summary[task] = [
            {
                "filename": f["filename"],
                "total_lines": f["total_lines"],
                "speak_lines": f["speak_turns"]
            }
            for f in files
        ]
    
    # Generate and save analysis for each subdirectory
    for subdir, results in all_results.items():
        # Generate regular analysis
        aggregate_metrics = analyzer.aggregate_results(results)
        
        # Add intersection information
        aggregate_metrics["intersect"] = intersection_summary
        
        # Save regular analysis
        metrics_file = os.path.join(output_dir, f"{subdir}.json")
        with open(metrics_file, 'w') as f:
            json.dump(aggregate_metrics, f, indent=2)
        print(f"\nDetailed metrics saved to {metrics_file}")
        
        # Generate speak analysis using the selected files
        speak_analysis = {}
        for task, files in selected_files.items():
            speak_analysis[task] = []
            # Find the matching files in this subdirectory's results
            for selected_file in files:
                matching_file = next(
                    (r for r in results if r["filename"] == selected_file["filename"]),
                    None
                )
                if matching_file:
                    for speak_line in matching_file["speak_lines"]:
                        speak_analysis[task].append({
                            "filename": matching_file["filename"],
                            "line": speak_line["line_number"],
                            "content": speak_line["content"]
                        })
        
        # Save speak analysis
        speak_file = os.path.join(output_dir, f"{subdir}_speak.json")
        with open(speak_file, 'w') as f:
            json.dump(speak_analysis, f, indent=2)
        print(f"Speak analysis saved to {speak_file}")
    
    # Print summary of selected files
    print("\n=== Selected Files Analysis ===")
    for task, files in selected_files.items():
        print(f"\nTask: {task}")
        print(f"Selected {len(files)} files:")
        for file_data in files:
            print(f"  - {file_data['filename']} ({file_data['speak_turns']} speak turns, {file_data['total_lines']} total lines)")

if __name__ == "__main__":
    main()
