# SESSION NOTES

## 현재 방향

- 공개 서비스 구조는 `Cloudflare Pages + Firebase Auth + Firestore`
- 더 이상 FastAPI 백엔드 배포가 필수 아님
- `web/` 폴더만 정적 배포하면 됨
- 사용자 데이터는 익명 로그인 기준으로 Firestore에 분리 저장

## 핵심 파일

- [web/index.html](C:/Users/prist/OneDrive/바탕%20화면/emotion_tracker/web/index.html)
- [web/styles.css](C:/Users/prist/OneDrive/바탕%20화면/emotion_tracker/web/styles.css)
- [web/app.js](C:/Users/prist/OneDrive/바탕%20화면/emotion_tracker/web/app.js)
- [web/config.js](C:/Users/prist/OneDrive/바탕%20화면/emotion_tracker/web/config.js)
- [firestore.rules](C:/Users/prist/OneDrive/바탕%20화면/emotion_tracker/firestore.rules)
- [README.md](C:/Users/prist/OneDrive/바탕%20화면/emotion_tracker/README.md)

## 현재 동작 방식

1. 브라우저에서 Firebase 초기화
2. Firebase Auth 익명 로그인
3. `users/{uid}` 문서에 현재 HQ와 누적 기록 저장
4. `users/{uid}/emotion_records/{recordId}`에 감정 기록 저장
5. Firestore 실시간 구독으로 대시보드 즉시 갱신

## Firestore 구조

```text
users/{uid}
users/{uid}/emotion_records/{recordId}
```

## 사용자가 직접 해야 하는 것

1. Firebase Console에서 웹앱 등록
2. Firebase Web App 설정값을 [web/config.js](C:/Users/prist/OneDrive/바탕%20화면/emotion_tracker/web/config.js)에 입력
3. Anonymous Auth 활성화
4. [firestore.rules](C:/Users/prist/OneDrive/바탕%20화면/emotion_tracker/firestore.rules)를 Firestore Rules에 반영
5. `.\run_frontend.bat` 또는 `.\run_stack.bat`로 로컬 확인
6. Cloudflare Pages에 `web` 디렉터리 배포

## 로컬 실행 명령

```powershell
.\run_frontend.bat
```

또는

```powershell
python -m http.server 5500 --bind 127.0.0.1 --directory web
```

## 다음 세션에서 바로 붙일 프롬프트

```text
Read SESSION_NOTES.md first.
이 프로젝트는 지금 Cloudflare Pages + Firebase Auth + Firestore 구조다.
backend는 공개 배포 기준 필수 아님.
먼저 web/config.js, firestore.rules, README.md, web/app.js 상태부터 확인하고 이어서 작업해.
```
