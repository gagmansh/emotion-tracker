# Emotion Tracker

Firebase Auth와 Firestore에 직접 연결되는 감정 기록 웹앱입니다.  
이제 백엔드 없이 `web/` 폴더만 Cloudflare Pages에 올려서 공개할 수 있습니다.

## 현재 구조

```text
emotion_tracker/
├─ web/
│  ├─ index.html
│  ├─ styles.css
│  ├─ app.js
│  ├─ config.js
│  ├─ config.example.js
│  └─ _headers
├─ firestore.rules
├─ run_frontend.bat
├─ run_stack.bat
├─ hq_logic.py
├─ analytics.py
└─ backend/   # 예전 API 실험용 코드, 현재 공개 배포에는 필수 아님
```

## 이 버전에서 바뀐 점

- 프론트엔드가 FastAPI를 거치지 않고 Firebase에 직접 연결됩니다.
- Firebase Authentication의 익명 로그인으로 사용자별 데이터가 분리됩니다.
- 감정 저장, HQ 계산, 최빈 감정 계산, 시간대별 HQ 변화, 요일별 HQ 변화가 브라우저에서 바로 처리됩니다.
- Cloudflare Pages에 `web/` 폴더만 배포하면 됩니다.

## 1. Firebase에서 먼저 해야 할 것

이 프로젝트는 `Firebase Web App 설정값`이 필요합니다.  
서비스 계정 JSON이 아니라, 웹앱용 공개 설정값입니다.

### 1-1. Firebase 프로젝트 준비

1. Firebase Console에 들어갑니다.
2. 이미 만든 프로젝트를 선택합니다.
3. 아직 Firestore를 안 켰다면 `Build -> Firestore Database -> Create database`로 생성합니다.

공식 문서:
- Firebase 웹 설정: https://firebase.google.com/docs/web/setup
- Firestore 시작: https://firebase.google.com/docs/firestore

### 1-2. 웹 앱 등록

1. Firebase Console에서 프로젝트를 엽니다.
2. 상단의 `프로젝트 개요` 화면에서 `웹 아이콘(</>)`을 누릅니다.
3. 앱 닉네임을 입력합니다.
4. `앱 등록`을 누릅니다.
5. 화면에 보이는 `firebaseConfig` 값을 복사합니다.

복사해야 하는 값은 보통 이 다섯 가지입니다.

```js
const firebaseConfig = {
  apiKey: "...",
  authDomain: "...",
  projectId: "...",
  appId: "...",
  messagingSenderId: "...",
};
```

주의:
- 이 값들은 웹앱 설정값이라 브라우저에 들어가도 됩니다.
- 비밀값은 아닙니다.
- 대신 접근 제어는 `Authentication + Firestore Rules`로 막아야 합니다.

참고:
- Firebase 프로젝트 API 키 설명: https://firebase.google.com/docs/projects/api-keys

### 1-3. 익명 로그인 활성화

이 앱은 각 사용자를 익명 계정으로 자동 로그인시켜서 데이터를 분리합니다.

1. Firebase Console -> `Build -> Authentication`
2. `Get started`
3. `Sign-in method`
4. `Anonymous` 활성화
5. 저장

공식 문서:
- 익명 로그인: https://firebase.google.com/docs/auth/web/anonymous-auth

## 2. 프로젝트 파일에 Firebase 설정 넣기

파일:
[web/config.js](C:/Users/prist/OneDrive/바탕%20화면/emotion_tracker/web/config.js)

현재 기본값은 비어 있습니다. 아래처럼 채우세요.

```js
window.EMOTION_TRACKER_CONFIG = {
  firebase: {
    apiKey: "YOUR_PUBLIC_API_KEY",
    authDomain: "your-project-id.firebaseapp.com",
    projectId: "your-project-id",
    appId: "1:1234567890:web:abcdef123456",
    messagingSenderId: "1234567890",
  },
  app: {
    collectionName: "emotion_records",
  },
};
```

예시 파일은 여기 있습니다.
[web/config.example.js](C:/Users/prist/OneDrive/바탕%20화면/emotion_tracker/web/config.example.js)

## 3. Firestore 보안 규칙 적용

파일:
[firestore.rules](C:/Users/prist/OneDrive/바탕%20화면/emotion_tracker/firestore.rules)

이 규칙은 다음을 보장합니다.

- 로그인한 사용자만 자기 데이터에 접근 가능
- `users/{uid}` 문서는 자기 것만 읽고 쓸 수 있음
- `users/{uid}/emotion_records/*`도 자기 것만 생성 가능
- 기록 필드 형식과 길이를 제한

### 3-1. 가장 쉬운 적용 방법

1. Firebase Console -> `Build -> Firestore Database`
2. `Rules` 탭
3. 현재 내용을 전부 지우고 `firestore.rules` 내용으로 교체
4. `Publish`

### 3-2. 데이터 구조

이 앱은 Firestore에 이렇게 저장합니다.

```text
users/{uid}
users/{uid}/emotion_records/{recordId}
```

`users/{uid}` 문서:
- 현재 HQ
- 누적 기록 수
- 마지막 감정

`users/{uid}/emotion_records/{recordId}` 문서:
- emotion
- emotionScore
- intensity
- note
- hqPrevious
- hqCurrent
- deltaHq
- adjustmentFactor
- recordedAt

## 4. 로컬에서 실행하기

이 앱은 정적 웹앱입니다.  
로컬 테스트는 간단한 HTTP 서버만 있으면 됩니다.

### 방법 1. 배치 파일 실행

```powershell
.\run_frontend.bat
```

또는

```powershell
.\run_stack.bat
```

주소:

```text
http://127.0.0.1:5500
```

### 방법 2. 직접 실행

```powershell
python -m http.server 5500 --bind 127.0.0.1 --directory web
```

## 5. Cloudflare Pages로 배포하기

이제는 백엔드가 없으므로 Cloudflare Pages만 있으면 됩니다.

공식 문서:
- Cloudflare Pages 시작: https://developers.cloudflare.com/pages/get-started/guide/
- 커스텀 도메인: https://developers.cloudflare.com/pages/configuration/custom-domains/

### 5-1. GitHub에 코드 올리기

현재 저장소를 GitHub에 푸시합니다.

### 5-2. Cloudflare Pages 프로젝트 만들기

1. Cloudflare Dashboard 로그인
2. `Workers & Pages`
3. `Create application`
4. `Pages`
5. `Connect to Git`
6. GitHub 저장소 선택

### 5-3. 빌드 설정

이 프로젝트는 빌드가 필요 없는 정적 사이트입니다.

- Framework preset: `None`
- Build command: 비워둠
- Build output directory: `web`

### 5-4. 배포 후 확인

배포가 끝나면 Cloudflare가 `https://something.pages.dev` 주소를 줍니다.  
그 주소로 접속해서 아래를 확인하세요.

- 익명 로그인 자동 완료
- 감정 저장 버튼 동작
- Firestore에 실제 기록 생성
- 대시보드 그래프와 최근 기록 반영

## 6. 도메인 연결

1. Cloudflare Pages 프로젝트 화면으로 이동
2. `Custom domains`
3. 원하는 도메인 추가
4. 안내에 따라 DNS 연결

예시:

```text
https://mood.yourdomain.com
```

## 7. 현재 프론트에서 하는 일

파일:
[web/app.js](C:/Users/prist/OneDrive/바탕%20화면/emotion_tracker/web/app.js)

여기서 처리하는 기능:

- Firebase 초기화
- 익명 로그인
- Firestore 실시간 구독
- 감정 저장 트랜잭션
- HQ 계산
- 최빈 감정 계산
- 시간대별 HQ 평균
- 요일별 HQ 평균

## 8. HQ 계산식

현재 HQ 로직은 Python 버전과 맞춰져 있습니다.

```text
delta_hq = emotion_score * (intensity / 15)
adjustment_factor = 1 - abs(hq_previous - 50) / 100
adjusted_delta = delta_hq * adjustment_factor
hq_current = clamp(hq_previous + adjusted_delta, 0, 100)
```

기준 점수:

- 행복: `9.0`
- 평온: `0.0`
- 슬픔: `-7.5`
- 불안: `-6.5`
- 분노: `-9.0`

## 9. 트러블슈팅

### 페이지는 열리는데 상단에 설정 필요가 뜬다

원인:
- [web/config.js](C:/Users/prist/OneDrive/바탕%20화면/emotion_tracker/web/config.js)가 비어 있음

해결:
- Firebase Console에서 웹앱 설정값을 다시 복사해서 넣습니다.

### 저장 버튼을 눌렀는데 권한 오류가 난다

원인:
- Firestore Rules가 적용되지 않았거나
- Anonymous Auth가 꺼져 있음

해결:
1. Authentication에서 Anonymous 활성화 확인
2. Firestore Rules 탭에 [firestore.rules](C:/Users/prist/OneDrive/바탕%20화면/emotion_tracker/firestore.rules) 적용

### Cloudflare Pages에 올렸는데 저장이 안 된다

원인:
- Firebase 설정값 누락
- Firestore Rules 미적용
- 브라우저 콘솔 에러 존재

해결:
1. `web/config.js` 값 확인
2. Rules 확인
3. 브라우저 개발자도구 콘솔 확인

## 10. 다음에 확장할 수 있는 것

- Google 로그인 추가
- 감정 종류 커스터마이징
- App Check 추가
- 주간/월간 리포트 카드 추가
- PWA 오프라인 지원
