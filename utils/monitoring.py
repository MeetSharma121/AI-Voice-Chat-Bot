"""
Monitoring Utility Module for Healthcare Chatbot
Provides performance metrics and health monitoring
"""

import os
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from flask import Flask, Response

# Prometheus metrics
REQUEST_COUNT = Counter('healthcare_chatbot_requests_total', 'Total requests', ['endpoint', 'method', 'status'])
REQUEST_DURATION = Histogram('healthcare_chatbot_request_duration_seconds', 'Request duration in seconds', ['endpoint'])
ACTIVE_CONVERSATIONS = Gauge('healthcare_chatbot_active_conversations', 'Number of active conversations')
TOTAL_MESSAGES = Gauge('healthcare_chatbot_total_messages', 'Total messages processed')
SAFETY_CHECK_DURATION = Histogram('healthcare_chatbot_safety_check_duration_seconds', 'Safety check duration in seconds')
VOICE_PROCESSING_DURATION = Histogram('healthcare_chatbot_voice_processing_duration_seconds', 'Voice processing duration in seconds')
RAG_QUERY_DURATION = Histogram('healthcare_chatbot_rag_query_duration_seconds', 'RAG query duration in seconds')

class PerformanceMonitor:
    """Performance monitoring for the healthcare chatbot"""
    
    def __init__(self):
        """Initialize performance monitor"""
        self.start_time = time.time()
        self.request_times = {}
        self.error_counts = {}
        self.endpoint_stats = {}
        
        logging.info("Performance Monitor initialized")
    
    def start_request(self, endpoint: str, method: str = 'GET'):
        """Start timing a request"""
        request_id = f"{endpoint}_{method}_{int(time.time() * 1000)}"
        self.request_times[request_id] = {
            'start_time': time.time(),
            'endpoint': endpoint,
            'method': method
        }
        return request_id
    
    def end_request(self, request_id: str, status: int = 200):
        """End timing a request and record metrics"""
        if request_id in self.request_times:
            request_data = self.request_times[request_id]
            duration = time.time() - request_data['start_time']
            
            # Record Prometheus metrics
            REQUEST_COUNT.labels(
                endpoint=request_data['endpoint'],
                method=request_data['method'],
                status=status
            ).inc()
            
            REQUEST_DURATION.labels(
                endpoint=request_data['endpoint']
            ).observe(duration)
            
            # Update endpoint statistics
            endpoint = request_data['endpoint']
            if endpoint not in self.endpoint_stats:
                self.endpoint_stats[endpoint] = {
                    'total_requests': 0,
                    'total_duration': 0,
                    'avg_duration': 0,
                    'error_count': 0
                }
            
            self.endpoint_stats[endpoint]['total_requests'] += 1
            self.endpoint_stats[endpoint]['total_duration'] += duration
            self.endpoint_stats[endpoint]['avg_duration'] = (
                self.endpoint_stats[endpoint]['total_duration'] / 
                self.endpoint_stats[endpoint]['total_requests']
            )
            
            if status >= 400:
                self.endpoint_stats[endpoint]['error_count'] += 1
            
            # Clean up
            del self.request_times[request_id]
    
    def record_error(self, endpoint: str, error: str):
        """Record an error"""
        if endpoint not in self.error_counts:
            self.error_counts[endpoint] = {}
        
        if error not in self.error_counts[endpoint]:
            self.error_counts[endpoint][error] = 0
        
        self.error_counts[endpoint][error] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get performance statistics"""
        uptime = time.time() - self.start_time
        
        return {
            'uptime_seconds': uptime,
            'uptime_formatted': str(timedelta(seconds=int(uptime))),
            'total_requests': sum(stats['total_requests'] for stats in self.endpoint_stats.values()),
            'average_response_time': sum(stats['avg_duration'] for stats in self.endpoint_stats.values()) / len(self.endpoint_stats) if self.endpoint_stats else 0,
            'endpoint_statistics': self.endpoint_stats,
            'error_counts': self.error_counts,
            'active_requests': len(self.request_times)
        }

class HealthMonitor:
    """Health monitoring for the healthcare chatbot"""
    
    def __init__(self):
        """Initialize health monitor"""
        self.health_checks = {}
        self.last_check = {}
        self.check_interval = 300  # 5 minutes
        
        logging.info("Health Monitor initialized")
    
    def register_health_check(self, name: str, check_function, interval: Optional[int] = None):
        """Register a health check function"""
        self.health_checks[name] = {
            'function': check_function,
            'interval': interval or self.check_interval
        }
        logging.info(f"Registered health check: {name}")
    
    def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}
        current_time = time.time()
        
        for name, check_info in self.health_checks.items():
            last_check_time = self.last_check.get(name, 0)
            interval = check_info['interval']
            
            # Check if it's time to run this health check
            if current_time - last_check_time >= interval:
                try:
                    start_time = time.time()
                    result = check_info['function']()
                    duration = time.time() - start_time
                    
                    results[name] = {
                        'status': 'healthy' if result else 'unhealthy',
                        'duration': duration,
                        'timestamp': datetime.now().isoformat(),
                        'last_check': datetime.fromtimestamp(current_time).isoformat()
                    }
                    
                    self.last_check[name] = current_time
                    
                except Exception as e:
                    results[name] = {
                        'status': 'error',
                        'error': str(e),
                        'timestamp': datetime.now().isoformat(),
                        'last_check': datetime.fromtimestamp(current_time).isoformat()
                    }
                    self.last_check[name] = current_time
            else:
                # Return cached result
                if name in results:
                    results[name]['cached'] = True
        
        return results
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        health_checks = self.run_health_checks()
        
        # Count statuses
        healthy_count = sum(1 for check in health_checks.values() if check['status'] == 'healthy')
        unhealthy_count = sum(1 for check in health_checks.values() if check['status'] == 'unhealthy')
        error_count = sum(1 for check in health_checks.values() if check['status'] == 'error')
        total_count = len(health_checks)
        
        # Determine overall status
        if error_count > 0:
            overall_status = 'critical'
        elif unhealthy_count > 0:
            overall_status = 'warning'
        elif healthy_count == total_count:
            overall_status = 'healthy'
        else:
            overall_status = 'unknown'
        
        return {
            'status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'checks': health_checks,
            'summary': {
                'total': total_count,
                'healthy': healthy_count,
                'unhealthy': unhealthy_count,
                'error': error_count
            }
        }

class MetricsCollector:
    """Collect and expose metrics for the healthcare chatbot"""
    
    def __init__(self):
        """Initialize metrics collector"""
        self.metrics = {}
        self.collection_time = None
        
        logging.info("Metrics Collector initialized")
    
    def collect_metrics(self, chatbot, voice_processor, rag_engine, conversation_manager):
        """Collect metrics from all components"""
        try:
            self.metrics = {
                'chatbot': chatbot.get_statistics() if hasattr(chatbot, 'get_statistics') else {},
                'voice_processor': voice_processor.get_statistics() if hasattr(voice_processor, 'get_statistics') else {},
                'rag_engine': rag_engine.get_statistics() if hasattr(rag_engine, 'get_statistics') else {},
                'conversation_manager': conversation_manager.get_statistics() if hasattr(conversation_manager, 'get_statistics') else {},
                'system': {
                    'timestamp': datetime.now().isoformat(),
                    'python_version': os.sys.version,
                    'platform': os.sys.platform
                }
            }
            
            # Update Prometheus gauges
            if 'conversation_manager' in self.metrics:
                conv_stats = self.metrics['conversation_manager']
                ACTIVE_CONVERSATIONS.set(conv_stats.get('active_conversations', 0))
                TOTAL_MESSAGES.set(conv_stats.get('total_messages', 0))
            
            self.collection_time = datetime.now()
            logging.debug("Metrics collected successfully")
            
        except Exception as e:
            logging.error(f"Error collecting metrics: {str(e)}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics"""
        return self.metrics
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        try:
            return generate_latest()
        except Exception as e:
            logging.error(f"Error exporting Prometheus metrics: {str(e)}")
            return ""

# Global instances
performance_monitor = PerformanceMonitor()
health_monitor = HealthMonitor()
metrics_collector = MetricsCollector()

def setup_monitoring(app: Flask):
    """Setup monitoring for the Flask application"""
    
    # Register health check endpoints
    @app.route('/metrics')
    def metrics():
        """Prometheus metrics endpoint"""
        try:
            metrics_data = generate_latest()
            return Response(metrics_data, mimetype=CONTENT_TYPE_LATEST)
        except Exception as e:
            logging.error(f"Error serving metrics: {str(e)}")
            return Response("Error generating metrics", status=500)
    
    @app.route('/health')
    def health():
        """Health check endpoint"""
        try:
            health_status = health_monitor.get_health_status()
            return health_status
        except Exception as e:
            logging.error(f"Error serving health check: {str(e)}")
            return {'status': 'error', 'error': str(e)}, 500
    
    @app.route('/stats')
    def stats():
        """Performance statistics endpoint"""
        try:
            stats_data = {
                'performance': performance_monitor.get_statistics(),
                'health': health_monitor.get_health_status(),
                'metrics': metrics_collector.get_metrics()
            }
            return stats_data
        except Exception as e:
            logging.error(f"Error serving statistics: {str(e)}")
            return {'error': str(e)}, 500
    
    # Register default health checks
    def check_system_health():
        """Basic system health check"""
        try:
            # Check if we can access basic system resources
            os.listdir('.')
            return True
        except Exception:
            return False
    
    def check_memory_health():
        """Memory usage health check"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return memory.percent < 90  # Consider unhealthy if >90% memory usage
        except ImportError:
            return True  # psutil not available, assume healthy
        except Exception:
            return False
    
    health_monitor.register_health_check('system', check_system_health, interval=60)
    health_monitor.register_health_check('memory', check_memory_health, interval=120)
    
    logging.info("Monitoring setup completed")

def monitor_request(endpoint: str, method: str = 'GET'):
    """Decorator to monitor request performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            request_id = performance_monitor.start_request(endpoint, method)
            try:
                result = func(*args, **kwargs)
                performance_monitor.end_request(request_id, 200)
                return result
            except Exception as e:
                performance_monitor.end_request(request_id, 500)
                performance_monitor.record_error(endpoint, str(e))
                raise
        return wrapper
    return decorator

def monitor_function(name: str):
    """Decorator to monitor function performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logging.debug(f"Function {name} completed in {duration:.4f} seconds")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logging.error(f"Function {name} failed after {duration:.4f} seconds: {str(e)}")
                raise
        return wrapper
    return decorator 