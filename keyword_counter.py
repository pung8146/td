import os
import sys
import time
import json
from collections import defaultdict
sys.path.insert(0, os.path.abspath('.'))
import tdjson

class KeywordCounter:
    def __init__(self):
        self.keyword_counter = defaultdict(int)
        self.chat_names = {}  # 채팅방 이름 캐시
        self.user_names = {}  # 사용자 이름 캐시
        self.target_keywords = ['안녕', 'hello', '테스트', 'test', '봇', 'bot']  # 추적할 키워드들
        self.client = None
        
    def setup_client(self):
        """TDLib 클라이언트 설정"""
        api_id = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        phone_number = os.getenv('TELEGRAM_PHONE_NUMBER')
        
        if not api_id or not api_hash or not phone_number:
            print("❌ 환경변수가 설정되지 않았습니다.")
            print("다음 환경변수를 설정해주세요:")
            print("export TELEGRAM_API_ID='your_api_id'")
            print("export TELEGRAM_API_HASH='your_api_hash'")
            print("export TELEGRAM_PHONE_NUMBER='your_phone_number'")
            sys.exit(1)
        
        self.client = tdjson.create()
        
        # TDLib 파라미터 설정
        self.client.send({
            "@type": "setTdlibParameters",
            "database_directory": "tdlib-db",
            "use_message_database": True,
            "use_secret_chats": False,
            "api_id": int(api_id),
            "api_hash": api_hash,
            "system_language_code": "ko",
            "device_model": "macOS",
            "application_version": "1.0",
            "enable_storage_optimizer": True,
            "use_test_dc": False
        })
        
        return self.authenticate()
    
    def authenticate(self):
        """인증 프로세스"""
        print("인증 중...")
        while True:
            result = self.client.receive()
            if result:
                if result.get("@type") == "updateAuthorizationState":
                    state = result["authorization_state"]["@type"]
                    print(f"인증 상태: {state}")
                    
                    if state == "authorizationStateWaitPhoneNumber":
                        phone = os.getenv('TELEGRAM_PHONE_NUMBER')
                        self.client.send({"@type": "setAuthenticationPhoneNumber", "phone_number": phone})
                        
                    elif state == "authorizationStateWaitCode":
                        code = input("인증 코드를 입력하세요: ")
                        self.client.send({"@type": "checkAuthenticationCode", "code": code})
                        
                    elif state == "authorizationStateReady":
                        print("✅ 인증 성공!")
                        return True
                        
                    elif state == "authorizationStateClosed":
                        print("❌ 인증 실패")
                        return False
                        
                elif result.get("@type") == "error":
                    print(f"❌ Error: {result}")
                    if "setTdlibParameters" in str(result):
                        continue
                    return False
            
            time.sleep(0.1)
    
    def get_chat_name(self, chat_id):
        """채팅방 이름 가져오기"""
        if chat_id not in self.chat_names:
            self.client.send({
                "@type": "getChat",
                "chat_id": chat_id
            })
            return f"채팅방_{chat_id}"
        return self.chat_names[chat_id]
    
    def get_user_name(self, user_id):
        """사용자 이름 가져오기"""
        if user_id not in self.user_names:
            self.client.send({
                "@type": "getUser",
                "user_id": user_id
            })
            return f"사용자_{user_id}"
        return self.user_names[user_id]
    
    def process_message(self, message):
        """메시지 처리 및 키워드 검사"""
        chat_id = message.get("chat_id")
        content = message.get("content", {})
        
        if content.get("@type") == "messageText":
            text = content.get("text", "")
            sender = message.get("sender_id", {})
            
            # 키워드 검사
            for keyword in self.target_keywords:
                if keyword.lower() in text.lower():
                    self.keyword_counter[keyword] += 1
                    
                    # 발신자 정보
                    sender_name = "알 수 없음"
                    if sender.get("@type") == "messageSenderUser":
                        user_id = sender.get("user_id")
                        sender_name = self.get_user_name(user_id)
                    
                    # 채팅방 이름
                    chat_name = self.get_chat_name(chat_id)
                    
                    print(f"🔍 키워드 '{keyword}' 발견!")
                    print(f"   채팅방: {chat_name}")
                    print(f"   발신자: {sender_name}")
                    print(f"   메시지: {text}")
                    print(f"   현재 카운트: {self.keyword_counter[keyword]}")
                    print("-" * 50)
    
    def handle_update(self, result):
        """업데이트 처리"""
        if result.get("@type") == "updateNewMessage":
            self.process_message(result.get("message", {}))
            
        elif result.get("@type") == "chat":
            chat = result
            chat_id = chat.get("id")
            title = chat.get("title", "")
            if title:
                self.chat_names[chat_id] = title
                
        elif result.get("@type") == "user":
            user = result
            user_id = user.get("id")
            first_name = user.get("first_name", "")
            last_name = user.get("last_name", "")
            full_name = f"{first_name} {last_name}".strip()
            if full_name:
                self.user_names[user_id] = full_name
    
    def start_monitoring(self):
        """키워드 모니터링 시작"""
        print(f"추적할 키워드: {self.target_keywords}")
        print("키워드 모니터링을 시작합니다...")
        print("종료하려면 Ctrl+C를 누르세요.")
        print("=" * 60)
        
        try:
            while True:
                result = self.client.receive()
                if result:
                    self.handle_update(result)
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            self.show_final_results()
    
    def show_final_results(self):
        """최종 결과 출력"""
        print("\n\n📊 최종 키워드 카운터 결과:")
        print("=" * 60)
        if self.keyword_counter:
            for keyword, count in sorted(self.keyword_counter.items(), key=lambda x: x[1], reverse=True):
                print(f"'{keyword}': {count}회")
        else:
            print("발견된 키워드가 없습니다.")
        print("=" * 60)
        print("프로그램을 종료합니다.")
    
    def cleanup(self):
        """정리 작업"""
        if self.client:
            self.client.destroy()

def main():
    print("=== TDLib Python 키워드 카운터 ===")
    print("텔레그램 API 자격증명이 필요합니다.")
    print("https://my.telegram.org 에서 api_id와 api_hash를 발급받으세요.")
    
    counter = KeywordCounter()
    
    try:
        if counter.setup_client():
            counter.start_monitoring()
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        counter.cleanup()

if __name__ == "__main__":
    main() 