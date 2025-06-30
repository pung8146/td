import os
import sys
import time
import json
from datetime import datetime
from collections import defaultdict
sys.path.insert(0, os.path.abspath('.'))
import tdjson

print("=== TDLib Python 키워드 카운터 (향상된 버전) ===")
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

# 키워드 카운터 및 캐시 초기화
keyword_counter = defaultdict(int)
target_keywords = ['안녕', 'hello', '테스트', 'test']  # 추적할 키워드들
user_cache = {}  # 사용자 정보 캐시
chat_cache = {}  # 채팅방 정보 캐시

print(f"추적할 키워드: {target_keywords}")

client = tdjson.create()

# TDLib 로그 레벨을 ERROR로 설정하여 불필요한 로그를 줄입니다
client.send({
    "@type": "setLogVerbosityLevel",
    "new_verbosity_level": 1  # 0=FATAL, 1=ERROR, 2=WARNING, 3=INFO, 4=DEBUG, 5=VERBOSE
})

def get_user_info(user_id):
    """사용자 정보 요청"""
    if user_id not in user_cache:
        client.send({
            "@type": "getUser",
            "user_id": user_id
        })
        return None
    return user_cache[user_id]

def get_chat_info(chat_id):
    """채팅방 정보 요청"""
    if chat_id not in chat_cache:
        client.send({
            "@type": "getChat",
            "chat_id": chat_id
        })
        return None
    return chat_cache[chat_id]

def format_timestamp(timestamp):
    """타임스탬프를 읽기 쉬운 형태로 변환"""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def get_sender_info(sender_id):
    """발신자 정보 반환"""
    if not sender_id:
        return "알 수 없음", "unknown"
    
    sender_type = sender_id.get("@type")
    if sender_type == "messageSenderUser":
        user_id = sender_id.get("user_id")
        user_info = get_user_info(user_id)
        if user_info:
            first_name = user_info.get("first_name", "")
            last_name = user_info.get("last_name", "")
            username = user_info.get("usernames", {}).get("editable_username", "")
            full_name = f"{first_name} {last_name}".strip()
            if username:
                return f"{full_name} (@{username})", f"user_{user_id}"
            return full_name or f"사용자_{user_id}", f"user_{user_id}"
        return f"사용자_{user_id}", f"user_{user_id}"
    
    elif sender_type == "messageSenderChat":
        chat_id = sender_id.get("chat_id")
        chat_info = get_chat_info(chat_id)
        if chat_info:
            chat_title = chat_info.get("title", "")
            chat_username = chat_info.get("usernames", {}).get("editable_username", "")
            if chat_username:
                return f"{chat_title} (@{chat_username})", f"chat_{chat_id}"
            return chat_title or f"채팅_{chat_id}", f"chat_{chat_id}"
        return f"채팅_{chat_id}", f"chat_{chat_id}"
    
    return "알 수 없음", "unknown"

def get_chat_name(chat_id):
    """채팅방 이름 반환"""
    chat_info = get_chat_info(chat_id)
    if chat_info:
        chat_title = chat_info.get("title", "")
        chat_username = chat_info.get("usernames", {}).get("editable_username", "")
        chat_type = chat_info.get("type", {}).get("@type", "")
        
        type_emoji = {
            "chatTypePrivate": "👤",
            "chatTypeBasicGroup": "👥",
            "chatTypeSupergroup": "🏢" if chat_info.get("type", {}).get("is_channel", False) else "👥",
            "chatTypeSecret": "🔒"
        }.get(chat_type, "💬")
        
        if chat_username:
            return f"{type_emoji} {chat_title} (@{chat_username})"
        return f"{type_emoji} {chat_title}"
    return f"💬 채팅_{chat_id}"

def display_message_details(message, keyword, text):
    """키워드 발견 시 자세한 메시지 정보 표시"""
    keyword_counter[keyword] += 1
    
    # 기본 정보
    chat_id = message.get("chat_id")
    message_id = message.get("id")
    date = message.get("date", 0)
    sender_id = message.get("sender_id")
    
    # 메시지 메타데이터
    is_outgoing = message.get("is_outgoing", False)
    is_channel_post = message.get("is_channel_post", False)
    is_pinned = message.get("is_pinned", False)
    edit_date = message.get("edit_date", 0)
    
    # 전달 정보
    forward_info = message.get("forward_info")
    
    # 답글 정보
    reply_to = message.get("reply_to")
    
    # 상호작용 정보
    interaction_info = message.get("interaction_info", {})
    view_count = interaction_info.get("view_count", 0)
    forward_count = interaction_info.get("forward_count", 0)
    
    # 발신자 및 채팅방 정보
    sender_name, sender_id_str = get_sender_info(sender_id)
    chat_name = get_chat_name(chat_id)
    
    print(f"\n{'='*80}")
    print(f"🎯 키워드 '{keyword}' 발견! (총 {keyword_counter[keyword]}회)")
    print(f"{'='*80}")
    
    # 채팅방 정보
    print(f"📍 채팅방: {chat_name}")
    print(f"   ├─ 채팅방 ID: {chat_id}")
    
    # 발신자 정보
    print(f"👤 발신자: {sender_name}")
    print(f"   ├─ 발신자 ID: {sender_id_str}")
    print(f"   ├─ 내가 보낸 메시지: {'예' if is_outgoing else '아니오'}")
    
    # 메시지 정보
    print(f"💬 메시지 정보:")
    print(f"   ├─ 메시지 ID: {message_id}")
    print(f"   ├─ 전송 시간: {format_timestamp(date)}")
    if edit_date > 0:
        print(f"   ├─ 수정 시간: {format_timestamp(edit_date)}")
    print(f"   ├─ 채널 포스트: {'예' if is_channel_post else '아니오'}")
    if is_pinned:
        print(f"   ├─ 고정된 메시지: 예")
    
    # 조회수 정보 (채널의 경우)
    if view_count > 0:
        print(f"   ├─ 조회수: {view_count:,}")
    if forward_count > 0:
        print(f"   ├─ 전달수: {forward_count:,}")
    
    # 전달 정보
    if forward_info:
        origin = forward_info.get("origin", {})
        origin_type = origin.get("@type", "")
        if origin_type == "messageOriginUser":
            origin_user_id = origin.get("sender_user_id")
            origin_user = get_user_info(origin_user_id)
            if origin_user:
                origin_name = f"{origin_user.get('first_name', '')} {origin_user.get('last_name', '')}".strip()
                print(f"   ├─ 전달됨: {origin_name}에서")
        elif origin_type == "messageOriginChannel":
            origin_chat_id = origin.get("chat_id")
            origin_chat = get_chat_info(origin_chat_id)
            if origin_chat:
                print(f"   ├─ 전달됨: {origin_chat.get('title', '')}에서")
    
    # 답글 정보
    if reply_to:
        reply_type = reply_to.get("@type", "")
        if reply_type == "messageReplyToMessage":
            reply_message_id = reply_to.get("message_id")
            print(f"   ├─ 답글: 메시지 {reply_message_id}에 대한 답글")
    
    # 메시지 내용
    print(f"📝 메시지 내용:")
    print(f"   └─ {text}")
    
    # 추가 정보 표시 가능 항목들
    print(f"\n💡 추가 가능한 정보:")
    print(f"   • 사용자 프로필 정보 (사진, 바이오, 상태 등)")
    print(f"   • 채팅방 멤버 수 및 관리자 정보")
    print(f"   • 메시지 반응 (리액션) 정보")
    print(f"   • 미디어 파일 정보 (사진, 동영상 등)")
    print(f"   • 봇을 통해 전송된 경우 봇 정보")
    print(f"   • 메시지 권한 정보 (편집/삭제/전달 가능 여부)")

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
        
        # 사용자 정보 캐시 업데이트
        if result_type == "user":
            user_id = result.get("id")
            user_cache[user_id] = result
            continue
            
        # 채팅방 정보 캐시 업데이트  
        elif result_type == "chat":
            chat_id = result.get("id")
            chat_cache[chat_id] = result
            continue
        
        # 중요한 메시지만 표시 - 불필요한 업데이트는 필터링
        elif result_type == "updateAuthorizationState":
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
    print("\n🔍 향상된 키워드 모니터링을 시작합니다...")
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
                
                # 사용자 정보 캐시 업데이트
                if result_type == "user":
                    user_id = result.get("id")
                    user_cache[user_id] = result
                    continue
                    
                # 채팅방 정보 캐시 업데이트  
                elif result_type == "chat":
                    chat_id = result.get("id")
                    chat_cache[chat_id] = result
                    continue
                
                # 새 메시지 업데이트 처리
                elif result_type == "updateNewMessage":
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
                                    display_message_details(message, keyword, text)
                                    print("─" * 80)
                
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
        print("═" * 80)
        if keyword_counter:
            for keyword, count in keyword_counter.items():
                print(f"🔤 '{keyword}': {count}회 발견")
        else:
            print("📭 발견된 키워드가 없습니다.")
        print("═" * 80)
        print("✅ 프로그램을 종료합니다.")

client.destroy()
