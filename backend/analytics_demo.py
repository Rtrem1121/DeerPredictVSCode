#!/usr/bin/env python3
"""
Analytics System Integration Demo

This script demonstrates the complete analytics system integration,
including data collection, performance monitoring, and dashboard API.
Perfect for showcasing the analytics capabilities.

Features:
- Simulates realistic prediction requests
- Generates sample analytics data
- Demonstrates real-time monitoring
- Shows dashboard functionality

Author: Vermont Deer Prediction System
Version: 1.0.0
"""

import asyncio
import time
import random
import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Import analytics components
from analytics import (
    get_analytics_collector,
    get_performance_monitor,
    record_prediction_analytics,
    record_system_performance,
    start_performance_monitoring,
    PredictionRecord
)

from config_manager import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AnalyticsDemo:
    """Analytics system demonstration with realistic data generation"""
    
    def __init__(self):
        self.analytics = get_analytics_collector()
        self.monitor = get_performance_monitor()
        self.config = get_config()
        
        # Demo parameters
        self.seasons = ['early_archery', 'rifle', 'late_archery', 'muzzleloader']
        self.weather_conditions = [
            ['clear', 'calm'], ['cloudy', 'light_wind'], ['overcast', 'windy'],
            ['light_rain', 'calm'], ['clear', 'cold'], ['foggy', 'calm']
        ]
        self.times_of_day = ['dawn', 'morning', 'midday', 'afternoon', 'dusk', 'night']
        
        # Vermont coordinates (rough bounding box)
        self.lat_range = (42.7, 45.0)
        self.lon_range = (-73.4, -71.5)
        
        logger.info("🎯 Analytics Demo initialized")
    
    def generate_sample_prediction(self) -> Dict[str, Any]:
        """Generate a realistic sample prediction request"""
        return {
            'lat': random.uniform(*self.lat_range),
            'lon': random.uniform(*self.lon_range),
            'season': random.choice(self.seasons),
            'weather_conditions': random.choice(self.weather_conditions),
            'time_of_day': random.choice(self.times_of_day)
        }
    
    def simulate_prediction_result(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate realistic prediction results based on request parameters"""
        # Base rating influenced by season and time
        base_rating = 50.0
        
        # Season modifiers
        season_modifiers = {
            'early_archery': 15.0,
            'rifle': 5.0,
            'late_archery': 10.0,
            'muzzleloader': 8.0
        }
        
        # Time of day modifiers
        time_modifiers = {
            'dawn': 20.0,
            'dusk': 18.0,
            'morning': 10.0,
            'afternoon': 5.0,
            'midday': -5.0,
            'night': -10.0
        }
        
        # Weather modifiers
        weather_bonus = 0.0
        if 'clear' in request['weather_conditions']:
            weather_bonus += 5.0
        if 'calm' in request['weather_conditions']:
            weather_bonus += 8.0
        if 'cold' in request['weather_conditions']:
            weather_bonus += 7.0
        if 'rain' in str(request['weather_conditions']):
            weather_bonus -= 10.0
        
        # Calculate final rating
        rating = base_rating + season_modifiers.get(request['season'], 0)
        rating += time_modifiers.get(request['time_of_day'], 0)
        rating += weather_bonus
        
        # Add some randomness
        rating += random.uniform(-15.0, 15.0)
        rating = max(0.0, min(100.0, rating))
        
        # Confidence based on rating and consistency
        confidence = rating * 0.8 + random.uniform(5.0, 20.0)
        confidence = max(30.0, min(100.0, confidence))
        
        # Mature buck score (higher for better conditions)
        mature_buck_score = rating * 0.7 + random.uniform(0.0, 25.0)
        mature_buck_score = max(0.0, min(100.0, mature_buck_score))
        
        return {
            'stand_rating': rating,
            'confidence_score': confidence,
            'mature_buck_score': mature_buck_score,
            'recommended': rating > 60.0
        }
    
    async def run_prediction_simulation(self, num_predictions: int = 50, delay: float = 0.5):
        """Run a series of simulated predictions to generate analytics data"""
        print(f"\n🎯 Running {num_predictions} simulated predictions...")
        
        for i in range(num_predictions):
            try:
                # Generate request
                request = self.generate_sample_prediction()
                
                # Simulate processing time
                start_time = time.time()
                await asyncio.sleep(random.uniform(0.1, 0.3))  # Simulate processing
                
                # Generate result
                result = self.simulate_prediction_result(request)
                end_time = time.time()
                
                # Calculate metrics
                response_time_ms = (end_time - start_time) * 1000
                
                # Record analytics
                prediction_id = f"demo_{uuid.uuid4().hex[:8]}"
                record_prediction_analytics(
                    prediction_id=prediction_id,
                    request_data=request,
                    response_data=result,
                    performance_data={'response_time_ms': response_time_ms}
                )
                
                # Show progress
                if (i + 1) % 10 == 0:
                    print(f"  ✅ Completed {i + 1}/{num_predictions} predictions")
                
                # Brief delay between predictions
                await asyncio.sleep(delay)
                
            except Exception as e:
                logger.error(f"Error in prediction {i + 1}: {e}")
        
        print(f"🎉 Completed {num_predictions} predictions simulation!")
    
    async def run_performance_simulation(self, duration_minutes: int = 5):
        """Run performance monitoring simulation"""
        print(f"\n📊 Running performance monitoring for {duration_minutes} minutes...")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        iteration = 0
        while time.time() < end_time:
            try:
                # Simulate varying performance metrics
                iteration += 1
                
                # CPU usage with some variation
                base_cpu = 15.0 + (iteration % 20) * 2.0
                cpu_noise = random.uniform(-5.0, 10.0)
                cpu_usage = max(5.0, min(85.0, base_cpu + cpu_noise))
                
                # Memory usage with gradual increase
                base_memory = 20.0 + (iteration * 0.1)
                memory_noise = random.uniform(-2.0, 5.0)
                memory_usage = max(10.0, min(75.0, base_memory + memory_noise))
                
                # Response time with occasional spikes
                base_response = 150.0
                if random.random() < 0.1:  # 10% chance of spike
                    response_spike = random.uniform(500.0, 2000.0)
                else:
                    response_spike = random.uniform(-50.0, 200.0)
                response_time = max(50.0, base_response + response_spike)
                
                # Predictions per minute
                predictions_per_min = random.uniform(2.0, 15.0)
                
                # Record performance metrics
                record_system_performance('cpu_usage', cpu_usage)
                record_system_performance('memory_usage', memory_usage)
                record_system_performance('response_time', response_time)
                record_system_performance('predictions_per_minute', predictions_per_min)
                
                # Show progress
                elapsed = (time.time() - start_time) / 60
                if iteration % 12 == 0:  # Every ~2 minutes
                    print(f"  📈 Performance monitoring: {elapsed:.1f}/{duration_minutes} minutes")
                
                # Wait between measurements
                await asyncio.sleep(10.0)  # 10 second intervals
                
            except Exception as e:
                logger.error(f"Error in performance simulation: {e}")
        
        print(f"📊 Performance monitoring simulation complete!")
    
    async def run_full_demo(self):
        """Run complete analytics demonstration"""
        print("🚀 VERMONT DEER PREDICTION ANALYTICS DEMO")
        print("=" * 60)
        
        try:
            # Start performance monitoring
            print("\n🔍 Starting performance monitoring...")
            start_performance_monitoring()
            
            # Wait a moment for monitoring to initialize
            await asyncio.sleep(2)
            
            # Run simulations concurrently
            await asyncio.gather(
                self.run_prediction_simulation(num_predictions=30, delay=0.3),
                self.run_performance_simulation(duration_minutes=3)
            )
            
            # Generate analytics summary
            print("\n📋 Generating analytics summary...")
            await asyncio.sleep(1)
            
            # Get current analytics
            prediction_analytics = self.analytics.get_prediction_analytics(days=1)
            performance_analytics = self.analytics.get_performance_analytics(hours=1)
            
            # Display summary
            print("\n📊 ANALYTICS SUMMARY")
            print("=" * 40)
            
            summary = prediction_analytics.get('summary', {})
            print(f"Total Predictions: {summary.get('total_predictions', 0)}")
            print(f"Average Confidence: {summary.get('avg_confidence', 0):.1f}%")
            print(f"Average Rating: {summary.get('avg_rating', 0):.1f}")
            print(f"Average Response Time: {summary.get('avg_response_time', 0):.1f}ms")
            
            print(f"\nPerformance Metrics: {len(performance_analytics.get('summary', []))} types")
            
            # Show confidence distribution
            conf_dist = prediction_analytics.get('confidence_distribution', [])
            if conf_dist:
                print("\nConfidence Distribution:")
                for dist in conf_dist:
                    print(f"  {dist['confidence_range']}: {dist['count']} predictions")
            
            print("\n🎉 Analytics demo completed successfully!")
            print("\nNext steps:")
            print("- Start the dashboard: python start_dashboard.py")
            print("- View analytics at: http://localhost:8002")
            print("- API available at: http://localhost:8001")
            
        except Exception as e:
            logger.error(f"Demo failed: {e}", exc_info=True)
            raise

async def main():
    """Main demo function"""
    demo = AnalyticsDemo()
    await demo.run_full_demo()

if __name__ == "__main__":
    try:
        print("🦌 Starting Vermont Deer Prediction Analytics Demo")
        print("This will simulate realistic system usage and generate analytics data")
        print()
        
        # Run the demo
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n👋 Demo stopped by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)
