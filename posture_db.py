#!/usr/bin/env python3
"""
Posture Metrics Converter
Converts posture_summary.json directly to endpoint_values.json (no database).
"""

import json
import os
from datetime import datetime
import statistics

class PostureConverter:
    """
    Simple converter that transforms posture_summary.json into endpoint_values.json.
    No database storage - direct JSON to JSON conversion.
    """
    
    def __init__(self, summary_file: str = "posture_summary.json", output_file: str = "endpoint_values.json"):
        """
        Initialize the posture converter.
        
        Args:
            summary_file (str): Path to posture summary log file
            output_file (str): Path to output endpoint values file
        """
        self.summary_file = summary_file
        self.output_file = output_file
        self.summary_data = None
    
    def load_summary_data(self) -> bool:
        """Load the posture summary data from JSON file."""
        if not os.path.exists(self.summary_file):
            print(f"❌ Summary file not found: {self.summary_file}")
            return False
        
        try:
            with open(self.summary_file, 'r') as f:
                self.summary_data = json.load(f)
            return True
        except Exception as e:
            print(f"❌ Error loading summary file: {e}")
            return False
    
    def calculate_endpoints(self) -> dict:
        """Calculate the 6 key posture endpoints."""
        logs = self.summary_data.get('summary_logs', [])
        
        if not logs:
            return {
                "posture_health_score": 0,
                "slouch_to_good_conversions": 0,
                "consistency_index": 0,
                "session_success_rate": 0,
                "recent_trend_score": 0,
                "total_good_posture_minutes": 0
            }
        
        # 1. POSTURE HEALTH SCORE (0-100%) - Primary health metric
        total_good = sum(log['good_posture_count'] for log in logs)
        total_readings = sum(log['total_readings'] for log in logs)
        health_score = round((total_good / total_readings * 100), 1) if total_readings > 0 else 0
        
        # 2. SLOUCH-TO-GOOD CONVERSIONS (count) - Improvement tracking
        conversions = 0
        for i in range(1, len(logs)):
            prev_pct = logs[i-1]['good_posture_percentage']
            curr_pct = logs[i]['good_posture_percentage']
            # Count as conversion if previous was poor (<60%) and current is good (≥70%)
            if prev_pct < 60 and curr_pct >= 70:
                conversions += 1
        
        # 3. CONSISTENCY INDEX (0-100%) - Reliability measure
        percentages = [log['good_posture_percentage'] for log in logs]
        if len(percentages) > 1:
            std_dev = statistics.stdev(percentages)
            consistency_index = round(max(0, 100 - std_dev), 1)
        else:
            consistency_index = 100
        
        # 4. SESSION SUCCESS RATE (0-100%) - Achievement metric
        successful_sessions = sum(1 for log in logs if log['good_posture_percentage'] >= 70)
        success_rate = round((successful_sessions / len(logs) * 100), 1)
        
        # 5. RECENT TREND SCORE (0-100%) - Current performance
        recent_logs = logs[-5:] if len(logs) >= 5 else logs
        recent_percentages = [log['good_posture_percentage'] for log in recent_logs]
        trend_score = round(statistics.mean(recent_percentages), 1) if recent_percentages else 0
        
        # 6. TOTAL GOOD POSTURE MINUTES (count) - Cumulative achievement
        # Assuming each reading represents 3 seconds, and 30-second windows
        total_good_minutes = round((total_good * 3) / 60, 1)  # Convert to minutes
        
        return {
            "posture_health_score": health_score,
            "slouch_to_good_conversions": conversions,
            "consistency_index": consistency_index,
            "session_success_rate": success_rate,
            "recent_trend_score": trend_score,
            "total_good_posture_minutes": total_good_minutes
        }
    
    def convert_to_endpoints(self) -> bool:
        """Convert posture summary to endpoint values JSON."""
        if not self.load_summary_data():
            return False
        
        print("📊 Converting posture summary to endpoint values...")
        
        # Calculate endpoint values
        endpoints = self.calculate_endpoints()
        
        try:
            with open(self.output_file, 'w') as f:
                json.dump(endpoints, f, indent=2)
            
            print(f"✅ Endpoint values saved to: {self.output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving endpoint values: {e}")
            return False
    
    def print_summary(self):
        """Print a summary of the converted metrics."""
        if not os.path.exists(self.output_file):
            print("❌ No endpoint values file found")
            return
        
        with open(self.output_file, 'r') as f:
            endpoints = json.load(f)
        
        print("\n🎯 CONVERTED ENDPOINT VALUES")
        print("=" * 50)
        
        for endpoint_name, value in endpoints.items():
            display_name = endpoint_name.replace("_", " ").title()
            unit = "%" if "score" in endpoint_name or "rate" in endpoint_name or "index" in endpoint_name else ("count" if "conversions" in endpoint_name else "minutes")
            
            # Status indicator
            if "score" in endpoint_name or "rate" in endpoint_name or "index" in endpoint_name:
                emoji = "🟢" if value >= 80 else "🟡" if value >= 60 else "🔴"
            elif "conversions" in endpoint_name:
                emoji = "🟢" if value >= 3 else "🟡" if value >= 1 else "🔴"
            else:  # minutes
                emoji = "🟢" if value >= 60 else "🟡" if value >= 30 else "🔴"
            
            print(f"{emoji} {display_name}: {value} {unit}")
        
        print("=" * 50)
        print(f"📄 Ready for dashboard integration!")

def main():
    """Main function to convert posture summary to endpoints."""
    converter = PostureConverter()
    
    if converter.convert_to_endpoints():
        converter.print_summary()
        print(f"\n✅ Conversion complete!")
        print("💡 Use endpoint_values.json in your dashboard")
    else:
        print("❌ Failed to convert posture summary")

if __name__ == "__main__":
    main() 