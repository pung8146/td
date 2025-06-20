import os
import sys
import time
sys.path.insert(0, os.path.abspath('.'))
import tdjson

print("=== TDLib Python Login ===")
print("텔레그램 API 자격증명이 필요합니다.")
print("https://my.telegram.org 에서 api_id와 api_hash를 발급받으세요.")

# 환경변수에서 API 자격증명을 읽어옵니다
api_id = os.getenv('TELEGRAM_API_ID')
api_hash = os.getenv('TELEGRAM_API_HASH')
phone_number = os.getenv('TELEGRAM_PHONE_NUMBER')

# 환경변수가 설정되지 않은 경우 사용자에게 안내
if not api_id or not api_hash or not phone_number:
    print("❌ 환경변수가 설정되지 않았습니다.")
    print("다음 환경변수를 설정해주세요:")
    print("export TELEGRAM_API_ID='your_api_id'")
    print("export TELEGRAM_API_HASH='your_api_hash'")
    print("export TELEGRAM_PHONE_NUMBER='your_phone_number'")
    sys.exit(1)

# 문자열을 정수로 변환
api_id = int(api_id)

print(f"Using API ID: {api_id}")
print(f"Using Phone: {phone_number}")

client = tdjson.create()

# 먼저 TDLib 파라미터를 설정
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

# 응답을 기다린 후 다음 단계로 진행
print("Waiting for authorization state...")
while True:
    result = client.receive()
    if result:
        print(f"Received: {result}")
        
        if result.get("@type") == "updateAuthorizationState":
            state = result["authorization_state"]["@type"]
            print(f"Authorization state: {state}")
            
            if state == "authorizationStateWaitTdlibParameters":
                # 이미 파라미터를 설정했으므로 다음 상태로 넘어갈 것
                continue
                
            elif state == "authorizationStateWaitPhoneNumber":
                print("Phone number required. Sending phone number...")
                client.send({"@type": "setAuthenticationPhoneNumber", "phone_number": phone_number})
                
            elif state == "authorizationStateWaitCode":
                code = input("인증 코드를 입력하세요: ")
                client.send({"@type": "checkAuthenticationCode", "code": code})
                
            elif state == "authorizationStateReady":
                print("✅ 로그인 성공!")
                break
                
            elif state == "authorizationStateClosed":
                print("❌ 인증 실패")
                break
                
        elif result.get("@type") == "error":
            print(f"❌ Error: {result}")
            if "setTdlibParameters" in str(result):
                print("TDLib parameters already set, continuing...")
                continue
            break
    
    time.sleep(0.1)

client.destroy()
