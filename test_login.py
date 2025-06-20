import os
import sys
import time
sys.path.insert(0, os.path.abspath('.'))
import tdjson

print("=== TDLib 로그인 상태 확인 ===")

# API 자격증명
api_id = 20726186
api_hash = "7d5e8f24ee48a20a50ff864cd611d5d7"

client = tdjson.create()

# TDLib 파라미터 설정
print("Setting TDLib parameters...")
client.send({
    "@type": "setTdlibParameters",
    "database_directory": "tdlib-db",
    "use_message_database": True,
    "use_secret_chats": False,
    "api_id": api_id,
    "api_hash": api_hash,
    "system_language_code": "ko",
    "device_model": "macOS",
    "application_version": "1.0",
    "enable_storage_optimizer": True,
    "use_test_dc": False
})

# 응답 확인
print("Checking authorization state...")
timeout = 0
while timeout < 10:  # 10초 대기
    result = client.receive()
    if result:
        print(f"Received: {result}")
        
        if result.get("@type") == "updateAuthorizationState":
            state = result["authorization_state"]["@type"]
            print(f"Authorization state: {state}")
            
            if state == "authorizationStateReady":
                print("✅ 로그인 성공! 사용자 정보를 가져오는 중...")
                
                # 사용자 정보 가져오기
                client.send({"@type": "getMe"})
                
                # 응답 대기
                user_result = client.receive()
                if user_result:
                    print(f"User info: {user_result}")
                
                break
                
            elif state == "authorizationStateWaitPhoneNumber":
                print("❌ 전화번호 인증이 필요합니다.")
                break
                
            elif state == "authorizationStateWaitCode":
                print("❌ 인증 코드가 필요합니다.")
                break
                
            elif state == "authorizationStateClosed":
                print("❌ 인증이 실패했습니다.")
                break
    
    time.sleep(0.1)
    timeout += 0.1

if timeout >= 10:
    print("❌ 타임아웃: 응답을 받지 못했습니다.")

client.destroy() 