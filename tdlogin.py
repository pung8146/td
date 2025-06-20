# tdlogin.py

import os
import tdjson
import time

# ✅ TDLib 빌드 후 생성된 .dylib 경로
TDJSON_PATH = os.path.abspath("../tdlib/lib/libtdjson.dylib")

# ✅ 자신의 api_id, api_hash 입력
API_ID = 1234567
API_HASH = "your_api_hash_here"

# ✅ 텔레그램에 등록된 전화번호
PHONE_NUMBER = "+821012345678"

client = tdjson.TdJson(lib_path=TDJSON_PATH)
client.execute({'@type': 'setLogVerbosityLevel', 'new_verbosity_level': 1})
client.execute({'@type': 'setTdlibParameters', 'parameters': {
    'database_directory': 'tdlib-db',
    'use_message_database': True,
    'use_secret_chats': False,
    'api_id': API_ID,
    'api_hash': API_HASH,
    'system_language_code': 'en',
    'device_model': 'iMac',
    'application_version': '0.1',
    'enable_storage_optimizer': True,
    'use_test_dc': False
}})
client.execute({'@type': 'checkDatabaseEncryptionKey', 'encryption_key': ''})

# 🔐 전화번호 제출
client.send({'@type': 'setAuthenticationPhoneNumber', 'phone_number': PHONE_NUMBER})

while True:
    r = client.receive()
    if r:
        print(r)

        if r.get('@type') == 'updateAuthorizationState':
            auth_state = r['authorization_state']['@type']

            if auth_state == 'authorizationStateWaitCode':
                code = input("Enter the code you received via Telegram: ")
                client.send({'@type': 'checkAuthenticationCode', 'code': code})

            elif auth_state == 'authorizationStateReady':
                print("✅ Logged in successfully!")
                break

    time.sleep(0.5)

client.close()
