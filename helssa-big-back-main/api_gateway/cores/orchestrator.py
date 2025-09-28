"""
هسته Orchestrator - هماهنگی بین سرویس‌ها
"""
import logging
import asyncio
import json
from typing import Dict, List, Tuple, Any, Optional, Callable
from datetime import datetime, timedelta
from django.conf import settings
from concurrent.futures import ThreadPoolExecutor, as_completed


logger = logging.getLogger(__name__)


class OrchestratorCore:
    """
    هسته هماهنگی و کنترل workflow
    
    این کلاس مسئول هماهنگی بین سرویس‌های مختلف، مدیریت workflow و monitoring است
    """
    
    def __init__(self):
        """مقداردهی اولیه هسته Orchestrator"""
        self.logger = logging.getLogger(__name__)
        self.max_concurrent_tasks = getattr(settings, 'MAX_CONCURRENT_TASKS', 10)
        self.task_timeout = getattr(settings, 'TASK_TIMEOUT', 300)  # 5 minutes
        self.active_workflows = {}
        self.executor = ThreadPoolExecutor(max_workers=self.max_concurrent_tasks)
        
    def execute_workflow(self, workflow_config: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        اجرای یک workflow کامل
        
        Args:
            workflow_config: تنظیمات workflow
            context: context اضافی برای اجرا
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (موفقیت، نتیجه/خطا)
        """
        try:
            workflow_id = self._generate_workflow_id()
            context = context or {}
            
            # validation تنظیمات workflow
            if not self._validate_workflow_config(workflow_config):
                return False, {
                    'error': 'Invalid workflow config',
                    'message': 'تنظیمات workflow نامعتبر است'
                }
            
            # ثبت workflow در لیست فعال
            self.active_workflows[workflow_id] = {
                'config': workflow_config,
                'context': context,
                'status': 'running',
                'start_time': datetime.now(),
                'steps_completed': [],
                'current_step': None
            }
            
            self.logger.info(
                'Workflow execution started',
                extra={
                    'workflow_id': workflow_id,
                    'steps_count': len(workflow_config.get('steps', []))
                }
            )
            
            # اجرای مراحل workflow
            result = self._run_workflow_steps(workflow_id, workflow_config, context)
            
            # بروزرسانی وضعیت نهایی
            if workflow_id in self.active_workflows:
                self.active_workflows[workflow_id]['status'] = 'completed' if result[0] else 'failed'
                self.active_workflows[workflow_id]['end_time'] = datetime.now()
                
                # حذف از لیست فعال پس از مدتی
                self._schedule_workflow_cleanup(workflow_id)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Workflow execution error: {str(e)}")
            if workflow_id in self.active_workflows:
                self.active_workflows[workflow_id]['status'] = 'error'
                self.active_workflows[workflow_id]['error'] = str(e)
            
            return False, {
                'error': 'Workflow execution failed',
                'message': 'خطا در اجرای workflow',
                'details': str(e)
            }
    
    def parallel_execute(self, tasks: List[Dict[str, Any]], max_workers: Optional[int] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        اجرای موازی چندین تسک
        
        Args:
            tasks: لیست تسک‌ها برای اجرا
            max_workers: حداکثر تعداد worker موازی
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (موفقیت، نتایج/خطا)
        """
        try:
            if not tasks:
                return True, {'results': []}
            
            max_workers = max_workers or min(len(tasks), self.max_concurrent_tasks)
            
            self.logger.info(
                'Parallel execution started',
                extra={
                    'tasks_count': len(tasks),
                    'max_workers': max_workers
                }
            )
            
            results = []
            failed_tasks = []
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # ارسال همه تسک‌ها برای اجرا
                future_to_task = {
                    executor.submit(self._execute_single_task, task): task 
                    for task in tasks
                }
                
                # جمع‌آوری نتایج
                for future in as_completed(future_to_task, timeout=self.task_timeout):
                    task = future_to_task[future]
                    try:
                        success, result = future.result()
                        if success:
                            results.append({
                                'task_id': task.get('id', len(results)),
                                'status': 'success',
                                'result': result
                            })
                        else:
                            failed_tasks.append({
                                'task_id': task.get('id', len(results)),
                                'status': 'failed',
                                'error': result
                            })
                    except Exception as e:
                        failed_tasks.append({
                            'task_id': task.get('id', len(results)),
                            'status': 'error',
                            'error': str(e)
                        })
            
            success = len(failed_tasks) == 0
            
            final_result = {
                'total_tasks': len(tasks),
                'successful_tasks': len(results),
                'failed_tasks': len(failed_tasks),
                'results': results
            }
            
            if failed_tasks:
                final_result['failures'] = failed_tasks
            
            self.logger.info(
                'Parallel execution completed',
                extra={
                    'total_tasks': len(tasks),
                    'successful': len(results),
                    'failed': len(failed_tasks)
                }
            )
            
            return success, final_result
            
        except Exception as e:
            self.logger.error(f"Parallel execution error: {str(e)}")
            return False, {
                'error': 'Parallel execution failed',
                'message': 'خطا در اجرای موازی تسک‌ها',
                'details': str(e)
            }
    
    def monitor_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        نظارت بر وضعیت workflow
        
        Args:
            workflow_id: شناسه workflow
            
        Returns:
            Dict[str, Any]: وضعیت فعلی workflow
        """
        try:
            if workflow_id not in self.active_workflows:
                return {
                    'status': 'not_found',
                    'message': 'workflow یافت نشد'
                }
            
            workflow = self.active_workflows[workflow_id]
            
            # محاسبه مدت زمان اجرا
            start_time = workflow['start_time']
            current_time = datetime.now()
            duration = (current_time - start_time).total_seconds()
            
            status = {
                'workflow_id': workflow_id,
                'status': workflow['status'],
                'start_time': start_time.isoformat(),
                'duration_seconds': duration,
                'steps_completed': len(workflow['steps_completed']),
                'current_step': workflow['current_step']
            }
            
            if 'end_time' in workflow:
                status['end_time'] = workflow['end_time'].isoformat()
                status['total_duration'] = (workflow['end_time'] - start_time).total_seconds()
            
            if 'error' in workflow:
                status['error'] = workflow['error']
            
            return status
            
        except Exception as e:
            self.logger.error(f"Workflow monitoring error: {str(e)}")
            return {
                'status': 'error',
                'message': 'خطا در نظارت بر workflow',
                'error': str(e)
            }
    
    def cancel_workflow(self, workflow_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        لغو workflow در حال اجرا
        
        Args:
            workflow_id: شناسه workflow
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (موفقیت، نتیجه)
        """
        try:
            if workflow_id not in self.active_workflows:
                return False, {
                    'error': 'Workflow not found',
                    'message': 'workflow یافت نشد'
                }
            
            workflow = self.active_workflows[workflow_id]
            
            if workflow['status'] in ['completed', 'failed', 'cancelled']:
                return False, {
                    'error': 'Workflow already finished',
                    'message': 'workflow قبلاً به پایان رسیده است',
                    'current_status': workflow['status']
                }
            
            # تغییر وضعیت به cancelled
            workflow['status'] = 'cancelled'
            workflow['end_time'] = datetime.now()
            
            self.logger.info(
                'Workflow cancelled',
                extra={'workflow_id': workflow_id}
            )
            
            return True, {
                'workflow_id': workflow_id,
                'status': 'cancelled',
                'message': 'workflow با موفقیت لغو شد'
            }
            
        except Exception as e:
            self.logger.error(f"Workflow cancellation error: {str(e)}")
            return False, {
                'error': 'Cancellation failed',
                'message': 'خطا در لغو workflow',
                'details': str(e)
            }
    
    def get_active_workflows(self) -> List[Dict[str, Any]]:
        """
        دریافت لیست workflow های فعال
        
        Returns:
            List[Dict[str, Any]]: لیست workflow های فعال
        """
        try:
            active_list = []
            
            for workflow_id, workflow in self.active_workflows.items():
                if workflow['status'] in ['running', 'paused']:
                    start_time = workflow['start_time']
                    duration = (datetime.now() - start_time).total_seconds()
                    
                    active_list.append({
                        'workflow_id': workflow_id,
                        'status': workflow['status'],
                        'start_time': start_time.isoformat(),
                        'duration_seconds': duration,
                        'steps_completed': len(workflow['steps_completed']),
                        'current_step': workflow['current_step']
                    })
            
            return active_list
            
        except Exception as e:
            self.logger.error(f"Get active workflows error: {str(e)}")
            return []
    
    def _validate_workflow_config(self, config: Dict[str, Any]) -> bool:
        """
        اعتبارسنجی تنظیمات workflow
        """
        try:
            required_fields = ['steps']
            for field in required_fields:
                if field not in config:
                    return False
            
            steps = config['steps']
            if not isinstance(steps, list) or len(steps) == 0:
                return False
            
            # بررسی هر مرحله
            for step in steps:
                if not isinstance(step, dict):
                    return False
                
                required_step_fields = ['name', 'type']
                for field in required_step_fields:
                    if field not in step:
                        return False
            
            return True
            
        except Exception:
            return False
    
    def _run_workflow_steps(self, workflow_id: str, config: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        اجرای مراحل workflow
        """
        try:
            steps = config['steps']
            workflow = self.active_workflows[workflow_id]
            results = []
            
            for i, step in enumerate(steps):
                if workflow['status'] == 'cancelled':
                    break
                
                workflow['current_step'] = step['name']
                
                self.logger.info(
                    'Executing workflow step',
                    extra={
                        'workflow_id': workflow_id,
                        'step_name': step['name'],
                        'step_index': i
                    }
                )
                
                # اجرای مرحله
                step_success, step_result = self._execute_workflow_step(step, context, results)
                
                results.append({
                    'step_name': step['name'],
                    'success': step_success,
                    'result': step_result
                })
                
                workflow['steps_completed'].append(step['name'])
                
                if not step_success:
                    # در صورت خطا، بررسی کنید که آیا workflow باید ادامه یابد یا نه
                    if step.get('continue_on_error', False):
                        self.logger.warning(
                            'Step failed but continuing workflow',
                            extra={
                                'workflow_id': workflow_id,
                                'step_name': step['name'],
                                'error': step_result
                            }
                        )
                        continue
                    else:
                        return False, {
                            'error': 'Workflow step failed',
                            'step_name': step['name'],
                            'step_error': step_result,
                            'completed_steps': results
                        }
            
            # workflow با موفقیت تکمیل شد
            return True, {
                'workflow_id': workflow_id,
                'status': 'completed',
                'steps_executed': len(results),
                'results': results
            }
            
        except Exception as e:
            return False, {
                'error': 'Workflow execution error',
                'details': str(e)
            }
    
    def _execute_workflow_step(self, step: Dict[str, Any], context: Dict[str, Any], previous_results: List[Dict]) -> Tuple[bool, Dict[str, Any]]:
        """
        اجرای یک مرحله از workflow
        """
        try:
            step_type = step['type']
            step_params = step.get('params', {})
            
            # شبیه‌سازی اجرای انواع مختلف step
            if step_type == 'text_processing':
                return self._execute_text_processing_step(step_params, context)
            elif step_type == 'speech_processing':
                return self._execute_speech_processing_step(step_params, context)
            elif step_type == 'api_call':
                return self._execute_api_call_step(step_params, context)
            elif step_type == 'data_validation':
                return self._execute_validation_step(step_params, context)
            elif step_type == 'delay':
                return self._execute_delay_step(step_params)
            else:
                return False, {
                    'error': 'Unknown step type',
                    'step_type': step_type
                }
                
        except Exception as e:
            return False, {
                'error': 'Step execution error',
                'details': str(e)
            }
    
    def _execute_single_task(self, task: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        اجرای یک تسک منفرد
        """
        try:
            task_type = task.get('type', 'unknown')
            task_params = task.get('params', {})
            
            # شبیه‌سازی اجرای تسک
            if task_type == 'compute':
                import time
                time.sleep(task_params.get('duration', 1))  # شبیه‌سازی محاسبات
                return True, {'computed_value': 42}
            elif task_type == 'fetch_data':
                return True, {'data': f"fetched_data_{task.get('id', 'unknown')}"}
            else:
                return True, {'result': f"processed_{task_type}"}
                
        except Exception as e:
            return False, {'error': str(e)}
    
    def _execute_text_processing_step(self, params: Dict, context: Dict) -> Tuple[bool, Dict[str, Any]]:
        """اجرای مرحله پردازش متن"""
        return True, {'text_processed': True, 'word_count': 100}
    
    def _execute_speech_processing_step(self, params: Dict, context: Dict) -> Tuple[bool, Dict[str, Any]]:
        """اجرای مرحله پردازش صدا"""
        return True, {'audio_processed': True, 'duration': 30}
    
    def _execute_api_call_step(self, params: Dict, context: Dict) -> Tuple[bool, Dict[str, Any]]:
        """اجرای مرحله فراخوانی API"""
        return True, {'api_response': {'status': 'success'}}
    
    def _execute_validation_step(self, params: Dict, context: Dict) -> Tuple[bool, Dict[str, Any]]:
        """اجرای مرحله اعتبارسنجی"""
        return True, {'validation_passed': True}
    
    def _execute_delay_step(self, params: Dict) -> Tuple[bool, Dict[str, Any]]:
        """اجرای مرحله تاخیر"""
        import time
        delay_seconds = params.get('seconds', 1)
        time.sleep(delay_seconds)
        return True, {'delayed_seconds': delay_seconds}
    
    def _generate_workflow_id(self) -> str:
        """تولید شناسه یکتا برای workflow"""
        import uuid
        return f"wf_{uuid.uuid4().hex[:8]}"
    
    def _schedule_workflow_cleanup(self, workflow_id: str, delay_minutes: int = 60):
        """زمان‌بندی پاکسازی workflow"""
        # در عمل باید با Celery یا سیستم queue مناسب پیاده‌سازی شود
        pass