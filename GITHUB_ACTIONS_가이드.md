# GitHub Actions로 KUJINO EXE 자동 빌드하기

> Windows PC가 없어도 GitHub의 무료 Windows VM에서 자동으로 EXE를 만들어줍니다.
> 한 번만 세팅하면 코드 수정할 때마다 자동으로 새 EXE가 빌드됩니다.

---

## 🎯 결과 미리보기

이 가이드 끝까지 따라 하면:
- ✅ GitHub에 KUJINO 저장소가 생김
- ✅ 코드 push할 때마다 자동으로 Windows EXE가 빌드됨
- ✅ Actions 탭에서 EXE 파일 다운로드 가능
- ✅ `v1.0` 같은 태그 만들면 GitHub Release 페이지까지 자동 생성

---

## 📋 준비물

- ✅ GitHub 계정 (없으면 https://github.com/signup 가입, 무료)
- ✅ 인터넷 브라우저 (크롬, 엣지 등)
- ❌ Python 설치 ❌ Windows ❌ 개발 도구 — **전부 필요 없음!**

---

## 🚀 1단계: GitHub 저장소 만들기

### 1-1. 새 저장소(Repository) 생성

1. https://github.com 접속, 로그인
2. 우측 상단 **`+` → `New repository`** 클릭
3. 다음과 같이 입력:
   - **Repository name**: `KUJINO` (원하는 이름)
   - **Public** 또는 **Private** 선택 (Private도 무료, Actions 월 2000분까지 무료)
   - 나머지는 기본값 그대로
4. 맨 아래 **`Create repository`** 클릭

---

## 📁 2단계: 파일 업로드 (드래그&드롭)

저장소가 생기면 파란 박스에 **"uploading an existing file"** 링크가 보입니다. 클릭!

### 2-1. 업로드할 파일/폴더 (제가 보내드린 KUJINO_github 폴더 안에 다 있어요)

```
KUJINO/
├── .github/
│   └── workflows/
│       └── build-exe.yml      ← ★ GitHub Actions 자동 빌드 설정
├── assets/
│   ├── logo.png
│   └── logo_small.png
├── sounds/
│   └── README.txt             ← (mp3 파일은 저작권 때문에 직접 넣기)
├── kujino_app.py              ← 메인 앱
├── build_exe.py
├── BUILD.bat                  ← (로컬 빌드용, 안 써도 됨)
├── .gitignore
└── README.md (선택)
```

### 2-2. 업로드 방법

**방법 A: 웹 브라우저에서 드래그&드롭 (가장 쉬움)**
1. 폴더 통째로 GitHub 업로드 페이지에 드래그
2. 자동으로 모든 파일 인식됨
3. 페이지 맨 아래 **`Commit changes`** 클릭

> ⚠️ 주의: GitHub 웹 업로드는 **숨겨진 폴더(`.github`)도 같이 업로드** 됩니다.
> 만약 안 올라가면, `.github/workflows/build-exe.yml` 파일 하나만 따로 다시 업로드하세요.

**방법 B: Git 명령어 (Git 설치되어 있으면)**
```bash
cd KUJINO_github
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/KUJINO.git
git push -u origin main
```

---

## ⚡ 3단계: 자동 빌드 확인

파일을 push하는 순간 **자동으로 빌드가 시작**됩니다!

### 3-1. 진행 상황 보기

1. GitHub 저장소 페이지 상단에서 **`Actions`** 탭 클릭
2. **"Build KUJINO EXE"** 워크플로우가 노란색 동그라미(진행중) 또는 초록 체크(완료)로 보임
3. 클릭하면 진행 상황을 실시간으로 볼 수 있음
4. 빌드 시간: **약 3~5분**

### 3-2. EXE 다운로드

빌드가 끝나면 (초록 체크 ✅):

1. 완료된 워크플로우 실행 클릭
2. 페이지 맨 아래 **`Artifacts`** 섹션
3. **`KUJINO-windows`** 클릭하면 ZIP 다운로드 시작
4. 압축 풀면 `KUJINO_windows.zip` → 또 풀면 → **`KUJINO.exe`** 등장!

> ⚠️ Artifact 다운로드는 **GitHub에 로그인된 상태**여야 가능합니다.

---

## 🏷️ 4단계 (선택): 정식 Release 만들기

매번 Artifact 들어가서 받기 번거롭다면, **태그(tag)**를 만들면 GitHub Release에 영구 보관됩니다.

### 4-1. 웹에서 태그 만들기 (가장 쉬움)

1. 저장소 페이지에서 **`Releases`** 클릭 (우측 사이드바)
2. **`Create a new release`** 또는 **`Draft a new release`**
3. **`Choose a tag`** → `v1.0` 입력 → **`Create new tag`**
4. **`Publish release`** 클릭

→ 자동으로 빌드가 다시 돌고, 끝나면 **Release 페이지에 KUJINO.exe와 ZIP이 첨부**됩니다.
→ 이 링크는 GitHub 로그인 없이도 누구나 받을 수 있어요. 다른 사람한테 EXE 공유할 때 편해요.

### 4-2. 명령어로 태그 만들기 (Git 설치된 경우)

```bash
git tag v1.0
git push origin v1.0
```

---

## 🔧 5단계 (선택): 수동 빌드

코드는 안 바꿨는데 그냥 한 번 더 빌드하고 싶을 때:

1. **Actions** 탭 → **Build KUJINO EXE** 워크플로우 선택
2. 우측의 **`Run workflow`** 버튼 클릭
3. **`Run workflow`** 한 번 더 클릭

---

## ❓ 자주 묻는 질문

### Q. 정말 무료인가요?
A. **Public 저장소**: 완전 무제한 무료
   **Private 저장소**: 월 2000분 무료 (한 번 빌드에 약 5분이니 월 400회 정도 가능)

### Q. 빌드가 빨간 X로 실패해요
A. Actions 탭에서 실패한 빌드 클릭 → 로그 펼쳐 보기
   가장 흔한 원인:
   - `assets/` 폴더가 누락 → 다시 업로드
   - `kujino_app.py` 파일명이 다름 → 정확히 맞추기
   - 라이브러리 버전 충돌 → 워크플로우 파일에 버전 고정 (도와드릴게요)

### Q. 사운드(mp3)는 어떻게 하나요?
A. 저작권 문제로 mp3는 GitHub에 올리지 마세요. 대신:
   1. EXE 다운로드 후 같은 폴더에 `sounds/` 폴더 만들기
   2. mp3 파일들 직접 넣기 (`bgm.mp3`, `win.mp3` 등)
   추천 무료 사운드: https://pixabay.com/sound-effects, https://freesound.org

### Q. 다른 사람이 EXE 받게 하고 싶어요
A. **방법 1**: Public 저장소 + Release 만들기 → 누구나 받기 가능
   **방법 2**: Artifact ZIP을 다운로드해서 다른 곳(구글 드라이브 등)에 업로드
   **방법 3**: 받을 사람한테 GitHub 협력자(Collaborator) 추가

### Q. 코드 수정하면 자동으로 다시 빌드되나요?
A. 네! `main` 브랜치에 push하면 자동으로 새 EXE가 빌드됩니다.

### Q. EXE에 Windows Defender가 경고를 띄워요
A. 코드 서명이 없는 모든 PyInstaller EXE의 정상 현상입니다.
   "추가 정보" → "실행" 클릭하면 됩니다.
   코드 서명 인증서는 연 10~30만원이라 개인 용도면 그냥 쓰세요.

---

## 🎬 정리: 한 번에 보기

```
1. GitHub 가입 → 새 저장소 생성
2. KUJINO_github 폴더 통째로 드래그&드롭 업로드
3. (자동) Actions에서 5분 안에 EXE 빌드 완료
4. Artifacts에서 KUJINO_windows.zip 다운로드
5. 압축 풀고 KUJINO.exe 더블클릭 → 끝! 🎉
```

막히는 부분 있으면 어느 단계인지, 어떤 메시지가 나오는지 알려주세요. 도와드릴게요!
