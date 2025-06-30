# TDLib 기반 텔레그램 키워드 모니터링 스크립트 개요

### 텔레그램 api 공식 문서

https://core.telegram.org/api

### 텔레그램 api 등록하는 방법

1. https://my.telegram.org/ 에 접속
2. Your Phone Number에 전화번호 입력 ex) 010-1234-5678 => +821012345678 형태로 입력후 인증
3. API development tools 메뉴 접속
4. API ID와 API Hash를 발급받음 (App title , Short name 임의로 작성하면됩니다.)
5. 발급받은 API ID와 API Hash를 .env 파일에 저장
6. 텔레그램 앱에서 로그인 후 키워드 모니터링 스크립트 실행

### tdlib 공식 문서

https://core.telegram.org/tdlib(공식 문서)
https://github.com/tdlib/td(소스코드)

## 1. 프로젝트 목적

텔레그램 채팅방(개인 대화, 그룹, 슈퍼그룹 포함)에서 **사용자가 미리 정의한 키워드가 얼마나 언급되었는지**를 자동으로 집계·파악하기 위한 도구입니다. 실시간 감지뿐 아니라 통계 기반 분석(빈도, 채팅방별ㆍ기간별 트렌드)까지 확장할 수 있도록 설계되었습니다.

## 2. 요구 사항 도출

| 요구 사항      | 설명                                                            |
| -------------- | --------------------------------------------------------------- |
| 실시간 감지    | 메시지 수신과 동시에 키워드 포함 여부를 판단해야 함             |
| 전체 채팅 범위 | 봇 권한과 무관하게 **내가 참여 중인 모든 방**을 모니터링해야 함 |
| 세션 유지      | 한 번 로그인 후 재실행 시 2차 인증 없이 자동 로그인             |
| 성능           | 키워드가 많아도 메시지 유실 없이 카운트 가능해야 함             |
| 보안           | API 자격증명 및 세션 데이터는 로컬에 안전하게 저장              |

## 3. 기술 스택 선정 이유 및 TDLib 선정 배경

### TDLib (Telegram Database Library)

공식 지원 및 오픈소스
텔레그램 팀이 직접 관리하며, Boost License 1.0 하에 상업 및 개인 프로젝트에 자유롭게 사용 가능

고성능 멀티스레드 구조
네트워킹, 암호화, 스토리지 작업을 내부에서 비동기로 분산 처리하여 대규모 메시지 수신 시에도 손실 없음

로우레벨 MTProto 추상화
시퀀스 번호, 데이터센터 라우팅, 재전송 로직을 자동 처리하여 개발 복잡도를 크게 감소시킴

크로스플랫폼 지원
Linux, macOS, Windows, Android, iOS에서 동일한 API 제공
→ 모바일과 서버 간 통합 전략에 유리

내 계정 기반 접근
Bot API처럼 제한 없이 내가 참여한 모든 채팅방의 메시지에 접근 가능

활발한 커뮤니티 및 지속적인 업데이트
Telegram Layer 업데이트와 기능 추가가 빠르게 이루어져 장기 유지보수에 안정적

### Python 3 + tdjson 래퍼

빠른 프로토타이핑과 비동기 생태계 활용 가능 (asyncio, rich, typer 등)

tdjson.py를 통해 별도의 C 바인딩 없이 TDLib 호출 가능

FastAPI, Flask 등과 손쉽게 통합 가능

### 가상환경 (venv) 및 dotenv

시스템 파이썬과 분리되어 의존성 충돌 방지

민감 정보를 .env로 관리하여 보안성 강화

## 4. 아키텍처 및 동작 흐름 아키텍처 및 동작 흐름

1. **초기화 단계**

   1. 환경변수 로드 → `api_id` `api_hash` `phone_number` 확보
   2. `setTdlibParameters` → TDLib 내부 데이터베이스 디렉토리 지정
   3. `checkDatabaseEncryptionKey` → (선택) 로컬 DB 암호화 키 설정

2. **인증 단계**

   1. `setAuthenticationPhoneNumber` 전송
   2. `authorizationStateWaitCode` 이벤트 수신 시, 터미널에 2FA 코드 입력
   3. 인증 성공 후 `authorizationStateReady` → 세션 파일 저장

3. **메시지 수신 루프**

   1. `updateNewMessage` 이벤트 스트림 수신
   2. 메시지 텍스트에서 **키워드 목록**과 정규식 매칭
   3. 매칭 시 → 카운터 객체(`dict[chat_id][keyword]`) 갱신 + 콘솔 로그 출력

4. **종료 및 요약 보고**

   - `Ctrl+C` 신호 감지 시, 카운트 결과를 테이블 형태로 요약 출력 후 종료

## 5. 설치 및 실행 절차

### 5.1 TDLib 빌드 (macOS 예시)

```bash
brew install cmake gperf openssl zlib
# TDLib 소스 다운로드
git clone https://github.com/tdlib/td.git
cd td && mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=../tdlib ..
cmake --build . --target install
```

### 5.2 프로젝트 구조 제안

```text
keyword-monitor/
├─ tdlib/                 # 빌드된 lib & include
├─ tdjson.py              # TDLib Python 래퍼 (예제 파일 리네임)
├─ monitor.py             # 메인 모니터 스크립트
├─ .env                   # API 자격증명 및 키워드 설정
└─ requirements.txt       # python-dotenv, rich 등
```

### 5.3 가상환경 및 의존성 설치

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5.4 환경변수(.env) 예시

```env
TELEGRAM_API_ID=1234567
TELEGRAM_API_HASH=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
TELEGRAM_PHONE_NUMBER=+821012345678
TARGET_KEYWORDS=중요,긴급,회의,공지
```

### 5.5 스크립트 실행 & 사용법

```bash
python monitor.py            # 최초 실행 → 인증 코드 입력
python monitor.py --once     # (옵션) 실시간 대신 최근 100개 메시지 스캔 후 종료
python monitor.py --export report.csv   # (옵션) 통계 결과 CSV 저장
```

옵션은 `monitor.py` 내부 `argparse` 예제 로직을 통해 손쉽게 확장할 수 있습니다.
