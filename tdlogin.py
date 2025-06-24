import os
import sys
import time
import json
from collections import defaultdict
sys.path.insert(0, os.path.abspath('.'))
import tdjson

print("=== TDLib Python 키워드 카운터 ===")
print("텔레그램 API 자격증명이 필요합니다.")
print("https://my.telegram.org 에서 api_id와 api_hash를 발급받으세요.")

# 환경변수에서 API 자격증명을 읽어옵니다
# api_id = os.getenv('TELEGRAM_API_ID')
# api_hash = os.getenv('TELEGRAM_API_HASH')
# phone_number = os.getenv('TELEGRAM_PHONE_NUMBER')
api_id = 1
api_hash = '1'
phone_number = '+1'

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

# 키워드 카운터 초기화
keyword_counter = defaultdict(int)
target_keywords = ['안녕', 'hello', '테스트', 'test']  # 추적할 키워드들

print(f"추적할 키워드: {target_keywords}")

client = tdjson.create()

# TDLib 로그 레벨을 ERROR로 설정하여 불필요한 로그를 줄입니다
client.send({
    "@type": "setLogVerbosityLevel",
    "new_verbosity_level": 1  # 0=FATAL, 1=ERROR, 2=WARNING, 3=INFO, 4=DEBUG, 5=VERBOSE
})

# 먼저 TDLib 파라미터를 설정
print("📱 TDLib 초기화 중...")
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
print("🔐 인증 상태를 확인하는 중...")
authorized = False

while True:
    result = client.receive()
    if result:
        result_type = result.get("@type")
        
        # 중요한 메시지만 표시 - 불필요한 업데이트는 필터링
        if result_type == "updateAuthorizationState":
            state = result["authorization_state"]["@type"]
            
            if state == "authorizationStateWaitTdlibParameters":
                # 이미 파라미터를 설정했으므로 다음 상태로 넘어갈 것
                continue
                
            elif state == "authorizationStateWaitPhoneNumber":
                print("📞 전화번호 인증 중...")
                client.send({"@type": "setAuthenticationPhoneNumber", "phone_number": phone_number})
                
            elif state == "authorizationStateWaitCode":
                code = input("📱 인증 코드를 입력하세요: ")
                client.send({"@type": "checkAuthenticationCode", "code": code})
                
            elif state == "authorizationStateReady":
                print("✅ 로그인 성공!")
                authorized = True
                break
                
            elif state == "authorizationStateClosed":
                print("❌ 인증 실패")
                break
                
        elif result_type == "error":
            error_message = result.get("message", "")
            if "setTdlibParameters" in error_message:
                # TDLib parameters already set 에러는 무시
                continue
            else:
                print(f"❌ 오류 발생: {error_message}")
                break
        
        # 다른 업데이트들은 로그로 표시하지 않음 (무음 처리)
    
    time.sleep(0.1)

if authorized:
    print("\n🔍 키워드 모니터링을 시작합니다...")
    print("📝 추적 중인 키워드:", ', '.join(target_keywords))
    print("⏹️  종료하려면 Ctrl+C를 누르세요.\n")
    
    # 불필요한 업데이트 타입들 (필터링할 항목들)
    filtered_updates = {
        'updateOption', 'updateConnectionState', 'updateFile', 
        'updateFileProgress', 'updateChatPosition', 'updateChatLastMessage',
        'updateChatReadInbox', 'updateChatReadOutbox', 'updateChatOnlineMemberCount',
        'updateUserStatus', 'updateChatDraftMessage', 'updateChatNotificationSettings',
        'updateScopeNotificationSettings', 'updateChatActionBar', 'updateMessageSendSucceeded',
        'updateMessageContent', 'updateDeleteMessages', 'updateChatAction',
        'updateChatAvailableReactions', 'updateChatPermissions', 'updateSupergroupFullInfo',
        'updateBasicGroupFullInfo', 'updateUserFullInfo', 'updateSecretChat',
        'updateChatTitle', 'updateChatPhoto', 'updateChatAccentColors',
        'updateChatBackground', 'updateChatTheme', 'updateChatUnreadMentionCount',
        'updateChatUnreadReactionCount', 'updateChatVideoChat', 'updateChatDefaultDisableNotification',
        'updateChatHasProtectedContent', 'updateChatIsTranslatable', 'updateChatIsMarkedAsUnread',
        'updateChatHasScheduledMessages', 'updateForumTopicInfo'
    }
    
    try:
        while True:
            result = client.receive()
            if result:
                result_type = result.get("@type")
                
                # 새 메시지 업데이트 처리
                if result_type == "updateNewMessage":
                    message = result.get("message", {})
                    chat_id = message.get("chat_id")
                    content = message.get("content", {})
                    
                    # 텍스트 메시지인지 확인
                    if content.get("@type") == "messageText":
                        # TDLib에서 text는 formattedText 객체입니다
                        formatted_text = content.get("text", {})
                        if isinstance(formatted_text, dict):
                            text = formatted_text.get("text", "")
                        else:
                            text = str(formatted_text) if formatted_text else ""
                        
                        # 텍스트가 있는 경우에만 키워드 검사
                        if text and isinstance(text, str):
                            # 키워드 검사
                            for keyword in target_keywords:
                                if isinstance(keyword, str) and keyword.lower() in text.lower():
                                    keyword_counter[keyword] += 1
                                    print(f"🎯 키워드 '{keyword}' 발견!")
                                    print(f"   📍 채팅방 ID: {chat_id}")
                                    print(f"   💬 메시지: {text[:100]}{'...' if len(text) > 100 else ''}")
                                    print(f"   📊 현재 카운트: {keyword_counter[keyword]}")
                                    print("─" * 60)
                
                # 에러 처리 (중요한 에러만 표시)
                elif result_type == "error":
                    error_code = result.get("code", 0)
                    error_message = result.get("message", "")
                    # 중요한 에러만 표시 (코드 400 이상)
                    if error_code >= 400:
                        print(f"❌ 오류 발생 (코드 {error_code}): {error_message}")
                
                # 필터링된 업데이트들은 무시 (로그로 표시하지 않음)
                elif result_type in filtered_updates:
                    continue
                
                # 기타 중요하지 않은 업데이트들도 무시
                # (user, chat, supergroup 등의 정보성 업데이트들)
                
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\n📊 최종 키워드 카운터 결과:")
        print("═" * 60)
        if keyword_counter:
            for keyword, count in keyword_counter.items():
                print(f"🔤 '{keyword}': {count}회 발견")
        else:
            print("📭 발견된 키워드가 없습니다.")
        print("═" * 60)
        print("✅ 프로그램을 종료합니다.")

client.destroy()
