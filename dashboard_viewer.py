#!/usr/bin/env python3
"""
Dashboard Viewer
Simple console-based dashboard to display posture metrics.
Now processes posture_summary.json directly and saves text reports.
"""

import json
import os
from datetime import datetime
from statistics import mean, stdev

class PostureDashboard:
    """
    Dashboard viewer that processes posture data and generates reports.
    """
    
    def __init__(self, posture_file: str = "posture_summary.json", report_file: str = "posture_report.txt"):
        """
        Initialize the dashboard viewer.
        
        Args:
            posture_file (str): Path to posture summary JSON file
            report_file (str): Path to output text report file
        """
        self.posture_file = posture_file
        self.report_file = report_file
        self.posture_data = None
        self.metrics = None
    
    def load_posture_data(self) -> bool:
        """Load posture data from JSON file."""
        if not os.path.exists(self.posture_file):
            print(f"❌ Posture file not found: {self.posture_file}")
            return False
        
        try:
            with open(self.posture_file, 'r') as f:
                self.posture_data = json.load(f)
            return True
        except Exception as e:
            print(f"❌ Error loading posture file: {e}")
            return False
    
    def calculate_metrics(self):
        """Calculate comprehensive metrics from posture data."""
        if not self.posture_data or 'summary_logs' not in self.posture_data:
            return
        
        logs = self.posture_data['summary_logs']
        if not logs:
            return
        
        # Basic metrics
        total_sessions = len(logs)
        total_good_posture = sum(log['good_posture_count'] for log in logs)
        total_slouching = sum(log['slouching_count'] for log in logs)
        total_readings = total_good_posture + total_slouching
        
        overall_good_percentage = (total_good_posture / total_readings * 100) if total_readings > 0 else 0
        
        # Session percentages
        session_percentages = [log['good_posture_percentage'] for log in logs]
        
        # Performance metrics
        best_session = max(session_percentages) if session_percentages else 0
        worst_session = min(session_percentages) if session_percentages else 0
        average_session = mean(session_percentages) if session_percentages else 0
        
        # Consistency (lower standard deviation = more consistent)
        consistency_score = max(0, 100 - (stdev(session_percentages) if len(session_percentages) > 1 else 0))
        
        # Quality categories
        excellent_sessions = sum(1 for pct in session_percentages if pct >= 80)
        poor_sessions = sum(1 for pct in session_percentages if pct < 50)
        good_sessions = total_sessions - excellent_sessions - poor_sessions
        
        # Trend analysis (compare first half vs second half)
        mid_point = len(session_percentages) // 2
        if mid_point > 0:
            first_half_avg = mean(session_percentages[:mid_point])
            second_half_avg = mean(session_percentages[mid_point:])
            improvement_rate = second_half_avg - first_half_avg
            
            if improvement_rate > 5:
                trend_direction = "improving"
            elif improvement_rate < -5:
                trend_direction = "declining"
            else:
                trend_direction = "stable"
        else:
            improvement_rate = 0
            trend_direction = "insufficient_data"
        
        # Recent performance (last 5 sessions)
        recent_sessions = session_percentages[-5:] if len(session_percentages) >= 5 else session_percentages
        recent_average = mean(recent_sessions) if recent_sessions else 0
        
        # Quality assessment
        if overall_good_percentage >= 80:
            quality_rating = "Excellent"
            rating_emoji = "🏆"
        elif overall_good_percentage >= 65:
            quality_rating = "Good"
            rating_emoji = "👍"
        elif overall_good_percentage >= 50:
            quality_rating = "Fair"
            rating_emoji = "⚠️"
        else:
            quality_rating = "Needs Improvement"
            rating_emoji = "📈"
        
        # Time metrics
        total_monitoring_time = sum(log['window_duration_minutes'] for log in logs)
        
        # Store calculated metrics
        self.metrics = {
            'generated_at': datetime.now().isoformat(),
            'basic_metrics': {
                'total_sessions': total_sessions,
                'total_good_posture': total_good_posture,
                'total_slouching': total_slouching,
                'total_readings': total_readings,
                'overall_good_percentage': round(overall_good_percentage, 1)
            },
            'performance_metrics': {
                'best_session_percentage': round(best_session, 1),
                'worst_session_percentage': round(worst_session, 1),
                'average_session_percentage': round(average_session, 1),
                'consistency_score': round(consistency_score, 1),
                'excellent_sessions': excellent_sessions,
                'good_sessions': good_sessions,
                'poor_sessions': poor_sessions
            },
            'improvement_trends': {
                'improvement_rate': round(improvement_rate, 1),
                'trend_direction': trend_direction
            },
            'recent_performance': {
                'recent_average_percentage': round(recent_average, 1),
                'recent_sessions_count': len(recent_sessions)
            },
            'quality_assessment': {
                'quality_rating': quality_rating,
                'rating_emoji': rating_emoji,
                'overall_quality_score': round(overall_good_percentage, 0)
            },
            'time_metrics': {
                'total_monitoring_time_minutes': round(total_monitoring_time, 1)
            }
        }
    
    def generate_text_report(self) -> str:
        """Generate a comprehensive text report."""
        if not self.metrics:
            return "No metrics available to generate report."
        
        basic = self.metrics['basic_metrics']
        performance = self.metrics['performance_metrics']
        trends = self.metrics['improvement_trends']
        recent = self.metrics['recent_performance']
        quality = self.metrics['quality_assessment']
        time_metrics = self.metrics['time_metrics']
        
        report_lines = []
        report_lines.append("=" * 70)
        report_lines.append("POSTURE MONITORING REPORT")
        report_lines.append("=" * 70)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Overall Quality Assessment
        report_lines.append("OVERALL QUALITY ASSESSMENT")
        report_lines.append("-" * 40)
        report_lines.append(f"Rating: {quality['quality_rating']} {quality['rating_emoji']}")
        report_lines.append(f"Overall Score: {quality['overall_quality_score']}/100")
        report_lines.append(f"Good Posture: {basic['overall_good_percentage']}%")
        report_lines.append("")
        
        # Key Statistics
        report_lines.append("KEY STATISTICS")
        report_lines.append("-" * 40)
        report_lines.append(f"Total Sessions: {basic['total_sessions']}")
        report_lines.append(f"Total Monitoring Time: {time_metrics['total_monitoring_time_minutes']} minutes")
        report_lines.append(f"Total Good Posture Readings: {basic['total_good_posture']}")
        report_lines.append(f"Total Slouching Readings: {basic['total_slouching']}")
        report_lines.append(f"Total Readings: {basic['total_readings']}")
        report_lines.append("")
        
        # Performance Metrics
        report_lines.append("PERFORMANCE METRICS")
        report_lines.append("-" * 40)
        report_lines.append(f"Best Session: {performance['best_session_percentage']}%")
        report_lines.append(f"Worst Session: {performance['worst_session_percentage']}%")
        report_lines.append(f"Average Session: {performance['average_session_percentage']}%")
        report_lines.append(f"Consistency Score: {performance['consistency_score']}/100")
        report_lines.append("")
        
        # Session Quality Breakdown
        report_lines.append("SESSION QUALITY BREAKDOWN")
        report_lines.append("-" * 40)
        report_lines.append(f"Excellent Sessions (>=80%): {performance['excellent_sessions']}")
        report_lines.append(f"Good Sessions (50-79%): {performance['good_sessions']}")
        report_lines.append(f"Poor Sessions (<50%): {performance['poor_sessions']}")
        
        if basic['total_sessions'] > 0:
            excellent_pct = (performance['excellent_sessions'] / basic['total_sessions']) * 100
            good_pct = (performance['good_sessions'] / basic['total_sessions']) * 100
            poor_pct = (performance['poor_sessions'] / basic['total_sessions']) * 100
            
            report_lines.append("")
            report_lines.append("Quality Distribution:")
            report_lines.append(f"  Excellent: {excellent_pct:.1f}%")
            report_lines.append(f"  Good: {good_pct:.1f}%")
            report_lines.append(f"  Poor: {poor_pct:.1f}%")
        report_lines.append("")
        
        # Improvement Trends
        report_lines.append("IMPROVEMENT TRENDS")
        report_lines.append("-" * 40)
        report_lines.append(f"Overall Trend: {trends['trend_direction'].title()}")
        report_lines.append(f"Improvement Rate: {trends['improvement_rate']}%")
        report_lines.append(f"Recent Performance: {recent['recent_average_percentage']}% (last {recent['recent_sessions_count']} sessions)")
        report_lines.append("")
        
        # Recommendations
        report_lines.append("RECOMMENDATIONS")
        report_lines.append("-" * 40)
        
        recommendations = self.generate_recommendations()
        for i, rec in enumerate(recommendations, 1):
            report_lines.append(f"{i}. {rec}")
        
        if not recommendations:
            report_lines.append("No specific recommendations - you're doing great!")
        
        report_lines.append("")
        report_lines.append("=" * 70)
        report_lines.append("End of Report")
        report_lines.append("=" * 70)
        
        return "\n".join(report_lines)
    
    def generate_recommendations(self) -> list:
        """Generate personalized recommendations based on metrics."""
        if not self.metrics:
            return []
        
        recommendations = []
        quality = self.metrics['quality_assessment']
        trends = self.metrics['improvement_trends']
        performance = self.metrics['performance_metrics']
        basic = self.metrics['basic_metrics']
        
        score = quality['overall_quality_score']
        trend = trends['trend_direction']
        consistency = performance['consistency_score']
        good_pct = basic['overall_good_percentage']
        
        # Score-based recommendations
        if score >= 80:
            recommendations.append("Excellent work! Keep maintaining your great posture habits.")
        elif score >= 60:
            recommendations.append("Good progress! Focus on consistency to reach the next level.")
        else:
            recommendations.append("Significant improvement needed. Consider ergonomic adjustments.")
        
        # Trend-based recommendations
        if trend == "declining":
            recommendations.append("Declining trend detected. Take more frequent breaks and check your setup.")
        elif trend == "improving":
            recommendations.append("Great improvement trend! Keep up the momentum.")
        
        # Consistency recommendations
        if consistency < 70:
            recommendations.append("Work on consistency - try setting hourly posture reminders.")
        
        # Percentage-based recommendations
        if good_pct < 60:
            recommendations.append("Consider adjusting your chair height and monitor position.")
        
        # Session quality recommendations
        if performance['poor_sessions'] > performance['excellent_sessions']:
            recommendations.append("Focus on reducing poor posture sessions through better workspace ergonomics.")
        
        return recommendations
    
    def save_report_to_file(self, report_text: str):
        """Save the text report to a file."""
        try:
            with open(self.report_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"✅ Report saved to: {self.report_file}")
        except Exception as e:
            print(f"❌ Error saving report: {e}")
    
    def display_console_summary(self):
        """Display a brief summary to console."""
        if not self.metrics:
            return
        
        quality = self.metrics['quality_assessment']
        basic = self.metrics['basic_metrics']
        
        print("\n" + "="*50)
        print("🏥 POSTURE MONITORING SUMMARY")
        print("="*50)
        print(f"📊 Overall Rating: {quality['quality_rating']} {quality['rating_emoji']}")
        print(f"📈 Good Posture: {basic['overall_good_percentage']}%")
        print(f"📋 Total Sessions: {basic['total_sessions']}")
        print(f"💾 Full report saved to: {self.report_file}")
        print("="*50)
    
    def process_and_generate_report(self):
        """Main method to process data and generate report."""
        print("🔄 Loading posture data...")
        if not self.load_posture_data():
            return False
        
        print("📊 Calculating metrics...")
        self.calculate_metrics()
        
        if not self.metrics:
            print("❌ No metrics calculated. Check your data file.")
            return False
        
        print("📝 Generating text report...")
        report_text = self.generate_text_report()
        
        print("💾 Saving report to file...")
        self.save_report_to_file(report_text)
        
        self.display_console_summary()
        return True

def main():
    """Main function to process posture data and generate report."""
    dashboard = PostureDashboard()
    success = dashboard.process_and_generate_report()
    
    if success:
        print(f"\n✨ Process completed successfully!")
        print(f"📄 Check '{dashboard.report_file}' for the detailed report.")
    else:
        print("\n❌ Process failed. Please check your posture data file.")

if __name__ == "__main__":
    main() 