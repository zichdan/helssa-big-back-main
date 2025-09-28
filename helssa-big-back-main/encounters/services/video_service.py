import jwt
from typing import Dict, Optional
from datetime import datetime, timedelta
import aiohttp
from django.conf import settings


class VideoConferenceService:
    """سرویس کنفرانس ویدیویی"""
    
    def __init__(self):
        self.jitsi_domain = getattr(settings, 'JITSI_DOMAIN', 'meet.jit.si')
        self.jwt_secret = getattr(settings, 'JITSI_JWT_SECRET', 'secret')
        self.turn_servers = getattr(settings, 'TURN_SERVERS', [])
        self.jibri_url = getattr(settings, 'JIBRI_URL', '')
        self.jibri_token = getattr(settings, 'JIBRI_TOKEN', '')
        
    async def create_room(
        self,
        encounter_id: str,
        scheduled_at: datetime,
        duration_minutes: int
    ) -> Dict:
        """ایجاد اتاق ویدیو"""
        
        room_id = f"helssa-{encounter_id[:8]}"
        
        # تولید JWT برای محدودسازی دسترسی
        patient_jwt = self._generate_room_jwt(
            room_id,
            'patient',
            duration_minutes
        )
        doctor_jwt = self._generate_room_jwt(
            room_id,
            'doctor',
            duration_minutes,
            is_moderator=True
        )
        
        # URL های اتصال
        base_url = f"https://{self.jitsi_domain}/{room_id}"
        
        return {
            'room_id': room_id,
            'patient_url': f"{base_url}?jwt={patient_jwt}",
            'doctor_url': f"{base_url}?jwt={doctor_jwt}",
            'turn_servers': self.turn_servers,
            'expires_at': scheduled_at + timedelta(
                minutes=duration_minutes + 30
            )
        }
        
    def _generate_room_jwt(
        self,
        room_id: str,
        user_type: str,
        duration_minutes: int,
        is_moderator: bool = False
    ) -> str:
        """تولید JWT برای دسترسی به اتاق"""
        
        now = datetime.utcnow()
        exp = now + timedelta(minutes=duration_minutes + 30)
        
        payload = {
            'aud': 'jitsi',
            'iss': 'helssa',
            'sub': self.jitsi_domain,
            'room': room_id,
            'exp': int(exp.timestamp()),
            'moderator': is_moderator,
            'context': {
                'user': {
                    'name': f"HELSSA {user_type.title()}",
                    'avatar': '',
                    'id': user_type
                },
                'features': {
                    'recording': is_moderator,
                    'livestreaming': False,
                    'transcription': False,
                    'outbound-call': False
                }
            }
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
        
    async def start_recording(
        self,
        room_id: str,
        encounter_id: str
    ) -> bool:
        """شروع ضبط ویدیو"""
        
        if not self.jibri_url:
            return False
            
        # ارسال درخواست به Jibri
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.jibri_url}/api/record/start",
                    json={
                        'room_id': room_id,
                        'session_id': encounter_id,
                        'stream_key': self._generate_stream_key(encounter_id)
                    },
                    headers={'Authorization': f'Bearer {self.jibri_token}'}
                ) as response:
                    return response.status == 200
            except Exception as e:
                print(f"خطا در شروع ضبط: {e}")
                return False
                
    async def stop_recording(
        self,
        room_id: str,
        encounter_id: str
    ) -> Optional[str]:
        """توقف ضبط و دریافت URL"""
        
        if not self.jibri_url:
            return None
            
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.jibri_url}/api/record/stop",
                    json={'room_id': room_id},
                    headers={'Authorization': f'Bearer {self.jibri_token}'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # آپلود به MinIO
                        file_url = await self._upload_recording(
                            data.get('file_path'),
                            encounter_id
                        )
                        
                        return file_url
            except Exception as e:
                print(f"خطا در توقف ضبط: {e}")
                
        return None
        
    async def get_room_status(
        self,
        room_id: str
    ) -> Dict:
        """دریافت وضعیت اتاق"""
        
        # TODO: اتصال به Jitsi API برای دریافت وضعیت
        return {
            'room_id': room_id,
            'is_active': False,
            'participant_count': 0,
            'is_recording': False
        }
        
    async def kick_participant(
        self,
        room_id: str,
        participant_id: str
    ) -> bool:
        """اخراج شرکت‌کننده از اتاق"""
        
        # TODO: اتصال به Jitsi API
        return False
        
    async def mute_participant(
        self,
        room_id: str,
        participant_id: str,
        mute_audio: bool = True,
        mute_video: bool = False
    ) -> bool:
        """قطع صدا/تصویر شرکت‌کننده"""
        
        # TODO: اتصال به Jitsi API
        return False
        
    async def send_chat_message(
        self,
        room_id: str,
        message: str,
        sender_name: str = "سیستم"
    ) -> bool:
        """ارسال پیام چت به اتاق"""
        
        # TODO: اتصال به Jitsi API
        return False
        
    async def end_meeting(
        self,
        room_id: str
    ) -> bool:
        """پایان جلسه برای همه شرکت‌کنندگان"""
        
        # TODO: اتصال به Jitsi API
        return False
        
    def _generate_stream_key(self, encounter_id: str) -> str:
        """تولید کلید استریم برای ضبط"""
        
        # ترکیب encounter_id با timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        return f"helssa_{encounter_id[:8]}_{timestamp}"
        
    async def _upload_recording(
        self,
        file_path: str,
        encounter_id: str
    ) -> Optional[str]:
        """آپلود فایل ضبط شده به MinIO"""
        
        if not file_path:
            return None
            
        # TODO: اتصال به MinIO service
        # فعلاً URL ساختگی
        return f"https://storage.helssa.ir/recordings/{encounter_id}/video.mp4"
        
    async def get_recording_info(
        self,
        encounter_id: str
    ) -> Optional[Dict]:
        """دریافت اطلاعات فایل ضبط شده"""
        
        # TODO: اتصال به storage service
        return {
            'url': f"https://storage.helssa.ir/recordings/{encounter_id}/video.mp4",
            'size_mb': 150.5,
            'duration_seconds': 1800,
            'format': 'mp4',
            'resolution': '1280x720',
            'created_at': datetime.utcnow().isoformat()
        }
        
    async def generate_meeting_report(
        self,
        room_id: str,
        encounter_id: str
    ) -> Dict:
        """تولید گزارش جلسه"""
        
        # TODO: جمع‌آوری آمار از Jitsi
        return {
            'room_id': room_id,
            'encounter_id': encounter_id,
            'participants': [
                {
                    'type': 'doctor',
                    'join_time': datetime.utcnow().isoformat(),
                    'leave_time': None,
                    'duration_minutes': 30,
                    'connection_quality': 'good'
                },
                {
                    'type': 'patient',
                    'join_time': datetime.utcnow().isoformat(),
                    'leave_time': None,
                    'duration_minutes': 28,
                    'connection_quality': 'fair'
                }
            ],
            'recording': {
                'enabled': True,
                'duration_seconds': 1680,
                'file_size_mb': 145.2
            },
            'network_stats': {
                'average_bandwidth_kbps': 512,
                'packet_loss_percent': 0.5,
                'average_latency_ms': 45
            }
        }